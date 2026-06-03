# =============================================================================
# knowledge_base.py
# Basis Pengetahuan (Knowledge Base) Sistem Pakar
# Diagnosa Kesulitan Belajar Mahasiswa
# =============================================================================
# Sistem bobot 3 level:
#   - "utama"      : Kata kunci sangat kuat / sangat spesifik  (+4 poin)
#   - "kuat"       : Kata kunci kuat / frasa spesifik          (+2 poin)
#   - "pendukung"  : Kata kunci pendukung / kontekstual        (+1 poin)
#
# Aturan kombinasi (IF-THEN rules):
#   Jika kombinasi kata kunci tertentu muncul bersama, tambah bonus skor.
# =============================================================================

BOBOT_UTAMA     = 4
BOBOT_KUAT      = 2
BOBOT_PENDUKUNG = 1

# =============================================================================
# Kamus Normalisasi Slang → Kata Baku / Kata Kunci Standar
# =============================================================================
# Diurutkan dari yang lebih panjang ke pendek agar tidak ada partial-replace.
# Format: "slang/typo": "kata baku"

KAMUS_SLANG = {
    # -----------------------------------------------------------------------
    # Prokrastinasi / Menunda
    # -----------------------------------------------------------------------
    "males bgt"         : "malas banget",
    "males bgtt"        : "malas banget",
    "mager bgt"         : "malas gerak banget",
    "mager banget"      : "malas gerak banget",
    "gabisa mulai"      : "tidak bisa mulai",
    "gbs mulai"         : "tidak bisa mulai",
    "belom ngerjain"    : "belum mengerjakan",
    "blm ngerjain"      : "belum mengerjakan",
    "blom ngerjain"     : "belum mengerjakan",
    "belum ngerjain"    : "belum mengerjakan",
    "gak ngerjain"      : "tidak mengerjakan",
    "ga ngerjain"       : "tidak mengerjakan",
    "nunda nunda"       : "tunda tunda",
    "ditunda terus"     : "tunda terus",
    "ntar dulu"         : "nanti dulu tunda",
    "besok aja deh"     : "tunda besok",
    "besok aja"         : "tunda besok",
    "nanti aja"         : "tunda nanti",
    "nanti dulu"        : "tunda nanti",
    "entar aja"         : "tunda nanti",
    "ntar aja"          : "tunda nanti",
    "ngerjain pas dkt"  : "mengerjakan mendekati deadline",
    "ngerjain h-1"      : "mengerjakan mendekati deadline",
    "h1 baru ngerjain"  : "mengerjakan mendekati deadline",
    "sistem kebut semalam" : "sistem kebut semalam",
    "sks beneran"       : "sistem kebut semalam",
    "sks mulu"          : "sistem kebut semalam",
    "kebut semalam"     : "sistem kebut semalam",
    "last minute bgt"   : "last minute",
    "sampe lupa"        : "lupa",
    "lupa ngerjain"     : "lupa mengerjakan",
    "numpuk semua"      : "numpuk",
    "numpuk bgt"        : "numpuk",
    "deadlinenya deket" : "deadline mepet",
    "deadlinenya mepet" : "deadline mepet",
    "deadline bentar lg": "deadline mepet",
    "deadline bentar lagi": "deadline mepet",
    "telat ngumpul"     : "terlambat mengumpulkan",
    "telat kumpul"      : "terlambat mengumpulkan",
    "gak sempet"        : "tidak sempat",
    "ga sempet"         : "tidak sempat",
    "belum kesentuh"    : "belum mulai",
    "belum disentuh"    : "belum mulai",
    "blum mulai"        : "belum mulai",
    "blm mulai"         : "belum mulai",
    "ga mood ngerjain"  : "tidak mood mengerjakan",
    "gak mood ngerjain" : "tidak mood mengerjakan",
    "ga mood belajar"   : "tidak mood belajar",
    "ogah ngerjain"     : "ogah mengerjakan",

    # -----------------------------------------------------------------------
    # Burnout / Kelelahan
    # -----------------------------------------------------------------------
    "capek bgt"         : "capek banget",
    "capek bgtt"        : "capek banget",
    "cape bgt"          : "capek banget",
    "kelelahan bgt"     : "kelelahan banget",
    "udah ga kuat"      : "tidak kuat",
    "udah gak kuat"     : "tidak kuat",
    "ga kuat lagi"      : "tidak kuat",
    "gak kuat lagi"     : "tidak kuat",
    "mau nyerah"        : "menyerah",
    "pengen nyerah"     : "menyerah",
    "hampir nyerah"     : "menyerah",
    "udah nyerah"       : "menyerah",
    "muak bgt"          : "muak banget",
    "muak sama kampus"  : "muak",
    "benci kuliah"      : "muak",
    "bosan kuliah"      : "jenuh",
    "jenuh bgt"         : "jenuh banget",
    "stres bgt"         : "stres banget",
    "stres berat"       : "stres berat",
    "stress bgt"        : "stres banget",
    "depresi bgt"       : "depresi",
    "nangis terus"      : "nangis",
    "nangis mulu"       : "nangis",
    "mau nangis"        : "nangis",
    "hampir nangis"     : "nangis",
    "sampe nangis"      : "nangis",
    "gabisa tidur"      : "tidak bisa tidur",
    "ga bisa tidur"     : "tidak bisa tidur",
    "gak bisa tidur"    : "tidak bisa tidur",
    "susah tidur"       : "tidak bisa tidur",
    "kurang tidur bgt"  : "kurang tidur",
    "tidurnya dikit"    : "kurang tidur",
    "overthinking mulu" : "overthinking",
    "overthink bgt"     : "overthinking",
    "kewalahan bgt"     : "kewalahan",
    "overwhelmed bgt"   : "kewalahan",
    "down bgt"          : "down",
    "ngerasa down"      : "down",
    "abis tenaga"       : "kelelahan",
    "ga ada tenaga"     : "kelelahan",
    "gak ada tenaga"    : "kelelahan",
    "mentok bgt"        : "mentok",
    "udah mentok"       : "mentok",
    "tertekan bgt"      : "tertekan",
    "tekanan berat"     : "tertekan",
    "tekanan tinggi"    : "tertekan",
    "beban berat"       : "beban berat",
    "banyak tekanan"    : "tekanan",
    "terlalu banyak tugas" : "banyak tugas",
    "tugasnya numpuk"   : "numpuk",
    "pusing banget"     : "pusing",
    "pusing bgt"        : "pusing",
    "kepala pusing"     : "pusing",
    "mau gila"          : "frustasi",
    "udah mau gila"     : "frustasi",

    # -----------------------------------------------------------------------
    # Distraksi / Tidak Fokus
    # -----------------------------------------------------------------------
    "gabisa fokus"      : "tidak bisa fokus",
    "ga bisa fokus"     : "tidak bisa fokus",
    "gak bisa fokus"    : "tidak bisa fokus",
    "susah fokus bgt"   : "susah fokus",
    "gak fokus bgt"     : "tidak fokus",
    "ga fokus bgt"      : "tidak fokus",
    "konsen buyar"      : "konsentrasi buyar",
    "fokus buyar"       : "konsentrasi buyar",
    "pikiran melayang"  : "tidak fokus",
    "pikiran kemana mana" : "tidak fokus",
    "main hp mulu"      : "main hp",
    "main hp terus"     : "main hp",
    "gak bisa lepas dari hp" : "kecanduan hp",
    "ketagihan tiktok"  : "kecanduan tiktok",
    "tiktok mulu"       : "tiktok",
    "scroll mulu"       : "scroll media sosial",
    "scroll terus"      : "scroll media sosial",
    "rebahan mulu"      : "rebahan",
    "rebahan terus"     : "rebahan",
    "nonton drakor mulu": "distraksi",
    "netflix mulu"      : "distraksi netflix",
    "gaming mulu"       : "main game",
    "game mulu"         : "main game",
    "main game terus"   : "main game",
    "ngantuk bgt"       : "ngantuk",
    "ngantuk terus"     : "ngantuk",
    "ketiduran mulu"    : "ngantuk",
    "notif mulu"        : "notifikasi",
    "keseringan buka hp": "main hp",
    "sering buka ig"    : "instagram",
    "sering buka tiktok": "tiktok",

    # -----------------------------------------------------------------------
    # Kurang Paham / Tidak Mengerti
    # -----------------------------------------------------------------------
    "gak ngerti blas"   : "tidak mengerti",
    "gak ngerti sama sekali" : "tidak mengerti",
    "ga ngerti sama sekali"  : "tidak mengerti",
    "ga ngerti bgt"     : "tidak mengerti",
    "gak ngerti bgt"    : "tidak mengerti",
    "ga paham bgt"      : "tidak paham",
    "gak paham bgt"     : "tidak paham",
    "ga mudeng blas"    : "tidak mengerti",
    "gak mudeng blas"   : "tidak mengerti",
    "ga mudeng bgt"     : "tidak mengerti",
    "bingung bgt"       : "bingung",
    "bingung banget"    : "bingung",
    "otakku mampet"     : "tidak mengerti",
    "gak masuk otak"    : "tidak masuk otak",
    "ga masuk otak"     : "tidak masuk otak",
    "gak nyambung"      : "tidak nyambung",
    "ga nyambung"       : "tidak nyambung",
    "gak nangkep"       : "tidak menangkap",
    "ga nangkep"        : "tidak menangkap",
    "ketinggalan mulu"  : "ketinggalan",
    "ketinggalan banyak": "ketinggalan",
    "dosennya kecepatan": "dosen terlalu cepat",
    "dosennya cepet bgt": "dosen terlalu cepat",
    "penjelasannya cepet": "dosen terlalu cepat",
    "susah dipahami bgt": "susah dipahami",
    "materi susah bgt"  : "materi sulit",
    "materinya susah"   : "materi sulit",
    "materinya ribet"   : "materi sulit",
    "ribet bgt"         : "rumit",
    "abstrak bgt"       : "abstrak",
    "ga jelas bgt"      : "tidak jelas",
    "gak jelas bgt"     : "tidak jelas",
    "ga ada yang masuk" : "tidak mengerti",
    "blank total"       : "blank",
    "kosong otaknya"    : "blank",
    "gak tau apa apa"   : "tidak mengerti",
    "ga tau apa apa"    : "tidak mengerti",
    "gatau"             : "tidak tahu",
    "gtw"               : "tidak tahu",
    "ga tau"            : "tidak tahu",
    "gak tau"           : "tidak tahu",

    # -----------------------------------------------------------------------
    # Slang Bahasa Inggris (campur Indo-English)
    # -----------------------------------------------------------------------
    "overwhelmed"       : "kewalahan",
    "procrastinating"   : "menunda",
    "procrastinate"     : "menunda",
    "burnout"           : "burnout",
    "give up"           : "menyerah",
    "overthink"         : "overthinking",
    "stuck"             : "mentok",
    "literally"         : "",
    "literally so"      : "",
    "rn"                : "",
    "tbh"               : "",
    "ngl"               : "",
    "imo"               : "",
    "lmao"              : "",
    "wth"               : "",
    "idk"               : "tidak tahu",
    "idc"               : "",
    "omg"               : "",
    "fr fr"             : "",
    "fr"                : "",
    "lowkey"            : "",
    "highkey"           : "",
    "deadass"           : "",
    "vibe"              : "",
    "mood"              : "suasana hati",
    "scrolling"         : "scroll media sosial",

    # -----------------------------------------------------------------------
    # Normalisasi Umum (Typo & Singkatan)
    # -----------------------------------------------------------------------
    "bgt"       : "banget",
    "bgtt"      : "banget",
    "bngt"      : "banget",
    "mager"     : "malas gerak",
    "males"     : "malas",
    "nunda"     : "tunda",
    "gabisa"    : "tidak bisa",
    "gbs"       : "tidak bisa",
    "gak"       : "tidak",
    "ga "       : "tidak ",
    "gk "       : "tidak ",
    "ngga"      : "tidak",
    "kagak"     : "tidak",
    "enggak"    : "tidak",
    "gapapa"    : "tidak apa",
    "gapp"      : "tidak apa",
    "udah"      : "sudah",
    "udh"       : "sudah",
    "blm"       : "belum",
    "blum"      : "belum",
    "belom"     : "belum",
    "ngerasa"   : "merasa",
    "ngerti"    : "mengerti",
    "ngerjain"  : "mengerjakan",
    "ngumpul"   : "mengumpulkan",
    "dikumpul"  : "dikumpulkan",
    "dikumpulin": "dikumpulkan",
    "ngantuk"   : "mengantuk",
    "bosen"     : "bosan",
    "bete"      : "kesal",
    "sebel"     : "kesal",
    "kesel"     : "kesal",
    "sampe"     : "sampai",
    "ampe"      : "sampai",
    "banget"    : "banget",
    "numpuk"    : "menumpuk",
    "mepet"     : "mepet",
    "pengen"    : "ingin",
    "pgn"       : "ingin",
    "hampir"    : "hampir",
    "seneng"    : "senang",
    "susah"     : "sulit",
    "ky"        : "seperti",
    "kyk"       : "seperti",
    "kayak"     : "seperti",
    "tp"        : "tapi",
    "tpi"       : "tapi",
    "soalnya"   : "karena",
    "krn"       : "karena",
    "karna"     : "karena",
    "sih"       : "",
    "deh"       : "",
    "dong"      : "",
    "nih"       : "",
    "loh"       : "",
    "nah"       : "",
    "wkwk"      : "",
    "haha"      : "",
    "hehe"      : "",
    "hm"        : "",
    "hmm"       : "",
    "eh"        : "",
    "laprak"    : "laporan praktikum",
    "laporan"   : "laporan",
    "matkul"    : "mata kuliah",
    "mkul"      : "mata kuliah",
    "dospem"    : "dosen pembimbing",
    "asdos"     : "asisten dosen",
    "kelas"     : "kuliah",
    "skripsi"   : "skripsi",
    "semprop"   : "seminar proposal",
    "sidang"    : "sidang",
    "ujian"     : "ujian",
    "uts"       : "ujian tengah semester",
    "uas"       : "ujian akhir semester",
    "nilainya"  : "nilai",
}

