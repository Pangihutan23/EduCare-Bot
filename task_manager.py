# =============================================================================
# task_manager.py
# Manajemen Tugas — Penyimpanan & Operasi CRUD berbasis JSON
# =============================================================================
# Struktur data (tasks.json):
# {
#   "123456789": [
#     {
#       "id"          : "abc12",
#       "nama_tugas"  : "Laporan Praktikum",
#       "mata_kuliah" : "Kimia Dasar",
#       "deadline"    : "25/05/2026",   ← format DD/MM/YYYY
#       "catatan"     : "Bab 1-3 saja",
#       "dibuat"      : "20/05/2026 10:30"
#     },
#     ...
#   ],
#   ...
# }
# =============================================================================

import json
import os
import uuid
from datetime import datetime, timedelta

# Path file penyimpanan tugas (satu folder dengan bot.py)
TASKS_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")

FORMAT_DEADLINE = "%d/%m/%Y"
FORMAT_DIBUAT   = "%d/%m/%Y %H:%M"


# =============================================================================
# Utilitas File
# =============================================================================

def _load_tasks() -> dict:
    """Memuat seluruh data tugas dari file JSON."""
    if not os.path.exists(TASKS_FILE):
        return {}
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_tasks(data: dict) -> None:
    """Menyimpan seluruh data tugas ke file JSON."""
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# =============================================================================
# CRUD — Tambah / Lihat / Hapus Tugas
# =============================================================================

def tambah_tugas(user_id: int, nama_tugas: str, mata_kuliah: str,
                 deadline_str: str, catatan: str = "") -> dict | None:
    """
    Menambahkan tugas baru untuk seorang user.

    Args:
        user_id      : Telegram user ID
        nama_tugas   : Nama/judul tugas
        mata_kuliah  : Nama mata kuliah
        deadline_str : String deadline format DD/MM/YYYY
        catatan      : Catatan tambahan (opsional)

    Returns:
        dict: Data tugas yang baru ditambahkan, atau None jika format deadline salah
    """
    # Validasi format deadline
    try:
        datetime.strptime(deadline_str, FORMAT_DEADLINE)
    except ValueError:
        return None

    data = _load_tasks()
    uid  = str(user_id)
    if uid not in data:
        data[uid] = []

    tugas_baru = {
        "id"          : str(uuid.uuid4())[:8],
        "nama_tugas"  : nama_tugas.strip(),
        "mata_kuliah" : mata_kuliah.strip(),
        "deadline"    : deadline_str.strip(),
        "catatan"     : catatan.strip(),
        "dibuat"      : datetime.now().strftime(FORMAT_DIBUAT),
        "sudah_diingatkan": []   # menyimpan ["H-3", "H-1", "H-0"] yang sudah dikirim
    }
    data[uid].append(tugas_baru)
    _save_tasks(data)
    return tugas_baru


def lihat_tugas(user_id: int) -> list:
    """
    Mengambil semua tugas milik user, diurutkan dari deadline terdekat.

    Returns:
        list: Daftar tugas (bisa kosong)
    """
    data = _load_tasks()
    tugas_list = data.get(str(user_id), [])

    # Urutkan berdasarkan deadline terdekat
    def parse_dl(t):
        try:
            return datetime.strptime(t["deadline"], FORMAT_DEADLINE)
        except ValueError:
            return datetime.max

    return sorted(tugas_list, key=parse_dl)


def hapus_tugas(user_id: int, tugas_id: str) -> bool:
    """
    Menghapus tugas berdasarkan ID pendek (8 karakter).

    Returns:
        bool: True jika berhasil dihapus, False jika tidak ditemukan
    """
    data = _load_tasks()
    uid  = str(user_id)
    if uid not in data:
        return False

    sebelum = len(data[uid])
    data[uid] = [t for t in data[uid] if t["id"] != tugas_id]
    if len(data[uid]) == sebelum:
        return False

    _save_tasks(data)
    return True


def hapus_semua_tugas(user_id: int) -> int:
    """
    Menghapus semua tugas milik seorang user.

    Returns:
        int: Jumlah tugas yang dihapus
    """
    data = _load_tasks()
    uid  = str(user_id)
    jumlah = len(data.get(uid, []))
    data[uid] = []
    _save_tasks(data)
    return jumlah


# =============================================================================
# Pengingat Deadline
# =============================================================================

