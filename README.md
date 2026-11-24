# BikeClub

- Add X/Y to photos and pinpoint in the map

## Fotos e vídeos no mapa

Depois de adicionar arquivos em `data/<rota>/`, rode:

```
python media_create.py
```

Ele gera `data/media.json` com o EXIF completo e a posição de cada arquivo:
GPS do próprio arquivo quando existe, senão estimada pelo horário cruzado com o GPX.

## Map style: Bike Club Outdoor

The map is drawn with [MapLibre GL JS](https://maplibre.org/) using a custom style,
[`styles/bikeclub-outdoor.json`](styles/bikeclub-outdoor.json), on top of MapTiler vector tiles
(OpenMapTiles schema), MapTiler contours and terrain-RGB.

- **Palette:** warm sand base, teal water and cycleways, orange kept for the club's routes.
- **Hierarchy by zoom:** motorways and primaries from z5–6, secondaries z8, minor roads z12,
  tracks and paths z12–13; casings only appear once roads are wide enough to need them.
- **Cycling focus:** cycleways (and paths with `bicycle=designated`) in teal with a light casing,
  unpaved roads dashed, tracks and footpaths in brown, POIs limited to what a rider needs
  (bike shops, drinking water, cafés, beer gardens, shelters, viewpoints).
- **Relief:** hillshade, 100 m index contours with labels from z14, peaks with elevation.
- **3D:** terrain-RGB as MapLibre terrain plus `fill-extrusion` buildings (the 3D button).
- **Icons:** drawn on a canvas at runtime (`drawIcon` in `index.html`), so no sprite file is needed.

The style file contains no API key: `transformRequest` in `index.html` appends it to every
MapTiler request. To edit the style visually, open it in [Maputnik](https://maplibre.org/maputnik/)
and add `?key=YOUR_KEY` to the source and glyph URLs there.