# =============================================================================
# Knowledge Base — Kata Kunci Per Kategori (3 level bobot)
# =============================================================================

knowledge_base = {

    # -------------------------------------------------------------------------
    "prokrastinasi": {
        "utama": [
            # Kata paling diagnostik
            "menunda", "tunda", "prokrastinasi", "sistem kebut semalam",
            "last minute", "deadline mepet", "terlambat mengumpulkan",
            "mengerjakan mendekati deadline", "tidak sempat", "belum mulai",
            "numpuk", "belum mengerjakan", "lupa mengerjakan",
        ],
        "kuat": [
            "malas banget", "malas gerak banget", "kebut", "mepet",
            "deadline", "ogah mengerjakan", "tidak mood mengerjakan",
            "tidak mood belajar", "belum mulai", "tidak bisa mulai",
            "menumpuk", "tidak mengerjakan",
        ],
        "pendukung": [
            "malas", "nanti", "menunda", "ogah", "ingin", "besok",
            "lupa", "santai", "enteng", "sebentar", "sebentar lagi",
            "akhir", "malam", "jam malam", "panik", "buru-buru",
            "kalang kabut", "telat", "terlambat", "tidur dulu",
            "nonton dulu", "mandi dulu", "main dulu",
        ]
    },

    # -------------------------------------------------------------------------
    "burnout": {
        "utama": [
            # Kata paling diagnostik
            "burnout", "menyerah", "depresi", "nangis",
            "tidak kuat", "frustasi", "muak banget",
            "kelelahan banget", "stres banget", "stres berat",
            "tidak bisa tidur", "kewalahan", "tertekan",
        ],
        "kuat": [
            "capek banget", "lelah", "kelelahan", "pusing",
            "kurang tidur", "overthinking", "down", "mentok",
            "muak", "stres", "stress", "beban berat", "tekanan",
            "banyak tugas", "jenuh banget", "frustrasi",
        ],
        "pendukung": [
            "capek", "cape", "penat", "berat", "bosan", "jenuh",
            "sedih", "pressure", "nilai", "ekspektasi", "orang tua",
            "dikritik", "gagal", "takut", "khawatir", "cemas",
            "insomnia", "mood", "semangat hilang", "lemes",
        ]
    },

    # -------------------------------------------------------------------------
    "distraksi": {
        "utama": [
            # Kata paling diagnostik
            "tidak fokus", "tidak bisa fokus", "konsentrasi buyar",
            "susah fokus", "distraksi", "kecanduan hp",
            "kecanduan tiktok", "terganggu",
        ],
        "kuat": [
            "main hp", "scroll media sosial", "tiktok", "instagram",
            "youtube", "main game", "distraksi netflix",
            "mengantuk", "notifikasi", "rebahan",
        ],
        "pendukung": [
            "hp", "sosial media", "medsos", "game", "reels",
            "shorts", "twitter", "facebook", "gadget", "handphone",
            "hape", "drakor", "series", "podcast", "earphone",
            "headset", "ramai", "berisik", "suara", "teman",
            "ngobrol", "chat", "wa", "whatsapp", "ketiduran",
        ]
    },

    # -------------------------------------------------------------------------
    "kurang_paham": {
        "utama": [
            # Kata paling diagnostik
            "tidak mengerti", "tidak paham", "tidak masuk otak",
            "tidak menangkap", "tidak nyambung",
            "ketinggalan", "dosen terlalu cepat",
        ],
        "kuat": [
            "blank", "bingung", "susah dipahami", "materi sulit", "rumit",
            "abstrak", "tidak jelas", "tidak tahu",
        ],
        "pendukung": [
            "lupa", "sulit", "kompleks", "rumus", "teori",
            "konsep", "dasar", "prasyarat", "nilai jelek",
            "remedial", "mengulang", "keteteran", "tertinggal",
            "tidak ikut", "bolos", "alfa", "izin",
        ]
    }
}

