"""
Gera data/media.json com o EXIF completo de cada foto/vídeo e a posição no mapa.

Posição, por ordem de preferência:
  1. "gps"  – coordenada gravada no próprio arquivo (EXIF GPS ou átomo ©xyz do MP4)
  2. "time" – horário do arquivo cruzado com o GPX da rota (ponto mais próximo no tempo)
  3. sem posição – quando não há GPS e o horário cai fora do passeio

Uso:  python media_create.py      (requer Pillow: pip install pillow)
"""
import json
import os
import re
import struct
from datetime import datetime, timedelta, timezone

from PIL import Image
from PIL.ExifTags import GPSTAGS, TAGS

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUT = os.path.join(DATA, "media.json")
PHOTO_EXT = (".jpg", ".jpeg", ".png")
VIDEO_EXT = (".mp4",)
MAX_GAP = timedelta(minutes=3)  # tolerância fora do intervalo do GPX

try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("Europe/Vienna")
except Exception:  # sem tzdata: inverno na Áustria = UTC+1
    LOCAL_TZ = timezone(timedelta(hours=1))

SKIP_TAGS = {"MakerNote", "UserComment", "PrintImageMatching", "ComponentsConfiguration"}


# ── Helpers ──────────────────────────────────────────────────────────────
def clean(value):
    """Converte valores EXIF em algo serializável e legível."""
    if isinstance(value, bool) or isinstance(value, int):
        return value
    if isinstance(value, bytes):
        if len(value) > 64:
            return None
        try:
            return value.decode("ascii").strip("\x00 ") or None
        except UnicodeDecodeError:
            return value.hex()
    if isinstance(value, tuple):
        items = [clean(v) for v in value]
        return items[0] if len(items) == 1 else items
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        return round(float(value), 6) if value.denominator else None
    if isinstance(value, str):
        return value.strip("\x00 ") or None
    return value


def dms_to_deg(dms, ref):
    deg = float(dms[0]) + float(dms[1]) / 60 + float(dms[2]) / 3600
    return -deg if ref in ("S", "W") else deg


def parse_exif_time(value, offset=None):
    if not value:
        return None
    try:
        dt = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None
    if offset and re.fullmatch(r"[+-]\d{2}:\d{2}", offset):
        sign = 1 if offset[0] == "+" else -1
        h, m = map(int, offset[1:].split(":"))
        return dt.replace(tzinfo=timezone(sign * timedelta(hours=h, minutes=m)))
    return dt.replace(tzinfo=LOCAL_TZ)


# ── Fotos ────────────────────────────────────────────────────────────────
def read_photo(path):
    img = Image.open(path)
    exif = img.getexif()
    sub = exif.get_ifd(0x8769)  # Exif IFD
    gps = exif.get_ifd(0x8825)  # GPS IFD

    tags = {}
    for ifd in (exif, sub):
        for k, v in ifd.items():
            name = TAGS.get(k, str(k))
            if name in SKIP_TAGS or name in ("ExifOffset", "GPSInfo"):
                continue
            v = clean(v)
            if v is not None:
                tags[name] = v
    gps_tags = {GPSTAGS.get(k, str(k)): clean(v) for k, v in gps.items()}
    gps_tags = {k: v for k, v in gps_tags.items() if v is not None}
    if gps_tags:
        tags["GPS"] = gps_tags

    info = {"type": "photo", "width": img.width, "height": img.height, "exif": tags}

    t = parse_exif_time(
        sub.get(36867) or exif.get(306),       # DateTimeOriginal / DateTime
        sub.get(36881) or sub.get(36880),      # OffsetTimeOriginal / OffsetTime
    )
    if t:
        info["time"] = t

    if 2 in gps and 4 in gps:
        info["lat"] = round(dms_to_deg(gps[2], gps.get(1, "N")), 7)
        info["lng"] = round(dms_to_deg(gps[4], gps.get(3, "E")), 7)
        info["source"] = "gps"
        if 6 in gps:
            alt = float(gps[6])
            info["alt"] = round(-alt if gps.get(5) == 1 else alt, 1)
    return info


