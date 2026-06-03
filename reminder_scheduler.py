# =============================================================================
# reminder_scheduler.py
# Scheduler Pengingat Deadline — Background Thread
# =============================================================================
# Menjalankan pengecekan deadline setiap 30 menit.
# Jika ada tugas yang H-3, H-1, atau H-0 dan belum diingatkan,
# akan mengirimkan notifikasi ke user lewat Telegram.
# =============================================================================

import threading
import logging
from datetime import datetime
from task_manager import cek_deadline_dekat, format_pesan_reminder

logger = logging.getLogger(__name__)

# Interval pengecekan dalam detik (30 menit)
INTERVAL_DETIK = 30 * 60

# Referensi global ke objek bot Telegram (di-inject dari bot.py)
_bot_instance = None


def set_bot(bot):
    """Menyimpan referensi ke objek bot Telegram."""
    global _bot_instance
    _bot_instance = bot


# =============================================================================
# Fungsi Pengecekan & Pengiriman Reminder
# =============================================================================

def _jalankan_pengecekan():
    """
    Fungsi inti yang dipanggil setiap siklus:
    1. Cek semua tugas dari semua user
    2. Untuk setiap tugas yang mendekati deadline → kirim notifikasi
    """
    if _bot_instance is None:
        logger.warning("[Scheduler] Bot instance belum di-set!")
        return

    try:
        pengingat_list = cek_deadline_dekat()  # cek semua user
        if pengingat_list:
            logger.info(f"[Scheduler] Menemukan {len(pengingat_list)} pengingat untuk dikirim.")

        for item in pengingat_list:
            user_id = item["user_id"]
            tugas   = item["tugas"]
            level   = item["level"]
            pesan   = format_pesan_reminder(level, tugas)

            try:
                _bot_instance.send_message(
                    chat_id    = int(user_id),
                    text       = pesan,
                    parse_mode = "Markdown"
                )
                logger.info(
                    f"[Scheduler] Pengingat {level} terkirim ke user {user_id} "
                    f"untuk tugas '{tugas['nama_tugas']}'"
                )
            except Exception as e:
                logger.error(
                    f"[Scheduler] Gagal kirim pengingat ke user {user_id}: {e}"
                )

    except Exception as e:
        logger.error(f"[Scheduler] Error saat pengecekan: {e}")


# =============================================================================
# Loop Scheduler dengan threading.Timer
# =============================================================================

class ReminderScheduler:
    """
    Scheduler berbasis threading.Timer.
    Berjalan secara rekursif setiap INTERVAL_DETIK.
    """

    def __init__(self, interval: int = INTERVAL_DETIK):
        self.interval   = interval
        self._timer     = None
        self._is_running = False

    def _loop(self):
        """Loop internal yang memanggil pengecekan dan menjadwalkan diri ulang."""
        jam_sekarang = datetime.now().strftime("%H:%M:%S")
        logger.info(f"[Scheduler] ⏰ Pengecekan deadline dimulai: {jam_sekarang}")
        _jalankan_pengecekan()

        # Jadwalkan iterasi berikutnya
        if self._is_running:
            self._timer = threading.Timer(self.interval, self._loop)
            self._timer.daemon = True   # mati otomatis saat main thread berhenti
            self._timer.start()

    def start(self):
        """Memulai scheduler (pengecekan pertama langsung dijalankan)."""
        if self._is_running:
            return
        self._is_running = True
        logger.info(
            f"[Scheduler] 🚀 Reminder Scheduler dimulai. "
            f"Interval: {self.interval // 60} menit."
        )
        # Jalankan langsung tanpa menunggu interval pertama
        self._loop()

    def stop(self):
        """Menghentikan scheduler."""
        self._is_running = False
        if self._timer:
            self._timer.cancel()
        logger.info("[Scheduler] 🛑 Reminder Scheduler dihentikan.")


# Singleton instance
scheduler = ReminderScheduler()