# =============================================================================
# Aturan Kombinasi (IF-THEN Rules)
# =============================================================================
# Format setiap rule:
# {
#   "nama"      : Nama rule (untuk debug/log)
#   "kondisi"   : list kata kunci yang SEMUA harus ada dalam teks
#   "target"    : kategori yang mendapat bonus skor
#   "bonus"     : poin bonus
# }
# Jika SEMUA kata dalam "kondisi" ditemukan → tambah "bonus" ke "target"

RULES = [
    # --- Prokrastinasi ---
    {
        "nama"    : "R01: Deadline + Belum Mulai",
        "kondisi" : ["deadline", "belum"],
        "target"  : "prokrastinasi",
        "bonus"   : 4
    },
    {
        "nama"    : "R02: SKS + Numpuk",
        "kondisi" : ["sistem kebut semalam", "menumpuk"],
        "target"  : "prokrastinasi",
        "bonus"   : 5
    },
    {
        "nama"    : "R03: Malas + Deadline",
        "kondisi" : ["malas", "deadline"],
        "target"  : "prokrastinasi",
        "bonus"   : 3
    },
    {
        "nama"    : "R04: Nunda + Panik",
        "kondisi" : ["tunda", "panik"],
        "target"  : "prokrastinasi",
        "bonus"   : 3
    },

    # --- Burnout ---
    {
        "nama"    : "R05: Capek + Menyerah",
        "kondisi" : ["capek", "menyerah"],
        "target"  : "burnout",
        "bonus"   : 5
    },
    {
        "nama"    : "R06: Kurang Tidur + Stres",
        "kondisi" : ["kurang tidur", "stres"],
        "target"  : "burnout",
        "bonus"   : 4
    },
    {
        "nama"    : "R07: Nangis + Tertekan",
        "kondisi" : ["nangis", "tertekan"],
        "target"  : "burnout",
        "bonus"   : 5
    },
    {
        "nama"    : "R08: Overthinking + Tidak Bisa Tidur",
        "kondisi" : ["overthinking", "tidak bisa tidur"],
        "target"  : "burnout",
        "bonus"   : 4
    },

    # --- Distraksi ---
    {
        "nama"    : "R09: Main HP + Tidak Fokus",
        "kondisi" : ["main hp", "tidak fokus"],
        "target"  : "distraksi",
        "bonus"   : 5
    },
    {
        "nama"    : "R10: TikTok/IG + Belajar",
        "kondisi" : ["tiktok", "kuliah"],
        "target"  : "distraksi",
        "bonus"   : 3
    },
    {
        "nama"    : "R11: Scroll + Tidak Bisa Fokus",
        "kondisi" : ["scroll media sosial", "tidak bisa fokus"],
        "target"  : "distraksi",
        "bonus"   : 4
    },
    {
        "nama"    : "R12: Game + Deadline",
        "kondisi" : ["main game", "deadline"],
        "target"  : "distraksi",
        "bonus"   : 3
    },

    # --- Kurang Paham ---
    {
        "nama"    : "R13: Blank + Dosen Cepat",
        "kondisi" : ["blank", "dosen terlalu cepat"],
        "target"  : "kurang_paham",
        "bonus"   : 5
    },
    {
        "nama"    : "R14: Tidak Mengerti + Materi Sulit",
        "kondisi" : ["tidak mengerti", "materi sulit"],
        "target"  : "kurang_paham",
        "bonus"   : 4
    },
    {
        "nama"    : "R15: Bingung + Tidak Nyambung",
        "kondisi" : ["bingung", "tidak nyambung"],
        "target"  : "kurang_paham",
        "bonus"   : 4
    },
    {
        "nama"    : "R16: Ketinggalan + Tidak Paham",
        "kondisi" : ["ketinggalan", "tidak paham"],
        "target"  : "kurang_paham",
        "bonus"   : 4
    },

    # --- Kombinasi Lintas Kategori (Ganda) ---
    {
        "nama"    : "R17: Burnout + Prokrastinasi Ganda",
        "kondisi" : ["capek", "tunda"],
        "target"  : "burnout",
        "bonus"   : 2
    },
    {
        "nama"    : "R18: Distraksi → Tidak Paham",
        "kondisi" : ["tidak fokus", "tidak mengerti"],
        "target"  : "kurang_paham",
        "bonus"   : 2
    },
]

