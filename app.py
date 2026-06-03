# =============================================================================
# app.py
# Web Backend & API Server — Sistem Pakar Pendamping Belajar v2.0
# Menggantikan bot.py untuk antarmuka ruang obrolan (chat room) mandiri
# =============================================================================

import os
import sys
import logging
from datetime import datetime
from collections import defaultdict
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Import modul sistem pakar & manajemen tugas
from inference_engine import diagnosa_masalah, format_skor
from knowledge_base    import solusi
from task_manager      import (
    tambah_tugas, lihat_tugas, hapus_tugas, hapus_semua_tugas,
    format_daftar_tugas, FORMAT_DEADLINE
)
from reminder_scheduler import scheduler, set_bot

# Setup Logging
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt= "%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)  # Aktifkan CORS untuk kemudahan pengembangan

# =============================================================================
# In-Memory State untuk FSM & Notifikasi
# =============================================================================
user_state = {}           # userId -> state string (seperti bot.py)
user_temp  = {}           # userId -> dict data sementara saat tambah tugas
user_notifications = defaultdict(list)  # userId -> list of notification dicts

def set_state(user_id, state, data=None):
    user_state[user_id] = state
    if data is not None:
        user_temp[user_id] = data
    elif state is None:
        user_temp.pop(user_id, None)

def get_state(user_id):
    return user_state.get(user_id)

def get_temp(user_id):
    return user_temp.get(user_id, {})

