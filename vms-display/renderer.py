import datetime
import pygame
import config

# ─── helpers ────────────────────────────────────────────────────────────────

def _zone_y(zone):
    zones = [config.ZONE_HEADER, config.ZONE_ID, config.ZONE_AXLE, config.ZONE_DETAIL, config.ZONE_STATUS]
    names = ['header', 'id', 'axle', 'detail', 'status']
    y = 0
    for name, h in zip(names, zones):
        if name == zone:
            return y
        y += h
    return y


def draw_divider(surface, y):
    pygame.draw.line(surface, config.COLOR_DIVIDER, (0, y), (config.SCREEN_W, y), 1)


# ─── waiting screen ──────────────────────────────────────────────────────────

def draw_waiting(surface, fonts):
    surface.fill(config.COLOR_BG)
    tick = pygame.time.get_ticks()
    visible = (tick // 800) % 2 == 0
    if visible:
        label = fonts['wait'].render('Menunggu data kendaraan...', True, config.COLOR_DIM)
        rect  = label.get_rect(center=(config.SCREEN_W // 2, config.SCREEN_H // 2))
        surface.blit(label, rect)
    draw_header(surface, fonts)


# ─── header zone ─────────────────────────────────────────────────────────────

def draw_header(surface, fonts):
    y  = _zone_y('header')
    h  = config.ZONE_HEADER
    pygame.draw.rect(surface, (10, 10, 10), (0, y, config.SCREEN_W, h))

    title = fonts['header'].render('WIM MONITORING — PALIMANAN', True, config.COLOR_GOLD)
    surface.blit(title, (16, y + (h - title.get_height()) // 2))

    now       = datetime.datetime.now().strftime('%H:%M:%S')
    time_surf = fonts['header'].render(now, True, config.COLOR_TEXT)
    surface.blit(time_surf, (config.SCREEN_W - time_surf.get_width() - 16,
                              y + (h - time_surf.get_height()) // 2))
    draw_divider(surface, y + h)


# ─── identity zone ────────────────────────────────────────────────────────────

def draw_identity(surface, fonts, data):
    y   = _zone_y('id')
    h   = config.ZONE_ID
    mid = config.SCREEN_W // 2

    lbl_plate = fonts['label'].render('NOMOR POLISI', True, config.COLOR_DIM)
    surface.blit(lbl_plate, (16, y + 12))
    plate = fonts['plate'].render(data.get('nomor_polisi', '-'), True, config.COLOR_TEXT)
    surface.blit(plate, (16, y + 12 + lbl_plate.get_height() + 6))

    pygame.draw.line(surface, config.COLOR_DIVIDER, (mid, y), (mid, y + h), 1)

    lbl_gol = fonts['label'].render('GOLONGAN', True, config.COLOR_DIM)
    surface.blit(lbl_gol, (mid + 16, y + 12))
    gol_text = f"{data.get('golongan', 0)} SUMBU"
    gol_surf = fonts['golongan'].render(gol_text, True, config.COLOR_TEXT)
    surface.blit(gol_surf, (mid + 16, y + 12 + lbl_gol.get_height() + 6))

    draw_divider(surface, y + h)


# ─── axle zone (text only, no bars) ──────────────────────────────────────────

def draw_axle(surface, fonts, data):
    y        = _zone_y('axle')
    h        = config.ZONE_AXLE
    mid      = config.SCREEN_W // 2
    axles    = data.get('berat_axle_kg', {})
    golongan = data.get('golongan', 0)
    total    = data.get('total_berat_kg', 0)

    lbl_zone = fonts['label'].render('BERAT PER SUMBU (KG)', True, config.COLOR_DIM)
    surface.blit(lbl_zone, (16, y + 10))

    row_start = y + 10 + lbl_zone.get_height() + 12
    row_h     = 44

    axle_keys = ['axle1', 'axle2', 'axle3', 'axle4', 'axle5', 'axle6']

    for i, key in enumerate(axle_keys):
        col    = i // 3          # 0 = left, 1 = right
        row    = i % 3
        active = (i < golongan)
        val    = axles.get(key, 0)

        ry         = row_start + row * row_h
        lbl_color  = config.COLOR_TEXT if active else config.COLOR_DIM
        val_color  = config.COLOR_TEXT if active else config.COLOR_DIM

        col_x = 16 if col == 0 else mid + 16

        lbl_surf = fonts['axle_lbl'].render(f'Sumbu {i + 1}', True, lbl_color)
        surface.blit(lbl_surf, (col_x, ry))

        val_fmt  = f'{val:,.0f} kg'.replace(',', '.') if active else '0 kg'
        val_surf = fonts['axle_val'].render(val_fmt, True, val_color)
        # right-align value within its column
        vx = (mid - 16 - val_surf.get_width()) if col == 0 else (config.SCREEN_W - 16 - val_surf.get_width())
        surface.blit(val_surf, (vx, ry))

    # total berat
    total_y   = row_start + 3 * row_h + 8
    total_fmt = f'{total:,.0f}'.replace(',', '.')
    tot_surf  = fonts['axle_tot'].render(f'TOTAL BERAT : {total_fmt} KG', True, config.COLOR_GOLD)
    surface.blit(tot_surf, (config.SCREEN_W - tot_surf.get_width() - 16, total_y))

    draw_divider(surface, y + h)


# ─── detail zone: berat (kiri) | dimensi (kanan) ─────────────────────────────

def _over_color(val, limit):
    if limit is not None and limit > 0 and val > limit:
        return config.COLOR_OVER_VALUE
    return config.COLOR_TEXT


def draw_detail(surface, fonts, data):
    y   = _zone_y('detail')
    h   = config.ZONE_DETAIL
    mid = config.SCREEN_W // 2

    dim   = data.get('dimensi_mm', {})
    limit = data.get('limit') or {}

    # ── kiri: BERAT ──
    lbl_berat = fonts['label'].render('BERAT', True, config.COLOR_DIM)
    surface.blit(lbl_berat, (16, y + 10))

    head_y = y + 10 + lbl_berat.get_height() + 6

    # column x positions (left panel)
    c_name  = 16
    c_val   = 110
    c_lim   = 220

    for txt, cx in [('', c_name), ('NILAI', c_val), ('BATAS', c_lim)]:
        s = fonts['tbl_head'].render(txt, True, config.COLOR_DIM)
        surface.blit(s, (cx, head_y))

    row_y       = head_y + fonts['tbl_head'].get_height() + 8
    total_berat = data.get('total_berat_kg', 0)
    lim_berat   = limit.get('limit_berat_kg')
    berat_color = _over_color(total_berat, lim_berat)

    surface.blit(fonts['tbl_name'].render('Total', True, config.COLOR_TEXT), (c_name, row_y))
    surface.blit(fonts['tbl_val'].render(f'{total_berat:,.0f} kg'.replace(',', '.'), True, berat_color), (c_val, row_y))
    if lim_berat is not None:
        surface.blit(fonts['tbl_val'].render(f'{lim_berat:,.0f} kg'.replace(',', '.'), True, config.COLOR_DIM), (c_lim, row_y))

    # vertical divider
    pygame.draw.line(surface, config.COLOR_DIVIDER, (mid, y), (mid, y + h), 1)

    # ── kanan: DIMENSI ──
    lbl_dim = fonts['label'].render('DIMENSI', True, config.COLOR_DIM)
    surface.blit(lbl_dim, (mid + 16, y + 10))

    head2_y = y + 10 + lbl_dim.get_height() + 6
    c2_name = mid + 16
    c2_val  = mid + 120
    c2_lim  = mid + 240

    for txt, cx in [('', c2_name), ('NILAI', c2_val), ('BATAS', c2_lim)]:
        s = fonts['tbl_head'].render(txt, True, config.COLOR_DIM)
        surface.blit(s, (cx, head2_y))

    rows_dim = [
        ('Panjang', dim.get('panjang', 0), limit.get('limit_panjang_mm'), 'mm'),
        ('Lebar',   dim.get('lebar',   0), limit.get('limit_lebar_mm'),   'mm'),
        ('Tinggi',  dim.get('tinggi',  0), limit.get('limit_tinggi_mm'),  'mm'),
    ]
    row_h2 = 44
    for idx, (name, val, lim, unit) in enumerate(rows_dim):
        ry        = head2_y + fonts['tbl_head'].get_height() + 8 + idx * row_h2
        val_color = _over_color(val, lim)
        surface.blit(fonts['tbl_name'].render(name, True, config.COLOR_TEXT), (c2_name, ry))
        surface.blit(fonts['tbl_val'].render(f'{val:,.0f} {unit}'.replace(',', '.'), True, val_color), (c2_val, ry))
        if lim is not None:
            surface.blit(fonts['tbl_val'].render(f'{lim:,.0f} {unit}'.replace(',', '.'), True, config.COLOR_DIM), (c2_lim, ry))

    draw_divider(surface, y + h)


# ─── status zone (teks saja) ──────────────────────────────────────────────────

_STATUS_MAP = {
    'normal':                   ('NORMAL',         config.COLOR_NORMAL,   None),
    'overload':                 ('OVERLOAD',        config.COLOR_OVERLOAD, 1200),
    'overdimension':            ('OVER DIMENSION',  config.COLOR_OVERDIM,  1200),
    'overload & overdimension': ('ODOL',            config.COLOR_OVERLOAD, 800),
}


def draw_status(surface, fonts, data, tick):
    y          = _zone_y('status')
    h          = config.ZONE_STATUS
    status     = data.get('status', {})
    kesimpulan = status.get('kesimpulan', 'normal').lower()

    label, color, blink_ms = _STATUS_MAP.get(kesimpulan, _STATUS_MAP['normal'])

    visible = True
    if blink_ms is not None:
        visible = (tick // blink_ms) % 2 == 0

    if visible:
        surf = fonts['status'].render(label, True, color)
        rect = surf.get_rect(center=(config.SCREEN_W // 2, y + h // 2))
        surface.blit(surf, rect)


# ─── full vehicle screen ──────────────────────────────────────────────────────

def draw_vehicle(surface, fonts, data, tick):
    surface.fill(config.COLOR_BG)
    draw_header(surface, fonts)
    draw_identity(surface, fonts, data)
    draw_axle(surface, fonts, data)
    draw_detail(surface, fonts, data)
    draw_status(surface, fonts, data, tick)
