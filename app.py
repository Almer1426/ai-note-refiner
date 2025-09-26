import streamlit as st
import google.generativeai as genai
from datetime import datetime  # BARU: Impor untuk memberi nama file unik

# --- Konfigurasi dan Fungsi AI (tidak ada perubahan di sini) ---
def refine_notes(catatan_kasar, api_key):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro') # Menggunakan model yang sudah terbukti bekerja
        
        prompt_template = f"""
        # PERAN & TUJUAN UTAMA
        Anda adalah seorang Ahli Strategi Pembelajaran dan Notulensi Akademik. Misi utama Anda adalah mengubah transkrip catatan mentah menjadi sebuah materi pembelajaran yang sangat terstruktur, mendalam, dan mudah dipahami. Tujuannya bukan hanya merapikan, tetapi mengubah catatan menjadi sebuah fondasi pengetahuan yang kokoh, setingkat materi persiapan untuk kompetisi tingkat tinggi.

        # INPUT
        Teks mentah dari catatan kuliah berikut:
        "{catatan_kasar}"

        # PROSES & INSTRUKSI
        Analisis input dan hasilkan output dalam format Markdown berdasarkan urutan dan aturan ketat berikut:

        1.  **Judul Utama (#):** Ciptakan judul yang paling relevan dan mencakup keseluruhan esensi materi.
        2.  **Ringkasan Eksekutif (###):** Di bawah judul, buat 2-3 kalimat ringkasan yang padat dan informatif, menyoroti konsep paling krusial yang dibahas.
        3.  **Identifikasi & Elaborasi Konsep Inti (###):**
            * Deteksi semua topik dan sub-topik utama dari catatan. Gunakan Heading 3 (###) untuk setiap topik.
            * Untuk setiap topik, lakukan elaborasi:
                * **Definisi & Penjelasan:** Sempurnakan semua definisi dan penjelasan. Jika user hanya menulis kata kunci (misal: "kompleksitas O(N)"), berikan penjelasan lengkapnya.
                * **Detail Pendukung:** Gunakan bullet points (-) untuk menyajikan detail, properti, atau langkah-langkah secara sistematis dan jelas.
                * **Contoh & Analogi:** Untuk setiap konsep yang kompleks, berikan **contoh konkret** atau **analogi sederhana** untuk mempermudah pemahaman.
                * **Penekanan Visual:** Tebalkan (**bold**) semua istilah, kata kunci, dan nama penting.
        4.  **Koneksi Antar Topik (###):** (Opsional) Jika relevan, buat satu bagian yang menjelaskan bagaimana satu topik terhubung dengan topik lainnya dalam catatan ini.
        5.  **Tugas & Pengumuman Penting (###):** Di bagian paling akhir, kumpulkan dan daftarkan semua tugas, *action item*, atau jadwal penting yang disebutkan.

        # ATURAN TAMBAHAN
        -   Perbaiki semua kesalahan ejaan dan tata bahasa menjadi bahasa Indonesia edukatif namun tetap santai seperti mentor dengan mentee dan mudah dipahami.
        -   Panjang catatan tidak menjadi masalah selama isinya relevan, penting, dan menambah nilai pembelajaran.
        -   Pastikan output akhir adalah sebuah dokumen yang mandiri, di mana seseorang bisa belajar secara efektif hanya dari catatan ini.
        """
        
        response = model.generate_content(prompt_template)
        return response.text
    except Exception as e:
        # Menangani error API key secara lebih spesifik jika memungkinkan
        if "API key not valid" in str(e):
            st.error("API Key yang Anda masukkan tidak valid. Mohon periksa kembali.")
            return None
        else:
            st.error(f"Terjadi kesalahan saat menghubungi AI: {e}")
            return None


# --- Tampilan Aplikasi Web ---
st.set_page_config(page_title="AI Note Refiner", page_icon="🤖", layout="wide")
st.title("✍️ AI Note Refiner")
st.caption("Ubah catatan kuliah kasarmu menjadi catatan rapi terstruktur dengan sekali klik!")

# Mengambil API Key dari secrets jika dideploy, jika tidak ada, minta input dari pengguna
try:
    # Untuk deployment di Streamlit Cloud
    api_key = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    # Untuk dijalankan di komputer lokal
    st.info("Untuk menjalankan aplikasi, silakan masukkan Google AI API Key Anda di bawah ini.")
    api_key = st.secrets["GEMINI_API_KEY"]


# Layout dengan dua kolom: satu untuk input, satu untuk output
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("Catatan Kasar Anda")
    catatan_kasar_input = st.text_area("Tempel catatan kasarmu di sini:", height=400, label_visibility="collapsed")
    
    # Tombol untuk memproses
    if st.button("✨ Rapikan Catatan!", use_container_width=True, type="primary"):
        if not api_key:
            st.error("Mohon masukkan API Key Anda terlebih dahulu.")
        elif not catatan_kasar_input:
            st.warning("Mohon masukkan catatan yang ingin dirapikan.")
        else:
            with st.spinner("AI sedang bekerja... Mohon tunggu sebentar..."):
                catatan_rapi_output = refine_notes(catatan_kasar_input, api_key)
                
                # Simpan hasilnya di session state agar tidak hilang
                st.session_state['hasil_catatan'] = catatan_rapi_output

with col2:
    st.subheader("Hasil Catatan Rapi")
    # Tampilkan hasil jika ada di session state
    if 'hasil_catatan' in st.session_state and st.session_state['hasil_catatan']:
        hasil = st.session_state['hasil_catatan']
        
        st.markdown(hasil) # Tampilkan pratinjau catatan yang sudah rapi
        
        # --- FITUR DOWNLOAD (BAGIAN BARU) ---
        sekarang = datetime.now().strftime("%Y-%m-%d_%H-%M")
        nama_file = f"catatan_rapi_{sekarang}.md"
        
        st.download_button(
           label="📥 Unduh File .md",
           data=hasil.encode('utf-8'), # Encode teks ke bytes
           file_name=nama_file,
           mime='text/markdown',
           use_container_width=True
        )