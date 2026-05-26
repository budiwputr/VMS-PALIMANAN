# ISSUE-09 — Python VMS Display Application

## Konteks

Dibutuhkan aplikasi Python fullscreen yang menampilkan data kendaraan dari WIM secara real-time
di layar **Variable Message Sign (VMS)** berukuran **1280 × 768 px**.

Alur hardware:

```
PC Server (Python App fullscreen) ──HDMI──► Linsn Sending Box ──LAN──► LED Panel VMS
```

Python app polling endpoint `GET /api/display/latest` setiap 3 detik,
lalu merender data ke layar menggunakan Pygame.

---

## Spesifikasi Teknis

| Item | Nilai |
|------|-------|
| Resolusi layar | 1280 × 768 px |
| Sending Box | Linsn (mirror HDMI dari PC) |
| Sumber data | `GET /api/display/latest` (lihat ISSUE-08) |
| Interval polling | 3 detik |
| Platform | Windows (PC Server) |
| Python | 3.10+ |
| Library utama | `pygame`, `requests` |

---

## Struktur Project

```
vms-display/
├── main.py           ← entry point
├── config.py         ← semua konstanta (URL, warna, font, resolusi)
├── api_client.py     ← thread polling API
├── renderer.py       ← semua logika render Pygame
└── requirements.txt  ← pygame, requests
```

> Project ini berdiri sendiri (repo/folder terpisah dari backend WIM).

---

## Layout Layar (1280 × 768)

```
┌──────────────────────────────────────────────── 1280px ──────────┐
│  WIM MONITORING — PALIMANAN                       08:25:41  68px │
├────────────────────────────────────┬─────────────────────────────┤
│  NOMOR POLISI                      │  GOLONGAN              150px│
│  B 9374 KCF                        │  2 SUMBU                    │
├────────────────────────────────────┴─────────────────────────────┤
│  BERAT PER SUMBU (KG)                                       188px│
│  Sumbu 1 ██████████  4.000   Sumbu 4 ░░░░░░░░░░░░     0        │
│  Sumbu 2 ████████    4.000   Sumbu 5 ░░░░░░░░░░░░     0        │
│  Sumbu 3 ░░░░░░░░░░░░    0   Sumbu 6 ░░░░░░░░░░░░     0        │
│                                  TOTAL BERAT : 8.000 KG          │
├────────────────────────────────────┬─────────────────────────────┤
│  DIMENSI      NILAI      BATAS     │  BERAT    NILAI    BATAS182px│
│  Panjang  8.000 mm  12.000 mm      │  Total 8.000 kg 12.000 kg  │
│  Lebar    2.000 mm   2.550 mm      │                             │
│  Tinggi   3.000 mm   4.000 mm      │                             │
├────────────────────────────────────┴─────────────────────────────┤
│                                                             180px │
│                          ✓  NORMAL                               │
└──────────────────────────────────────────────────────────────────┘
```

---

## Zona Layar

| Zona | Tinggi | Konten |
|------|--------|--------|
| Header | 68px | Judul stasiun + jam digital real-time |
| Identitas | 150px | Nomor polisi (besar) + golongan (sumbu) |
| Berat sumbu | 188px | Bar chart teks 6 sumbu + total berat |
| Dimensi & Berat | 182px | Tabel panjang/lebar/tinggi vs batas, total berat vs batas |
| Status | 180px | Kesimpulan besar dengan warna & animasi |

---

## Warna Status

| Kesimpulan | Warna | Animasi |
|-----------|-------|---------|
| `normal` | Hijau `#00EE00` | Statis |
| `overload` | Merah `#FF2222` | Berkedip (1.2 detik) |
| `overdimension` | Oranye `#FF8C00` | Berkedip (1.2 detik) |
| `overload & overdimension` | Merah `#FF2222` | Berkedip cepat (0.8 detik) |

Nilai yang melebihi batas (dimensi/berat) ditampilkan dengan warna merah `#FF3333`.

---

## Detail Per File

### `config.py`

Berisi semua konstanta — **tidak ada hardcode di file lain**:

```python
# Koneksi API
API_BASE_URL  = 'http://localhost:3000'
API_KEY       = 'test-client-key'       # CLIENT_API_KEY di .env backend
POLL_INTERVAL = 3                       # detik

# Layar
SCREEN_W = 1280
SCREEN_H = 768
FPS      = 30

# Zona tinggi (px) — total harus = SCREEN_H
ZONE_HEADER  = 68
ZONE_ID      = 150
ZONE_AXLE    = 188
ZONE_DETAIL  = 182
ZONE_STATUS  = 180   # = 768 - 68 - 150 - 188 - 182

# Warna (R, G, B)
COLOR_BG          = (0,   0,   0)
COLOR_TEXT        = (255, 255, 255)
COLOR_DIM         = (85,  85,  85)
COLOR_GOLD        = (255, 215, 0)
COLOR_DIVIDER     = (30,  30,  30)
COLOR_BAR_BG      = (26,  26,  26)
COLOR_BAR_FILL    = (0,   153, 255)
COLOR_NORMAL      = (0,   238, 0)
COLOR_OVERLOAD    = (255, 34,  34)
COLOR_OVERDIM     = (255, 140, 0)
COLOR_OVER_VALUE  = (255, 51,  51)

# Ukuran font (px)
FONT_HEADER    = 20
FONT_LABEL     = 13
FONT_PLATE     = 66
FONT_GOLONGAN  = 50
FONT_AXLE_LBL  = 15
FONT_AXLE_VAL  = 19
FONT_AXLE_TOT  = 20
FONT_TBL_HEAD  = 12
FONT_TBL_VAL   = 22
FONT_TBL_NAME  = 17
FONT_STATUS    = 88
FONT_WAIT      = 32
```

