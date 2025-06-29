# -*- coding: utf-8 -*-
"""Analisis Pola Trafik dan Keamanan Jaringan - RevanaFS.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1pDK8ps2mx0Vfbq__8vP73hNrAP8E3RV_
"""

from google.colab import drive      # Untuk menghubungkan Google Drive dengan Google Colab.
import matplotlib.pyplot as plt     # Untuk membuat visualisasi data seperti plot dan grafik.
import re                           # Untuk operasi ekspresi reguler (pencocokan pola teks).
from collections import Counter     # Untuk menghitung frekuensi item dalam sebuah koleksi.
import pandas as pd                 # Untuk manipulasi dan analisis data, terutama struktur DataFrame.

# Menghubungkan Google Drive ke direktori '/content/drive' di lingkungan Colab.
drive.mount('/content/drive')

# Mendefinisikan path lengkap menuju file CSV yang akan diakses di Google Drive.
file_path = '/content/drive/MyDrive/dataset/part-00000-79fa9d08-cdc2-480e-9edf-1349b798379c-c000.csv'

# Menentukan jumlah item teratas yang ingin ditampilkan dalam analisis.
N_TOP_ITEMS = 10

# Menentukan ukuran setiap bagian (chunk) data yang akan dibaca dari file besar.
CHUNKSIZE = 10**6

# Daftar nama kolom yang akan dipilih dan digunakan dari file CSV.
COLUMNS_TO_USE = ['url', 'domain', 'protocol']

# Daftar nama kolom yang akan diperiksa; jika ada nilai null (kosong) di salah satu kolom ini, seluruh baris akan dihapus.
COLUMNS_FOR_NULL_CHECK_AND_DROP = ['url', 'domain', 'protocol']

aggregated_null_counts_initial = Counter() # Inisialisasi Counter untuk mengakumulasi jumlah nilai null awal per kolom.
total_rows_initial = 0                     # Inisialisasi penghitung total baris awal.
processed_chunks_pass1 = 0                 # Inisialisasi penghitung jumlah chunk yang diproses pada tahap pertama.
observed_dtypes_pass1 = None               # Variabel untuk menyimpan tipe data yang terobservasi dari chunk pertama.

try:
    # Membaca file CSV per chunk, hanya kolom yang ditentukan, low_memory=False untuk konsistensi tipe data.
    file_iterator_pass1 = pd.read_csv(file_path, chunksize=CHUNKSIZE, usecols=COLUMNS_TO_USE, low_memory=False)

    # Iterasi melalui setiap chunk dalam file, menggunakan enumerate untuk mendapatkan indeks chunk (i).
    for i, chunk in enumerate(file_iterator_pass1):
        processed_chunks_pass1 += 1       # Tambah jumlah chunk yang diproses.
        total_rows_initial += len(chunk)  # Tambah jumlah total baris yang dibaca.

        if i == 0: # Jika ini adalah chunk pertama.
            observed_dtypes_pass1 = chunk.dtypes # Simpan tipe data dari kolom-kolom di chunk pertama.

        for col in COLUMNS_TO_USE:    # Iterasi melalui setiap kolom yang akan digunakan.
            if col in chunk.columns:  # Jika kolom ada dalam chunk saat ini.
                # Hitung jumlah nilai null di kolom tersebut dan tambahkan ke Counter.
                aggregated_null_counts_initial[col] += chunk[col].isnull().sum()

    del file_iterator_pass1 # Hapus iterator untuk membebaskan memori setelah selesai.
    print(f"Proses selesai. Total {processed_chunks_pass1} chunk diproses.") # Cetak konfirmasi.
except FileNotFoundError: # Jika file tidak ditemukan pada path yang diberikan.
    print(f"ERROR: File tidak ditemukan di path: {file_path} saat Pass 1.")
    print("Pastikan path file sudah benar. Program akan berhenti.")
    exit()
