# 🤖 EduCare-Bot — Sistem Pakar Pendamping Belajar

Aplikasi berbasis Python untuk diagnosa kesulitan belajar dan manajemen tugas. Proyek ini berjalan sebagai web backend menggunakan `app.py`.

## 🚀 Fitur Utama

- Diagnosa masalah belajar berbasis keyword matching
- Manajemen tugas dengan penyimpanan JSON (`tasks.json`)
- Reminder deadline otomatis melalui scheduler
- API backend yang dapat digunakan untuk antarmuka web atau client lain

## 🗂️ Struktur File

```
├── app.py                 # Entry point aplikasi web backend
├── knowledge_base.py      # Basis pengetahuan (kata kunci & solusi)
├── inference_engine.py    # Mesin inferensi (keyword matching & scoring)
├── reminder_scheduler.py  # Scheduler pengingat deadline
├── task_manager.py        # CRUD tugas dan logika deadline
├── requirements.txt       # Daftar dependency Python
├── tasks.json             # Data tugas pengguna (jika sudah dibuat)
└── README.md              # Dokumentasi ini
```

## ⚙️ Cara Instalasi & Menjalankan   

1. Install dependency:

```bash
pip install -r requirements.txt
```

2. Jalankan backend:

```bash
python app.py
```

3. Buka browser atau client yang terhubung ke API untuk menggunakan aplikasi.

## � Alur Kerja Aplikasi

1. User mengirim pesan atau permintaan melalui antarmuka web/API
2. `app.py` memproses input dan mengelola status pengguna
3. `inference_engine.py` melakukan diagnosa keyword matching
4. `task_manager.py` menyimpan dan membaca tugas dari `tasks.json`
5. `reminder_scheduler.py` memeriksa deadline dan menghasilkan notifikasi


1. User mengirim pesan atau permintaan melalui antarmuka web/API
2. `app.py` memproses input dan mengelola status pengguna
3. `inference_engine.py` melakukan diagnosa keyword matching
4. `task_manager.py` menyimpan dan membaca tugas dari `tasks.json`
5. `reminder_scheduler.py` memeriksa deadline dan menghasilkan notifikasi

## 📌 Catatan Tambahan

- Jika `tasks.json` belum ada, aplikasi akan membuatnya saat tugas pertama ditambahkan.
- Kalau ingin memodifikasi logika diagnosa, periksa `inference_engine.py` dan `knowledge_base.py`.

## 📝 Lisensi

Proyek ini dibuat untuk keperluan akademik / tugas kuliah.