---

### `api_client.py`

Thread background yang polling API secara terus-menerus.

**Tanggung jawab:**
- Panggil `GET /api/display/latest` dengan header `x-api-key`
- Jika response **200** → parse JSON, simpan ke `shared_state['data']`
- Jika response **204** → set `shared_state['data'] = None` (tampil waiting)
- Jika **error network / timeout** → **jangan ubah state** (biarkan data terakhir tetap tampil)
- Gunakan `threading.Lock` untuk akses `shared_state` yang thread-safe

**State yang di-share ke renderer:**

```python
shared_state = {
    'data':    None,    # dict dari API, atau None jika belum ada
    'updated': False,   # flag: ada data baru yang belum dirender
}
```

---

### `renderer.py`

Semua fungsi menggambar ke Pygame surface.

**Fungsi utama:**

| Fungsi | Keterangan |
|--------|-----------|
| `draw_waiting(surface, fonts)` | Layar "Menunggu data kendaraan..." dengan teks berkedip |
| `draw_vehicle(surface, fonts, data, tick)` | Render semua zona dari data API |
| `draw_header(surface, fonts)` | Judul + jam digital (update tiap detik) |
| `draw_identity(surface, fonts, data)` | Nomor polisi + golongan |
| `draw_axle(surface, fonts, data)` | 6 bar sumbu + total berat |
| `draw_detail(surface, fonts, data)` | Tabel dimensi (kiri) + tabel berat (kanan) |
| `draw_status(surface, fonts, data, tick)` | Status besar dengan warna + efek kedip |
| `draw_bar(surface, rect, val, max_val)` | Satu bar horizontal untuk berat sumbu |
| `draw_divider(surface, y)` | Garis pemisah horizontal antar zona |

**Parameter `tick`** dipakai untuk animasi kedip — diisi dari `pygame.time.get_ticks()` di main loop.

---

### `main.py`

Orkestrasi semua komponen.

**Alur:**

```
1. Init Pygame → set window 1280×768 fullscreen
2. Load semua font dari config
3. Start api_client thread (daemon=True)
4. Masuk main loop:
   a. Cek event (ESC → quit saat development)
   b. Baca shared_state dengan lock
   c. Jika data ada → draw_vehicle()
      Jika tidak    → draw_waiting()
   d. pygame.display.flip()
   e. clock.tick(FPS)
```

**Catatan:**
- Thread `api_client` berjalan sebagai `daemon` agar otomatis berhenti saat main loop keluar
- Gunakan `pygame.FULLSCREEN` flag saat produksi; `pygame.RESIZABLE` atau tanpa flag saat development

---

## Sumber Data API

Endpoint: `GET /api/display/latest`  
Header: `x-api-key: <CLIENT_API_KEY>`

Response yang dipakai:

```json
{
  "data": {
    "nomor_polisi":   "B 9374 KCF",
    "golongan":       2,
    "berat_axle_kg":  { "axle1": 4000, "axle2": 4000, "axle3": 0, "axle4": 0, "axle5": 0, "axle6": 0 },
    "total_berat_kg": 8000,
    "dimensi_mm":     { "panjang": 8000, "lebar": 2000, "tinggi": 3000 },
    "limit": {
      "limit_panjang_mm": 12000,
      "limit_lebar_mm":    2550,
      "limit_tinggi_mm":   4000,
      "limit_berat_kg":   12000
    },
    "status": {
      "is_overload":      false,
      "is_overdimension": false,
      "kesimpulan":       "normal"
    }
  }
}
```

Jika `limit` bernilai `null`, semua perbandingan dimensi/berat dinonaktifkan (tidak tampilkan batas).

---

## Testing

Gunakan simulation script dari backend WIM:

```bash
node src/scripts/simulate-display.js
```

Script mengirim 4 skenario ke database dengan jeda 8 detik:

| Skenario | Ekspektasi tampilan |
|----------|-------------------|
| NORMAL | Status hijau statis |
| OVERLOAD | Status merah berkedip, nilai berat merah |
| OVERDIMENSION | Status oranye berkedip, nilai lebar/tinggi merah |
| OVERLOAD + OVERDIMENSION | Status merah berkedip cepat, semua pelanggaran merah |

---

## Autostart Windows

Buat file `start-vms.bat`:

```bat
@echo off
cd /d C:\vms-display
call venv\Scripts\activate
python main.py
```

Daftarkan ke **Windows Task Scheduler**:
- Trigger: At startup
- Action: jalankan `start-vms.bat`
- Setting: Run whether user is logged on or not

---

## Urutan Pengerjaan

```
Step 1: Setup project + requirements.txt
Step 2: config.py
Step 3: api_client.py + test polling manual (print ke terminal)
Step 4: renderer.py — draw_waiting() dulu
Step 5: main.py — integrasi waiting screen
Step 6: renderer.py — draw_vehicle() semua zona
Step 7: Testing dengan simulate-display.js
Step 8: Autostart Windows
```