except Exception as e: # Jika terjadi error lain saat pemrosesan.
    print(f"ERROR: Terjadi kesalahan saat Pass 1: {e}")
    print("Program akan berhenti.")
    exit()

# Mencetak informasi total baris awal yang dibaca dari file.
print(f"\n1. Total Baris: {total_rows_initial}")

# Jika tipe data berhasil diobservasi dari chunk pertama.
if observed_dtypes_pass1 is not None:
    print("\n2. Tipe Data Kolom:")  # Judul bagian tipe data.
    print(observed_dtypes_pass1)    # Cetak tipe data per kolom.
else: # Jika tipe data tidak berhasil diobservasi.
    print("\n2. Tipe Data Kolom: Tidak dapat diobservasi (mungkin file kosong atau error pada chunk pertama).")

print("\n3. Agregat Nilai Null/NaN dan Non-Null per Kolom:")
# Jika ada data nilai null yang teragregasi atau total baris lebih dari 0.
if aggregated_null_counts_initial or total_rows_initial > 0 :
    # Iterasi melalui kolom-kolom yang didefinisikan dalam COLUMNS_TO_USE untuk menjaga urutan.
    for col in COLUMNS_TO_USE:
        # Ambil jumlah null untuk kolom saat ini dari Counter, default 0 jika kolom tidak ada.
        null_count = aggregated_null_counts_initial.get(col, 0)

        # Hitung jumlah non-null dengan mengurangi total baris dengan jumlah null.
        non_null_count = total_rows_initial - null_count

        # Hitung persentase nilai null, hindari pembagian dengan nol jika total_rows_initial adalah 0.
        persen_null = (null_count / total_rows_initial) * 100 if total_rows_initial > 0 else 0

        # Hitung persentase nilai non-null, hindari pembagian dengan nol.
        persen_non_null = (non_null_count / total_rows_initial) * 100 if total_rows_initial > 0 else 0

        # Cetak nama kolom yang sedang diproses.
        print(f"   Kolom '{col}':")

        # Cetak jumlah dan persentase nilai null (format persentase dengan 2 angka desimal).
        print(f"     - Nilai Null: {null_count} ({persen_null:.2f}%)")

        # Cetak jumlah dan persentase nilai non-null.
        print(f"     - Nilai Non-Null: {non_null_count} ({persen_non_null:.2f}%)")

else: # Jika tidak ada statistik yang bisa ditampilkan (misalnya file kosong).
    print("   Tidak ada statistik nilai null/non-null yang dapat ditampilkan.")

# Fungsi untuk mendeteksi apakah domain adalah domain pemerintah Indonesia atau .gov umum.
def is_gov_domain(domain):
    # Jika domain adalah NaN atau string 'nan', kembalikan False.
    if pd.isna(domain) or domain == 'nan':
        return False
    # Ubah domain menjadi string huruf kecil untuk konsistensi.
    domain_str = str(domain).lower()

    # Periksa apakah domain diakhiri dengan pola domain pemerintah/militer Indonesia.
    if re.search(r'(\.go\.id$|\.gov\.go\.id$|\.mil\.id$)', domain_str):
        return True # Jika cocok, kembalikan True.
    # Periksa apakah domain diakhiri dengan .gov (umum) TAPI BUKAN .go.id.
    if re.search(r'\.gov$', domain_str) and not re.search(r'\.go\.id$', domain_str):
        return True # Jika cocok, kembalikan True.
    # Jika tidak ada pola yang cocok, kembalikan False.
    return False

