import os
import json
import requests
import re
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={API_KEY}"

def classify_document(text: str) -> Dict[str, Any]:
    if not text or len(text.strip()) < 5:
        return {"error": "Teks tidak terbaca"}

    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    Kamu adalah sistem klasifikasi dokumen untuk Desa Sukasari Kidul.

    ## ATURAN UTAMA (Wajib diperiksa PERTAMA sebelum klasifikasi)

    Dokumen HARUS masuk kategori "Lainnya" jika memenuhi salah satu kondisi berikut:
    - Dokumen akademik/ilmiah: makalah, skripsi, tesis, jurnal, paper, laporan praktikum (KECUALI surat pengantar resmi permohonan KKN/penelitian dari kampus kepada Kepala Desa)
    - Data institusi non-desa: nilai mahasiswa/siswa, absensi sekolah/kampus, transkrip akademik
    - Dokumen perusahaan/korporat yang tidak berkaitan dengan kegiatan desa
    - Teks tidak bermakna, konten random, atau tidak bisa diidentifikasi
    - Topiknya relevan secara umum (misal: pertanahan, pendidikan) TAPI konteksnya bukan urusan pemerintahan desa

    ## KATEGORI DOKUMEN DESA

    Gunakan kategori berikut HANYA jika dokumen berasal dari atau ditujukan untuk konteks pemerintahan Desa Sukasari Kidul:

    1. Layanan Kependudukan (KPD) — KK, KTP, SKTM, surat domisili, keterangan warga
    2. Administrasi Umum (ADM) — Notulen rapat desa, disposisi, SK Kepala Desa, berita acara, arsip kantor desa, surat tugas perangkat desa
    3. Keuangan & Anggaran (KEU) — Laporan keuangan desa, RAB, LPJ, APBDes
    4. Pembangunan & Proyek (BNG) — Proposal proyek desa, monitoring infrastruktur, laporan kegiatan pembangunan
    5. Kesejahteraan Sosial (KSS) — Data bansos, laporan kesehatan warga, program stunting, PKH
    6. Pertanahan & Perkebunan (TNH) — SKT, AJB, sporadik, sertifikat tanah milik warga desa, sengketa tanah desa
    7. Pemberdayaan Masyarakat (PMD) — Kelompok tani, UMKM desa, PKK, BUMDes, organisasi kepemudaan desa (misal: Pemuda Pemudi, Karang Taruna, Remaja Masjid,dll), surat pemberitahuan/permohonan izin kegiatan warga kepada desa
    8. Keamanan & Ketertiban (KMN) — Laporan kejadian di desa, jadwal ronda, surat keterangan catatan kepolisian warga
    9. Pendidikan (PDK) — Surat keterangan ijazah warga, rekomendasi beasiswa warga desa, laporan PAUD/TK desa, surat dari institusi pendidikan/kampus (seperti pengantar KKN, izin penelitian, magang mahasiswa/siswa di desa)
    10. Lainnya (LNY) — Semua dokumen yang tidak termasuk kategori 1–9 di atas

    ## PANDUAN KATEGORI AMBIGU

    Gunakan dua pertanyaan ini secara berurutan:

    Pertanyaan 1: Siapa yang membuat atau membutuhkan dokumen ini?
    - Dibuat oleh / untuk / atas nama Pemerintah Desa Sukasari Kidul → lanjut ke pertanyaan berikutnya
    - Dibuat oleh warga, organisasi kemasyarakatan desa, atau kelompok masyarakat desa (seperti karang taruna, pemuda desa, PKK, kelompok tani,dll) dan DITUJUKAN kepada pemerintah desa → lanjut ke pertanyaan berikutnya
    - Dibuat oleh institusi luar desa (seperti kampus, sekolah, dinas kabupaten) dan DITUJUKAN resmi kepada pemerintah desa untuk koordinasi, perizinan kegiatan (KKN, penelitian, magang), atau urusan resmi desa → lanjut ke pertanyaan berikutnya
    - Dibuat oleh institusi luar desa (perusahaan swasta komersial, LSM non-desa, pribadi tanpa kaitan desa) yang tidak ada kaitannya dengan pelayanan desa → "Lainnya"

    Pertanyaan 2: Apa fungsi operasional dokumen ini di desa?
    - Digunakan untuk melayani warga, mencatat kegiatan, atau mengelola aset desa → pilih kategori 1–9
    - Hanya membahas topik terkait desa tetapi tidak memiliki fungsi operasional → "Lainnya"

    ## ATURAN PENENTUAN TANGGAL & NAMA FILE

    - document_date:
    - Ambil tanggal yang tercantum secara jelas pada dokumen (misal: tanggal surat dibuat/diterbitkan) dengan format YYYY-MM-DD.
    - Jika TIDAK ADA tanggal yang tercantum di dalam teks dokumen, kamu WAJIB mengisi dengan null (jangan menebak/mengarang tanggal).

    - suggested_filename (WAJIB mengikuti format berikut, TANPA ekstensi):
    - Jika document_date ADA nilainya: [KODE-KATEGORI]_[JENIS-DOKUMEN]_[NAMA-atau-NIK]_[YYYY-MM-DD]
    - Jika document_date bernilai null: [KODE-KATEGORI]_[JENIS-DOKUMEN]_[NAMA-atau-NIK]

    Ketentuan Pemformatan Karakter (Sangat Ketat!):
    - Gunakan KODE-KATEGORI (KPD, ADM, KEU, BNG, KSS, TNH, PMD, KMN, PDK, LNY)
    - Gunakan tanda hubung/strip (-) untuk memisahkan kata di dalam JENIS-DOKUMEN dan NAMA-atau-NIK jika terdiri dari lebih dari satu kata.
    - DILARANG KERAS menggunakan spasi ( ), garis bawah (_), atau menyatukan kata (tanpa pemisah) di dalam sub-field JENIS-DOKUMEN dan NAMA-atau-NIK. Garis bawah (_) HANYA boleh digunakan sebagai pemisah antar field utama (pemisah kode kategori, jenis dokumen, nama, dan tanggal).

    Contoh Yang Benar:
    - KPD_Akta-Kelahiran_Muhammad-Wisnu-Pradana_2024-05-02 (Benar, menggunakan strip di dalam sub-field, garis bawah hanya sebagai pemisah utama)
    - KEU_Rencana-Anggaran-Biaya_Pembangunan-Jalan_2025-03-01 (Benar)
    - ADM_Surat-Pengantar_Bagus-Gunawan-07-24 (Benar)

    Contoh Yang Salah (JANGAN DILAKUKAN):
    - KPD_Akta_Kelahiran_Muhammad_Wisnu_Pradana_2024-05-02 (Salah, menggunakan garis bawah di dalam sub-field)
    - KPD_Akta Kelahiran_Muhammad Wisnu Pradana_2024-05-02 (Salah, menggunakan spasi)
    - KPD_AktaKelahiran_MuhammadWisnuPradana_2024-05-02 (Salah, kata digabung tanpa pemisah)

    ## FORMAT OUTPUT

    Kembalikan HANYA JSON berikut tanpa teks tambahan:
    {{
    "category": "<nama kategori tanpa kode>",
    "confidence_score": <0.0–1.0>,
    "analysis_reason": "<Jelaskan secara positif mengapa dokumen ini masuk ke kategori yang dipilih. Fokus pada: (1) siapa pembuat/penerima dokumen dan konteks operasional desanya, (2) fungsi dokumen dalam kegiatan desa, (3) mengapa kategori ini paling tepat dibanding kategori lain yang mungkin mirip. JANGAN menggunakan kalimat negatif seperti 'dokumen ini tidak masuk ke Lainnya karena...>",
    "summary": "<ringkasan isi dokumen>",
    "suggested_filename": "",
    "document_date": ""
    }}

    ## TEKS DOKUMEN

    {text[:3000]}
    """

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.0
        }
    }

    try:
        response = requests.post(URL, headers=headers, json=payload)
        if response.status_code == 200:
            res_json = response.json()
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
            match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if match:
                return json.loads(match.group(1))
        return {"error": f"API Error {response.status_code}"}
    except Exception as e:
        return {"error": str(e)}