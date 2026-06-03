# =============================================================================
# inference_engine.py
# Mesin Inferensi (Inference Engine) Sistem Pakar
# Menggunakan: Normalisasi Slang + Rule-Based Scoring + Deteksi Negasi
# =============================================================================

import re
from knowledge_base import (
    knowledge_base, RULES, KAMUS_SLANG,
    BOBOT_UTAMA, BOBOT_KUAT, BOBOT_PENDUKUNG, KATA_NEGASI
)


# =============================================================================
# Langkah 1 — Normalisasi Slang
# =============================================================================

def normalisasi_slang(teks: str) -> str:
    """
    Mengganti kata slang / typo dengan padanan kata baku/standar.
    Penggantian dilakukan dari frasa terpanjang ke terpendek agar
    tidak ada tumpang tindih (overlap replacement).

    Returns:
        str: Teks yang sudah dinormalisasi
    """
    teks = teks.lower()
    # Urutkan kamus dari entri terpanjang ke terpendek
    kamus_terurut = sorted(KAMUS_SLANG.items(), key=lambda x: len(x[0]), reverse=True)
    for slang, baku in kamus_terurut:
        teks = teks.replace(slang, baku)
    return teks


# =============================================================================
# Langkah 2 — Preprocessing
# =============================================================================

def preprocess_teks(teks: str) -> str:
    """
    Membersihkan teks setelah normalisasi slang:
    1. Lowercase
    2. Hapus tanda baca (kecuali spasi)
    3. Hapus whitespace berlebih

    Returns:
        str: Teks bersih siap matching
    """
    teks = teks.lower()
    teks = re.sub(r'[^\w\s]', ' ', teks)   # hapus tanda baca
    teks = re.sub(r'\s+', ' ', teks).strip()  # normalkan spasi
    return teks


# =============================================================================
# Langkah 3 — Deteksi Negasi
# =============================================================================

def cek_negasi(kata: str, teks: str) -> bool:
    """
    Mengecek apakah kata kunci dinegasikan dalam teks.
    Menggunakan DUA pola deteksi:

    Pola 1 — Direct (jarak 0 kata):
        "tidak malas" → kata "malas" tepat setelah negasi → diabaikan

    Pola 2 — Window (jarak 1-3 kata):
        "ga suka nunda"   → "tidak suka tunda"   → diabaikan
        "ga pernah malas" → "tidak pernah malas"  → diabaikan
        "jarang buka hp"  → "jarang" + 1 kata + "hp" → diabaikan

    Returns:
        bool: True jika kata kunci dinegasikan, False jika tidak
    """
    for negasi in KATA_NEGASI:
        negasi_esc = re.escape(negasi)
        kata_esc   = re.escape(kata)

        # Pola 1: Direct — negasi langsung sebelum kata kunci
        pola_direct = rf'\b{negasi_esc}\s+{kata_esc}\b'
        if re.search(pola_direct, teks):
            return True

        # Pola 2: Window — negasi + 1 s/d 4 kata perantara + kata kunci
        # Contoh: "tidak suka nunda", "ga fokus itu bukan masalah"
        pola_window = rf'\b{negasi_esc}\s+(?:\w+\s+){{1,4}}{kata_esc}\b'
        if re.search(pola_window, teks):
            return True

    return False


# =============================================================================
# Langkah 4 — Hitung Skor Keyword Matching (3 Level)
# =============================================================================

def _cocok(kata: str, teks: str) -> bool:
    """
    Mengecek apakah kata kunci muncul sebagai kata utuh (bukan substring)
    menggunakan word boundary regex.

    Contoh: 'tunda' tidak akan cocok dengan 'metunda'.

    Returns:
        bool: True jika kata kunci ditemukan sebagai kata utuh
    """
    pola = rf'\b{re.escape(kata)}\b'
    return bool(re.search(pola, teks))


def hitung_skor_keyword(teks_bersih: str) -> dict:
    """
    Menghitung skor keyword matching dengan 3 level bobot.
    Menggunakan word-boundary matching agar tidak ada partial match.
    Kata kunci yang dinegasikan tidak dihitung.

    Returns:
        dict: Skor per kategori dari keyword matching
    """
    skor = {kategori: 0 for kategori in knowledge_base}

    for kategori, kata_kunci_dict in knowledge_base.items():
        # Level 1 — Utama (bobot +4)
        for kata in kata_kunci_dict.get("utama", []):
            if _cocok(kata, teks_bersih):
                if not cek_negasi(kata, teks_bersih):
                    skor[kategori] += BOBOT_UTAMA

        # Level 2 — Kuat (bobot +2)
        for kata in kata_kunci_dict.get("kuat", []):
            if _cocok(kata, teks_bersih):
                if not cek_negasi(kata, teks_bersih):
                    skor[kategori] += BOBOT_KUAT

        # Level 3 — Pendukung (bobot +1)
        for kata in kata_kunci_dict.get("pendukung", []):
            if _cocok(kata, teks_bersih):
                if not cek_negasi(kata, teks_bersih):
                    skor[kategori] += BOBOT_PENDUKUNG

    return skor