# Fungsi untuk mengklasifikasikan protokol sebagai 'Aman', 'Tidak Aman', atau 'Lainnya/Tidak Diketahui'.
def classify_protocol_security(proto):
    # Jika protokol adalah NaN atau string 'nan', kembalikan 'Lainnya/Tidak Diketahui'.
    if pd.isna(proto) or proto == 'nan':
        return 'Lainnya/Tidak Diketahui'
    # Ubah protokol menjadi string huruf kecil untuk konsistensi.
    proto_str = str(proto).lower()

    # Daftar kata kunci yang mengindikasikan protokol aman.
    secure_keywords = [
        'https', 'ssl', 'tls', 'quic', 'ssh', 'sftp', 'smtps', 'ftps',
        'dns over https', 'dns over tls', 'doq', 'dot', 'doh'
    ]
    # Jika ada kata kunci aman dalam string protokol, kembalikan 'Aman'.
    if any(keyword in proto_str for keyword in secure_keywords):
        return 'Aman'

    # Daftar kata kunci yang mengindikasikan protokol tidak aman.
    insecure_keywords = ['http', 'ftp', 'telnet', 'smtp']
    # Jika ada kata kunci tidak aman DAN tidak ada kata kunci aman yang lebih spesifik (misalnya 'https' vs 'http').
    if any(keyword in proto_str for keyword in insecure_keywords) and \
       not any(secure_keyword in proto_str for secure_keyword in ['https', 'sftp', 'smtps']):
        return 'Tidak Aman' # Kembalikan 'Tidak Aman'.

    # Jika tidak ada kondisi di atas yang terpenuhi, kembalikan 'Lainnya/Tidak Diketahui'.
    return 'Lainnya/Tidak Diketahui'

total_rows_after_preprocessing = 0      # Variabel untuk menyimpan total baris setelah proses dropna (penghapusan baris null).
total_traffic_count = 0                 # Variabel untuk menyimpan total hitungan lalu lintas (jumlah baris yang diproses).
gov_traffic_count = 0                   # Variabel untuk menyimpan hitungan lalu lintas yang berasal dari domain pemerintah.
non_gov_traffic_count = 0               # Variabel untuk menyimpan hitungan lalu lintas yang berasal dari domain non-pemerintah.
protocol_security_counts = Counter()    # Counter untuk menghitung frekuensi kategori keamanan protokol ('Aman', 'Tidak Aman', 'Lainnya/Tidak Diketahui').
all_protocol_counts = Counter()         # Counter untuk menghitung frekuensi semua jenis protokol yang muncul.
gov_domain_counts = Counter()           # Counter untuk menghitung frekuensi kemunculan domain pemerintah.
non_gov_domain_counts = Counter()       # Counter untuk menghitung frekuensi kemunculan domain non-pemerintah.
gov_domain_insecure_access = Counter()  # Counter untuk menghitung domain pemerintah yang diakses menggunakan protokol tidak aman.

# Pproses pembacaan file keseluruhan per chunk dimulai.
print(f"\nMemulai pemrosesan KESELURUHAN file per {CHUNKSIZE} baris...")

