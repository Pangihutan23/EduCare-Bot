# 🤖 Bot Sistem Pakar — Diagnosa Kesulitan Belajar Mahasiswa

Bot Telegram yang menggunakan metode **Sistem Pakar** dengan teknik **Keyword Matching (Pembobotan Kata Kunci)** untuk mendiagnosis kesulitan belajar yang dialami mahasiswa.

## 📋 Kategori Diagnosis

| # | Kategori | Deskripsi |
|---|----------|-----------|
| 1 | **Prokrastinasi** | Kebiasaan menunda-nunda tugas |
| 2 | **Burnout** | Kelelahan akademik secara fisik & mental |
| 3 | **Distraksi** | Kurang fokus akibat gadget/lingkungan |
| 4 | **Kurang Pemahaman Dasar** | Tidak menguasai konsep/materi dasar |

## 🗂️ Struktur File

```
├── bot.py                 # File utama bot Telegram
├── knowledge_base.py      # Basis pengetahuan (kata kunci & solusi)
├── inference_engine.py    # Mesin inferensi (keyword matching & scoring)
├── requirements.txt       # Daftar dependency Python
└── README.md              # Dokumentasi ini
```

## ⚙️ Cara Instalasi & Menjalankan

### 1. Buat Bot Telegram

1. Buka aplikasi **Telegram**, cari **@BotFather**.
2. Kirim perintah `/newbot`.
3. Ikuti instruksi untuk memberi nama bot.
4. Anda akan mendapatkan **Token API** (contoh: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`).

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Masukkan Token

Buka file `bot.py`, lalu ganti baris berikut dengan token Anda:

```python
TOKEN = "MASUKKAN_TOKEN_BOT_ANDA_DISINI"
```

### 4. Jalankan Bot

```bash
python bot.py
```

Bot akan menampilkan pesan:
```
=======================================================
  🤖 Bot Sistem Pakar Kesulitan Belajar — AKTIF!
  Tekan Ctrl+C untuk menghentikan bot.
=======================================================
```

### 5. Uji Bot

1. Buka Telegram, cari nama bot Anda.
2. Kirim perintah `/start`.
3. Ceritakan masalah belajar Anda, contoh:

   > "Aku akhir-akhir ini males banget, tugas numpuk semua tapi aku cuma rebahan main hp terus. Udah gak fokus dan capek banget rasanya."

4. Bot akan memberikan **diagnosis** dan **solusi** secara otomatis!

## 🧠 Alur Sistem

```
User mengirim /start
        ↓
Bot menyapa & memberi instruksi
        ↓
User menceritakan masalahnya (teks bebas)
        ↓
Teks diubah ke lowercase & dibersihkan
        ↓
Keyword Matching: cek setiap kata kunci di Knowledge Base
        ↓
Hitung skor tiap kategori (bobot utama: +3, pendukung: +1)
        ↓
Kategori skor tertinggi = Diagnosis
        ↓
Bot mengirim solusi + detail skor
```

## 📝 Lisensi

Proyek ini dibuat untuk keperluan akademik / tugas kuliah.