# =============================================================================
# Langkah 5 — Terapkan IF-THEN Rules (Rule-Based Bonus)
# =============================================================================

def terapkan_rules(teks_bersih: str, skor: dict) -> tuple[dict, list]:
    """
    Menerapkan aturan kombinasi (IF-THEN rules) dari knowledge base.
    Sebuah rule aktif HANYA jika:
      - SEMUA kondisi ditemukan dalam teks (word-boundary)
      - DAN tidak ada kondisi yang dinegasikan

    Returns:
        tuple: (skor yang sudah diupdate, list nama rule yang aktif)
    """
    rules_aktif = []
    for rule in RULES:
        semua_kondisi_terpenuhi = all(
            _cocok(kondisi, teks_bersih) and not cek_negasi(kondisi, teks_bersih)
            for kondisi in rule["kondisi"]
        )
        if semua_kondisi_terpenuhi:
            skor[rule["target"]] += rule["bonus"]
            rules_aktif.append(rule["nama"])
    return skor, rules_aktif


# =============================================================================
# Fungsi Utama — Diagnosa Masalah
# =============================================================================

def diagnosa_masalah(teks_asli: str) -> tuple:
    """
    Pipeline lengkap diagnosa:
    1. Normalisasi slang
    2. Preprocessing
    3. Hitung skor keyword (3 level + deteksi negasi)
    4. Terapkan IF-THEN rules
    5. Tentukan kategori terpilih + hitung confidence

    Returns:
        tuple: (kategori: str, skor: dict, confidence: float, rules_aktif: list)
    """
    # Step 1 & 2: Normalisasi + preprocessing
    teks_norm   = normalisasi_slang(teks_asli)
    teks_bersih = preprocess_teks(teks_norm)

    # Step 3: Keyword matching
    skor = hitung_skor_keyword(teks_bersih)

    # Step 4: Terapkan rules
    skor, rules_aktif = terapkan_rules(teks_bersih, skor)

    # Step 5: Tentukan kategori
    skor_max = max(skor.values())

    # Threshold minimum: butuh skor >= 4 agar tidak salah diagnosa
    # dari 1-2 kata pendek yang kebetulan match kuat (misal: 'capek bgt')
    # Skor 4 = minimal 1 kata utama ATAU 2 kata kuat
    if skor_max < 4:
        return "tidak_diketahui", skor, 0.0, []

    kategori_tertinggi = max(skor, key=skor.get)
    total_skor = sum(skor.values())
    confidence = (skor[kategori_tertinggi] / total_skor * 100) if total_skor > 0 else 0.0

    return kategori_tertinggi, skor, round(confidence, 1), rules_aktif


# =============================================================================
# Format Output Skor
# =============================================================================

LABEL_MAP = {
    "prokrastinasi": "📋 Prokrastinasi",
    "burnout"       : "🔥 Burnout",
    "distraksi"     : "📱 Distraksi",
    "kurang_paham"  : "📚 Kurang Paham",
}

def format_skor(skor: dict, confidence: float, rules_aktif: list) -> str:
    """
    Memformat detail skor menjadi pesan Telegram yang informatif.
    Menampilkan: bar skor tiap kategori, confidence %, dan rules yang aktif.

    Returns:
        str: Pesan terformat untuk dikirim ke Telegram
    """
    skor_max = max(skor.values()) if skor else 1

    lines = [f"📊 *Detail Analisis Sistem Pakar* _(Confidence: {confidence:.1f}%)_\n"]
    for kategori, nilai in sorted(skor.items(), key=lambda x: x[1], reverse=True):
        label = LABEL_MAP.get(kategori, kategori)
        # Bar proporsional maks 10 karakter
        panjang_bar = round((nilai / skor_max) * 10) if skor_max > 0 else 0
        bar = "█" * panjang_bar + "░" * (10 - panjang_bar)
        lines.append(f"  {label}: `{bar}` ({nilai} poin)")

    if rules_aktif:
        lines.append("\n🔗 *Aturan yang Aktif:*")
        for nama_rule in rules_aktif:
            lines.append(f"  ✅ `{nama_rule}`")

    return "\n".join(lines)