# Inisialisasi penghitung jumlah chunk yang diproses pada tahap kedua.
processed_chunks_pass2 = 0
try:
    # Membaca file CSV per chunk, hanya kolom yang ditentukan, low_memory=False untuk konsistensi tipe data.
    file_iterator_pass2 = pd.read_csv(file_path, chunksize=CHUNKSIZE, usecols=COLUMNS_TO_USE, low_memory=False)
    # Iterasi melalui setiap chunk dalam file.
    for chunk in file_iterator_pass2:
        processed_chunks_pass2 += 1 # Tambah jumlah chunk yang diproses.
        print(f"Memproses chunk ke-{processed_chunks_pass2}...")

        initial_rows_in_chunk = len(chunk) # Simpan jumlah baris awal dalam chunk.
        # Hapus baris dalam chunk yang memiliki nilai null pada kolom yang ditentukan di COLUMNS_FOR_NULL_CHECK_AND_DROP.
        chunk.dropna(subset=COLUMNS_FOR_NULL_CHECK_AND_DROP, inplace=True)
        rows_after_dropna_in_chunk = len(chunk) # Simpan jumlah baris setelah penghapusan null.

        if chunk.empty: # Jika chunk menjadi kosong setelah penghapusan baris null.
            print(f"Chunk ke-{processed_chunks_pass2} kosong setelah penghapusan baris dengan null pada kolom penting.") # Info.
            continue # Lanjutkan ke chunk berikutnya.

        # Akumulasi total baris setelah pra-pemrosesan (penghapusan null).
        total_rows_after_preprocessing += rows_after_dropna_in_chunk

        # Ubah kolom 'domain' menjadi string, huruf kecil, dan hapus spasi di awal/akhir.
        chunk['domain'] = chunk['domain'].astype(str).str.lower().str.strip()
        # Ubah kolom 'protocol' menjadi string, huruf kecil, dan hapus spasi di awal/akhir.
        chunk['protocol'] = chunk['protocol'].astype(str).str.lower().str.strip()

        # Buat kolom 'is_gov' dengan menerapkan fungsi is_gov_domain ke kolom 'domain'.
        chunk['is_gov'] = chunk['domain'].apply(is_gov_domain)
        # Akumulasi jumlah lalu lintas dari domain pemerintah.
        gov_traffic_count += chunk['is_gov'].sum()

        # Buat kolom 'security_level' dengan menerapkan fungsi classify_protocol_security ke kolom 'protocol'.
        chunk['security_level'] = chunk['protocol'].apply(classify_protocol_security)
        # Update Counter protocol_security_counts dengan frekuensi level keamanan protokol.
        protocol_security_counts.update(chunk['security_level'])

        # Update Counter all_protocol_counts dengan frekuensi semua jenis protokol.
        all_protocol_counts.update(chunk['protocol'])

        # Ambil domain pemerintah dalam chunk saat ini.
        gov_domains_in_chunk = chunk[chunk['is_gov']]['domain']
        # Ambil domain non-pemerintah dalam chunk saat ini.
        non_gov_domains_in_chunk = chunk[~chunk['is_gov']]['domain']
        # Update Counter gov_domain_counts dengan frekuensi domain pemerintah.
        gov_domain_counts.update(gov_domains_in_chunk)
        # Update Counter non_gov_domain_counts dengan frekuensi domain non-pemerintah.
        non_gov_domain_counts.update(non_gov_domains_in_chunk)
        # Akumulasi jumlah lalu lintas dari domain non-pemerintah dari data yang sudah bersih.
        non_gov_traffic_count += len(non_gov_domains_in_chunk)

        # Filter baris yang merupakan domain pemerintah DAN diakses dengan protokol 'Tidak Aman'.
        insecure_gov_hits = chunk[chunk['is_gov'] & (chunk['security_level'] == 'Tidak Aman')]
        if not insecure_gov_hits.empty: # Jika ada domain pemerintah yang diakses tidak aman.
            # Buat pasangan (domain, protocol) dari baris yang terfilter.
            domain_protocol_pairs = zip(insecure_gov_hits['domain'], insecure_gov_hits['protocol'])
            # Update Counter gov_domain_insecure_access dengan frekuensi pasangan domain-protokol tidak aman.
            gov_domain_insecure_access.update(domain_protocol_pairs)

    del file_iterator_pass2 # Hapus iterator file untuk membebaskan memori setelah selesai.
    print(f"\nTotal {processed_chunks_pass2} chunk diproses.") # Cetak konfirmasi jumlah chunk.

except FileNotFoundError: # Jika file tidak ditemukan
    print(f"ERROR: File tidak ditemukan di path: {file_path} saat Pass 2.")
    print("Program akan berhenti.")
    exit()
except Exception as e: # Jika terjadi error lain saat pemrosesan.
    print(f"ERROR: Terjadi kesalahan saat Pass 2: {e}")
    print("Program akan berhenti.")
    exit()

# Jika tidak ada baris data awal yang berhasil dibaca (misalnya, file kosong atau error di Pass 1).
if total_rows_initial == 0:
    # Cetak pesan bahwa informasi pra-pemrosesan tidak dapat ditampilkan.
    print("Tidak ada data awal yang dibaca, informasi pra-pemrosesan tidak dapat ditampilkan.")