# =============================================================================
# Mock Bot Object untuk Reminder Scheduler
# =============================================================================
class WebBotMock:
    """
    Mocking kelas telebot agar reminder_scheduler.py dapat berjalan tanpa modifikasi.
    Alih-alih mengirim ke Telegram, ia menyimpan notifikasi ke queue in-memory
    yang nantinya di-poll oleh client web.
    """
    def send_message(self, chat_id, text, parse_mode=None):
        uid = str(chat_id)
        # Hilangkan tanda markdown tebal (*) dan miring (_) untuk kenyamanan notifikasi web jika diperlukan,
        # atau biarkan agar dirender oleh frontend parser.
        user_notifications[uid].append({
            "message": text,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        logger.info(f"[MockBot] Menampung reminder untuk user {uid}: {text[:40]}...")

# Register bot mock ke scheduler
web_bot = WebBotMock()
set_bot(web_bot)
scheduler.start()
logger.info("Reminder Scheduler berjalan di latar belakang.")

# =============================================================================
# Helper Tombol Menu (Serupa Inline Keyboard Telegram)
# =============================================================================
def buat_menu_utama():
    return [
        {"text": "🧠 Diagnosa Masalah", "callback_data": "menu_diagnosis"},
        {"text": "📋 Manajemen Tugas", "callback_data": "menu_tugas"},
        {"text": "ℹ️ Bantuan & Info", "callback_data": "menu_bantuan"},
        {"text": "🔔 Cek Pengingat", "callback_data": "menu_reminder"}
    ]

def buat_menu_tugas():
    return [
        {"text": "➕ Tambah Tugas Baru", "callback_data": "tugas_tambah"},
        {"text": "📋 Lihat Daftar Tugas", "callback_data": "tugas_lihat"},
        {"text": "🗑️ Hapus Tugas", "callback_data": "tugas_hapus"},
        {"text": "💥 Hapus Semua Tugas", "callback_data": "tugas_hapus_semua"},
        {"text": "🏠 Kembali ke Menu Utama", "callback_data": "menu_utama"}
    ]

def buat_tombol_kembali(label="🏠 Kembali ke Menu Utama"):
    return [{"text": label, "callback_data": "menu_utama"}]

def buat_konfirmasi_hapus_semua():
    return [
        {"text": "🔥 Ya, Hapus Semua!", "callback_data": "konfirmasi_hapus_semua"},
        {"text": "❌ Batal", "callback_data": "menu_tugas"}
    ]

def buat_menu_keluhan_umum():
    return [
        {"text": "📋 Mulai Tanya-Jawab", "callback_data": "diag_metode_tanya"},
        {"text": "🧠 Pilih Masalah Sendiri", "callback_data": "diag_pilih_kategori"},
        {"text": "🏠 Menu Utama", "callback_data": "menu_utama"}
    ]

def buat_menu_pilih_kategori():
    return [
        {"text": "📋 Sering Menunda (Prokrastinasi)", "callback_data": "tj_pilih_prokrastinasi"},
        {"text": "🔥 Stres & Lelah (Burnout)", "callback_data": "tj_pilih_burnout"},
        {"text": "📱 Terganggu HP/Sosmed (Distraksi)", "callback_data": "tj_pilih_distraksi"},
        {"text": "📚 Pusing Materi Kuliah (Kurang Paham)", "callback_data": "tj_pilih_kurang_paham"},
        {"text": "🏠 Menu Utama", "callback_data": "menu_utama"}
    ]

def buat_menu_pilihan_ganda(prefix, label_tinggi="Sering banget / Parah", label_sedang="Kadang-kadang saja", label_rendah="Jarang / Gak pernah"):
    return [
        {"text": label_tinggi, "callback_data": f"{prefix}_tinggi"},
        {"text": label_sedang, "callback_data": f"{prefix}_sedang"},
        {"text": label_rendah, "callback_data": f"{prefix}_rendah"}
    ]

# Pesan-pesan statis
PESAN_SELAMAT_DATANG = (
    "👋 **Halo! Selamat datang di Ruang Obrolan PakarBelajar!**\n\n"
    "Kenalin, aku asisten akademik pintarmu. Di sini kita bisa santai curhat tentang apa aja yang bikin kamu males atau stres kuliah. Aku bisa:\n\n"
    "🧠 **Mendiagnosa kesulitan belajarmu** (kayak prokrastinasi, burnout, susah fokus/distraksi, atau pusing materi kuliah).\n\n"
    "📋 **Mencatat deadline tugas** — nanti aku bakal ingetin kamu otomatis di H-3, H-1, dan hari-H biar gak panik! 🔔\n\n"
    "Kuy, pilih menu di bawah atau langsung ketik aja curhatanmu di sini, aku siap dengerin! 👇"
)

PESAN_BANTUAN = (
    "ℹ️ **Panduan Penggunaan Sistem Pakar**\n\n"
    "🧠 **FITUR DIAGNOSA**\n"
    "Sistem pakar menggunakan:\n"
    "• Normalisasi 200+ kata slang dan salah ketik (typo)\n"
    "• Pencocokan kata kunci dengan 3 level bobot\n"
    "• 18 aturan IF-THEN berbasis kombinasi kata kunci\n"
    "• Deteksi negasi (contoh: 'tidak malas' diabaikan)\n"
    "• Perhitungan tingkat keyakinan (confidence %)\n\n"
    "Kategori diagnosa:\n"
    "📋 Prokrastinasi | 🔥 Burnout | 📱 Distraksi | 📚 Kurang Paham\n\n"
    "📋 **FITUR MANAJEMEN TUGAS**\n"
    "• Catat tugas dengan nama, mata kuliah, dan deadline\n"
    "• Notifikasi otomatis di web pada H-3, H-1, H-0 sebelum deadline\n"
    "• Visualisasi status tugas (Merah/Kuning/Hijau) di panel sebelah kanan\n\n"
    "**Perintah teks cepat:**\n"
    "• `/start` - Tampilkan menu utama\n"
    "• `/tugas` - Masuk ke manajemen tugas\n"
    "• `/diagnosis` - Mulai diagnosa masalah\n"
    "• `/help` - Bantuan ini\n"
    "• `/batal` - Membatalkan alur yang sedang berjalan"
)

PESAN_MINTA_CERITA = (
    "🧠 **Yuk, curhatin masalah belajarmu!**\n\n"
    "Tulis aja apa yang kamu rasain sekarang secara bebas. Pakai bahasa santai atau slang sehari-hari juga gak apa-apa, aku paham kok! \n\n"
    "*Contoh:*\n"
    "_\"Aku males bgt ngerjain laprak, tugas udah numpuk tapi bawaannya pengen rebahan sambil scroll Tiktok terus...\"_\n\n"
    "Ketik `/batal` kalau mau kembali ke menu utama."
)

PESAN_TERLALU_PENDEK = (
    "⚠️ **Curhatnya kependekan nih...**\n\n"
    "Coba ceritain lebih detail lagi dong biar aku bisa tahu masalahmu lebih dalam. Semakin panjang ceritamu, diagnosaku bakal semakin akurat! 😊"
)

# =============================================================================
# Logika Pemrosesan Pesan / FSM Router (Web Equivalent)
# =============================================================================
def proses_pesan_web(user_id, teks_asli):
    teks = teks_asli.strip()
    state = get_state(user_id)
    replies = []

    # Filter Perintah Dasar
    if teks == "/start":
        set_state(user_id, None)
        return [{"text": PESAN_SELAMAT_DATANG, "buttons": buat_menu_utama()}]
    
    elif teks == "/help":
        set_state(user_id, None)
        return [{"text": PESAN_BANTUAN, "buttons": buat_tombol_kembali()}]
    
    elif teks == "/tugas":
        set_state(user_id, None)
        return [{"text": "📋 **Manajemen Tugas**\n\nPilih aksi yang ingin kamu lakukan:", "buttons": buat_menu_tugas()}]
    
    elif teks == "/diagnosis":
        set_state(user_id, "diagnosis")
        return [{"text": PESAN_MINTA_CERITA, "buttons": buat_tombol_kembali("❌ Batal Diagnosa")}]
    
    elif teks == "/batal":
        old_state = get_state(user_id)
        set_state(user_id, None)
        if old_state:
            return [{"text": "Dibatalkan. Kembali ke menu utama.", "buttons": buat_menu_utama()}]
        else:
            return [{"text": "Tidak ada proses aktif yang sedang berjalan.", "buttons": buat_menu_utama()}]

    # --- ROUTING FSM STATES ---
    
    # State: Diagnosa
    if state == "diagnosis":
        if len(teks.split()) < 3:
            return [{"text": PESAN_TERLALU_PENDEK, "buttons": buat_tombol_kembali("❌ Batal Diagnosa")}]
        
        kategori, skor, confidence, rules_aktif = diagnosa_masalah(teks)
        pesan_solusi = solusi.get(kategori, solusi["tidak_diketahui"])
        replies.append({"text": pesan_solusi})
        
        if kategori != "tidak_diketahui":
            pesan_skor = format_skor(skor, confidence, rules_aktif)
            replies.append({"text": pesan_skor})
        
        set_state(user_id, None)
        replies.append({
            "text": "💬 **Mau diagnosa masalah lain atau kelola tugasmu?**",
            "buttons": buat_menu_utama()
        })
        return replies

    # State: Tambah Tugas — Nama
    elif state == "tambah_nama":
        if len(teks) < 3:
            return [{"text": "⚠️ Nama tugasnya kependekan nih. Coba tulis nama tugasnya lagi ya:"}]
        data = get_temp(user_id)
        data["nama_tugas"] = teks
        set_state(user_id, "tambah_matkul", data)
        return [{
            "text": "👍 **Sip, nama tugas dicatat!**\n\n**Langkah 2/4** — Tugas ini untuk mata kuliah apa?"
        }]

    # State: Tambah Tugas — Mata Kuliah
    elif state == "tambah_matkul":
        if len(teks) < 2:
            return [{"text": "⚠️ Nama mata kuliahnya kependekan. Coba ketik lagi ya:"}]
        data = get_temp(user_id)
        data["mata_kuliah"] = teks
        set_state(user_id, "tambah_deadline", data)
        return [{
            "text": "📅 **Oke, mata kuliah dicatat!**\n\n**Langkah 3/4** — Kapan tanggal pengumpulannya (deadline)?\nTilis dengan format tanggal: `DD/MM/YYYY` ya.\n_(Contoh: `25/05/2026`)_"
        }]

    # State: Tambah Tugas — Deadline
    elif state == "tambah_deadline":
        try:
            tgl = datetime.strptime(teks, "%d/%m/%Y")
            if tgl.date() < datetime.now().date():
                return [{"text": "⚠️ Wah, deadline gak boleh di masa lalu ya! Tulis tanggal yang akan datang (format `DD/MM/YYYY`):"}]
        except ValueError:
            return [{"text": "⚠️ Format tanggal salah! Gunakan format `DD/MM/YYYY` ya\n_(Contoh: `25/05/2026`):"}]
        
        data = get_temp(user_id)
        data["deadline"] = teks
        set_state(user_id, "tambah_catatan", data)
        return [{
            "text": "📝 **Tenggat waktu tersimpan!**\n\n**Langkah 4/4** — Terakhir, ada catatan tambahan gak? (misal: *bab 1-3 aja* atau *kumpul di portal*).\n\nKetik `-` kalau gak ada catatan apa-apa."
        }]

    # State: Tambah Tugas — Catatan
    elif state == "tambah_catatan":
        data = get_temp(user_id)
        catatan = "" if teks == "-" else teks
        
        tugas = tambah_tugas(
            user_id      = int(user_id) if user_id.isdigit() else 9999, # Handle non-numeric web UUIDs safely
            nama_tugas   = data["nama_tugas"],
            mata_kuliah  = data["mata_kuliah"],
            deadline_str = data["deadline"],
            catatan      = catatan
        )
        
        # Simpan kembali tasks ke JSON dengan userId non-numerik (supaya multi-user web kompatibel)
        # task_manager.py menduga user_id adalah integer, tapi di web kita butuh support string UUID.
        # Mari kita adaptasi: kita manipulasi berkas tasks JSON jika user_id adalah string non-numeric.
        if not user_id.isdigit():
            import task_manager
            # Load tasks, ubah ID 9999 ke UUID string yang sesuai
            tasks_all = task_manager._load_tasks()
            if "9999" in tasks_all and tasks_all["9999"]:
                latest_task = tasks_all["9999"].pop()
                if user_id not in tasks_all:
                    tasks_all[user_id] = []
                tasks_all[user_id].append(latest_task)
                # Cleanup 9999 jika kosong
                if not tasks_all["9999"]:
                    del tasks_all["9999"]
                task_manager._save_tasks(tasks_all)
                tugas = latest_task
                
        set_state(user_id, None)
        
        if tugas:
            return [{
                "text": f"🎉 **Yey! Tugasmu berhasil disimpan dengan aman!**\n\n📌 **{tugas['nama_tugas']}**\n📚 {tugas['mata_kuliah']}\n📅 Deadline: {tugas['deadline']}\nID: `{tugas['id']}`\n\n🔔 Tenang aja, aku bakal ingetin kamu otomatis pas H-3, H-1, sama pas hari-H deadline biar gak kelewat! Semangat!",
                "buttons": buat_menu_tugas()
            }]
        else:
            return [{"text": "❌ Yah, gagal menyimpan tugas. Silakan coba lagi.", "buttons": buat_menu_tugas()}]

    # State: Hapus Tugas — ID
    elif state == "hapus_id":
        tugas_id = teks.strip()
        uid_int = int(user_id) if user_id.isdigit() else 9999
        
        berhasil = hapus_tugas(uid_int, tugas_id)
        if not berhasil and not user_id.isdigit():
            # Manual delete untuk non-numeric user_id
            import task_manager
            data_all = task_manager._load_tasks()
            if user_id in data_all:
                sebelum = len(data_all[user_id])
                data_all[user_id] = [t for t in data_all[user_id] if t["id"] != tugas_id]
                if len(data_all[user_id]) < sebelum:
                    task_manager._save_tasks(data_all)
                    berhasil = True
        
        set_state(user_id, None)
        if berhasil:
            return [{"text": f"✅ Tugas dengan ID `{tugas_id}` berhasil dihapus!", "buttons": buat_menu_tugas()}]
        else:
            return [{"text": f"❌ ID tugas `{tugas_id}` tidak ditemukan atau gagal dihapus.", "buttons": buat_menu_tugas()}]

    # State: Tanya Jawab Interaktif (jika user mengetik manual alih-alih klik tombol)
    elif state in ["tj_prokrastinasi", "tj_burnout", "tj_distraksi", "tj_kurang_paham"]:
        if state == "tj_prokrastinasi":
            text = "Seberapa sering kamu sengaja menunda-nunda ngerjain tugas kuliah sampai mendekati deadline?"
            prefix = "tj_ans_prok"
            lbls = ("Sering banget / Hampir selalu", "Kadang-kadang saja", "Jarang / Gak pernah")
        elif state == "tj_burnout":
            text = "Apakah kamu ngerasa capek banget secara fisik, mental, atau stres berat karena beban kuliah?"
            prefix = "tj_ans_burn"
            lbls = ("Ya, capek & stres berat", "Agak capek tapi aman", "Gak, santai aja")
        elif state == "tj_distraksi":
            text = "Ketika lagi belajar atau kuliah, seberapa gampang fokusmu teralihkan oleh HP, sosmed, game, atau lingkungan sekitar?"
            prefix = "tj_ans_dist"
            lbls = ("Gampang banget teralih", "Kadang terdistraksi", "Bisa fokus dengan baik")
        elif state == "tj_kurang_paham":
            text = "Seberapa sering kamu merasa bingung, blank, atau tidak paham dengan materi kuliah yang dijelaskan oleh dosen?"
            prefix = "tj_ans_paham"
            lbls = ("Sering bingung & gak nyambung", "Kadang-kadang bingung", "Paham-paham aja")
            
        return [{
            "text": f"⚠️ **Mohon gunakan tombol pilihan di bawah ya untuk menjawab:**\n\n{text}",
            "buttons": buat_menu_pilihan_ganda(prefix, *lbls)
        }]

    # Default Fallback (Mencoba diagnosa keluhan langsung)
    kategori, skor, confidence, rules_aktif = diagnosa_masalah(teks)
    
    if kategori != "tidak_diketahui":
        pesan_solusi = solusi.get(kategori, solusi["tidak_diketahui"])
        replies.append({"text": pesan_solusi})
        pesan_skor = format_skor(skor, confidence, rules_aktif)
        replies.append({"text": pesan_skor})
        replies.append({
            "text": "💬 **Mau diagnosa masalah lain atau kelola tugasmu?**",
            "buttons": buat_menu_utama()
        })
        return replies
        
    # Jika tidak terdiagnosa spesifik, cek apakah mengandung keluhan akademik umum
    kata_kunci_akademik = [
        "belajar", "kuliah", "kelas", "tugas", "stres", "pusing", "susah", "males", "nilai", "dosen", "ujian", "mager", "capek", "lelah", "deadline", "buku", "materi", "matkul"
    ]
    if any(k in teks.lower() for k in kata_kunci_akademik):
        return [{
            "text": (
                "👋 **Aku denger keluhanmu.**\n\n"
                "Kuliah emang kadang bikin pusing dan susah belajar. Biar kita cari tahu penyebab spesifiknya, coba ceritakan kendalamu lebih detail (misal: *seberapa sering nunda tugas*, atau *apakah terganggu HP*).\n\n"
                "Atau kamu juga bisa pilih metode di bawah ini agar kita bisa mengidentifikasi masalahnya bersama:"
            ),
            "buttons": buat_menu_keluhan_umum()
        }]
        
    # Jika benar-benar di luar akademik / sapaan biasa
    import random
    FALLBACK_RESPONSES = [
        "Hmm, aku denger kamu. Coba ceritain lebih banyak tentang kendala belajarmu sekarang, aku siap dengerin kok! Atau kamu bisa pilih menu di bawah ini:",
        "Wah, kayaknya ada yang lagi mengganjal di pikiranmu ya. Coba tumpahkan keluh kesahmu tentang tugas atau kuliah di sini biar aku bantu diagnosa. Atau mau pakai menu? Pilih di bawah:",
        "Hey! Ada yang bisa kubantu? Curhatin aja masalah belajarmu secara detail di sini, nanti aku kasih solusi terbaik. Atau mau kelola tugas? Pilih tombol di bawah ya:",
        "Tenang, tarik napas dalam-dalam... Kuliah emang kadang bikin pusing kepala. Ceritain apa yang bikin kamu ganjel dalam belajar, aku bantu cari solusinya. Atau gunakan menu berikut:"
    ]
    return [{
        "text": "💬 " + random.choice(FALLBACK_RESPONSES),
        "buttons": buat_menu_utama()
    }]

# =============================================================================
# Logika Pemrosesan Callback (Tombol Menu)
# =============================================================================
def proses_callback_web(user_id, callback_data):
    # Reset state default kecuali untuk jawaban tanya-jawab interaktif
    if not callback_data.startswith("tj_ans_"):
        set_state(user_id, None)
    replies = []
    
    if callback_data == "menu_utama":
        return [{"text": "🏠 **Menu Utama** — Pilih fitur yang kamu butuhkan:", "buttons": buat_menu_utama()}]
        
    elif callback_data == "menu_diagnosis":
        return [{
            "text": (
                "🧠 **Mulai Sesi Konsultasi Pendamping Belajar**\n\n"
                "Hai! Aku siap bantu kamu urai kesulitan belajarmu. Gimana cara konsultasi yang paling bikin kamu nyaman?\n\n"
                "💬 **Curhat Bebas**: Kamu tulis curhatan kuliahmu secara panjang lebar, nanti aku diagnosa langsung.\n"
                "📋 **Tanya Jawab**: Aku tanya 4 pertanyaan singkat satu per satu secara bergilir, kamu tinggal jawab lewat tombol."
            ),
            "buttons": [
                {"text": "💬 Curhat Bebas", "callback_data": "diag_metode_curhat"},
                {"text": "📋 Tanya Jawab Santai", "callback_data": "diag_metode_tanya"},
                {"text": "🏠 Kembali ke Menu Utama", "callback_data": "menu_utama"}
            ]
        }]
        
    elif callback_data == "diag_metode_curhat":
        set_state(user_id, "diagnosis")
        return [{"text": PESAN_MINTA_CERITA, "buttons": buat_tombol_kembali("❌ Batal Diagnosa")}]
        
    elif callback_data == "diag_metode_tanya":
        data = {"skor_interaktif": {"prokrastinasi": 0, "burnout": 0, "distraksi": 0, "kurang_paham": 0}}
        set_state(user_id, "tj_prokrastinasi", data)
        return [{
            "text": (
                "📋 **Pertanyaan 1 dari 4** (Tenggat Waktu & Tugas)\n\n"
                "Seberapa sering kamu sengaja menunda-nunda ngerjain tugas kuliah sampai mendekati deadline?"
            ),
            "buttons": buat_menu_pilihan_ganda("tj_ans_prok", "Sering banget / Hampir selalu", "Kadang-kadang saja", "Jarang / Gak pernah")
        }]
        
    elif callback_data == "diag_pilih_kategori":
        return [{
            "text": (
                "🧠 **Pilih Kategori Masalah Belajarmu**\n\n"
                "Jika kamu sudah tahu apa yang paling mengganggumu, silakan klik salah satu kategori di bawah untuk langsung mendapatkan penjelasan & solusinya:"
            ),
            "buttons": buat_menu_pilih_kategori()
        }]

    elif callback_data.startswith("tj_pilih_"):
        kategori = callback_data.replace("tj_pilih_", "")
        pesan_solusi = solusi.get(kategori, solusi["tidak_diketahui"])
        
        # Buat visualisasi skor buatan (skor 4 poin untuk kategori yang dipilih, 0 untuk lainnya)
        skor = {"prokrastinasi": 0, "burnout": 0, "distraksi": 0, "kurang_paham": 0}
        skor[kategori] = 4
        pesan_skor = format_skor(skor, 100.0, ["Pemilihan Mandiri"])
        
        return [
            {"text": pesan_solusi},
            {"text": pesan_skor},
            {
                "text": "💬 **Mau konsultasi lagi atau ada hal lain yang bisa kubantu?**",
                "buttons": buat_menu_utama()
            }
        ]

    elif callback_data.startswith("tj_ans_"):
        state = get_state(user_id)
        data = get_temp(user_id)
        if "skor_interaktif" not in data:
            data["skor_interaktif"] = {"prokrastinasi": 0, "burnout": 0, "distraksi": 0, "kurang_paham": 0}
            
        points = 0
        if callback_data.endswith("_tinggi"):
            points = 4
        elif callback_data.endswith("_sedang"):
            points = 2
            
        if state == "tj_prokrastinasi":
            data["skor_interaktif"]["prokrastinasi"] = points
            set_state(user_id, "tj_burnout", data)
            return [{
                "text": (
                    "🔥 **Pertanyaan 2 dari 4** (Stres & Kelelahan)\n\n"
                    "Apakah kamu ngerasa capek banget secara fisik, mental, atau stres berat karena beban kuliah?"
                ),
                "buttons": buat_menu_pilihan_ganda("tj_ans_burn", "Ya, capek & stres berat", "Agak capek tapi aman", "Gak, santai aja")
            }]
            
        elif state == "tj_burnout":
            data["skor_interaktif"]["burnout"] = points
            set_state(user_id, "tj_distraksi", data)
            return [{
                "text": (
                    "📱 **Pertanyaan 3 dari 4** (Fokus & Gangguan)\n\n"
                    "Ketika lagi belajar atau kuliah, seberapa gampang fokusmu teralihkan oleh HP, sosmed, game, atau lingkungan sekitar?"
                ),
                "buttons": buat_menu_pilihan_ganda("tj_ans_dist", "Gampang banget teralih", "Kadang terdistraksi", "Bisa fokus dengan baik")
            }]
            
        elif state == "tj_distraksi":
            data["skor_interaktif"]["distraksi"] = points
            set_state(user_id, "tj_kurang_paham", data)
            return [{
                "text": (
                    "📚 **Pertanyaan 4 dari 4** (Materi & Dosen)\n\n"
                    "Seberapa sering kamu merasa bingung, blank, atau tidak paham dengan materi kuliah yang dijelaskan oleh dosen?"
                ),
                "buttons": buat_menu_pilihan_ganda("tj_ans_paham", "Sering bingung & gak nyambung", "Kadang-kadang bingung", "Paham-paham aja")
            }]
            
        elif state == "tj_kurang_paham":
            data["skor_interaktif"]["kurang_paham"] = points
            skor = data["skor_interaktif"]
            skor_max = max(skor.values())
            
            set_state(user_id, None)
            replies = []
            
            if skor_max == 0:
                replies.append({
                    "text": (
                        "🎉 **Diagnosis Selesai!**\n\n"
                        "Hasil menunjukkan kondisimu sangat baik! Kamu tidak mengalami kendala belajar yang berarti saat ini. Tetap pertahankan ritme belajarmu ya! Semangat!"
                    )
                })
                pesan_skor = format_skor(skor, 100.0, ["Kondisi Belajar Prima"])
                replies.append({"text": pesan_skor})
            else:
                kategori_tertinggi = max(skor, key=skor.get)
                rules_aktif = []
                
                # Virtual rules evaluation
                if skor["prokrastinasi"] >= 4 and skor["distraksi"] >= 4:
                    rules_aktif.append("Distraksi HP Memicu Prokrastinasi")
                    skor["prokrastinasi"] += 1
                if skor["burnout"] >= 4 and skor["prokrastinasi"] >= 4:
                    rules_aktif.append("Burnout Karena Tugas Numpuk")
                    skor["burnout"] += 1
                if skor["kurang_paham"] >= 4 and skor["prokrastinasi"] >= 4:
                    rules_aktif.append("Menunda Karena Bingung Materi")
                    skor["kurang_paham"] += 1
                    
                kategori_tertinggi = max(skor, key=skor.get)
                total_skor = sum(skor.values())
                confidence = (skor[kategori_tertinggi] / total_skor * 100) if total_skor > 0 else 0.0
                
                pesan_solusi = solusi.get(kategori_tertinggi, solusi["tidak_diketahui"])
                replies.append({"text": pesan_solusi})
                pesan_skor = format_skor(skor, confidence, rules_aktif)
                replies.append({"text": pesan_skor})
                
            replies.append({
                "text": "💬 **Mau konsultasi lagi atau ada hal lain yang bisa kubantu?**",
                "buttons": buat_menu_utama()
            })
            return replies

    elif callback_data == "menu_tugas":
        return [{"text": "📋 **Manajemen Tugas**\n\nPilih aksi yang ingin kamu lakukan:", "buttons": buat_menu_tugas()}]
        
    elif callback_data == "menu_bantuan":
        return [{"text": PESAN_BANTUAN, "buttons": buat_tombol_kembali()}]
        
    elif callback_data == "menu_reminder":
        uid_int = int(user_id) if user_id.isdigit() else 9999
        pengingat = cek_deadline_dekat(uid_int)
        
        # Manual check untuk string user_id
        if not user_id.isdigit():
            import task_manager
            # Karena cek_deadline_dekat memanggil _load_tasks, dan filter user_id berjalan pada keys() string,
            # sebenarnya cek_deadline_dekat(None) memindai semua kunci termasuk UUID string!
            # Kita bisa memfilter hasil secara manual
            semua_pengingat = cek_deadline_dekat()
            pengingat = [item for item in semua_pengingat if item["user_id"] == user_id]

        if pengingat:
            replies.append({"text": "🔔 **Tugas mendekati deadline:**"})
            from task_manager import format_pesan_reminder
            for item in pengingat:
                pesan = format_pesan_reminder(item["level"], item["tugas"])
                replies.append({"text": pesan})
        else:
            replies.append({
                "text": "✅ **Tidak ada tugas mendekati deadline saat ini.**\n\nSistem akan memunculkan notifikasi otomatis saat H-3, H-1, dan H-0.",
                "buttons": buat_tombol_kembali()
            })
        return replies

    elif callback_data == "tugas_tambah":
        set_state(user_id, "tambah_nama", {})
        return [{
            "text": "➕ **Tambah Tugas Baru**\n\n**Langkah 1/4** — Apa nama tugasnya?\n_(Contoh: Laporan Praktikum Kimia)_\n\nKetik `/batal` untuk membatalkan."
        }]

    elif callback_data == "tugas_lihat":
        uid_int = int(user_id) if user_id.isdigit() else 9999
        tugas_list = lihat_tugas(uid_int)
        if not user_id.isdigit():
            # Manual load tugas untuk non-numeric UUID
            import task_manager
            tasks_all = task_manager._load_tasks()
            tugas_list = tasks_all.get(user_id, [])
            # Urutkan
            def parse_dl(t):
                try:
                    return datetime.strptime(t["deadline"], FORMAT_DEADLINE)
                except ValueError:
                    return datetime.max
            tugas_list = sorted(tugas_list, key=parse_dl)
            
        pesan = format_daftar_tugas(tugas_list)
        return [{"text": pesan, "buttons": buat_menu_tugas()}]

    elif callback_data == "tugas_hapus":
        uid_int = int(user_id) if user_id.isdigit() else 9999
        tugas_list = lihat_tugas(uid_int)
        if not user_id.isdigit():
            import task_manager
            tugas_list = task_manager._load_tasks().get(user_id, [])
            
        if not tugas_list:
            return [{"text": "📭 Daftar tugasmu kosong, tidak ada yang bisa dihapus.", "buttons": buat_menu_tugas()}]
        else:
            pesan_list = format_daftar_tugas(tugas_list)
            set_state(user_id, "hapus_id")
            return [{
                "text": pesan_list + "\n\n🗑️ **Ketik ID tugas** yang ingin dihapus:\n_(Contoh: `abc12345`)_\n\nKetik `/batal` untuk membatalkan."
            }]

    elif callback_data == "tugas_hapus_semua":
        uid_int = int(user_id) if user_id.isdigit() else 9999
        tugas_list = lihat_tugas(uid_int)
        if not user_id.isdigit():
            import task_manager
            tugas_list = task_manager._load_tasks().get(user_id, [])
            
        if not tugas_list:
            return [{"text": "📭 Daftar tugasmu sudah kosong.", "buttons": buat_menu_tugas()}]
        else:
            return [{
                "text": f"⚠️ **Konfirmasi Hapus Semua**\n\nKamu akan menghapus **{len(tugas_list)} tugas**.\nTindakan ini tidak bisa dibatalkan!\n\nLanjutkan?",
                "buttons": buat_konfirmasi_hapus_semua()
            }]

    elif callback_data == "konfirmasi_hapus_semua":
        uid_int = int(user_id) if user_id.isdigit() else 9999
        jumlah = hapus_semua_tugas(uid_int)
        if not user_id.isdigit():
            import task_manager
            data_all = task_manager._load_tasks()
            jumlah = len(data_all.get(user_id, []))
            data_all[user_id] = []
            task_manager._save_tasks(data_all)
            
        return [{"text": f"✅ **{jumlah} tugas berhasil dihapus.**", "buttons": buat_menu_utama()}]
        
    return [{"text": "Opsi tidak valid.", "buttons": buat_menu_utama()}]

# =============================================================================
# REST API Endpoints
# =============================================================================

# 1. API: Chat (Kirim Pesan atau Klik Tombol)
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json or {}
    user_id = str(data.get("userId", "")).strip()
    message = data.get("message", None)
    callback_data = data.get("callbackData", None)
    
    if not user_id:
        return jsonify({"error": "userId is required"}), 400
        
    try:
        if callback_data:
            logger.info(f"[API Chat] Callback dari user {user_id}: {callback_data}")
            replies = proses_callback_web(user_id, callback_data)
        elif message is not None:
            logger.info(f"[API Chat] Pesan dari user {user_id}: '{message}'")
            replies = proses_pesan_web(user_id, message)
        else:
            return jsonify({"error": "message or callbackData is required"}), 400
            
        return jsonify({
            "replies": replies,
            "state": get_state(user_id)
        })
    except Exception as e:
        logger.exception("Error pada API Chat:")
        return jsonify({"replies": [{"text": f"❌ Terjadi kesalahan pada server: {str(e)}"}]}), 500

# 2. API: Mendapatkan Semua Tugas (untuk Board UI)
@app.route("/api/tasks", methods=["GET"])
def api_get_tasks():
    user_id = request.args.get("userId", "").strip()
    if not user_id:
        return jsonify({"error": "userId is required"}), 400
        
    uid_int = int(user_id) if user_id.isdigit() else 9999
    tugas_list = lihat_tugas(uid_int)
    if not user_id.isdigit():
        import task_manager
        tugas_list = task_manager._load_tasks().get(user_id, [])
        # Urutkan berdasarkan deadline
        def parse_dl(t):
            try:
                return datetime.strptime(t["deadline"], FORMAT_DEADLINE)
            except ValueError:
                return datetime.max
        tugas_list = sorted(tugas_list, key=parse_dl)
        
    return jsonify({"tasks": tugas_list})

# 3. API: Menambahkan Tugas Langsung via Form UI
@app.route("/api/tasks", methods=["POST"])
def api_add_task():
    data = request.json or {}
    user_id = str(data.get("userId", "")).strip()
    nama_tugas = data.get("nama_tugas", "").strip()
    mata_kuliah = data.get("mata_kuliah", "").strip()
    deadline = data.get("deadline", "").strip()
    catatan = data.get("catatan", "").strip()
    
    if not all([user_id, nama_tugas, mata_kuliah, deadline]):
        return jsonify({"error": "Missing required fields"}), 400
        
    # Validasi format deadline
    try:
        tgl = datetime.strptime(deadline, "%d/%m/%Y")
        if tgl.date() < datetime.now().date():
            return jsonify({"error": "Deadline tidak boleh di masa lalu!"}), 400
    except ValueError:
        return jsonify({"error": "Format tanggal salah! Gunakan DD/MM/YYYY"}), 400

    uid_int = int(user_id) if user_id.isdigit() else 9999
    tugas = tambah_tugas(uid_int, nama_tugas, mata_kuliah, deadline, catatan)
    
    if tugas and not user_id.isdigit():
        # Pindahkan dari 9999 ke user_id UUID
        import task_manager
        tasks_all = task_manager._load_tasks()
        if "9999" in tasks_all and tasks_all["9999"]:
            latest_task = tasks_all["9999"].pop()
            if user_id not in tasks_all:
                tasks_all[user_id] = []
            tasks_all[user_id].append(latest_task)
            if not tasks_all["9999"]:
                del tasks_all["9999"]
            task_manager._save_tasks(tasks_all)
            tugas = latest_task
            
    if tugas:
        return jsonify({"success": True, "task": tugas})
    return jsonify({"error": "Gagal menyimpan tugas"}), 500

# 4. API: Menghapus Tugas Langsung via Board UI
@app.route("/api/tasks/<tugas_id>", methods=["DELETE"])
def api_delete_task(tugas_id):
    user_id = request.args.get("userId", "").strip()
    if not user_id:
        return jsonify({"error": "userId is required"}), 400
        
    uid_int = int(user_id) if user_id.isdigit() else 9999
    berhasil = hapus_tugas(uid_int, tugas_id)
    
    if not berhasil and not user_id.isdigit():
        import task_manager
        data_all = task_manager._load_tasks()
        if user_id in data_all:
            sebelum = len(data_all[user_id])
            data_all[user_id] = [t for t in data_all[user_id] if t["id"] != tugas_id]
            if len(data_all[user_id]) < sebelum:
                task_manager._save_tasks(data_all)
                berhasil = True
                
    if berhasil:
        return jsonify({"success": True})
    return jsonify({"error": "Tugas tidak ditemukan"}), 404

# 5. API: Polling Notifikasi Pengingat
@app.route("/api/notifications", methods=["GET"])
def api_get_notifications():
    user_id = request.args.get("userId", "").strip()
    if not user_id:
        return jsonify({"error": "userId is required"}), 400
        
    notes = user_notifications.get(user_id, [])
    # Clear notifikasi setelah diambil agar tidak ganda
    user_notifications[user_id] = []
    return jsonify({"notifications": notes})

# Route: Melayani Frontend Statis
@app.route("/")
def index():
    return app.send_static_file("index.html")

# =============================================================================
# Main Entry Point
# =============================================================================
if __name__ == "__main__":
    # Paksa stdout menggunakan UTF-8 agar tidak crash di Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        
    print("=" * 60)
    print("  🚀 Server Web Sistem Pakar Pendamping Belajar v2.0 Aktif!")
    print("  Buka browser Anda di: http://127.0.0.1:5000")
    print("  Tekan Ctrl+C untuk menghentikan server.")
    print("=" * 60)
    
    try:
        app.run(host="127.0.0.1", port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("Server dihentikan oleh user.")
    finally:
        scheduler.stop()
        logger.info("Scheduler dihentikan. Server offline.")