# ── Vídeos (MP4) ─────────────────────────────────────────────────────────
def read_video(path):
    size = os.path.getsize(path)
    info = {"type": "video", "exif": {}}
    with open(path, "rb") as f:

        def walk(end, depth=0):
            while f.tell() + 8 <= end:
                start = f.tell()
                atom_size, kind = struct.unpack(">I4s", f.read(8))
                if atom_size == 1:
                    atom_size = struct.unpack(">Q", f.read(8))[0]
                elif atom_size == 0:
                    atom_size = end - start
                if atom_size < 8:
                    return
                if kind == b"moov":
                    # Localização do celular: moov/udta/meta/ilst/©xyz/data "+47.7618+13.0382+000/"
                    body = f.read(min(atom_size - 8, 8 << 20))
                    m = re.search(rb"\xa9xyz.{0,24}?([+-]\d+\.\d+)([+-]\d+\.\d+)([+-][\d.]+)?", body, re.S)
                    if m:
                        info["lat"], info["lng"] = float(m[1]), float(m[2])
                        info["source"] = "gps"
                        info["exif"]["Location"] = b"".join(g for g in m.groups() if g).decode()
                    f.seek(start + 8)
                    walk(start + atom_size, depth + 1)
                elif kind == b"trak" and depth < 4:
                    walk(start + atom_size, depth + 1)
                elif kind == b"mvhd":
                    version = f.read(4)[0]
                    fmt, n = (">Q", 8) if version else (">I", 4)
                    created = struct.unpack(fmt, f.read(n))[0]
                    f.read(n)
                    scale = struct.unpack(">I", f.read(4))[0]
                    dur = struct.unpack(fmt, f.read(n))[0]
                    if created:
                        info["_created"] = datetime(1904, 1, 1) + timedelta(seconds=created)
                    if scale:
                        info["exif"]["Duration"] = round(dur / scale, 2)
                elif kind == b"tkhd" and "width" not in info:
                    data = f.read(atom_size - 8)
                    w, h = struct.unpack(">II", data[-8:])
                    if w >> 16:
                        info["width"], info["height"] = w >> 16, h >> 16
                f.seek(start + atom_size)

        walk(size)
        f.seek(0)
        head = f.read(1 << 20)

    created = info.pop("_created", None)
    is_gopro = b"GoPro" in head or os.path.basename(path).upper().startswith(("GX", "GH", "GOPR"))
    info["exif"]["Make"] = "GoPro" if is_gopro else info["exif"].get("Make")
    if not info["exif"]["Make"]:
        del info["exif"]["Make"]
    if created and created.year > 1970:
        # Celulares gravam em UTC; a GoPro grava no horário local da câmera.
        info["time"] = created.replace(tzinfo=LOCAL_TZ if is_gopro else timezone.utc)
        info["exif"]["CreationTime"] = created.isoformat() + ("" if is_gopro else "Z")
    return info


# ── Trilha GPX (geojson) ─────────────────────────────────────────────────
def load_track(route_dir, route):
    path = os.path.join(route_dir, f"{route}.geojson")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        features = json.load(f)["features"]
    track = []
    for feat in features:
        p = feat.get("properties") or {}
        c = (feat.get("geometry") or {}).get("coordinates")
        if c and p.get("START_DateTime"):
            track.append((p["START_DateTime"] / 1000, c[0][1], c[0][0], p.get("START_Elevation")))
    track.sort()
    return track


def place_by_time(track, t):
    if not track or not t:
        return None
    ts = t.timestamp()
    if ts < track[0][0] - MAX_GAP.total_seconds() or ts > track[-1][0] + MAX_GAP.total_seconds():
        return None
    best = min(track, key=lambda p: abs(p[0] - ts))
    return best


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    result = {}
    for route in sorted(os.listdir(DATA)):
        route_dir = os.path.join(DATA, route)
        if not os.path.isdir(route_dir):
            continue
        track = load_track(route_dir, route)
        ride_day = datetime.fromtimestamp(track[0][0], LOCAL_TZ).date() if track else None
        items = []

        for name in sorted(os.listdir(route_dir)):
            path = os.path.join(route_dir, name)
            low = name.lower()
            try:
                if low.endswith(PHOTO_EXT):
                    info = read_photo(path)
                elif low.endswith(VIDEO_EXT):
                    info = read_video(path)
                else:
                    continue
            except Exception as e:
                print(f"  ! {route}/{name}: {e}")
                continue

            t = info.get("time")
            if "lat" not in info:
                hit = place_by_time(track, t)
                if hit:
                    info["lat"], info["lng"] = round(hit[1], 7), round(hit[2], 7)
                    if hit[3] is not None:
                        info["alt"] = round(hit[3], 1)
                    info["source"] = "time"
            if t and ride_day and t.astimezone(LOCAL_TZ).date() != ride_day:
                info["otherDay"] = True
            if t:
                info["time"] = t.astimezone(LOCAL_TZ).isoformat(timespec="seconds")

            items.append({"file": name, **info})
            where = info.get("source") or "sem posição"
            extra = "  (outro dia)" if info.get("otherDay") else ""
            print(f"  {route}/{name:28} {info['type']:5}  {where}{extra}")

        items.sort(key=lambda x: x.get("time") or "9999")
        result[route] = items

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\nGerado {OUT}")


if __name__ == "__main__":
    main()