else: # Jika ada data awal yang dibaca.
    # Cetak jumlah total baris awal sebelum dilakukan pra-pemrosesan (penghapusan null, dll.).
    print(f"Total Baris Awal Sebelum Pra-pemrosesan: {total_rows_initial}")
    # Cetak jumlah total baris setelah pra-pemrosesan (data bersih yang benar-benar dianalisis).
    print(f"Total Baris Setelah Pra-pemrosesan (data bersih yang dianalisis): {total_rows_after_preprocessing}")

"""#EVALUASI POLA TRAFIK"""

print("\n1. Proporsi Trafik Berdasarkan Jenis Domain")
print(f"Total trafik yang dianalisis (data bersih): {total_rows_after_preprocessing}")

# Jika ada data bersih yang diproses.
if total_rows_after_preprocessing > 0:
    # Cetak jumlah dan persentase trafik ke domain pemerintah.
    print(f"Trafik ke domain pemerintahan: {gov_traffic_count} ({(gov_traffic_count/total_rows_after_preprocessing)*100:.2f}%)")
    # Cetak jumlah dan persentase trafik ke domain non-pemerintah.
    print(f"Trafik ke domain non-pemerintahan: {non_gov_traffic_count} ({(non_gov_traffic_count/total_rows_after_preprocessing)*100:.2f}%)")
else: # Jika tidak ada data bersih.
    # Cetak jumlah trafik ke domain pemerintah (persentase tidak tersedia).
    print(f"Trafik ke domain pemerintahan: {gov_traffic_count} (N/A)")
    # Cetak jumlah trafik ke domain non-pemerintah (persentase tidak tersedia).
    print(f"Trafik ke domain non-pemerintahan: {non_gov_traffic_count} (N/A)")

# Mencetak baris baru untuk spasi.
print("\n")

# Menyiapkan label untuk pie chart jenis domain.
labels_domain_type = ['Pemerintahan', 'Non-Pemerintahan']
# Menyiapkan nilai (jumlah trafik) untuk pie chart jenis domain.
values_domain_type = [gov_traffic_count, non_gov_traffic_count]
# Membuat plot
if sum(values_domain_type) > 0:
    colors_domain_type = ['#66b3ff', '#ff9999']
    explode_domain_type = (0.05, 0)
    plt.figure(figsize=(7, 7))
    plt.pie(values_domain_type, labels=labels_domain_type, autopct='%1.1f%%',
            colors=colors_domain_type, startangle=90, explode=explode_domain_type,
            wedgeprops={'edgecolor': 'grey'})
    plt.title('Proporsi Trafik Berdasarkan Jenis Domain\n', fontsize=14)
    plt.axis('equal')
    plt.tight_layout()
    plt.show()
else: # Jika tidak ada data untuk divisualisasikan.
    print("Tidak ada data proporsi domain untuk divisualisasikan.")

print(f"\n2. Top {N_TOP_ITEMS} Domain yang Paling Sering Diakses")

# Fungsi untuk membuat dan menampilkan plot horizontal bar untuk N item teratas dari sebuah Counter.
def plot_top_n_horizontal_bar(counts, title, color, N):
    if not counts: # Jika Counter 'counts' kosong.
        print(f"Tidak ada data untuk '{title}'.")
        return
    # Ubah N item teratas dari Counter menjadi DataFrame dengan kolom 'Domain' dan 'Jumlah Trafik'.
    top_df = pd.DataFrame(counts.most_common(N), columns=['Domain', 'Jumlah Trafik'])
    if top_df.empty: # Jika DataFrame hasil konversi kosong (seharusnya sudah ditangani oleh 'if not counts').
        print(f"Tidak ada data untuk '{title}'.")
        return

    # Cetak judul dan tabel N item teratas.
    print(f"\nTop {N} {title}:")
    print(top_df.to_string(index=False))
    print("\n")

    # Membuat plot
    plt.figure(figsize=(10, max(6, N * 0.6)))
    plt.barh(top_df['Domain'], top_df['Jumlah Trafik'], color=color, edgecolor='grey')
    plt.xlabel('Jumlah Trafik', fontsize=12)
    plt.ylabel('Domain', fontsize=12)
    plt.title(f'Top {N} {title}\n', fontsize=14)
    plt.gca().invert_yaxis()
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()

