# =============================================================================
# bot.py
# Telegram Bot — Sistem Pakar Pendamping Belajar
# Versi 2.0 — Interaktif + Manajemen Tugas + Pengingat Deadline
# =============================================================================

import sys
import logging
import telebot
from telebot import types

from inference_engine import diagnosa_masalah, format_skor
from knowledge_base    import solusi
from task_manager      import (
    tambah_tugas, lihat_tugas, hapus_tugas, hapus_semua_tugas,
    format_daftar_tugas
)
from reminder_scheduler import scheduler, set_bot

# =============================================================================
# Konfigurasi
# =============================================================================

TOKEN = "8981001239:AAGVccvnAuu-Dw3bV4bwyYgF-jGYRBoPWe4"

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt= "%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# =============================================================================
# FSM — State per User
# =============================================================================
# State yang mungkin untuk setiap user_id:
#   None              -> Tidak ada percakapan aktif
#   "tambah_nama"     -> Menunggu input nama tugas
#   "tambah_matkul"   -> Menunggu input mata kuliah
#   "tambah_deadline" -> Menunggu input deadline
#   "tambah_catatan"  -> Menunggu input catatan
#   "hapus_id"        -> Menunggu input ID tugas yang akan dihapus
#   "diagnosis"       -> Menunggu cerita masalah belajar

user_state = {}   # user_id -> state string
user_temp  = {}   # user_id -> dict data sementara saat proses tambah tugas


def set_state(user_id: int, state, data: dict = None):
    user_state[user_id] = state
    if data is not None:
        user_temp[user_id] = data
    elif state is None:
        user_temp.pop(user_id, None)


def get_state(user_id: int):
    return user_state.get(user_id)


def get_temp(user_id: int) -> dict:
    return user_temp.get(user_id, {})


# =============================================================================
# Keyboard Helpers
# =============================================================================

