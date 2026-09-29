"""Achica fotos a tamaño web. Uso: python3 src/fotos.py <carpeta-con-fotos-originales> IMG_1234.jpg ...
Genera img/<nombre>.jpg (2000px) e img/<nombre>-sm.jpg (640px) y actualiza src/fotos.json."""
import sys, os, json
from PIL import Image, ImageOps
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
meta_p = os.path.join(ROOT, 'src', 'fotos.json')
meta = json.load(open(meta_p)) if os.path.exists(meta_p) else {}
src = sys.argv[1]
for fn in sys.argv[2:]:
    im = ImageOps.exif_transpose(Image.open(os.path.join(src, fn))).convert('RGB')
    name = fn.rsplit('.', 1)[0].lower().replace('_', '-')
    w, h = im.size
    avg = im.resize((1, 1), Image.LANCZOS).getpixel((0, 0))
    for tag, side, q in (('', 2000, 82), ('-sm', 640, 78)):
        c = im.copy(); c.thumbnail((side, side), Image.LANCZOS)
        c.save(os.path.join(ROOT, 'img', f'{name}{tag}.jpg'), quality=q, optimize=True, progressive=True)
    meta[fn] = {'file': name, 'w': w, 'h': h, 'avg': '#%02x%02x%02x' % avg}
    print('ok', fn)
json.dump(meta, open(meta_p, 'w'), indent=1)