# Panggil fungsi untuk menampilkan top N domain pemerintah.
plot_top_n_horizontal_bar(gov_domain_counts, "Domain Pemerintah", '#66b3ff', N_TOP_ITEMS)
# Panggil fungsi untuk menampilkan top N domain non-pemerintah.
plot_top_n_horizontal_bar(non_gov_domain_counts, "Domain Non-Pemerintah", '#ff9999', N_TOP_ITEMS)

"""#EVALUASI KEAMANAN JARINGAN"""

print("\n3. Proporsi Trafik Berdasarkan Keamanan Protokol\n")
# Ambil label (kategori keamanan) dari keys Counter protocol_security_counts.
labels_proto_sec = list(protocol_security_counts.keys())
# Ambil nilai (jumlah trafik) yang sesuai dengan setiap label dari Counter.
values_proto_sec = [protocol_security_counts[k] for k in labels_proto_sec]

# Lanjutkan jika ada data untuk diplot (total nilai lebih dari 0).
if sum(values_proto_sec) > 0:
    colors_proto_map = {'Aman': '#77dd77', 'Tidak Aman': '#ff6961', 'Lainnya/Tidak Diketahui': '#D3D3D3'}
    pie_colors_proto = [colors_proto_map.get(label, '#CCCCCC') for label in labels_proto_sec]
    explode_proto = [0.05 if label == 'Tidak Aman' else 0 for label in labels_proto_sec]
    plt.figure(figsize=(7, 7))
    # Buat pie chart dengan nilai, label, format persentase otomatis, warna, sudut awal, efek explode, dan properti garis tepi.
    plt.pie(values_proto_sec, labels=labels_proto_sec, autopct='%1.1f%%',
            colors=pie_colors_proto, startangle=90, explode=explode_proto,
            wedgeprops={'edgecolor': 'grey'})
    plt.title('Proporsi Trafik Berdasarkan Keamanan Protokol\n', fontsize=14)
    plt.axis('equal')
    plt.tight_layout()
    plt.show()

    print("\nRincian Jumlah Trafik per Kategori Keamanan Protokol (Data Bersih):")
    # Iterasi melalui setiap item (level keamanan dan jumlahnya) dalam protocol_security_counts.
    for level, count in protocol_security_counts.items():
        # Hitung persentase trafik untuk level keamanan saat ini terhadap total data bersih.
        percent = (count / total_rows_after_preprocessing) * 100 if total_rows_after_preprocessing > 0 else 0
        # Cetak rincian jumlah dan persentase trafik untuk level keamanan.
        print(f"   Trafik '{level}': {count} ({percent:.2f}%)")
else: # Jika tidak ada data klasifikasi keamanan protokol.
    print("Tidak ada data klasifikasi keamanan protokol untuk ditampilkan.")

print(f"\nTop {N_TOP_ITEMS} Protokol yang Paling Sering Digunakan")

# Jika Counter all_protocol_counts tidak kosong (ada data protokol).
if all_protocol_counts:
    # Ubah N protokol teratas dari Counter menjadi DataFrame dengan kolom 'Protokol' dan 'Jumlah'.
    top_protocols_df = pd.DataFrame(all_protocol_counts.most_common(N_TOP_ITEMS), columns=['Protokol', 'Jumlah'])
    # Cetak DataFrame N protokol teratas tanpa indeks.
    print(top_protocols_df.to_string(index=False))
    print("\n")

    # Buat area gambar (figure) untuk plot.
    plt.figure(figsize=(10, 6))
    plt.bar(top_protocols_df['Protokol'], top_protocols_df['Jumlah'], color='#aec6cf', edgecolor='grey')
    plt.xlabel('Protokol', fontsize=12)
    plt.ylabel('Jumlah Penggunaan', fontsize=12)
    plt.title(f'Top {N_TOP_ITEMS} Protokol Paling Sering Digunakan', fontsize=14)
    plt.xticks(rotation=45, ha="right")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
