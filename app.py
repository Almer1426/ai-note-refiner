import streamlit as st
import google.generativeai as genai
from datetime import datetime
import json
import csv
import io


def refine_notes(catatan_kasar, api_key, model_id='gemini-2.0-flash'):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_id)

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
        if "API key not valid" in str(e):
            st.error("API Key yang Anda masukkan tidak valid. Mohon periksa kembali.")
            return None
        else:
            st.error(f"Terjadi kesalahan saat menghubungi AI: {e}")
            return None


def generate_flashcards(catatan_rapi, api_key, model_id='gemini-2.0-flash'):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_id)

        prompt = f"""
        Kamu adalah mesin pembuat flashcard Anki untuk mahasiswa.

        Dari materi berikut, ekstrak semua konsep penting dan buat flashcard dalam format JSON.
        Setiap flashcard harus memiliki:
        - "depan": pertanyaan singkat atau istilah yang diuji
        - "belakang": jawaban lengkap tapi ringkas (maks 3 kalimat)

        Buat minimal 10 flashcard, maksimal 25. Fokus pada konsep yang paling penting dan kemungkinan besar keluar di ujian.

        Materi:
        {catatan_rapi}

        Balas HANYA dengan JSON valid, tanpa teks tambahan apapun. Format:
        [
          {{"depan": "...", "belakang": "..."}},
          ...
        ]
        """

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Bersihkan markdown code block kalau ada
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        cards = json.loads(raw)
        return cards
    except json.JSONDecodeError:
        st.error("AI mengembalikan format yang tidak terbaca. Coba lagi.")
        return None
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membuat flashcard: {e}")
        return None


def cards_to_anki_csv(cards):
    output = io.StringIO()
    writer = csv.writer(output, delimiter='\t')
    for card in cards:
        writer.writerow([card['depan'], card['belakang']])
    return output.getvalue().encode('utf-8')


# --- Tampilan Aplikasi Web ---
st.set_page_config(page_title="AI Note Refiner", page_icon="🤖", layout="wide")
st.title("✍️ AI Note Refiner")
st.caption("Ubah catatan kuliah kasarmu menjadi catatan rapi terstruktur dengan sekali klik!")

# Mengambil API Key dari secrets jika dideploy, jika tidak ada, minta input dari pengguna
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    st.info("Untuk menjalankan aplikasi secara lokal, masukkan Google AI API Key kamu di bawah ini.")
    api_key = st.text_input("Google AI API Key", type="password", placeholder="AIza...")

MODEL_OPTIONS = {
    "Gemini 2.0 Flash (Cepat & Hemat)": "gemini-2.0-flash",
    "Gemini 2.5 Pro (Paling Canggih)": "gemini-2.5-pro",
}
selected_model_label = st.sidebar.selectbox("🤖 Pilih Model AI", list(MODEL_OPTIONS.keys()))
selected_model_id = MODEL_OPTIONS[selected_model_label]


# Layout dengan dua kolom: satu untuk input, satu untuk output
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("Catatan Kasar Anda")
    catatan_kasar_input = st.text_area("Tempel catatan kasarmu di sini:", height=400, label_visibility="collapsed")

    jumlah_kata_input = len(catatan_kasar_input.split()) if catatan_kasar_input.strip() else 0
    st.caption(f"📝 {jumlah_kata_input} kata")

    if st.button("✨ Rapikan Catatan!", use_container_width=True, type="primary"):
        if not api_key:
            st.error("Mohon masukkan API Key Anda terlebih dahulu.")
        elif not catatan_kasar_input:
            st.warning("Mohon masukkan catatan yang ingin dirapikan.")
        else:
            with st.spinner(f"AI ({selected_model_label}) sedang bekerja... Mohon tunggu sebentar..."):
                catatan_rapi_output = refine_notes(catatan_kasar_input, api_key, selected_model_id)
                st.session_state['hasil_catatan'] = catatan_rapi_output
                st.session_state.pop('flashcards', None)  # Reset flashcard lama

with col2:
    st.subheader("Hasil Catatan Rapi")
    if 'hasil_catatan' in st.session_state and st.session_state['hasil_catatan']:
        hasil = st.session_state['hasil_catatan']

        jumlah_kata_output = len(hasil.split())
        st.caption(f"📄 {jumlah_kata_output} kata")

        st.markdown(hasil)

        sekarang = datetime.now().strftime("%Y-%m-%d_%H-%M")
        nama_file = f"catatan_rapi_{sekarang}.md"

        st.download_button(
           label="📥 Unduh File .md",
           data=hasil.encode('utf-8'),
           file_name=nama_file,
           mime='text/markdown',
           use_container_width=True
        )

# --- Fitur Flashcard Anki ---
if 'hasil_catatan' in st.session_state and st.session_state['hasil_catatan']:
    st.divider()
    st.subheader("🃏 Generate Flashcard Anki")
    st.caption("Buat kartu hafalan siap pakai dari catatanmu — langsung bisa diimpor ke Anki.")

    if st.button("⚡ Generate Flashcard", use_container_width=True):
        with st.spinner("AI sedang membuat flashcard..."):
            cards = generate_flashcards(st.session_state['hasil_catatan'], api_key, selected_model_id)
            if cards:
                st.session_state['flashcards'] = cards

    if 'flashcards' in st.session_state and st.session_state['flashcards']:
        cards = st.session_state['flashcards']
        st.success(f"{len(cards)} flashcard berhasil dibuat!")

        # Tampilkan preview flashcard
        cols = st.columns(2)
        for i, card in enumerate(cards):
            with cols[i % 2]:
                with st.expander(f"🃏 {card['depan']}"):
                    st.write(card['belakang'])

        st.divider()

        # Export ke Anki
        anki_csv = cards_to_anki_csv(cards)
        sekarang = datetime.now().strftime("%Y-%m-%d_%H-%M")
        st.download_button(
            label="📦 Unduh untuk Anki (.txt)",
            data=anki_csv,
            file_name=f"anki_{sekarang}.txt",
            mime='text/plain',
            use_container_width=True,
            help="Import ke Anki: File → Import → pilih file ini. Pastikan separator diset ke Tab."
        )