def buat_menu_utama() -> types.InlineKeyboardMarkup:
    """Membuat keyboard menu utama."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("Diagnosa Masalah",   callback_data="menu_diagnosis"),
        types.InlineKeyboardButton("Manajemen Tugas",    callback_data="menu_tugas"),
    )
    kb.add(
        types.InlineKeyboardButton("Bantuan",            callback_data="menu_bantuan"),
        types.InlineKeyboardButton("Cek Reminder",       callback_data="menu_reminder"),
    )
    return kb


def buat_menu_tugas() -> types.InlineKeyboardMarkup:
    """Membuat keyboard sub-menu tugas."""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Tambah Tugas",       callback_data="tugas_tambah"),
        types.InlineKeyboardButton("Lihat Daftar Tugas", callback_data="tugas_lihat"),
        types.InlineKeyboardButton("Hapus Tugas",        callback_data="tugas_hapus"),
        types.InlineKeyboardButton("Hapus Semua Tugas",  callback_data="tugas_hapus_semua"),
        types.InlineKeyboardButton("Kembali ke Menu",    callback_data="menu_utama"),
    )
    return kb


def buat_tombol_kembali(label="Kembali ke Menu Utama") -> types.InlineKeyboardMarkup:
    """Tombol kembali ke menu utama."""
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(label, callback_data="menu_utama"))
    return kb


def buat_konfirmasi_hapus_semua() -> types.InlineKeyboardMarkup:
    """Keyboard konfirmasi hapus semua tugas."""
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("Ya, Hapus Semua!", callback_data="konfirmasi_hapus_semua"),
        types.InlineKeyboardButton("Batal",            callback_data="menu_tugas"),
    )
    return kb


# =============================================================================
# Pesan Teks Statis (semua menggunakan Markdown biasa)
# =============================================================================

PESAN_SELAMAT_DATANG = (
    "👋 *Halo! Selamat datang di Bot Pakar Pendamping Belajar v2.0!*\n\n"
    "Aku adalah asisten akademik pintarmu yang bisa:\n\n"
    "🧠 *Mendiagnosa masalah belajarmu* menggunakan Sistem Pakar\n"
    "(Prokrastinasi, Burnout, Distraksi, Kurang Paham)\n\n"
    "📋 *Mencatat tugas dan deadline* — dan mengingatkanmu otomatis\n"
    "H-3, H-1, serta H-0 sebelum tenggat!\n\n"
    "Pilih menu di bawah untuk memulai 👇"
)

PESAN_BANTUAN = (
    "ℹ️ *Panduan Penggunaan Bot Pakar v2.0*\n\n"
    "🧠 *FITUR DIAGNOSA*\n"
    "Bot menggunakan Sistem Pakar dengan:\n"
    "• Normalisasi 200+ kata slang dan typo\n"
    "• Keyword matching 3 level bobot\n"
    "• 18 aturan IF-THEN berbasis kombinasi kata\n"
    "• Deteksi negasi (contoh: 'tidak males' tidak dihitung)\n"
    "• Tingkat keyakinan (confidence %)\n\n"
    "Kategori yang bisa dideteksi:\n"
    "📋 Prokrastinasi | 🔥 Burnout | 📱 Distraksi | 📚 Kurang Paham\n\n"
    "📋 *FITUR MANAJEMEN TUGAS*\n"
    "• Catat tugas dengan nama, mata kuliah, dan deadline\n"
    "• Bot otomatis mengingatkan H-3, H-1, H-0\n"
    "• Lihat status tugas dengan indikator warna\n\n"
    "*Perintah cepat:*\n"
    "/start - Menu utama\n"
    "/tugas - Manajemen tugas\n"
    "/diagnosis - Mulai diagnosa\n"
    "/help - Bantuan ini\n"
)

PESAN_MINTA_CERITA = (
    "🧠 *Mode Diagnosa Aktif*\n\n"
    "Ceritakan masalah, kendala, atau perasaanmu terkait kuliah secara bebas.\n"
    "Gunakan bahasa sehari-hari, slang pun tidak masalah!\n\n"
    "*Contoh:*\n"
    "_\"Aku mager bgt ngerjain laprak, udah numpuk semua deadline mepet "
    "dan aku masih scroll tiktok mulu gak bisa fokus sama sekali\"_\n\n"
    "Ketik /batal untuk membatalkan."
)

PESAN_TERLALU_PENDEK = (
    "⚠️ Pesanmu terlalu singkat.\n\n"
    "Coba ceritakan lebih detail ya, minimal 1 kalimat.\n"
    "Semakin detail ceritamu, semakin akurat diagnosisnya! 😊"
)


# =============================================================================
# Handler — Command /start
# =============================================================================

@bot.message_handler(commands=['start'])
def handle_start(message):
    set_state(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        PESAN_SELAMAT_DATANG,
        parse_mode   = "Markdown",
        reply_markup = buat_menu_utama()
    )


# =============================================================================
# Handler — Command /help
# =============================================================================

@bot.message_handler(commands=['help'])
def handle_help(message):
    set_state(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        PESAN_BANTUAN,
        parse_mode   = "Markdown",
        reply_markup = buat_tombol_kembali()
    )


# =============================================================================
# Handler — Command /tugas
# =============================================================================

@bot.message_handler(commands=['tugas'])
def handle_cmd_tugas(message):
    set_state(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        "📋 *Manajemen Tugas*\n\nPilih aksi yang ingin kamu lakukan:",
        parse_mode   = "Markdown",
        reply_markup = buat_menu_tugas()
    )


# =============================================================================
# Handler — Command /diagnosis
# =============================================================================

@bot.message_handler(commands=['diagnosis'])
def handle_cmd_diagnosis(message):
    set_state(message.from_user.id, "diagnosis")
    bot.send_message(
        message.chat.id,
        PESAN_MINTA_CERITA,
        parse_mode   = "Markdown",
        reply_markup = buat_tombol_kembali("Batal Diagnosa")
    )


# =============================================================================
# Handler — Command /batal
# =============================================================================

@bot.message_handler(commands=['batal'])
def handle_batal(message):
    state = get_state(message.from_user.id)
    set_state(message.from_user.id, None)
    if state:
        bot.send_message(
            message.chat.id,
            "Dibatalkan. Kembali ke menu utama.",
            reply_markup = buat_menu_utama()
        )
    else:
        bot.send_message(
            message.chat.id,
            "Tidak ada proses yang aktif.",
            reply_markup = buat_menu_utama()
        )


# =============================================================================
# Handler — Callback Query (Tombol InlineKeyboard)
# =============================================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    data    = call.data

    # Hapus loading di tombol
    try:
        bot.answer_callback_query(call.id)
    except Exception:
        pass

    # Menu Utama
    if data == "menu_utama":
        set_state(user_id, None)
        bot.send_message(
            chat_id,
            "🏠 *Menu Utama* — Pilih fitur yang kamu butuhkan:",
            parse_mode   = "Markdown",
            reply_markup = buat_menu_utama()
        )

    # Menu Diagnosa
    elif data == "menu_diagnosis":
        set_state(user_id, "diagnosis")
        bot.send_message(
            chat_id,
            PESAN_MINTA_CERITA,
            parse_mode   = "Markdown",
            reply_markup = buat_tombol_kembali("Batal Diagnosa")
        )

    # Menu Tugas
    elif data == "menu_tugas":
        set_state(user_id, None)
        bot.send_message(
            chat_id,
            "📋 *Manajemen Tugas*\n\nPilih aksi yang ingin kamu lakukan:",
            parse_mode   = "Markdown",
            reply_markup = buat_menu_tugas()
        )

    # Menu Bantuan
    elif data == "menu_bantuan":
        bot.send_message(
            chat_id,
            PESAN_BANTUAN,
            parse_mode   = "Markdown",
            reply_markup = buat_tombol_kembali()
        )

    # Cek Reminder Manual
    elif data == "menu_reminder":
        from task_manager import cek_deadline_dekat, format_pesan_reminder
        pengingat = cek_deadline_dekat(user_id)
        if pengingat:
            bot.send_message(
                chat_id,
                "🔔 *Tugas mendekati deadline:*",
                parse_mode = "Markdown"
            )
            for item in pengingat:
                pesan = format_pesan_reminder(item["level"], item["tugas"])
                bot.send_message(chat_id, pesan, parse_mode="Markdown")
        else:
            bot.send_message(
                chat_id,
                "✅ *Tidak ada tugas mendekati deadline saat ini.*\n\n"
                "Bot akan otomatis mengingatkanmu saat H-3, H-1, dan H-0.",
                parse_mode   = "Markdown",
                reply_markup = buat_tombol_kembali()
            )

    # Tambah Tugas — Mulai Flow
    elif data == "tugas_tambah":
        set_state(user_id, "tambah_nama", {})
        bot.send_message(
            chat_id,
            "➕ *Tambah Tugas Baru*\n\n"
            "*Langkah 1/4* — Apa nama tugasnya?\n"
            "_(Contoh: Laporan Praktikum Kimia)_\n\n"
            "Ketik /batal untuk membatalkan.",
            parse_mode = "Markdown"
        )

    # Lihat Tugas
    elif data == "tugas_lihat":
        tugas_list = lihat_tugas(user_id)
        pesan = format_daftar_tugas(tugas_list)
        bot.send_message(
            chat_id,
            pesan,
            parse_mode   = "Markdown",
            reply_markup = buat_menu_tugas()
        )

    # Hapus Tugas — Minta ID
    elif data == "tugas_hapus":
        tugas_list = lihat_tugas(user_id)
        if not tugas_list:
            bot.send_message(
                chat_id,
                "📭 Daftar tugasmu kosong, tidak ada yang bisa dihapus.",
                parse_mode   = "Markdown",
                reply_markup = buat_menu_tugas()
            )
        else:
            pesan_list = format_daftar_tugas(tugas_list)
            set_state(user_id, "hapus_id")
            bot.send_message(
                chat_id,
                pesan_list + "\n\n🗑 *Ketik ID tugas* yang ingin dihapus:\n"
                "_(Contoh: `abc12345`)_\n\nKetik /batal untuk membatalkan.",
                parse_mode = "Markdown"
            )

    # Hapus Semua — Konfirmasi
    elif data == "tugas_hapus_semua":
        tugas_list = lihat_tugas(user_id)
        if not tugas_list:
            bot.send_message(
                chat_id,
                "📭 Daftar tugasmu sudah kosong.",
                parse_mode   = "Markdown",
                reply_markup = buat_menu_tugas()
            )
        else:
            bot.send_message(
                chat_id,
                f"⚠️ *Konfirmasi Hapus Semua*\n\n"
                f"Kamu akan menghapus *{len(tugas_list)} tugas*.\n"
                f"Tindakan ini tidak bisa dibatalkan!\n\nLanjutkan?",
                parse_mode   = "Markdown",
                reply_markup = buat_konfirmasi_hapus_semua()
            )

    # Konfirmasi Hapus Semua
    elif data == "konfirmasi_hapus_semua":
        jumlah = hapus_semua_tugas(user_id)
        bot.send_message(
            chat_id,
            f"✅ *{jumlah} tugas berhasil dihapus.*",
            parse_mode   = "Markdown",
            reply_markup = buat_menu_utama()
        )


# =============================================================================
# Handler — Pesan Teks Biasa (FSM Router)
# =============================================================================

@bot.message_handler(func=lambda message: True)
def handle_teks(message):
    user_id = message.from_user.id
    teks    = message.text.strip()
    state   = get_state(user_id)

    # State: Diagnosa
    if state == "diagnosis":
        _proses_diagnosis(message, teks)
        return

    # State: Tambah Tugas — Nama
    if state == "tambah_nama":
        if len(teks) < 3:
            bot.send_message(
                message.chat.id,
                "⚠️ Nama tugas terlalu pendek. Coba lagi:",
                parse_mode = "Markdown"
            )
            return
        data = get_temp(user_id)
        data["nama_tugas"] = teks
        set_state(user_id, "tambah_matkul", data)
        bot.send_message(
            message.chat.id,
            "✅ Nama tugas dicatat!\n\n"
            "*Langkah 2/4* — Nama mata kuliah?\n"
            "_(Contoh: Kimia Dasar, Kalkulus, Pemrograman Web)_",
            parse_mode = "Markdown"
        )
        return

    # State: Tambah Tugas — Mata Kuliah
    if state == "tambah_matkul":
        if len(teks) < 2:
            bot.send_message(
                message.chat.id,
                "⚠️ Nama mata kuliah terlalu pendek. Coba lagi:",
                parse_mode = "Markdown"
            )
            return
        data = get_temp(user_id)
        data["mata_kuliah"] = teks
        set_state(user_id, "tambah_deadline", data)
        bot.send_message(
            message.chat.id,
            "✅ Mata kuliah dicatat!\n\n"
            "*Langkah 3/4* — Kapan deadlinenya?\n"
            "Format: `DD/MM/YYYY`\n"
            "_(Contoh: `25/05/2026`)_",
            parse_mode = "Markdown"
        )
        return

    # State: Tambah Tugas — Deadline
    if state == "tambah_deadline":
        from datetime import datetime
        try:
            tgl = datetime.strptime(teks, "%d/%m/%Y")
            if tgl.date() < datetime.now().date():
                bot.send_message(
                    message.chat.id,
                    "⚠️ Deadline tidak boleh di masa lalu!\n"
                    "Masukkan tanggal yang akan datang dengan format `DD/MM/YYYY`",
                    parse_mode = "Markdown"
                )
                return
        except ValueError:
            bot.send_message(
                message.chat.id,
                "⚠️ Format tanggal salah! Gunakan format: `DD/MM/YYYY`\n"
                "_(Contoh: `25/05/2026`)_",
                parse_mode = "Markdown"
            )
            return
        data = get_temp(user_id)
        data["deadline"] = teks
        set_state(user_id, "tambah_catatan", data)
        bot.send_message(
            message.chat.id,
            "✅ Deadline dicatat!\n\n"
            "*Langkah 4/4* — Ada catatan tambahan?\n"
            "_(Contoh: bab 1-3 saja, dikumpul via email)_\n\n"
            "Atau ketik `-` jika tidak ada catatan.",
            parse_mode = "Markdown"
        )
        return

    # State: Tambah Tugas — Catatan (Opsional)
    if state == "tambah_catatan":
        data    = get_temp(user_id)
        catatan = "" if teks == "-" else teks

        tugas = tambah_tugas(
            user_id      = user_id,
            nama_tugas   = data["nama_tugas"],
            mata_kuliah  = data["mata_kuliah"],
            deadline_str = data["deadline"],
            catatan      = catatan
        )

        set_state(user_id, None)

        if tugas:
            bot.send_message(
                message.chat.id,
                f"🎉 *Tugas berhasil ditambahkan!*\n\n"
                f"📌 *{tugas['nama_tugas']}*\n"
                f"📚 {tugas['mata_kuliah']}\n"
                f"📅 Deadline: {tugas['deadline']}\n"
                f"ID: `{tugas['id']}`\n\n"
                f"🔔 Kamu akan otomatis diingatkan *H-3, H-1, dan H-0* sebelum deadline!",
                parse_mode   = "Markdown",
                reply_markup = buat_menu_tugas()
            )
        else:
            bot.send_message(
                message.chat.id,
                "❌ Gagal menyimpan tugas. Coba ulangi dari awal.",
                parse_mode   = "Markdown",
                reply_markup = buat_menu_tugas()
            )
        return

    # State: Hapus Tugas — Input ID
    if state == "hapus_id":
        tugas_id = teks.strip()
        berhasil = hapus_tugas(user_id, tugas_id)
        set_state(user_id, None)
        if berhasil:
            bot.send_message(
                message.chat.id,
                f"✅ Tugas dengan ID `{tugas_id}` berhasil dihapus!",
                parse_mode   = "Markdown",
                reply_markup = buat_menu_tugas()
            )
        else:
            bot.send_message(
                message.chat.id,
                f"❌ ID `{tugas_id}` tidak ditemukan. Pastikan ID yang kamu ketik sudah benar.",
                parse_mode   = "Markdown",
                reply_markup = buat_menu_tugas()
            )
        return

    # Default: Tidak Ada State Aktif
    # Jika pesan >= 5 kata, langsung diagnosa
    if len(teks.split()) >= 5:
        set_state(user_id, None)
        _proses_diagnosis(message, teks)
    else:
        bot.send_message(
            message.chat.id,
            "💬 Halo! Gunakan menu di bawah, atau ceritakan masalahmu "
            "secara langsung (minimal 5 kata) untuk mendapatkan diagnosis.",
            parse_mode   = "Markdown",
            reply_markup = buat_menu_utama()
        )


# =============================================================================
# Fungsi Proses Diagnosis
# =============================================================================

def _proses_diagnosis(message, teks: str):
    """
    Menjalankan pipeline diagnosa dan mengirimkan hasilnya ke user.
    """
    if len(teks.split()) < 3:
        bot.send_message(
            message.chat.id,
            PESAN_TERLALU_PENDEK,
            parse_mode = "Markdown"
        )
        return

    # Tampilkan indikator "sedang menganalisis"
    msg_tunggu = bot.send_message(
        message.chat.id,
        "🔍 _Sedang menganalisis ceritamu..._",
        parse_mode = "Markdown"
    )

    # Jalankan mesin inferensi
    kategori, skor, confidence, rules_aktif = diagnosa_masalah(teks)

    # Hapus pesan "sedang menganalisis"
    try:
        bot.delete_message(message.chat.id, msg_tunggu.message_id)
    except Exception:
        pass

    # Kirim solusi / hasil diagnosa
    pesan_solusi = solusi.get(kategori, solusi["tidak_diketahui"])
    bot.send_message(
        message.chat.id,
        pesan_solusi,
        parse_mode = "Markdown"
    )

    # Kirim detail skor (hanya jika ada hasil)
    if kategori != "tidak_diketahui":
        pesan_skor = format_skor(skor, confidence, rules_aktif)
        bot.send_message(
            message.chat.id,
            pesan_skor,
            parse_mode = "Markdown"
        )

    # Kirim menu lanjutan
    set_state(message.from_user.id, None)
    bot.send_message(
        message.chat.id,
        "💬 *Mau diagnosa masalah lain atau kelola tugasmu?*",
        parse_mode   = "Markdown",
        reply_markup = buat_menu_utama()
    )


# =============================================================================
# Main — Jalankan Bot
# =============================================================================

if __name__ == "__main__":
    # Paksa stdout pakai UTF-8 agar tidak crash di Windows terminal
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 60)
    print("  Bot Pakar Pendamping Belajar v2.0 -- AKTIF")
    print("  Fitur: Diagnosis | Manajemen Tugas | Pengingat Deadline")
    print("  Tekan Ctrl+C untuk menghentikan bot.")
    print("=" * 60)

    # Inject bot ke scheduler dan mulai background thread
    set_bot(bot)
    scheduler.start()
    logger.info("Reminder Scheduler dimulai sebagai background thread.")

    # Jalankan bot (blocking)
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except KeyboardInterrupt:
        logger.info("Bot dihentikan oleh user.")
    finally:
        scheduler.stop()
        logger.info("Scheduler dihentikan. Bot offline.")