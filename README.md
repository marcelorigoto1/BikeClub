# BikeClub

- Add X/Y to photos and pinpoint in the map

## Fotos e vídeos no mapa

Depois de adicionar arquivos em `data/<rota>/`, rode:

```
python media_create.py
```

Ele gera `data/media.json` com o EXIF completo e a posição de cada arquivo:
GPS do próprio arquivo quando existe, senão estimada pelo horário cruzado com o GPX.