def cek_deadline_dekat(user_id: int = None) -> list:
    """
    Memeriksa tugas yang deadlinenya H-3, H-1, atau H-0 (hari ini).
    Hanya mengembalikan tugas yang BELUM pernah diingatkan pada level tersebut.

    Args:
        user_id: Jika diisi, hanya cek tugas milik user tersebut.
                 Jika None, cek SEMUA user.

    Returns:
        list of dict: [
            {
                "user_id": "...",
                "tugas"  : {...},
                "level"  : "H-3" / "H-1" / "H-0"
            },
            ...
        ]
    """
    data     = _load_tasks()
    sekarang = datetime.now().date()
    hasil    = []

    uid_filter = [str(user_id)] if user_id else list(data.keys())

    for uid in uid_filter:
        tugas_list = data.get(uid, [])
        perlu_simpan = False
        for tugas in tugas_list:
            try:
                tgl_deadline = datetime.strptime(tugas["deadline"], FORMAT_DEADLINE).date()
            except ValueError:
                continue

            selisih = (tgl_deadline - sekarang).days

            level = None
            if selisih == 3:
                level = "H-3"
            elif selisih == 1:
                level = "H-1"
            elif selisih == 0:
                level = "H-0"

            if level and level not in tugas.get("sudah_diingatkan", []):
                hasil.append({
                    "user_id": uid,
                    "tugas"  : tugas,
                    "level"  : level
                })
                # Tandai sudah diingatkan agar tidak kirim berulang
                if "sudah_diingatkan" not in tugas:
                    tugas["sudah_diingatkan"] = []
                tugas["sudah_diingatkan"].append(level)
                perlu_simpan = True

        if perlu_simpan:
            _save_tasks(data)

    return hasil


# =============================================================================
# Formatter Pesan
# =============================================================================

def format_daftar_tugas(tugas_list: list) -> str:
    """
    Memformat daftar tugas menjadi string Telegram yang rapi.

    Returns:
        str: Pesan terformat
    """
    if not tugas_list:
        return (
            "📭 *Daftar tugasmu kosong!*\n\n"
            "Gunakan tombol *➕ Tambah Tugas* untuk mencatat tugas baru.\n"
            "Bot akan otomatis mengingatkanmu H-3, H-1, dan H-0 sebelum deadline! 🔔"
        )

    sekarang = datetime.now().date()
    lines = ["📋 *Daftar Tugasmu:*\n"]

    for i, t in enumerate(tugas_list, 1):
        try:
            tgl = datetime.strptime(t["deadline"], FORMAT_DEADLINE).date()
            selisih = (tgl - sekarang).days
            if selisih < 0:
                status = "🔴 Terlewat!"
            elif selisih == 0:
                status = "🚨 Hari ini!"
            elif selisih == 1:
                status = "🔴 Besok!"
            elif selisih <= 3:
                status = f"⚠️ {selisih} hari lagi"
            else:
                status = f"🟢 {selisih} hari lagi"
        except ValueError:
            status = "❓"
            tgl = "?"

        lines.append(
            f"*{i}. {t['nama_tugas']}*\n"
            f"   📚 {t['mata_kuliah']}\n"
            f"   📅 Deadline: {t['deadline']} — {status}\n"
            f"   🆔 ID: `{t['id']}`"
            + (f"\n   📝 _{t['catatan']}_" if t.get("catatan") else "")
        )

    lines.append("\n💡 Untuk menghapus tugas, gunakan tombol *🗑 Hapus Tugas*.")
    return "\n\n".join(lines) if len(lines) > 1 else lines[0]


def format_pesan_reminder(level: str, tugas: dict) -> str:
    """
    Memformat pesan notifikasi pengingat deadline.

    Returns:
        str: Pesan pengingat
    """
    emoji_map = {
        "H-3": "⚠️",
        "H-1": "🔴",
        "H-0": "🚨",
    }
    pesan_map = {
        "H-3": "Tenggat *3 hari lagi*! Sudah mulai dikerjakan?",
        "H-1": "*BESOK* adalah hari terakhir pengumpulan!",
        "H-0": "*HARI INI* adalah hari pengumpulan!",
    }
    emoji = emoji_map.get(level, "🔔")
    pesan = pesan_map.get(level, "Deadline semakin dekat!")

    return (
        f"{emoji} *PENGINGAT DEADLINE {level}*\n\n"
        f"📌 *{tugas['nama_tugas']}*\n"
        f"📚 Mata Kuliah: {tugas['mata_kuliah']}\n"
        f"📅 Deadline: {tugas['deadline']}\n\n"
        f"⏰ {pesan}\n\n"
        f"Semangat! Kamu pasti bisa menyelesaikannya! 💪"
    )
