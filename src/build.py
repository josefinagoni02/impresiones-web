"""Genera index.html a partir de las fichas de obras.

Uso: python3 src/build.py <carpeta-con-json-de-obras> [config.json]
- Lee cada ficha (JSON exportado del formulario "Fichas de obras").
- Usa img/<nombre>.jpg y img/<nombre>-sm.jpg (generadas con src/fotos.py).
- Ubica cada lugar en el mapa con la tabla LUGARES (agregar acá lugares nuevos).
"""
import json, os, sys, glob, re, colorsys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# lugar (texto que aparece en la ficha, en minúsculas) -> (lat, lon, región del mapa, nombre para mostrar)
LUGARES = {
    # clave: (lat, lon, lugar, país) — coordenadas del punto exacto
    'rio de janeiro': (-22.9068, -43.1729, 'Río de Janeiro', 'Brasil'),
    'venao': (7.4337, -80.1914, 'Playa Venao', 'Panamá'),
    'san blas': (9.5594, -78.9481, 'San Blas', 'Panamá'),
    'santa teresa': (9.6436, -85.1683, 'Santa Teresa', 'Costa Rica'),
    'isla tortuga': (9.7736, -84.8895, 'Isla Tortuga', 'Costa Rica'),
    'puerto viejo': (9.6563, -82.7539, 'Puerto Viejo', 'Costa Rica'),
    'golden gate': (37.8199, -122.4783, 'Golden Gate', 'Estados Unidos'),
    'san francisco': (37.7599, -122.5107, 'San Francisco', 'Estados Unidos'),
    'tigre': (-34.4264, -58.5796, 'Tigre', 'Argentina'),
    'obelisco': (-34.6037, -58.3816, 'Obelisco', 'Argentina'),
    'capital federal': (-34.6037, -58.3816, 'Obelisco', 'Argentina'),
    'caba': (-34.6037, -58.3816, 'Obelisco', 'Argentina'),
    'tafí': (-26.8527, -65.7098, 'Tafí del Valle', 'Argentina'),
    'tafi': (-26.8527, -65.7098, 'Tafí del Valle', 'Argentina'),
    'jardín botánico': (-34.5823, -58.4168, 'Jardín Botánico', 'Argentina'),
    'jardin botanico': (-34.5823, -58.4168, 'Jardín Botánico', 'Argentina'),
    'chapadmalal': (-38.1700, -57.6600, 'Chapadmalal', 'Argentina'),
    'puntarenas': (9.9763, -84.8384, 'Puntarenas', 'Costa Rica'),
    'mar del plata': (-38.0055, -57.5426, 'Mar del Plata', 'Argentina'),
    'las criollas': (-26.6200, -65.4200, 'Las Criollas', 'Argentina'),  # aprox. (CP 4122, Tucumán)
    'bolsón': (-41.9644, -71.5332, 'El Bolsón', 'Argentina'),
    'bolson': (-41.9644, -71.5332, 'El Bolsón', 'Argentina'),
}
REGION_TXT = {'Estados Unidos': 'California, EE.UU.', 'Argentina': 'Buenos Aires, Argentina'}
# nombre de la zona en el mapa cuando se agrupan lugares (si no está, se usa REGION)
MAP_REGION = {'mar del plata': 'Mar Argentino', 'chapadmalal': 'Mar Argentino'}
REGION = {'obelisco': 'Buenos Aires', 'capital federal': 'Buenos Aires', 'caba': 'Buenos Aires', 'golden gate': 'California', 'san francisco': 'California', 'tigre': 'Buenos Aires', 'tafí': 'Tucumán', 'tafi': 'Tucumán', 'jardín botánico': 'Buenos Aires', 'jardin botanico': 'Buenos Aires', 'mar del plata': 'Buenos Aires', 'chapadmalal': 'Buenos Aires', 'las criollas': 'Tucumán', 'bolsón': 'Patagonia', 'bolson': 'Patagonia'}
# Precios de venta publicados (redondeados a $500). Medidas en vertical.
PRECIOS = {
    'print': [dict(w=20, h=30, pw=20, ph=30, p=15500), dict(w=30, h=40, pw=30, ph=40, p=31000), dict(w=40, h=60, pw=40, ph=60, p=62000)],
    'marco': [dict(w=30, h=40, pw=30, ph=40, p=50000), dict(w=40, h=60, pw=40, ph=60, p=100500)],
    'marco_mat': [dict(w=30, h=40, pw=20, ph=30, mat=5, p=34500), dict(w=40, h=50, pw=30, ph=40, mat=5, p=65500), dict(w=60, h=80, pw=40, ph=60, mat=10, p=134000)],
    'canvas': [dict(w=20, h=30, pw=20, ph=30, p=35500), dict(w=30, h=45, pw=30, ph=45, p=39500), dict(w=40, h=60, pw=40, ph=60, p=49500), dict(w=50, h=75, pw=50, ph=75, p=65000)],
    'square': [30, 50, 70],
}
TONOS = [
    {'id': None, 'label': 'Todos los tonos', 'c': 'conic-gradient(#4f7f95,#c9ae83,#c9683f,#a8437a,#6f8a5a,#26303a,#d9dedb,#4f7f95)'},
    {'id': 'azul', 'label': 'Azul', 'c': '#4f7f95'},
    {'id': 'arena', 'label': 'Arena', 'c': '#c9ae83'},
    {'id': 'cálido', 'label': 'Cálido', 'c': '#c9683f'},
    {'id': 'magenta', 'label': 'Magenta', 'c': '#a8437a'},
    {'id': 'verde', 'label': 'Verde', 'c': '#6f8a5a'},
    {'id': 'oscuro', 'label': 'Oscuro', 'c': '#26303a'},
    {'id': 'claro', 'label': 'Claro', 'c': '#d9dedb'},
]