else: # Jika tidak ada data protokol.
    print("Tidak ada data protokol untuk ditampilkan.")

print("\n5. Domain Pemerintah yang Diakses dengan Protokol Tidak Aman\n")

# Jika Counter gov_domain_insecure_access tidak kosong (ada data).
if gov_domain_insecure_access:
    # Menyiapkan list untuk menyimpan data yang akan diubah menjadi DataFrame.
    # Setiap item dalam most_common adalah tuple: ((domain, protocol), count).
    items_for_df = []
    # Iterasi melalui N_TOP_ITEMS * 2 item teratas dari Counter.
    for (domain, protocol), count in gov_domain_insecure_access.most_common(N_TOP_ITEMS * 2):
        # Tambahkan domain, protokol, dan jumlah akses ke list.
        items_for_df.append([domain, protocol, count])

    # Buat DataFrame dari list items_for_df.
    insecure_gov_df = pd.DataFrame(items_for_df,
                                     columns=['Domain Pemerintah', 'Protokol Tidak Aman', 'Jml Akses'])

    # Cetak informasi jumlah kombinasi domain pemerintah & protokol tidak aman yang ditemukan.
    print(f"Ditemukan {len(gov_domain_insecure_access)} kombinasi domain pemerintah & protokol tidak aman yang terindikasi.\n")
    # Cetak informasi bahwa yang ditampilkan adalah N_TOP_ITEMS * 2 teratas.
    print(f"Menampilkan hingga {N_TOP_ITEMS * 2} teratas:")
    print(insecure_gov_df.to_string(index=False))
    print("\n")

    # Jika DataFrame insecure_gov_df tidak kosong (ada data untuk diplot).
    if not insecure_gov_df.empty:
        # Tentukan jumlah item teratas yang akan diplot (N_plot).
        N_plot = N_TOP_ITEMS
        # Ambil N_plot item teratas dari Counter untuk diplot.
        plot_data = gov_domain_insecure_access.most_common(N_plot)

        # Jika ada data untuk diplot setelah pemfilteran N_plot.
        if plot_data:
            # Buat label untuk sumbu y plot, menggabungkan domain dan protokol: "Domain (Protokol)".
            labels_for_plot = [f"{item[0][0]} ({item[0][1]})" for item in plot_data]
            # Ambil jumlah akses untuk setiap item yang akan diplot.
            counts_for_plot = [item[1] for item in plot_data]

            # Buat area gambar (figure) untuk plot, tinggi disesuaikan dengan N_plot.
            plt.figure(figsize=(12, max(6, N_plot * 0.6)))
            plt.barh(labels_for_plot, counts_for_plot, color='#ff6961', edgecolor='grey')
            plt.xlabel('Jumlah Akses Tidak Aman', fontsize=12)
            plt.ylabel('Domain Pemerintah (Protokol Tidak Aman)', fontsize=12)
            plt.title(f'Top {N_plot} Domain Pemerintah dengan Akses Protokol Tidak Aman\n', fontsize=14)
            plt.gca().invert_yaxis()
            plt.grid(axis='x', linestyle='--', alpha=0.7)
            plt.tight_layout()
            plt.show()
        else: # Jika tidak ada data untuk divisualisasikan setelah pemfilteran N_plot.
            print("Tidak ada data untuk divisualisasikan setelah pemfilteran N_TOP_ITEMS.")

else: # Jika tidak ada domain pemerintah yang diakses dengan protokol tidak aman.
    print("Tidak ditemukan domain pemerintah yang diakses dengan protokol tidak aman berdasarkan data bersih yang diproses.")