# =============================================================================
# Kata-kata Negasi
# =============================================================================
# Digunakan oleh cek_negasi() dengan dua pola:
#   1. Direct  : negasi + kata ("tidak malas")
#   2. Window  : negasi + 1-3 kata + kata ("ga suka nunda", "ga pernah buka hp")
# Urutan dari yang TERPANJANG ke TERPENDEK agar frasa multi-kata dicek dulu.
KATA_NEGASI = [
    # Frasa multi-kata (cek dulu sebelum yang pendek)
    "sudah tidak", "sudah bukan", "tidak lagi", "bukan lagi",
    "belum pernah", "tidak pernah", "hampir tidak",
    "tidak mau", "tidak suka", "tidak mungkin",
    "masih jauh", "masih lama", "masih banyak waktu",
    "bukan masalah", "tidak masalah", "ga masalah", "bukan berarti",
    # Kata tunggal
    "tidak", "bukan", "tanpa", "enggak", "kagak",
    # Frekuensi rendah ("jarang buka hp" → hp dinegasi)
    "jarang", "hampir",
]

# =============================================================================
# Basis Solusi — Template balasan bot untuk setiap kategori
# =============================================================================

solusi = {
    "prokrastinasi": (
        "📋 *Hasil Diagnosis: PROKRASTINASI*\n"
        "_(Tingkat keyakinan sistem > 70%)_\n\n"
        "Dari ceritamu, kamu sedang terjebak dalam siklus *menunda-nunda* "
        "yang bikin tugas makin menumpuk. Ini lebih umum dari yang kamu kira — "
        "otak kita memang suka menghindari hal yang terasa besar atau "
        "mengintimidasi.\n\n"
        "*🛠 Strategi yang terbukti efektif:*\n\n"
        "1️⃣ *Aturan 2 Menit* — Mulai hal terkecil sekarang juga. Buka "
        "dokumennya, tulis namamu di file itu. Sesederhana itu. Otak yang "
        "sudah 'mulai' jauh lebih mudah melanjutkan.\n\n"
        "2️⃣ *Teknik Pomodoro* — Belajar 25 menit, istirahat 5 menit. "
        "Atur timer, fokus, lalu bebas istirahat. Ulang 4x → istirahat panjang.\n\n"
        "3️⃣ *Pecah jadi sub-tugas* — \"Kerjakan laporan\" terlalu abstrak. "
        "Ganti dengan: \"Tulis bagian Pendahuluan dulu, 200 kata saja.\"\n\n"
        "4️⃣ *Gunakan Bot ini untuk catat tugas!* Ketik /tugas untuk menambahkan "
        "tugasmu — bot akan otomatis mengingatkanmu H-3, H-1, dan H-0 sebelum deadline.\n\n"
        "💪 *Ingat:* Mulai saja dulu, sempurna belakangan!"
    ),

    "burnout": (
        "🔥 *Hasil Diagnosis: BURNOUT (Kelelahan Akademik)*\n"
        "_(Tingkat keyakinan sistem > 70%)_\n\n"
        "Sistem mendeteksi kamu sedang mengalami *Burnout* — kelelahan fisik "
        "dan mental yang ekstrem akibat tekanan akademik berkepanjangan.\n\n"
        "Ini bukan kelemahan. Ini sinyal dari tubuhmu bahwa kamu perlu berhenti "
        "sejenak dan mengurus diri sendiri dulu.\n\n"
        "*🛠 Yang harus dilakukan sekarang:*\n\n"
        "1️⃣ *Rest Day Total* — Ambil satu hari untuk benar-benar istirahat. "
        "Tidak membuka tugas, tidak membuka chat kampus. Hanya tidur, makan, "
        "dan melakukan hal yang kamu suka.\n\n"
        "2️⃣ *Ceritakan ke orang terdekat* — Burnout yang disimpan sendiri "
        "akan makin berat. Hubungi sahabat, keluarga, atau manfaatkan layanan "
        "konseling psikologi di kampusmu (biasanya gratis).\n\n"
        "3️⃣ *Prioritaskan, bukan sempurnakan* — Kerjakan hanya tugas yang "
        "benar-benar mendesak. Nilai A tidak ada artinya jika kesehatanmu "
        "dikorbankan.\n\n"
        "4️⃣ *Tidur yang cukup* — 7-8 jam tidur lebih produktif dari "
        "begadang 12 jam dalam kondisi kelelahan.\n\n"
        "🫂 *Kamu sudah berjuang keras. Istirahat itu hak, bukan kemalasan.*"
    ),

    "distraksi": (
        "📱 *Hasil Diagnosis: DISTRAKSI & GANGGUAN FOKUS*\n"
        "_(Tingkat keyakinan sistem > 70%)_\n\n"
        "Dari analisis ceritamu, masalah utamamu adalah *distraksi digital dan "
        "lingkungan* yang mengganggu konsentrasi belajarmu.\n\n"
        "*🛠 Strategi membangun fokus kembali:*\n\n"
        "1️⃣ *Aturan HP Laci* — Saat mulai belajar, masukkan HP ke dalam laci "
        "atau taruh di ruangan lain. Jarak fisik = jarak mental dari distraksi.\n\n"
        "2️⃣ *Mode Fokus Digital* — Aktifkan mode 'Do Not Disturb' atau gunakan "
        "aplikasi seperti *Forest*, *Cold Turkey*, atau *BlockSite* untuk "
        "memblokir media sosial saat belajar.\n\n"
        "3️⃣ *Pindah tempat belajar* — Perpustakaan atau kafe sepi sangat "
        "membantu. Lingkungan baru me-reset otakmu ke mode produktif.\n\n"
        "4️⃣ *Jadwalkan waktu HP* — Bukan melarang, tapi membatasi. Contoh: "
        "\"HP bebas selama 15 menit setelah 1 jam belajar.\" Ini lebih "
        "sustainable dari total ban.\n\n"
        "🎯 *Fokus itu otot — semakin dilatih, semakin kuat!*"
    ),

    "kurang_paham": (
        "📚 *Hasil Diagnosis: KURANG PEMAHAMAN MATERI*\n"
        "_(Tingkat keyakinan sistem > 70%)_\n\n"
        "Dari ceritamu, kamu mengalami *kesenjangan pemahaman* — merasa materi "
        "yang diajarkan tidak masuk atau tidak nyambung.\n\n"
        "Ini sangat normal, terutama di mata kuliah yang membutuhkan dasar "
        "yang kuat. Solusinya bukan belajar lebih keras, tapi belajar lebih cerdas.\n\n"
        "*🛠 Langkah pemulihan pemahaman:*\n\n"
        "1️⃣ *Identifikasi gap* — Cari tahu di mana tepatnya kamu mulai tidak "
        "paham. Mungkin ada konsep dasar yang terlewat yang jadi fondasi materi "
        "selanjutnya.\n\n"
        "2️⃣ *Gunakan YouTube/sumber alternatif* — Jika penjelasan dosen tidak "
        "nyambung, coba cari penjelasan dengan gaya berbeda. Khan Academy, "
        "tutorial Indonesia, atau video visual seringkali lebih efektif.\n\n"
        "3️⃣ *Tutor sebaya (teman sekelas)* — Minta teman yang paham untuk "
        "menjelaskan. Seringkali bahasa teman lebih mudah dicerna dari buku.\n\n"
        "4️⃣ *Office hours dosen/asdos* — Beranikan diri bertanya langsung "
        "ke dosen atau asisten dosen di luar jam kelas. Mereka ada untuk ini!\n\n"
        "🌱 *Tidak paham bukan berarti bodoh — itu berarti butuh pendekatan berbeda!*"
    ),

    "tidak_diketahui": (
        "🤔 *Hmm, belum bisa mendeteksi masalah spesifikmu dari ceritamu.*\n\n"
        "Bisa ceritakan lebih detail? Bot ini bisa mendiagnosis:\n\n"
        "📋 *Prokrastinasi* — Sering menunda tugas hingga deadline mepet?\n"
        "🔥 *Burnout* — Merasa kelelahan ekstrem, stres, atau ingin menyerah?\n"
        "📱 *Distraksi* — Sulit fokus karena HP, sosmed, atau lingkungan?\n"
        "📚 *Kurang Paham* — Merasa blank, bingung, atau tidak nyambung dengan materi?\n\n"
        "Atau gunakan menu di bawah untuk menggunakan fitur lainnya! 👇"
    )
}