def dms(v, pos, neg):
    a = abs(v); d = int(a); m = round((a - d) * 60)
    if m == 60: d, m = d + 1, 0
    return f"{d}°{m:02d}′{pos if v >= 0 else neg}"


def darker(hexc, f=0.8):
    r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
    return '#%02x%02x%02x' % tuple(int(c * f) for c in (r, g, b))


def main():
    src = sys.argv[1]
    cfg = {}
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        cfg = json.load(open(sys.argv[2]))
    meta = json.load(open(os.path.join(ROOT, 'src', 'fotos.json')))
    fichas = []
    for f in sorted(glob.glob(os.path.join(src, '*.json'))):
        d = json.load(open(f))
        d = d.get('data', d)
        d['_id'] = os.path.basename(f)[:-5]
        fichas.append(d)
    fichas.sort(key=lambda d: d.get('createdAt', ''))
    works, warn = [], []
    for d in fichas:
        if d.get('example'):
            continue
        fn = (d.get('fileName') or '').strip()
        m = meta.get(fn)
        if not m:
            warn.append(f"sin foto procesada: {d.get('title')} ({fn})"); continue
        if d.get('photoId') and m.get('photoId') and d['photoId'] != m['photoId']:
            warn.append(f"FOTO CAMBIADA en la ficha (bajar asset {d['photoId']} y reprocesar): {d.get('title')} ({fn})")
        place = (d.get('place') or '').strip()
        key = next((k for k in LUGARES if k in place.lower()), None)
        if not key:
            warn.append(f"lugar sin coordenadas: {d.get('title')} ({place})"); continue
        lat, lon, short, country = LUGARES[key]
        reg = REGION.get(key, country)
        pretty = ", ".join([short] + ([reg] if reg != country else []) + ["EE.UU." if country == "Estados Unidos" else country])
        ver = f"?v={m['photoId'][:8]}" if m.get('photoId') else ''
        tones = [t for t in [d.get('tone')] if t]
        if 'magenta' in (d.get('notes') or '').lower() and 'magenta' not in tones:
            tones.append('magenta')
        ar = m['w'] / m['h']
        works.append({
            'id': d['_id'], 't': (d.get('title') or 'Sin título').strip(), 'serie': (d.get('serie') or '').strip(),
            'year': d.get('year') or None, 'when': (d.get('when') or '').strip(),
            'place': pretty, 'short': short, 'country': country, 'region': MAP_REGION.get(key, REGION.get(key, country)), 'lat': lat, 'lon': lon, 'coords': f"{dms(lat, 'N', 'S')} {dms(lon, 'E', 'O')}",
            'fmt': 'h' if ar > 1.05 else 'v' if ar < 0.95 else 'q', 'ar': round(ar, 4),
            'img': f"img/{m['file']}.jpg{ver}", 'sm': f"img/{m['file']}-sm.jpg{ver}", 'edge': m['avg'], 'edgeD': darker(m['avg']),
            'tones': tones, 'moods': d.get('mood') or [], 'text': (d.get('phrase') or '').strip(), 'story': (d.get('story') or '').strip(),
            'notes': d.get('notes') or '',
        })
    # sets desde las notas "combina con X"
    sets, seen = [], set()
    for i, w in enumerate(works):
        for m in re.finditer(r'combina con ([^\n,.;]+)', w['notes'], re.I):
            name = m.group(1).strip().lower()
            j = next((k for k, o in enumerate(works) if k != i and (o['t'].lower().startswith(name) or name.startswith(o['t'].lower()[:4]))), None)
            if j is None: continue
            pair = tuple(sorted((i, j)))
            if pair in seen: continue
            seen.add(pair)
            a, b = works[pair[0]], works[pair[1]]
            serie = a['serie'] or b['serie']
            orient = a['fmt']
            sets.append({'name': f"Díptico {serie}".strip(), 'desc': f"{a['t']} + {b['t']} · {'horizontal, marco negro' if orient == 'h' else 'vertical, marco madera con paspartú'}",
                         'works': list(pair), 'orient': orient, 'frame': 'negro' if orient == 'h' else 'madera', 'mat': 'sin' if orient == 'h' else 'blanco'})
    for w in works: w.pop('notes')
    # extensión del mapa: América por defecto, se agranda si hace falta
    lat0, lat1, lon0, lon1 = 46, -44, -128, -34
    for w in works:
        lat0 = max(lat0, w['lat'] + 8); lat1 = min(lat1, w['lat'] - 8)
        lon0 = min(lon0, w['lon'] - 10); lon1 = max(lon1, w['lon'] + 10)
    config = {
        'name': cfg.get('name') or 'Impresiones', 'bio': cfg.get('bio') or '', 'whatsapp': cfg.get('whatsapp') or '',
        'instagram': cfg.get('instagram') or '', 'email': cfg.get('email') or '', 'tagline': cfg.get('tagline') or '',
    }
    data = {'pricing': PRECIOS, 'works': works, 'config': config, 'sets': sets, 'tones': [t for t in TONOS if t['id'] is None or any(t['id'] in w['tones'] for w in works)],
            'extent': {'lat0': lat0, 'lat1': lat1, 'lon0': lon0, 'lon1': lon1},
            'oceans': [{'name': 'Océano Pacífico', 'lat': -8, 'lon': -112}, {'name': 'Océano Atlántico', 'lat': 24, 'lon': -68}]}
    tpl = open(os.path.join(ROOT, 'src', 'template.html')).read()
    desc = config['tagline'] or 'Un pedacito fotográfico del mundo en mi atlas personal. Te invito a explorar cada lugar desde el mapa, o recorrer la grilla de norte a sur.'
    html = (tpl.replace('__SITE_NAME__', config['name']).replace('__SITE_DESC__', desc)
            .replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
    open(os.path.join(ROOT, 'index.html'), 'w').write(html)
    print(f"{len(works)} obras, {len(sets)} sets")
    for x in warn: print('AVISO:', x)


if __name__ == '__main__':
    main()
