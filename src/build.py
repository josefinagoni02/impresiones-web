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
    'tafí': (-26.8527, -65.7098, 'Tafí del Valle', 'Argentina'),
    'tafi': (-26.8527, -65.7098, 'Tafí del Valle', 'Argentina'),
}
REGION_TXT = {'Estados Unidos': 'California, EE.UU.', 'Argentina': 'Buenos Aires, Argentina'}
REGION = {'golden gate': 'California', 'san francisco': 'California', 'tigre': 'Buenos Aires', 'tafí': 'Tucumán', 'tafi': 'Tucumán'}
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
        place = (d.get('place') or '').strip()
        key = next((k for k in LUGARES if k in place.lower()), None)
        if not key:
            warn.append(f"lugar sin coordenadas: {d.get('title')} ({place})"); continue
        lat, lon, short, country = LUGARES[key]
        reg = REGION.get(key, country)
        pretty = ", ".join([short] + ([reg] if reg != country else []) + ["EE.UU." if country == "Estados Unidos" else country])
        tones = [t for t in [d.get('tone')] if t]
        if 'magenta' in (d.get('notes') or '').lower() and 'magenta' not in tones:
            tones.append('magenta')
        ar = m['w'] / m['h']
        works.append({
            'id': d['_id'], 't': (d.get('title') or 'Sin título').strip(), 'serie': (d.get('serie') or '').strip(),
            'year': d.get('year') or None, 'when': (d.get('when') or '').strip(),
            'place': pretty, 'short': short, 'country': country, 'region': REGION.get(key, country), 'lat': lat, 'lon': lon, 'coords': f"{dms(lat, 'N', 'S')} {dms(lon, 'E', 'O')}",
            'fmt': 'h' if ar > 1.05 else 'v' if ar < 0.95 else 'q', 'ar': round(ar, 4),
            'img': f"img/{m['file']}.jpg", 'sm': f"img/{m['file']}-sm.jpg", 'edge': m['avg'], 'edgeD': darker(m['avg']),
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
            sets.append({'name': f"Díptico {serie}".strip(), 'desc': f"{a['t']} + {b['t']} · {'horizontal 75×50' if orient == 'h' else 'vertical 50×75'}",
                         'works': list(pair), 'orient': orient, 'frame': 'negro' if orient == 'h' else 'roble', 'mat': 'sin' if orient == 'h' else 'blanco'})
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
    data = {'works': works, 'config': config, 'sets': sets, 'tones': [t for t in TONOS if t['id'] is None or any(t['id'] in w['tones'] for w in works)],
            'extent': {'lat0': lat0, 'lat1': lat1, 'lon0': lon0, 'lon1': lon1},
            'oceans': [{'name': 'Océano Pacífico', 'lat': -8, 'lon': -112}, {'name': 'Océano Atlántico', 'lat': 24, 'lon': -68}]}
    tpl = open(os.path.join(ROOT, 'src', 'template.html')).read()
    desc = config['tagline'] or 'Fotografías impresas en marco o canvas. Recorré el atlas de obras y probalas en tu pared.'
    html = (tpl.replace('__SITE_NAME__', config['name']).replace('__SITE_DESC__', desc)
            .replace('__DATA__', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
    open(os.path.join(ROOT, 'index.html'), 'w').write(html)
    print(f"{len(works)} obras, {len(sets)} sets")
    for x in warn: print('AVISO:', x)


if __name__ == '__main__':
    main()
