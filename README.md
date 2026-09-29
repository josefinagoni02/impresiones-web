# Impresiones — web de obras

Sitio estático (sin build): `index.html` + `img/`.

- **Catálogo (Atlas):** mapa por lugares y grilla de norte a sur, con filtros por serie, tono y búsqueda.
- **Probador:** marco o canvas, paspartú, formato y medida, rotar y encuadrar la foto, 1 a 3 cuadros, sets armados.

## Cómo se actualiza
1. Los datos se cargan en el formulario **Fichas de obras** (Claude).
2. `src/fotos.py` achica las fotos nuevas a `img/`.
3. `src/build.py <carpeta-json-fichas> [config.json]` regenera `index.html`.
4. Se sube a GitHub y Vercel publica solo.

Lugares nuevos: agregarlos en `LUGARES` dentro de `src/build.py`.
