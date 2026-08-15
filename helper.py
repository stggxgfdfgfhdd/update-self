#============ In The Name Of God ============#
# Source Name: Ultra Self
# Developer: @IVGalaxy
# © 2024 Ultra Self LLC. All rights reserved.
#================== Import ==================#
from pyrogram import Client, filters, idle, errors, StopPropagation
from pyrogram.types import *
from pyrogram.raw import functions, base, types
from colorama import Fore
import requests
import pymysql
import json
import sys
import os
import asyncio
import hashlib
import time
from pathlib import Path
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps
FIX_VERSION = "2026-08-13-titan-paginated-help-v10-7"
print(f"{Fore.GREEN}Ultra Self helper fix version: {FIX_VERSION}{Fore.RESET}")

#================= Config =================#
def _env(name, default=""): 
    return os.environ.get(name, str(default))

owner = int(_env("ADMIN_ID", "00000"))
api_id = int(_env("API_ID", "00000"))
api_hash = _env("API_HASH", "00000")
bot_token = _env("HELPER_BOT_TOKEN", _env("BOT_TOKEN", "00000"))

# MySQL - Try EVERY possible Railway variable name
from urllib.parse import urlparse as _urlparse

# Debug: print all MySQL-related env vars
print(f"{Fore.CYAN}{'='*60}")
print(f"{Fore.CYAN}Helper MySQL Environment Variables Check:")
for _k in sorted(os.environ.keys()):
    if any(_needle in _k.upper() for _needle in ["MYSQL", "DB_", "DATABASE", "DBHOST"]):
        _v = os.environ[_k]
        _masked = "***" + _v[-4:] if len(_v) > 6 else "***" if _v else "(empty)"
        print(f"{Fore.CYAN}  {_k} = {_masked}")
print(f"{Fore.CYAN}{'='*60}{Fore.RESET}")

# Strategy 1: DATABASE_URL
_db_url = _env("DATABASE_URL", "")
_parsed = False
if _db_url:
    try:
        if _db_url.startswith("mysql://") or _db_url.startswith("mysql+"):
            clean_url = _db_url.replace("mysql+pymysql://", "mysql://").replace("mysql+mysqldb://", "mysql://")
            _p = _urlparse(clean_url)
            DBHost = _p.hostname or "localhost"
            DBPort = _p.port or 3306
            DBName = _p.path.lstrip("/") or ""
            DBUser = _p.username or "root"
            DBPass = _p.password or ""
            if DBName and DBHost != "localhost":
                _parsed = True
                print(f"{Fore.GREEN}✓ Helper connected via DATABASE_URL: {DBHost}:{DBPort}/{DBName}{Fore.RESET}")
    except Exception as _e:
        print(f"{Fore.YELLOW}Helper DATABASE_URL parse failed: {_e}{Fore.RESET}")

# Strategy 2: Individual MYSQL* vars
if not _parsed:
    DBHost = _env("MYSQLHOST", _env("MYSQL_HOST", ""))
    DBPort = int(_env("MYSQLPORT", _env("MYSQL_PORT", "3306")))
    DBName = _env("MYSQLDATABASE", _env("MYSQL_DATABASE", ""))
    DBUser = _env("MYSQLUSER", _env("MYSQL_USERNAME", _env("MYSQL_USER", "root")))
    DBPass = _env("MYSQLPASSWORD", _env("MYSQL_PASSWORD", ""))
    if DBHost and DBName and DBHost != "localhost":
        _parsed = True
        print(f"{Fore.GREEN}✓ Helper connected via MYSQL* vars: {DBHost}:{DBPort}/{DBName}{Fore.RESET}")

# Strategy 3: RAILWAY_MYSQL_* vars
if not _parsed:
    DBHost = _env("RAILWAY_MYSQL_HOST", "")
    DBPort = int(_env("RAILWAY_MYSQL_PORT", "3306"))
    DBName = _env("RAILWAY_MYSQL_DATABASE", "")
    DBUser = _env("RAILWAY_MYSQL_USERNAME", "root")
    DBPass = _env("RAILWAY_MYSQL_PASSWORD", "")
    if DBHost and DBName:
        _parsed = True
        print(f"{Fore.GREEN}✓ Helper connected via RAILWAY_MYSQL* vars: {DBHost}:{DBPort}/{DBName}{Fore.RESET}")

if not _parsed or DBHost == "localhost":
    print(f"{Fore.RED}{'='*60}")
    print(f"{Fore.RED} Helper MySQL NOT configured!")
    print(f"{Fore.RED}  DBHost = {DBHost}")
    print(f"{Fore.RED}  DBName = {DBName}")
    print(f"{Fore.RED}{'='*60}{Fore.RESET}")
#==========================================#

def get_data(query):
     with pymysql.connect(host=DBHost, port=DBPort, database=DBName, user=DBUser, password=DBPass, cursorclass=pymysql.cursors.DictCursor) as connect:
          db = connect.cursor()
          db.execute(query)
          result = db.fetchone()
          return result

def get_datas(query):
     with pymysql.connect(host=DBHost, port=DBPort, database=DBName, user=DBUser, password=DBPass) as connect:
          db = connect.cursor()
          db.execute(query)
          result = db.fetchall()
          return result

def update_data(query):
     with pymysql.connect(host=DBHost, port=DBPort, database=DBName, user=DBUser, password=DBPass) as connect:
          db = connect.cursor()
          db.execute(query)
          connect.commit()

def ensure_column(table_name, column_name, column_definition):
     """Add missing columns to old Railway tables without deleting data."""
     rows = get_datas(f"SHOW COLUMNS FROM `{table_name}` LIKE '{column_name}'")
     if not rows:
          print(f"{Fore.YELLOW}[Helper DB Migration] Adding missing column `{column_name}` to `{table_name}`...{Fore.RESET}")
          update_data(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_definition}")

update_data("""
CREATE TABLE IF NOT EXISTS user(
id bigint PRIMARY KEY,
step varchar(150) DEFAULT 'none',
phone varchar(150) DEFAULT NULL,
amount bigint DEFAULT '0',
expir bigint DEFAULT '0',
account varchar(50) DEFAULT 'unverified',
self varchar(50) DEFAULT 'inactive',
pid bigint DEFAULT NULL
) default charset=utf8mb4;
""")
update_data("""
CREATE TABLE IF NOT EXISTS ownerlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")
update_data("""
CREATE TABLE IF NOT EXISTS adminlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")

# Keep helper and worker database schema compatible.
ensure_column("user", "step", "varchar(150) DEFAULT 'none'")
ensure_column("user", "phone", "varchar(150) DEFAULT NULL")
ensure_column("user", "amount", "bigint DEFAULT '0'")
ensure_column("user", "expir", "bigint DEFAULT '0'")
ensure_column("user", "account", "varchar(50) DEFAULT 'unverified'")
ensure_column("user", "self", "varchar(50) DEFAULT 'inactive'")
ensure_column("user", "pid", "bigint DEFAULT NULL")
update_data("UPDATE `user` SET step = 'none' WHERE step IS NULL")
update_data("UPDATE `user` SET amount = 0 WHERE amount IS NULL")
update_data("UPDATE `user` SET expir = 0 WHERE expir IS NULL")
update_data("UPDATE `user` SET account = 'unverified' WHERE account IS NULL")
update_data("UPDATE `user` SET self = 'inactive' WHERE self IS NULL")
print(f"{Fore.GREEN}✓ Helper database schema checked/migrated successfully{Fore.RESET}")

OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{owner}' LIMIT 1")
if OwnerUser is None:
     update_data(f"INSERT INTO ownerlist(id) VALUES({owner})")

AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{owner}' LIMIT 1")
if AdminUser is None:
     update_data(f"INSERT INTO adminlist(id) VALUES({owner})")

# Config validation
_helper_errors = []
if owner == 0:
    _helper_errors.append("ADMIN_ID is not set")
if api_id == 0:
    _helper_errors.append("API_ID is not set")
if api_hash == "00000":
    _helper_errors.append("API_HASH is not set")
if bot_token == "00000":
    _helper_errors.append("BOT_TOKEN is not set")
if not _parsed or DBHost == "localhost" or not DBName:
    _helper_errors.append(f"Helper MySQL not configured! DBHost={DBHost}, DBName={DBName}")
if _helper_errors:
    print(f"{Fore.RED}{'='*50}")
    print(f"{Fore.RED}Helper Config Errors:")
    for err in _helper_errors:
        print(f"{Fore.RED}  ✗ {err}")
    print(f"{Fore.RED}{'='*50}{Fore.RESET}")

app = Client("Helper", api_id, api_hash, bot_token=bot_token)

#================ TITAN User Identity Card =================#
# The Titan card assets live in source/assets and source/fonts.
# The code below deliberately does NOT redraw the template. It only composites
# the user's photo and dynamic values onto a fresh copy of the original card.
BASE_DIR = Path(__file__).resolve().parent

# Support both common layouts:
#   project/helper.py + project/source/assets + project/source/fonts
#   project/source/helper.py + project/source/assets + project/source/fonts
_source_candidates = (BASE_DIR / "source", BASE_DIR)
TITAN_SOURCE_DIR = next(
     (candidate for candidate in _source_candidates
      if (candidate / "assets").is_dir() and (candidate / "fonts").is_dir()),
     BASE_DIR / "source"
)
TITAN_ASSETS_DIR = TITAN_SOURCE_DIR / "assets"
TITAN_FONTS_DIR = TITAN_SOURCE_DIR / "fonts"


def _titan_find_template():
     """Find the user's original Titan template without hard-coding one filename."""
     explicit = os.environ.get("TITAN_CARD_TEMPLATE", "").strip()
     if explicit:
          candidate = Path(explicit)
          if not candidate.is_absolute():
               candidate = BASE_DIR / candidate
          if candidate.is_file():
               return candidate

     preferred = (
          # Prefer the active helper panel template uploaded for this project.
          "helper_panel_template.png",
          "helper_panel_template.jpg",
          "helper_panel_template.jpeg",
          "titan_card_template.png",
          "titan_card.png",
          "titan.png",
     )
     for name in preferred:
          candidate = TITAN_ASSETS_DIR / name
          if candidate.is_file():
               return candidate

     image_files = sorted(
          p for p in TITAN_ASSETS_DIR.iterdir()
          if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
     ) if TITAN_ASSETS_DIR.is_dir() else []
     if image_files:
          return image_files[0]

     raise FileNotFoundError(
          "Titan card template not found. Put the raw card image inside "
          f"{TITAN_ASSETS_DIR} or set TITAN_CARD_TEMPLATE."
     )


TITAN_TEMPLATE_PATH = _titan_find_template()


def _titan_find_font(folder, preferred_names, keywords=()):
     """Find a TTF font by preferred name first, then by useful filename keywords."""
     folder = Path(folder)
     if not folder.is_dir():
          raise FileNotFoundError(f"Titan font folder not found: {folder}")

     files = sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".ttf")
     if not files:
          raise FileNotFoundError(f"No TTF font found in: {folder}")

     by_lower = {p.name.lower(): p for p in files}
     for name in preferred_names:
          if name.lower() in by_lower:
               return by_lower[name.lower()]

     for p in files:
          low = p.name.lower()
          if all(keyword.lower() in low for keyword in keywords):
               return p

     # If a folder contains only one TTF, using it is safer than inventing a filename.
     if len(files) == 1:
          return files[0]

     # Last-resort deterministic fallback. This keeps the card functional even when
     # the downloaded font package uses different weight names.
     return files[0]


TITAN_FONT_PATHS = {
     "orbitron_black": _titan_find_font(
          TITAN_FONTS_DIR / "Orbitron",
          ("Orbitron-Black.ttf", "Orbitron-ExtraBold.ttf", "Orbitron-Bold.ttf"),
          ("orbitron", "black"),
     ),
     "orbitron_medium": _titan_find_font(
          TITAN_FONTS_DIR / "Orbitron",
          ("Orbitron-Medium.ttf", "Orbitron-Regular.ttf", "Orbitron.ttf"),
          ("orbitron", "medium"),
     ),
     "rajdhani_semibold": _titan_find_font(
          TITAN_FONTS_DIR / "Rajdhani",
          ("Rajdhani-SemiBold.ttf", "Rajdhani-Bold.ttf", "Rajdhani-Medium.ttf"),
          ("rajdhani", "semibold"),
     ),
     "rajdhani_medium": _titan_find_font(
          TITAN_FONTS_DIR / "Rajdhani",
          ("Rajdhani-Medium.ttf", "Rajdhani-Regular.ttf", "Rajdhani-SemiBold.ttf"),
          ("rajdhani", "medium"),
     ),
     "vazirmatn_semibold": _titan_find_font(
          TITAN_FONTS_DIR / "Vazirmatn",
          ("Vazirmatn-SemiBold.ttf", "Vazirmatn-Bold.ttf", "Vazirmatn-Medium.ttf", "Vazirmatn-Regular.ttf"),
          ("vazirmatn", "semibold"),
     ),
}

# Coordinates are based on the native 1280x853 Titan template supplied by the user.
TITAN_NATIVE_SIZE = (1280, 853)
TITAN_PROFILE_AREA = (98, 149, 418, 469)
TITAN_PROFILE_POLYGON = (
     (104, 228), (185, 149), (329, 149), (412, 229),
     (412, 389), (329, 469), (185, 469), (104, 389),
)

TITAN_TEXT_AREAS = {
     "name": (766, 255, 992, 303),
     "id": (766, 331, 992, 379),
     "username": (766, 408, 992, 456),
     "status": (766, 484, 992, 532),
}

TITAN_TEXT_COLOR = (245, 245, 245, 255)


def load_titan_fonts():
     """Validate every required font and return loaded fonts."""
     fonts = {}
     for name, path in TITAN_FONT_PATHS.items():
          if not path.is_file():
               raise FileNotFoundError(f"TITAN font not found: {path}")
          fonts[name] = ImageFont.truetype(str(path), 28)
     return fonts


def _titan_font(path, size):
     return ImageFont.truetype(str(path), int(size))


def _titan_text_bbox(draw, text, font, direction=None):
     kwargs = {"font": font}
     if direction:
          kwargs["direction"] = direction
          if direction == "rtl":
               kwargs["language"] = "fa"
     try:
          return draw.textbbox((0, 0), text, **kwargs)
     except Exception:
          # Some Pillow builds do not include libraqm. Keep the card usable rather
          # than crashing the whole helper when RTL shaping is unavailable.
          kwargs.pop("direction", None)
          kwargs.pop("language", None)
          return draw.textbbox((0, 0), text, **kwargs)


def _titan_contains_rtl(text):
     return any(
          ("\u0600" <= ch <= "\u06ff") or ("\u0750" <= ch <= "\u077f")
          for ch in str(text or "")
     )


def fit_text_to_area(draw, text, area, font_path, max_size=28, min_size=13, direction=None):
     """Fit dynamic text inside its reserved card area without touching the artwork."""
     left, top, right, bottom = area
     max_width = max(1, right - left)
     max_height = max(1, bottom - top)
     clean_text = str(text or "").strip() or "—"

     for size in range(int(max_size), int(min_size) - 1, -1):
          font = _titan_font(font_path, size)
          bbox = _titan_text_bbox(draw, clean_text, font, direction)
          if (bbox[2] - bbox[0]) <= max_width and (bbox[3] - bbox[1]) <= max_height:
               return font, clean_text

     # Only truncate after all sensible font sizes have been exhausted.
     ellipsis = "…"
     candidate = clean_text
     while len(candidate) > 1:
          candidate = candidate[:-1].rstrip()
          shortened = candidate + ellipsis
          font = _titan_font(font_path, min_size)
          bbox = _titan_text_bbox(draw, shortened, font, direction)
          if (bbox[2] - bbox[0]) <= max_width and (bbox[3] - bbox[1]) <= max_height:
               return font, shortened

     return _titan_font(font_path, min_size), ellipsis


def draw_titan_text(draw, text, area, font_path, max_size=28, min_size=13, direction=None):
     left, top, right, bottom = area
     font, fitted_text = fit_text_to_area(
          draw, text, area, font_path,
          max_size=max_size,
          min_size=min_size,
          direction=direction,
     )
     center_y = (top + bottom) // 2

     if direction == "rtl":
          try:
               draw.text(
                    (right, center_y), fitted_text, font=font,
                    fill=TITAN_TEXT_COLOR, anchor="rm",
                    direction="rtl", language="fa"
               )
               return
          except Exception:
               # Fallback for Pillow builds without libraqm.
               pass

     draw.text(
          (left, center_y), fitted_text, font=font,
          fill=TITAN_TEXT_COLOR, anchor="lm"
     )


def _titan_status_text(user):
     status = getattr(user, "status", None)
     status_name = getattr(status, "__class__", type(status)).__name__.lower()
     status_map = {
          "userstatusonline": "ONLINE",
          "userstatusoffline": "OFFLINE",
          "userstatusrecently": "RECENTLY",
          "userstatuslastweek": "LAST WEEK",
          "userstatuslastmonth": "LAST MONTH",
          "userstatusempty": "UNKNOWN",
     }
     return status_map.get(status_name, "UNKNOWN")


async def get_titan_profile_photo(client, user_id, user_obj=None):
     """Download the CURRENT user's real Telegram profile photo in memory.

     Pyrogram returns two different photo-related objects:
     - get_users(user_id).photo is a ChatPhoto and has big_file_id/small_file_id.
     - get_chat_photos(user_id) yields Photo objects and usually has file_id.

     The old implementation mixed these two types and looked for big_file_id on
     Photo objects, so file_id became None and download_media was never called.
     This function intentionally tries the reliable ChatPhoto path first, then
     falls back to get_chat_photos(). It never uses another user's photo.
     """
     try:
          # Strategy 0: the User object from the incoming update may already include ChatPhoto.
          chat_photo = getattr(user_obj, "photo", None) if user_obj else None
          file_id = (
               getattr(chat_photo, "big_file_id", None)
               or getattr(chat_photo, "small_file_id", None)
          )
          if file_id:
               downloaded = await client.download_media(file_id, in_memory=True)
               if downloaded:
                    try:
                         downloaded.seek(0)
                    except Exception:
                         pass
                    print(f"{Fore.GREEN}TITAN profile photo: downloaded via update User.photo.big_file_id{Fore.RESET}")
                    downloaded.titan_cache_key = str(file_id)
                    return downloaded

          # Strategy 1: reliable for bot/user objects returned by Pyrogram.
          try:
               tg_user = await client.get_users(int(user_id))
          except Exception:
               tg_user = None

          chat_photo = getattr(tg_user, "photo", None) if tg_user else None
          file_id = (
               getattr(chat_photo, "big_file_id", None)
               or getattr(chat_photo, "small_file_id", None)
          )
          if file_id:
               downloaded = await client.download_media(file_id, in_memory=True)
               if downloaded:
                    try:
                         downloaded.seek(0)
                    except Exception:
                         pass
                    downloaded.titan_cache_key = str(file_id)
                    print(f"{Fore.GREEN}TITAN profile photo: downloaded via get_users().photo.big_file_id{Fore.RESET}")
                    return downloaded

          # Strategy 2: fallback for environments where get_users().photo is empty.
          async for photo in client.get_chat_photos(int(user_id), limit=1):
               file_id = (
                    getattr(photo, "file_id", None)
                    or getattr(photo, "big_file_id", None)
                    or getattr(photo, "small_file_id", None)
               )
               if file_id:
                    downloaded = await client.download_media(file_id, in_memory=True)
                    if downloaded:
                         try:
                              downloaded.seek(0)
                         except Exception:
                              pass
                         downloaded.titan_cache_key = str(file_id)
                         print(f"{Fore.GREEN}TITAN profile photo: downloaded via get_chat_photos().file_id{Fore.RESET}")
                         return downloaded
               break

          # Strategy 3: Telegram Bot API fallback. This often works even when
          # Pyrogram bot-mode objects do not expose a downloadable media object.
          try:
               api_token = str(bot_token or "").strip()
               if api_token and api_token != "00000":
                    photos_res = requests.get(
                         f"https://api.telegram.org/bot{api_token}/getUserProfilePhotos",
                         params={"user_id": int(user_id), "limit": 1},
                         timeout=20
                    ).json()
                    if photos_res.get("ok") and photos_res.get("result", {}).get("photos"):
                         sizes = photos_res["result"]["photos"][0]
                         best = sizes[-1]
                         file_id = best.get("file_id")
                         if file_id:
                              file_res = requests.get(
                                   f"https://api.telegram.org/bot{api_token}/getFile",
                                   params={"file_id": file_id},
                                   timeout=20
                              ).json()
                              file_path = file_res.get("result", {}).get("file_path") if file_res.get("ok") else None
                              if file_path:
                                   content = requests.get(
                                        f"https://api.telegram.org/file/bot{api_token}/{file_path}",
                                        timeout=30
                                   ).content
                                   if content:
                                        bio = BytesIO(content)
                                        bio.name = "titan_profile_photo.jpg"
                                        bio.seek(0)
                                        bio.titan_cache_key = str(file_id)
                                        print(f"{Fore.GREEN}TITAN profile photo: downloaded via Bot API fallback{Fore.RESET}")
                                        return bio
                    else:
                         print(f"{Fore.YELLOW}TITAN Bot API profile lookup returned no photos for user {user_id}{Fore.RESET}")
          except Exception as exc:
               print(f"{Fore.YELLOW}TITAN Bot API profile fallback failed: {exc}{Fore.RESET}")

          print(f"{Fore.YELLOW}TITAN profile photo: no downloadable profile photo for user {user_id}{Fore.RESET}")
          return None
     except Exception as exc:
          print(f"{Fore.YELLOW}TITAN profile photo download failed: {exc}{Fore.RESET}")
          return None


def _titan_paste_profile_photo(card, photo_stream):
     """Fit the user's profile photo into the TiTaN octagon without touching the card design.

     This function modifies ONLY the inner profile-photo polygon. The red neon
     border/cyber lines remain untouched. The photo is resized with preserved
     aspect ratio and smart center-crop so the octagon is fully covered without
     stretch, squeeze, extra inner frames, or black gaps.
     """
     if photo_stream is None:
          return

     source = None
     should_close = False
     try:
          # Support BytesIO, bytes, bytearray, and file paths for testability.
          source = photo_stream
          if isinstance(photo_stream, (bytes, bytearray)):
               source = BytesIO(photo_stream)
          elif isinstance(photo_stream, (str, os.PathLike)):
               source = open(photo_stream, "rb")
               should_close = True
          else:
               try:
                    source.seek(0)
               except Exception:
                    pass

          with Image.open(source) as photo:
               photo = ImageOps.exif_transpose(photo)

               # Preserve transparent images safely by compositing over card-dark.
               if photo.mode in ("RGBA", "LA") or (photo.mode == "P" and "transparency" in photo.info):
                    rgba = photo.convert("RGBA")
                    solid = Image.new("RGBA", rgba.size, (5, 5, 7, 255))
                    solid.alpha_composite(rgba)
                    photo = solid.convert("RGB")
               else:
                    photo = photo.convert("RGB")

               # Exact inner octagon, inset from the glowing red border.
               # Only this polygon is changed; the original TiTaN frame remains above/around it.
               inner_polygon = (
                    # Expanded to fill the visible black photo well while staying inside the red neon border.
                    # This removes the 'small photo / second frame' look without touching the card frame.
                    (112, 226), (190, 150), (330, 150), (408, 228),
                    (408, 391), (330, 468), (190, 468), (112, 391),
               )
               xs = [p[0] for p in inner_polygon]
               ys = [p[1] for p in inner_polygon]
               paste_box = (min(xs), min(ys), max(xs), max(ys))
               width = paste_box[2] - paste_box[0]
               height = paste_box[3] - paste_box[1]

               # Smart cover crop: fills the octagon completely but keeps aspect ratio.
               # For portrait images we bias the crop slightly upward to keep faces/heads visible.
               source_ratio = photo.width / max(1, photo.height)
               target_ratio = width / max(1, height)
               if source_ratio > target_ratio:
                    crop_h = photo.height
                    crop_w = int(crop_h * target_ratio)
                    left = max(0, int((photo.width - crop_w) * 0.5))
                    top = 0
               else:
                    crop_w = photo.width
                    crop_h = int(crop_w / target_ratio)
                    left = 0
                    # Portrait Telegram avatars often have the face in the upper half.
                    focus_y = 0.34 if photo.height > photo.width else 0.5
                    top = max(0, int((photo.height - crop_h) * focus_y))
               right = min(photo.width, left + crop_w)
               bottom = min(photo.height, top + crop_h)
               if right <= left or bottom <= top:
                    cropped = ImageOps.fit(photo, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))
               else:
                    cropped = photo.crop((left, top, right, bottom)).resize((width, height), Image.Resampling.LANCZOS)
               cropped = cropped.convert("RGBA")

               mask = Image.new("L", (width, height), 0)
               mask_draw = ImageDraw.Draw(mask)
               polygon = [(x - paste_box[0], y - paste_box[1]) for x, y in inner_polygon]
               mask_draw.polygon(polygon, fill=255)

               layer = Image.new("RGBA", card.size, (0, 0, 0, 0))
               layer.paste(cropped, paste_box[:2], mask)
               card.alpha_composite(layer)

          if should_close:
               try:
                    source.close()
               except Exception:
                    pass
     except Exception as exc:
          print(f"{Fore.YELLOW}TITAN profile photo processing failed: {exc}{Fore.RESET}")


def generate_titan_user_card(user, profile_photo=None):
     """Render dynamic user data onto a fresh copy of the original Titan template."""
     load_titan_fonts()

     with Image.open(TITAN_TEMPLATE_PATH) as source:
          source = ImageOps.exif_transpose(source).convert("RGBA")
          if source.size != TITAN_NATIVE_SIZE:
               print(
                    f"{Fore.YELLOW}TITAN template is {source.size}, expected {TITAN_NATIVE_SIZE}. "
                    f"Coordinates will be scaled automatically.{Fore.RESET}"
               )
               source = source.resize(TITAN_NATIVE_SIZE, Image.Resampling.LANCZOS)
          card = source.copy()

     _titan_paste_profile_photo(card, profile_photo)

     draw = ImageDraw.Draw(card)
     first_name = (getattr(user, "first_name", None) or "").strip()
     last_name = (getattr(user, "last_name", None) or "").strip()
     display_name = " ".join(part for part in (first_name, last_name) if part).strip() or "Unknown"

     username = (getattr(user, "username", None) or "").strip().lstrip("@")
     username_text = f"@{username}" if username else "@NoUsername"
     user_id = str(getattr(user, "id", "") or "0")
     status_text = _titan_status_text(user)

     has_rtl_name = _titan_contains_rtl(display_name)
     draw_titan_text(
          draw, display_name, TITAN_TEXT_AREAS["name"],
          TITAN_FONT_PATHS["vazirmatn_semibold"] if has_rtl_name else TITAN_FONT_PATHS["rajdhani_semibold"],
          max_size=27, min_size=15,
          direction="rtl" if has_rtl_name else None,
     )
     draw_titan_text(
          draw, user_id, TITAN_TEXT_AREAS["id"],
          TITAN_FONT_PATHS["orbitron_medium"], max_size=24, min_size=15,
     )
     draw_titan_text(
          draw, username_text, TITAN_TEXT_AREAS["username"],
          TITAN_FONT_PATHS["rajdhani_semibold"], max_size=27, min_size=15,
     )
     draw_titan_text(
          draw, status_text, TITAN_TEXT_AREAS["status"],
          TITAN_FONT_PATHS["rajdhani_semibold"], max_size=27, min_size=15,
     )

     output = BytesIO()
     output.name = "titan_user_identity_card.png"
     card.save(output, format="PNG", optimize=False, compress_level=1)
     output.seek(0)
     return output


def _titan_photo_key_from_user(user):
     photo = getattr(user, "photo", None)
     return (
          getattr(photo, "big_photo_unique_id", None)
          or getattr(photo, "small_photo_unique_id", None)
          or getattr(photo, "big_file_id", None)
          or getattr(photo, "small_file_id", None)
          or "no-photo"
     )


def _titan_card_cache_key(user, photo_key="no-photo"):
     template_mtime = 0
     try:
          template_mtime = int(TITAN_TEMPLATE_PATH.stat().st_mtime)
     except Exception:
          pass
     parts = [
          "titan-card-v10-2",
          str(getattr(user, "id", "0")),
          str(getattr(user, "first_name", "") or ""),
          str(getattr(user, "last_name", "") or ""),
          str(getattr(user, "username", "") or ""),
          str(_titan_status_text(user)),
          str(TITAN_PANEL_VERSION),
          str(TITAN_SELFSZ_VERSION),
          str(photo_key or "no-photo"),
          str(template_mtime),
     ]
     return hashlib.sha256("|".join(parts).encode("utf-8", errors="ignore")).hexdigest()[:28]


async def render_titan_user_card_cached(client, user):
     """Return a cached PNG file path for this user's current card.

     If name/username/status/template/photo changes, the cache key changes and a
     fresh card is generated. Otherwise the previous PNG is reused.
     """
     cache_dir = BASE_DIR / "panel_cache" / "cards"
     cache_dir.mkdir(parents=True, exist_ok=True)

     initial_photo_key = _titan_photo_key_from_user(user)
     initial_path = cache_dir / f"titan_{_titan_card_cache_key(user, initial_photo_key)}.png"
     if initial_path.is_file():
          print(f"{Fore.CYAN}TITAN card cache hit: {initial_path.name}{Fore.RESET}")
          return str(initial_path)

     profile_photo = await get_titan_profile_photo(client, user.id, user)
     downloaded_key = getattr(profile_photo, "titan_cache_key", None) if profile_photo else None
     final_photo_key = downloaded_key or initial_photo_key or "no-photo"
     final_path = cache_dir / f"titan_{_titan_card_cache_key(user, final_photo_key)}.png"
     if final_path.is_file():
          print(f"{Fore.CYAN}TITAN card cache hit after photo lookup: {final_path.name}{Fore.RESET}")
          return str(final_path)

     titan_card = generate_titan_user_card(user, profile_photo)
     final_path.write_bytes(titan_card.getvalue())
     print(f"{Fore.GREEN}TITAN card generated and cached: {final_path.name}{Fore.RESET}")
     return str(final_path)


#=========================================================#

@app.on_message(filters.private, group=-1)
async def update(c, m):
     OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{m.chat.id}' LIMIT 1")
     AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{m.chat.id}' LIMIT 1")
     if OwnerUser is not None or AdminUser is not None:
          user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
          if user is None:
               update_data(f"INSERT INTO user(id) VALUES({m.chat.id})")
  
fahelp1 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ سراسری - شخصی ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
سکوت کاربر
➤ [ `.mute` ]
———————————————
حذف سکوت کاربر
➤ [ `.unmute` ]
———————————————
پاکسازی لیست سکوت
➤ [ `.allunmute` ]
———————————————
بلاک کاربر
➤ [ `.block` ]
———————————————
آنبلاک کاربر
➤ [ `.unblock` ]
———————————————
افزودن کاربر به لیست دشمنان
➤ [ `.setenemy` ]
———————————————
حذف کاربر از لیست دشمنان
➤ [ `.delenemy` ]
———————————————
پاکسازی لیست دشمنان
➤ [ `.clearenemy` ]
———————————————
افزودن کاربر به لیست عشق
➤ [ `.setlove` ]
———————————————
حذف کاربر از لیست عشق
➤ [ `.dellove` ]
———————————————
پاکسازی لیست عشق
➤ [ `.clearlove` ]
———————————————
تنظیم متن منشی خودکار
➤ [ `.monshi` ] **⤳** (TEXT)
———————————————
غیرفعال کردن منشی خودکار
➤ [ `.monshioff` ]
———————————————
تنظیم متن حالت آفلاینی
➤ [ `.afk` ] **⤳** (TEXT)
———————————————
غیرفعال کردن حالت آفلاینی
➤ [ `.unafk` ]
———————————————
دریافت هشدار تگ شدن
➤ [ `.tagalert` ] **⤳** (on OR off)
———————————————
ساخت کانال
➤ [ `.creatchannel` ] **⤳** (Name)
———————————————
ساخت گروه
➤ [ `.creatgroup` ] **⤳** (Name)
———————————————
ساخت سوپر گروه
➤ [ `.creatsupergroup` ] **⤳** (Name)
———————————————
اسپم متن معمولی
➤ [ `.spam` ] **⤳** (NUM TEXT)
———————————————
اسپم متن آرام
➤ [ `.slowspam` ] **⤳** (NUM TEXT)
———————————————
اسپم متن و حذف
➤ [ `.statspam` ] **⤳** (NUM TEXT)
———————————————
اسپم متن سریع
➤ [ `.fastspam` ] **⤳** (NUM TEXT)
———————————————
فعال کردن کامنت اول
➤ [ `.firstcom` ] **⤳** (on OR off)
———————————————
تنظیم متن کامنت اول
➤ [ `.first_message` ] **⤳** (TEXT) (Reply)
———————————————
تنظیم زمان ارسال خودکار متن
➤ [ `.text_time` ] **⤳** (HH:MM)
———————————————
تنظیم زمان ارسال خودکار عکس
➤ [ `.photo_time` ] **⤳** (HH:MM)
———————————————
تنظیم متن ارسال خودکار متن
➤ [ `.text_send_time` ] **⤳** (TEXT) (Reply)
———————————————
تنظیم عکس ارسال خودکار عکس
➤ [ `.photo_send_time` ] **⤳** (Reply)
———————————————
فعال یا غیرفعال کردن پاسخ خودکار
➤ [ `.answer` ] **⤳** (on OR off)
———————————————
تنظیم سوال جواب برای پاسخ خودکار
➤ [ `.addan` ] **⤳** (Question:Answer)
———————————————
حذف یک سوال جواب
➤ [ `.delan` ] **⤳** (Answer)
———————————————
مشاهده لیست سوال جواب ها
➤ [ `.anlist` ]
———————————————
پاکسازی لیست پاسخ خودکار
➤ [ `.anclear` ]
———————————————
فعال یا غیرفعال کردن حالت خوش آمد گویی
➤ [ `.welcome` ] **⤳** (on OR off)
———————————————
تنظیم متن خوش آمد گویی
➤ [ `.welcome_add` ] **⤳** (TEXT)
———————————————
نمایش متن خوش آمد گویی
➤ [ `.welcome_show` ]
———————————————
ریست متن خوش آمد گویی
➤ [ `.welcome_reset` ]
———————————————
**توجه! برای استفاده از دستورات زیر باید مالک یا ادمین گروه مورد نظر با دسترسی های لازم باشید**

بن کاربر در گروه
➤ [ `.ban` ] **⤳** (ID) (Reply)
———————————————
آنبن کاربر در گروه
➤ [ `.unban` ] **⤳** (ID) (Reply)
———————————————
سکوت کاربر در گروه
➤ [ `.setmute` ] **⤳** (ID) (Reply)
———————————————
حذف سکوت کاربر در گروه
➤ [ `.delmute` ] **⤳** (ID) (Reply)
———————————————
تنظیم عکس گروه
➤ [ `.setchatphoto` ] **⤳** (Reply)
———————————————
تنظیم نام گروه
➤ [ `.setchattitle` ] **⤳** (TEXT)
———————————————
تنظیم بیوگرافی گروه
➤ [ `.setchatbio` ] **⤳** (TEXT)
———————————————
تنظیم نام کاربری گروه
➤ [ `.setchatusername` ] **⤳** (Username)
———————————————
سنجاق پیام در گروه
➤ [ `.pin` ] **⤳** (Reply)
———————————————
حذف سنجاق پیام در گروه
➤ [ `.unpin` ] **⤳** (Reply)
———————————————
حذف همه سنجاق های گروه
➤ [ `.unpinall` ]
———————————————
حذف کانال
➤ [ `.deletechannel` ] **⤳** (Username)
———————————————
حذف گروه
➤ [ `.deletegroup` ] **⤳** (Username)
———————————————
حذف همه پیام های کاربر در گروه
➤ [ `.delallmsguser` ] **⤳** (Reply)
———————————————
تنظیم زمان بین ارسال هر پیام برای اعضای گروه برحسب ثانیه
➤ [ `.slowmod` ] **⤳** (NUM)
———————————————
حذف تعدادی از پیام ها
➤ [ `.delete` ] **⤳** (NUM)
———————————————
تگ ادمین های گروه
➤ [ `.tadmin` ]
———————————————
تگ همه کاربران گروه
➤ [ `.tagall` ] **⤳** (TEXT) (Reply)
———————————————
لغو تگ کاربران گروه
➤ [ `.cancel` ]
———————————————
پاکسازی تاریخچه
➤ [ `.delethistory` ]
———————————————
حذف یک پیام
➤ [ `.del` ] **⤳** (Reply)
———————————————
"""

fahelp2 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ پروفایل ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
تنظیم نام اکانت
➤ [ `.setname` ] **⤳** (TEXT)
———————————————
تنظیم نام خانوادگی اکانت
➤ [ `.setlastname` ] **⤳** (TEXT)
———————————————
تنظیم بیوگرافی اکانت
➤ [ `.setbio` ] **⤳** (TEXT)
———————————————
تنظیم فونت خودکار نام
➤ [ `.fontname` ] **⤳** (on OR off)
———————————————
تنظیم ساعت روی نام
➤ [ `.timename` ] **⤳** (on OR off)
———————————————
تنظیم ساعت روی نام 2
➤ [ `.2timename` ] **⤳** (on OR off)
———————————————
تنظیم ساعت در بیوگرافی ساده
➤ [ `.timebio` ] **⤳** (on OR off)
———————————————
تنظیم ساعت در بیوگرافی رندوم
➤ [ `.2timebio` ] **⤳** (on OR off)
———————————————
تنظیم ساعت در بیوگرافی با خورشید و ماه
➤ [ `.3timebio` ] **⤳** (on OR off)
———————————————
تنظیم ساعت در بیوگرافی با خورشید و ماه و روز
➤ [ `.4timebio` ] **⤳** (on OR off)
———————————————
تنظیم ساعت در بیوگرافی با قلب رنگی
➤ [ `.5timebio` ] **⤳** (on OR off)
———————————————
تنظیم ساعت در بیوگرافی با ثبت فضولی
➤ [ `.6timebio` ] **⤳** (on OR off)
———————————————
تنظیم عکس پروفایل اکانت
➤ [ `.setprofile` ] **⤳** (Reply)
———————————————
حذف عکس پروفایل اکانت
➤ [ `.delprofile` ]
———————————————
تنظیم ساعت روی عکس پروفایل
➤ [ `.autopic` ]
———————————————
تنظیم ساعت روی عکس پروفایل 2
➤ [ `.2autopic` ]
———————————————
تنظیم ساعت روی عکس پروفایل 3
➤ [ `.3autopic` ]
———————————————
تنظیم ساعت روی عکس پروفایل 4
➤ [ `.4autopic` ]
———————————————
"""

fahelp3 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ دانلودر ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
دریافت اطلاعات پیج اینستاگرام
➤ [ `.iginfo` ] **⤳** (Username)
———————————————
دانلود از اینستاگرام
➤ [ `.igdl` ] **⤳** (URL)
———————————————
دانلود از اینستاگرام & یوتیوب &  فیسبوک & تیک تاک
➤ [ `.down` ] **⤳** (URL)
———————————————
جستجو و دانلود از یوتیوب با متن
➤ [ `.youtube` ] **⤳** (TEXT)
———————————————
جستجوی اپلیکیشن
➤ [ `.app` ] **⤳** (TEXT)
———————————————
جستجوی اپلیکیشن 2
➤ [ `.apk` ] **⤳** (TEXT)
———————————————
"""

fahelp4 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ آپلودر ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
آپلود متن
➤ [ `.neko` ] **⤳** (Reply)
———————————————
آپلود عکس
➤ [ `.telegraph` ] **⤳** (Reply)
———————————————
"""

fahelp5 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ حالت متن ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
حالت بولد
➤ [ `.bold` ] **⤳** (on OR off)
———————————————
حالت اسپویلر
➤ [ `.spoiler` ] **⤳** (on OR off)
———————————————
حالت کج نویس
➤ [ `.italic` ] **⤳** (on OR off)
———————————————
حالت کد نویس
➤ [ `.code` ] **⤳** (on OR off)
———————————————
حالت زیر خط
➤ [ `.underline` ] **⤳** (on OR off)
———————————————
حالت خط خوردگی
➤ [ `.strike` ] **⤳** (on OR off)
———————————————
حالت ایموجی
➤ [ `.emoji` ] **⤳** (on OR off)
———————————————
حالت نقل قول
➤ [ `.quote` ] **⤳** (on OR off)
———————————————
حالت منشن
➤ [ `.mention` ] **⤳** (on OR off)
———————————————
تنظیم ری اکشن روی کاربر
➤ [ `.setreact` ] **⤳** (Emoji) (Reply)
———————————————
حذف ری اکشن
➤ [ `.delreact` ] **⤳** (Reply)
———————————————
لیست ری اکشن ها
➤ [ `.reactlist` ]
———————————————
ارسال متن به صورت پله ای
➤ [ `.lad` ] **⤳** (TEXT)
———————————————
"""

fahelp6 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ حالت اکشن ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
حالت نوشتن
➤ [ `.typing` ] **⤳** (on OR off)
———————————————
حالت بازی کردن
➤ [ `.playing` ] **⤳** (on OR off)
———————————————
حالت ضبط ویدیو
➤ [ `.record_vid` ] **⤳** (on OR off)
———————————————
حالت انتخاب استیکر
➤ [ `.choose_sticker` ] **⤳** (on OR off)
———————————————
حالت آپلود ویدیو
➤ [ `.upload_vid` ] **⤳** (on OR off)
———————————————
حالت آپلود فایل
➤ [ `.upload_doc` ] **⤳** (on OR off)
———————————————
حالت آپلود فایل صوتی
➤ [ `.upload_audio` ] **⤳** (on OR off)
———————————————
حالت صحبت کردن
➤ [ `.speaking` ] **⤳** (on OR off)
———————————————
حالت آنلاین بودن اکانت
➤ [ `.online` ] **⤳** (on OR off)
———————————————
حالت آفلاین بودن اکانت
➤ [ `.offline` ] **⤳** (on OR off)
———————————————
"""

fahelp7 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ وبهوک ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
تنظیم وبهوک
➤ [ `.setwebhook` ] **⤳** (Token URL)
———————————————
حذف وبهوک
➤ [ `.delwebhook` ] **⤳** (Token)
———————————————
پاکسازی آپدیت های در انتظار
➤ [ `.delupdate` ] **⤳** (Token)
———————————————
دریافت اطلاعات وبهوک
➤ [ `.webhookinfo` ] **⤳** (Token)
———————————————
دریافت اطلاعات ربات
➤ [ `.botinfo` ] **⤳** (Token)
———————————————
"""

fahelp8 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ قفل ها ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
فعال یا غیرفعال کردن قفل پیوی
➤ [ `.pvlock` ] **⤳** (on OR off)
———————————————
فعال یا غیرفعال کردن جوین اجباری پیوی
➤ [ `.monshi2` ] **⤳** (on OR off)
———————————————
لیست نام قفل ها
➤ [ `.hlock` ]
———————————————
وضعیت قفل گروه
➤ [ `.locks` ]
———————————————
قفل یک ویژگی
➤ [ `.lock` ] **⤳** (Name)
———————————————
بازکردن قفل یک ویژگی
➤ [ `.unlock` ] **⤳** (Name)
———————————————
قفل همه ویژگی ها
➤ [ `.lock all` ]
———————————————
بازکردن قفل همه ویژگی ها
➤ [ `.unlock all` ]
———————————————
"""

fahelp9 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ کرون جاب ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
تنظیم کرون جاب برحسب دقیقه
➤ [ `.cron` ] **⤳** (URL Time)
Time: 1, 2, 5, 10, 15, 30 ...
———————————————
"""

fahelp10 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ آنتی لاگین ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
فعال یا غیرفعال کردن آنتی لاگین اکانت
➤ [ `.antilog` ] **⤳** (on OR off)
———————————————
"""

fahelp11 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ تبچی ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
وضعیت تبچی
➤ [ `.tabchi status` ]
———————————————
فعال یا غیرفعال کردن ارسال خودکار به پیوی ها
➤ [ `.tabchipv` ] **⤳** (on OR off)
———————————————
فعال یا غیرفعال کردن ارسال خودکار به گروه ها
➤ [ `.tabchigp` ] **⤳** (on OR off)
———————————————
تنظیم بنر ارسال خودکار به پیوی ها
➤ [ `.setbannerpv` ] **⤳** (TEXT) (Reply)
———————————————
تنظیم بنر ارسال خودکار به گروه ها
➤ [ `.setbannergp` ] **⤳** (TEXT) (Reply)
———————————————
تنظیم زمان ارسال خودکار به پیوی ها برحسب ثانیه
➤ [ `.settimerpv` ] **⤳** (NUM)
———————————————
تنظیم زمان ارسال خودکار به گروه ها برحسب ثانیه
➤ [ `.settimergp` ] **⤳** (NUM)
———————————————
ارسال همگانی به پیوی ها
➤ [ `.sendpv` ] **⤳** (TEXT) (Reply)
———————————————
ارسال همگانی به گروه ها
➤ [ `.sendgp` ] **⤳** (TEXT) (Reply)
———————————————
تنظیم بنر ارسال به پیوی اعضای گروه
➤ [ `.setbannersender` ] **⤳** (TEXT) (Reply)
———————————————
ارسال به پیوی اعضای گروه مورد نظر
➤ [ `.sendall` ] **⤳** (Username)
———————————————
دریافت لینک گروه
➤ [ `.invitelink` ]
———————————————
پیوستن به گروه
➤ [ `.join` ] **⤳** (Link)
———————————————
خروج از گروه
➤ [ `.leave` ] **⤳** (Link)
———————————————
خروج از تمام گروه ها
➤ [ `.leaveallgc` ]
———————————————
خروج از تمام کانال ها
➤ [ `.leaveallch` ]
———————————————
"""

fahelp12 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ ویرایشگر عکس ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**با دستورات زیر می‌توانید متن مورد نظر خود را روی عکس طرح کنید**

➤ [ `.kanna` ] **⤳** (TEXT)
———————————————
➤ [ `.clyde` ] **⤳** (TEXT)
———————————————
➤ [ `.write` ] **⤳** (TEXT)
———————————————
➤ [ `.mind` ] **⤳** (TEXT)
———————————————
➤ [ `.trump` ] **⤳** (TEXT)
———————————————
➤ [ `.o` ] **⤳** (TEXT)
———————————————
➤ [ `.o2` ] **⤳** (TEXT)
———————————————
➤ [ `.bish` ] **⤳** (TEXT)
———————————————
➤ [ `.latex` ] **⤳** (TEXT)
———————————————
**با دستورات زیر می‌توانید روی عکس مورد نظر خود فیلتر های مختلف ست کنید**

➤ [ `.blue` ] **⤳** (Reply)
———————————————
➤ [ `.green` ] **⤳** (Reply)
———————————————
➤ [ `.red` ] **⤳** (Reply)
———————————————
➤ [ `.grey` ] **⤳** (Reply)
———————————————
➤ [ `.grey2` ] **⤳** (Reply)
———————————————
➤ [ `.sepia` ] **⤳** (Reply)
———————————————
➤ [ `.threshold` ] **⤳** (Reply)
———————————————
➤ [ `.blurple` ] **⤳** (Reply)
———————————————
➤ [ `.filter` ] **⤳** (Reply)
———————————————
**با دستورات زیر می‌توانید استایل و ابعاد عکس مورد نظر خود را تغییر دهید**

➤ [ `.bisexual` ] **⤳** (Reply)
———————————————
➤ [ `.blur` ] **⤳** (Reply)
———————————————
➤ [ `.horny` ] **⤳** (Reply)
———————————————
➤ [ `.stupid` ] **⤳** (Reply)
———————————————
➤ [ `.lesbian` ] **⤳** (Reply)
———————————————
➤ [ `.lgbt` ] **⤳** (Reply)
———————————————
➤ [ `.lolice` ] **⤳** (Reply)
———————————————
➤ [ `.non` ] **⤳** (Reply)
———————————————
➤ [ `.psexual` ] **⤳** (Reply)
———————————————
➤ [ `.pixel` ] **⤳** (Reply)
———————————————
➤ [ `.simp` ] **⤳** (Reply)
———————————————
➤ [ `.spin` ] **⤳** (Reply)
———————————————
➤ [ `.toni` ] **⤳** (Reply)
———————————————
**با دستورات زیر می‌توانید روی عکس مورد نظر خود فیلتر ها و تغییرات فان ست کنید**

➤ [ `.comrade` ] **⤳** (Reply)
———————————————
➤ [ `.gay` ] **⤳** (Reply)
———————————————
➤ [ `.glass` ] **⤳** (Reply)
———————————————
➤ [ `.jail` ] **⤳** (Reply)
———————————————
➤ [ `.wasted` ] **⤳** (Reply)
———————————————
➤ [ `.pass` ] **⤳** (Reply)
———————————————
"""

fahelp13 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ گیف و لوگو ساز ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
ساخت لوگو با متن
➤ [ `.logo` ] **⤳** (TEXT)
———————————————
ساخت لوگو با متن 2
➤ [ `.logo2` ] **⤳** (TEXT)
———————————————
ساخت لوگو با متن و طرح دلخواه
➤ [ `.lg` ] **⤳** (TEXT Mode)
Mode: 1-138
———————————————
ساخت گیف با متن
➤ [ `.gif` ] **⤳** (TEXT)
———————————————
ساخت گیف با متن 2
➤ [ `.giff` ] **⤳** (TEXT)
———————————————
"""

fahelp14 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ کامپایلر ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
➤ [ `.py` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.js` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.php` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.kotlin` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.go` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.java` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.lua` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.exec` ] **⤳** (Code)
———————————————
"""

fahelp15 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ ابزار ها ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
استخراج فایل از حالت فشرده
➤ [ `.unzip` ] **⤳** (Reply)
———————————————
تغییر نام فایل
➤ [ `.rname` ] **⤳** (TEXT) (Reply)
———————————————
چکر شماره مجازی
➤ [ `.check` ] **⤳** (Number)
———————————————
اسکرین شات از متن
➤ [ `.q` ] **⤳** (Reply)
———————————————
اسکرین شات از متن دلخواه
➤ [ `.qq` ] **⤳** (TEXT)
———————————————
دریافت نتایج بازی های Cricket
➤ [ `.cricket` ] **⤳**
———————————————
وضعیت آب و هوا
➤ [ `.weather` ] **⤳** (City Name)
———————————————
زمان اذان
➤ [ `.azan` ] **⤳** (City Name)
———————————————
تبدیل کننده دما
➤ [ `.t` ] **⤳** (NUM c OR f)
eg: .t 25 c
———————————————
تبدیل کننده ارز دیجیتال
➤ [ `.c` ] **⤳** (NUM Currency1 Currency2)
eg: .c 100 usdt eur
———————————————
ماشین حساب ریاضی
➤ [ `.e` ] **⤳** (Match)
eg: .e 2+2
———————————————
دریافت آیپی سایت
➤ [ `.ip` ] **⤳** (Domain)
———————————————
دریافت اطلاعات آیپی
➤ [ `.whoisip` ] **⤳** (IP)
———————————————
کوتاه کننده لینک
➤ [ `.link` ] **⤳** (URL)
———————————————
کوتاه کننده لینک 2
➤ [ `.link2` ] **⤳** (URL)
———————————————
دریافت پینگ سایت
➤ [ `.p` ] **⤳** (Domain)
———————————————
اسکرین شات از سایت
➤ [ `.screenshot` ] **⤳** (Domain)
———————————————
اسکرین شات از سایت 2
➤ [ `.screenshot2` ] **⤳** (Domain)
———————————————
اسکرین شات از سایت 3
➤ [ `.screenshot3` ] **⤳** (Domain)
———————————————
اسکرین شات از سایت 4
➤ [ `.screenshot4` ] **⤳** (Domain)
———————————————
اسکرین شات از سایت 5
➤ [ `.shot` ] **⤳** (Domain)
———————————————
دریافت اطلاعات اکانت گیت هاب
➤ [ `.github` ] **⤳** (Username)
———————————————
دریافت اطلاعات پروژه
➤ [ `.git` ] **⤳** (TEXT)
———————————————
جستجو در دیکشنری
➤ [ `.dict` ] **⤳** (Word)
———————————————
کپی کردن پروفایل یک اکانت
➤ [ `.clone` ] **⤳** (ID) (Reply)
———————————————
دریافت تاریخ ساخت اکانت
➤ [ `.i` ] **⤳** (ID) (Reply)
———————————————
دریافت تاریخ ساخت اکانت سلف
➤ [ `.creation` ]
———————————————
وضعیت محدودیت اکانت سلف
➤ [ `.limit` ]
———————————————
دریافت اطلاعات کشور
➤ [ `.country` ] **⤳** (Name)
———————————————
تبدیل استیکر به عکس
➤ [ `.tp` ] **⤳** (Reply)
———————————————
تبدیل عکس به استیکر
➤ [ `.ts` ] **⤳** (Reply)
———————————————
ساخت گیف
➤ [ `.tg` ] **⤳** (Reply)
———————————————
ترجمه به فارسی
➤ [ `.fa` ] **⤳** (TEXT)
———————————————
ترجمه به انگلیسی
➤ [ `.en` ] **⤳** (TEXT)
———————————————
دریافت فیلم
➤ [ `.movie` ] **⤳** (TEXT)
———————————————
دریافت انیمه
➤ [ `.anim` ] **⤳** (TEXT)
———————————————
ساخت پسورد با تعداد کاراکتر دلخواه
➤ [ `.pass` ] **⤳** (NUM)
———————————————
تبدیل متن به کد مورس
➤ [ `.morset` ] **⤳** (TEXT)
———————————————
تبدیل کد مورس به متن
➤ [ `.unmorset` ] **⤳** (Code)
———————————————
دریافت تاریخ
➤ [ `.date` ]
———————————————
دریافت اطلاعات یک اکانت
➤ [ `.id` ] **⤳** (ID) (Reply)
———————————————
دریافت اطلاعات یک پیام
➤ [ `.get_message` ] **⤳** (Reply)
———————————————
منشن کردن یک کاربر
➤ [ `.mention` ] **⤳** (ID) (Reply)
———————————————
بررسی صحت کد ملی
➤ [ `.meli` ] **⤳** (Number)
———————————————
استعلام کارت بانکی
➤ [ `.estelam` ] **⤳** (Number)
———————————————
دریافت اخبار روز
➤ [ `.news` ] **⤳** (Category)
Category: business, entertainment, general, health, science, sports, technology
———————————————
دریافت کارت بین
➤ [ `.ccgen` ]
———————————————
دریافت اخبار روز
➤ [ `.yjc` ]
———————————————
استخراج متن از عکس
➤ [ `.ocr` ] **⤳** (Reply)
———————————————
دانلود عکس زمان دار
➤ [ `.dl` ] **⤳** (Reply)
———————————————
ذخیره محتوا در پیام های ذخیره شده
➤ [ `.waitt` ] **⤳** (Reply)
———————————————
دریافت ساعت
➤ [ `.time` ]
———————————————
"""

fahelp16 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ اکانت ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
افزودن ادمین به سلف
➤ [ `.addadmin` ] **⤳** (ID) (Reply)
———————————————
حذف ادمین سلف
➤ [ `.deladmin` ] **⤳** (ID) (Reply)
———————————————
لیست ادمین های سلف
➤ [ `.adminlist` ]
———————————————
پاکسازی لیست ادمین های سلف
➤ [ `.clearadminlist` ]
———————————————
دریافت آیدی عددی اکانت سلف
➤ [ `id` ]
———————————————
وضعیت محدودیت اکانت سلف
➤ [ `.limit` ]
———————————————
دریافت تاریخ ساخت اکانت سلف
➤ [ `.creation` ]
———————————————
دریافت اطلاعات سشن اکانت سلف
➤ [ `.session` ]
———————————————
"""

fahelp17 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ کتاب ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
دریافت جوک
➤ [ `.joke` ]
———————————————
دریافت شعر
➤ [ `.poem` ]
———————————————
دریافت دانستنی
➤ [ `.know` ]
———————————————
دریافت نقل قول
➤ [ `.quote` ]
———————————————
جستجو در ویکی پدیا
➤ [ `.wiki` ] **⤳** (TEXT)
———————————————
جستجو در گوگل
➤ [ `.google` ] **⤳** (TEXT)
———————————————
تبدیل عدد به حروف
➤ [ `.num` ] **⤳** (NUM)
———————————————
دریافت اطلاعات نام
➤ [ `.name` ] **⤳** (Name)
———————————————
دریافت بیوگرافی
➤ [ `.bio` ]
———————————————
دریافت خاطره
➤ [ `.memo` ]
———————————————
دریافت پ ن پ
➤ [ `.pnp` ]
———————————————
دریافت الکی
➤ [ `.alaki` ]
———————————————
دریافت حدیث
➤ [ `.hadis` ]
———————————————
دریافت داستان
➤ [ `.dastan` ]
———————————————
دریافت نام رندوم
➤ [ `.rname` ]
———————————————
دریافت فال
➤ [ `.fal` ]
———————————————
دریافت استخاره
➤ [ `.estekhare` ]
———————————————
دریافت ذکر
➤ [ `.zekr` ]
———————————————
"""

fahelp18 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ سرگرمی ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
تقلب در تاس
➤ [ `.tas` ] **⤳** (1-6)
———————————————
تقلب در دارت
➤ [ `.dart` ]
———————————————
تقلب در بولینگ
➤ [ `.bowling` ]
———————————————
تقلب در بسکتبال
➤ [ `.basketball` ]
———————————————
تقلب در فوتبال
➤ [ `.football` ] **⤳** (1 OR 6)
1: Fail
4: Goal
———————————————
دریافت بازی رندوم 1
➤ [ `.game` ]
———————————————
دریافت بازی رندوم 2
➤ [ `.bazi` ]
———————————————
دریافت بازی رندوم 3
➤ [ `.hehe` ]
———————————————
**سایر سرگرمی ها**

➤ [ `.moon` ]
———————————————
➤ [ `.clock` ]
———————————————
➤ [ `.thunder` ]
———————————————
➤ [ `.earth` ]
———————————————
➤ [ `.heart` ]
———————————————
➤ [ `.love` ]
———————————————
➤ [ `.santet` ]
———————————————
➤ [ `.nah` ]
———————————————
➤ [ `.ajg` ]
———————————————
➤ [ `.babi` ]
———————————————
➤ [ `.tank` ]
———————————————
➤ [ `.y` ]
———————————————
➤ [ `.awk` ]
———————————————
➤ [ `.tembak` ]
———————————————
➤ [ `.heli` ]
———————————————
➤ [ `.gabut` ]
———————————————
➤ [ `.syg` ]
———————————————
➤ [ `.dino` ]
———————————————
➤ [ `.hack` ]
———————————————
➤ [ `.fuck` ]
———————————————
➤ [ `.koc` ]
———————————————
➤ [ `.charging` ]
———————————————
➤ [ `.gang` ]
———————————————
➤ [ `.hypo` ]
———————————————
➤ [ `.ding` ]
———————————————
➤ [ `.wtf` ]
———————————————
➤ [ `.call` ]
———————————————
➤ [ `.bomb` ]
———————————————
➤ [ `.brain` ]
———————————————
➤ [ `.ahh` ]
———————————————
➤ [ `.hmm` ]
———————————————
"""

fahelp19 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ بازار ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
قیمت کالا در بازار ایران (باسلام)
➤ [ `.price` ] **⤳** (TEXT)
———————————————
قیمت کالا در بازار ایران (ترب)
➤ [ `.qeymat` ] **⤳** (TEXT)
———————————————
لیست نماد ارز های دیجیتال
➤ [ `.cryptolist` ]
———————————————
قیمت ارز دیجیتال
➤ [ `.crypto` ] **⤳** (Name)
———————————————
تبدیل کننده ارز دیجیتال
➤ [ `.c` ] **⤳** (NUM Currency1 Currency2)
eg: .c 100 usdt eur
———————————————
قیمت ترون
➤ [ `.trx` ]
———————————————
لیست قیمت ارز ها
➤ [ `.arz` ]
———————————————
استعلام کارت بانکی
➤ [ `.estelam` ] **⤳** (Number)
———————————————
دریافت اطلاعات تراکنش ارز دیجیتال
➤ [ `.tara` ] **⤳** (TransLink)
———————————————
"""

fahelp20 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ استیکر - گیف ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
ساخت استیکر با متن
➤ [ `.sticker` ] **⤳** (TEXT)
———————————————
دریافت اطلاعات استیکر
➤ [ `.stickerinfo` ] **⤳** (Reply)
———————————————
ساخت استیکر با کد ارور
➤ [ `.error` ] **⤳** (Code)
eg: .error 404
———————————————
کوچک کردن استیکر و عکس
➤ [ `.tiny` ] **⤳** (Reply)
———————————————
تبدیل عکس به استیکر
➤ [ `.ts` ] **⤳** (Reply)
———————————————
ساخت گیف
➤ [ `.tg` ] **⤳** (Reply)
———————————————
**دریافت گیف رندوم**

➤ [ `.palm` ]
———————————————
➤ [ `.wink` ]
———————————————
➤ [ `.hug` ]
———————————————
➤ [ `.pat` ]
———————————————
"""

fahelp21 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ هوش مصنوعی ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**هوش مصنوعی متنی**

➤ [ `.gpt3` ] **⤳** (TEXT)
———————————————
➤ [ `.gpt4` ] **⤳** (TEXT)
———————————————
➤ [ `.bard` ] **⤳** (TEXT)
———————————————
➤ [ `.asq` ] **⤳** (TEXT)
———————————————
➤ [ `.messi` ] **⤳** (TEXT)
———————————————
➤ [ `.ronaldo` ] **⤳** (TEXT)
———————————————
➤ [ `.ilon` ] **⤳** (TEXT)
———————————————
**هوش مصنوعی صوتی**

➤ [ `.` ] **⤳** (TEXT) زن
———————————————
➤ [ `/` ] **⤳** (TEXT) مرد
———————————————
➤ [ `.voice` ] **⤳** (TEXT)
———————————————
➤ [ `.crush` ] **⤳** (TEXT)
———————————————
➤ [ `.wo` ] **⤳** (TEXT) زن
———————————————
➤ [ `.ma` ] **⤳** (TEXT) مرد
———————————————
➤ [ `.v` ] **⤳** (TEXT)
———————————————
دریافت لیست آیدی ها
➤ [ `.vl` ]
———————————————
تنظیم لهجه مورد نظر با آیدی
➤ [ `.sv` ] **⤳** (Mode)
———————————————
**هوش مصنوعی تصویری**

➤ [ `.pgpt` ] **⤳** (TEXT)
———————————————
"""

fahelp22 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ عکس ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
ساخت رنگ
➤ [ `.color` ] **⤳** (Color)
———————————————
**دریافت عکس رندوم حیوانات**

➤ [ `.pikachu` ]
———————————————
➤ [ `.whale` 
———————————————
➤ [ `.foxx` ]
———————————————
➤ [ `.doggg` ]
———————————————
➤ [ `.rpanda` ]
———————————————
➤ [ `.raccoon` ]
———————————————
➤ [ `.panda` ]
———————————————
➤ [ `.koala` ]
———————————————
➤ [ `.kangroo` ]
———————————————
➤ [ `.fox` ]
———————————————
➤ [ `.dogg` ]
———————————————
➤ [ `.birdd` ]
———————————————
➤ [ `.catt` ]
———————————————
➤ [ `.bird` ]
———————————————
➤ [ `.dog` ]
———————————————
➤ [ `.cat` ]
———————————————
➤ [ `.robo` ] **⤳** (1-999999)
———————————————
**دریافت عکس رندوم +18**

➤ [ `.couple` ]
———————————————
➤ [ `.ayang` ]
———————————————
➤ [ `.boob` ]
———————————————
➤ [ `.nude` ]
———————————————
➤ [ `.nude2` ]
———————————————
**جستجوی عکس**

➤ [ `.pic` ]
———————————————
➤ [ `.bing` ]
———————————————
➤ [ `.uns` ]
———————————————
➤ [ `.photo` ]
———————————————
➤ [ `.photos` ]
———————————————
"""

fahelp23 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ موزیک ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**جستجو و دریافت موزیک با دستورات زیر**

➤ [ `.music` ] **⤳** (TEXT)
———————————————
➤ [ `.youtube` ] **⤳** (TEXT)
———————————————
➤ [ `.musicc` ] **⤳** (TEXT)
———————————————
➤ [ `.remix` ] **⤳** (TEXT)
———————————————
➤ [ `.demo` ] **⤳** (TEXT)
———————————————
➤ [ `.classic` ] **⤳** (TEXT)
———————————————
➤ [ `.ahang` ] **⤳** (TEXT)
———————————————
➤ [ `.melo` ] **⤳** (TEXT)
———————————————
➤ [ `.global` ] **⤳** (TEXT)
———————————————
"""

fahelp24 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
                                                   **[ تنظیمات سیستم ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
روشن کردن سلف
[ ➤ `.on` ]
———————————————
خاموش کردن سلف
[ ➤ `.off` ]
———————————————
راه اندازی مجدد سلف
➤ [ `.restart` ]
———————————————
غیرفعال کردن اضطراری سلف
➤ [ `.shutdown` ]
———————————————
دریافت پینگ سلف
➤ [ `.ping` ]
———————————————
وضعیت سلف
➤ [ `self` ]
———————————————
دریافت آمار سلف
➤ [ `.on_off_status` ]
———————————————
اطلاعات پردازشگر
➤ [ `.cpu` ]
———————————————
اطلاعات مموری
➤ [ `.memory` ]
———————————————
اطلاعات سیستم
➤ [ `.system-inf` ]
———————————————
"""

enhelp1 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Global - Personal ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
User mute
➤ [ `.mute` ]
———————————————
User unmute
➤ [ `.unmute` ]
———————————————
Clear mute list
➤ [ `.allunmute` ]
———————————————
User block
➤ [ `.block` ]
———————————————
User unblock
➤ [ `.unblock` ]
———————————————
Add User to enemy list
➤ [ `.setenemy` ]
———————————————
Remove User from the enemy list
➤ [ `.delenemy` ]
———————————————
Clear enemy list
➤ [ `.clearenemy` ]
———————————————
Add User to love list
➤ [ `.setlove` ]
———————————————
Remove User from the love list
➤ [ `.dellove` ]
———————————————
Clear love list
➤ [ `.clearlove` ]
———————————————
Set Auto monshi text
➤ [ `.monshi` ] **⤳** (TEXT)
———————————————
Disable Auto monshi
➤ [ `.monshioff` ]
———————————————
Set Offline mode text
➤ [ `.afk` ] **⤳** (TEXT)
———————————————
Disable Offline mode
➤ [ `.unafk` ]
———————————————
Receive Tagalert
➤ [ `.tagalert` ] **⤳** (on OR off)
———————————————
Create Channel
➤ [ `.creatchannel` ] **⤳** (Name)
———————————————
Create Group
➤ [ `.creatgroup` ] **⤳** (Name)
———————————————
Create Supergroup
➤ [ `.creatsupergroup` ] **⤳** (Name)
———————————————
Normal Spam text
➤ [ `.spam` ] **⤳** (NUM TEXT)
———————————————
Slow Spam text
➤ [ `.slowspam` ] **⤳** (NUM TEXT)
———————————————
Spam Text and delete
➤ [ `.statspam` ] **⤳** (NUM TEXT)
———————————————
Fast Spam text
➤ [ `.fastspam` ] **⤳** (NUM TEXT)
———————————————
Enable first comment
➤ [ `.firstcom` ] **⤳** (on OR off)
———————————————
Set first comment text
➤ [ `.first_message` ] **⤳** (TEXT) (Reply)
———————————————
Set time for Auto send text
➤ [ `.text_time` ] **⤳** (HH:MM)
———————————————
Set time for Auto send photo
➤ [ `.photo_time` ] **⤳** (HH:MM)
———————————————
Set Text for Auto send text
➤ [ `.text_send_time` ] **⤳** (TEXT) (Reply)
———————————————
Set Photo for Auto send photo
➤ [ `.photo_send_time` ] **⤳** (Reply)
———————————————
Auto answer
➤ [ `.answer` ] **⤳** (on OR off)
———————————————
Set Question and Answer for Auto answer
➤ [ `.addan` ] **⤳** (Question:Answer)
———————————————
Delete an answer
➤ [ `.delan` ] **⤳** (Answer)
———————————————
Answer list
➤ [ `.anlist` ]
———————————————
Clear Auto answer list
➤ [ `.anclear` ]
———————————————
Welcome Mode
➤ [ `.welcome` ] **⤳** (on OR off)
———————————————
Set Welcome text
➤ [ `.welcome_add` ] **⤳** (TEXT)
———————————————
Show Welcome text
➤ [ `.welcome_show` ]
———————————————
Reset Welcome text
➤ [ `.welcome_reset` ]
———————————————
**Attention! To use the following commands, you must be the owner or administrator of the desired group with the necessary permissions**

Ban a User in the group
➤ [ `.ban` ] **⤳** (ID) (Reply)
———————————————
Unban a User in the group
➤ [ `.unban` ] **⤳** (ID) (Reply)
———————————————
Mute a User in the group
➤ [ `.setmute` ] **⤳** (ID) (Reply)
———————————————
Unmute a User in the group
➤ [ `.delmute` ] **⤳** (ID) (Reply)
———————————————
Set Chat photo
➤ [ `.setchatphoto` ] **⤳** (Reply)
———————————————
Set Chat title
➤ [ `.setchattitle` ] **⤳** (TEXT)
———————————————
Set Chat bio
➤ [ `.setchatbio` ] **⤳** (TEXT)
———————————————
Set Chat Username
➤ [ `.setchatusername` ] **⤳** (Username)
———————————————
Pin a Message in the group
➤ [ `.pin` ] **⤳** (Reply)
———————————————
Unpin a Message in the group
➤ [ `.unpin` ] **⤳** (Reply)
———————————————
Unpin All messages
➤ [ `.unpinall` ]
———————————————
Delete Channel
➤ [ `.deletechannel` ] **⤳** (Username)
———————————————
Delete Group
➤ [ `.deletegroup` ] **⤳** (Username)
———————————————
Delete All messages from a User in the group
➤ [ `.delallmsguser` ] **⤳** (Reply)
———————————————
Set time between sending each message for group members (Second)
➤ [ `.slowmod` ] **⤳** (NUM)
———————————————
Delete some messages
➤ [ `.delete` ] **⤳** (NUM)
———————————————
Tag Group admins
➤ [ `.tadmin` ]
———————————————
Tag All members group
➤ [ `.tagall` ] **⤳** (TEXT) (Reply)
———————————————
Cancel Group members tag
➤ [ `.cancel` ]
———————————————
Clear history
➤ [ `.delethistory` ]
———————————————
Delete a message
➤ [ `.del` ] **⤳** (Reply)
———————————————
"""

enhelp2 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Profile ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Set Account name
➤ [ `.setname` ] **⤳** (TEXT)
———————————————
Set Account lastname
➤ [ `.setlastname` ] **⤳** (TEXT)
———————————————
Set Account bio
➤ [ `.setbio` ] **⤳** (TEXT)
———————————————
Auto Font name
➤ [ `.fontname` ] **⤳** (on OR off)
———————————————
Set Time name
➤ [ `.timename` ] **⤳** (on OR off)
———————————————
Set Time name 2
➤ [ `.2timename` ] **⤳** (on OR off)
———————————————
Set Time bio
➤ [ `.timebio` ] **⤳** (on OR off)
———————————————
Set Time bio 2
➤ [ `.2timebio` ] **⤳** (on OR off)
———————————————
Set Time bio 3
➤ [ `.3timebio` ] **⤳** (on OR off)
———————————————
Set Time bio 4
➤ [ `.4timebio` ] **⤳** (on OR off)
———————————————
Set Time bio 5
➤ [ `.5timebio` ] **⤳** (on OR off)
———————————————
Set Time bio 6
➤ [ `.6timebio` ] **⤳** (on OR off)
———————————————
Set Account profile photo
➤ [ `.setprofile` ] **⤳** (Reply)
———————————————
Delete Account profile photo
➤ [ `.delprofile` ]
———————————————
Set Time on profile photo
➤ [ `.autopic` ]
———————————————
Set Time on profile photo 2
➤ [ `.2autopic` ]
———————————————
Set Time on profile photo 3
➤ [ `.3autopic` ]
———————————————
Set Time on profile photo 4
➤ [ `.4autopic` ]
———————————————
"""

enhelp3 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Downloader ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Get Instagram page information
➤ [ `.iginfo` ] **⤳** (Username)
———————————————
Download from Instagram
➤ [ `.igdl` ] **⤳** (URL)
———————————————
Download from Instagram, YouTube, Facebook & TikTok
➤ [ `.down` ] **⤳** (URL)
———————————————
Search and download from YouTube with text
➤ [ `.youtube` ] **⤳** (TEXT)
———————————————
Application Search
➤ [ `.app` ] **⤳** (TEXT)
———————————————
Application Search 2
➤ [ `.apk` ] **⤳** (TEXT)
———————————————
"""

enhelp4 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Uploader ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Upload Text
➤ [ `.neko` ] **⤳** (Reply)
———————————————
Upload Photo
➤ [ `.telegraph` ] **⤳** (Reply)
———————————————
"""

enhelp5 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Text Mode ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Bold Mode
➤ [ `.bold` ] **⤳** (on OR off)
———————————————
Spoiler Mode
➤ [ `.spoiler` ] **⤳** (on OR off)
———————————————
Italic Mode
➤ [ `.italic` ] **⤳** (on OR off)
———————————————
Code Mode
➤ [ `.code` ] **⤳** (on OR off)
———————————————
Underline Mode
➤ [ `.underline` ] **⤳** (on OR off)
———————————————
Strike Mode
➤ [ `.strike` ] **⤳** (on OR off)
———————————————
Emoji Mode
➤ [ `.emoji` ] **⤳** (on OR off)
———————————————
Quote Mode
➤ [ `.quote` ] **⤳** (on OR off)
———————————————
Mention Mode
➤ [ `.mention` ] **⤳** (on OR off)
———————————————
Set Reaction
➤ [ `.setreact` ] **⤳** (Emoji) (Reply)
———————————————
Delete Reaction
➤ [ `.delreact` ] **⤳** (Reply)
———————————————
Reaction List
➤ [ `.reactlist` ]
———————————————
Send ladder text
➤ [ `.lad` ] **⤳** (TEXT)
———————————————
"""

enhelp6 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Action Mode ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Typing Mode
➤ [ `.typing` ] **⤳** (on OR off)
———————————————
Playing Mode
➤ [ `.playing` ] **⤳** (on OR off)
———————————————
Recording Mode
➤ [ `.record_vid` ] **⤳** (on OR off)
———————————————
Sticker Selection Mode
➤ [ `.choose_sticker` ] **⤳** (on OR off)
———————————————
Video Uploading Mode
➤ [ `.upload_vid` ] **⤳** (on OR off)
———————————————
Document Uploading Mode
➤ [ `.upload_doc` ] **⤳** (on OR off)
———————————————
Audio Uploading Mode
➤ [ `.upload_audio` ] **⤳** (on OR off)
———————————————
Speaking Mode
➤ [ `.speaking` ] **⤳** (on OR off)
———————————————
Account Online Mode
➤ [ `.online` ] **⤳** (on OR off)
———————————————
Account Offline Mode
➤ [ `.offline` ] **⤳** (on OR off)
———————————————
"""

enhelp7 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Webhook ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Set Webhook
➤ [ `.setwebhook` ] **⤳** (Token URL)
———————————————
Delete Webhook
➤ [ `.delwebhook` ] **⤳** (Token)
———————————————
Clear Pending Updates
➤ [ `.delupdate` ] **⤳** (Token)
———————————————
Get Webhook information
➤ [ `.webhookinfo` ] **⤳** (Token)
———————————————
Get Bot information
➤ [ `.botinfo` ] **⤳** (Token)
———————————————
"""

enhelp8 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Locks ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
PV Lock Mode
➤ [ `.pvlock` ] **⤳** (on OR off)
———————————————
Mandatory join
➤ [ `.monshi2` ] **⤳** (on OR off)
———————————————
Lock Name list
➤ [ `.hlock` ]
———————————————
Group Lock status
➤ [ `.locks` ]
———————————————
Lock a option
➤ [ `.lock` ] **⤳** (Name)
———————————————
Unlock a option
➤ [ `.unlock` ] **⤳** (Name)
———————————————
Lock All options
➤ [ `.lock all` ]
———————————————
Unlock All options
➤ [ `.unlock all` ]
———————————————
"""

enhelp9 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Cron Job ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Set Cron Job (Minute)
➤ [ `.cron` ] **⤳** (URL Time)
Time: 1, 2, 5, 10, 15, 30 ...
———————————————
"""

enhelp10 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Anti Login ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Anti Login Account
➤ [ `.antilog` ] **⤳** (on OR off)
———————————————
"""

enhelp11 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Tabchi ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Tabchi Status
➤ [ `.tabchi status` ]
———————————————
Auto Send to PVs
➤ [ `.tabchipv` ] **⤳** (on OR off)
———————————————
Auto Send to Groups
➤ [ `.tabchigp` ] **⤳** (on OR off)
———————————————
Set Banner for Auto Send to PVs
➤ [ `.setbannerpv` ] **⤳** (TEXT) (Reply)
———————————————
Set Banner for Auto Send to Groups
➤ [ `.setbannergp` ] **⤳** (TEXT) (Reply)
———————————————
Set Timer for Auto Send to PVs (Second)
➤ [ `.settimerpv` ] **⤳** (NUM)
———————————————
Set Timer for Auto Send to Groups (Second)
➤ [ `.settimergp` ] **⤳** (NUM)
———————————————
Send to PVs
➤ [ `.sendpv` ] **⤳** (TEXT) (Reply)
———————————————
Send to Groups
➤ [ `.sendgp` ] **⤳** (TEXT) (Reply)
———————————————
Set Banner for Send to Group members
➤ [ `.setbannersender` ] **⤳** (TEXT) (Reply)
———————————————
Send to Group membes
➤ [ `.sendall` ] **⤳** (Username)
———————————————
Get the group invitation link
➤ [ `.invitelink` ]
———————————————
Join the Group
➤ [ `.join` ] **⤳** (Link)
———————————————
Leave the Group
➤ [ `.leave` ] **⤳** (Link)
———————————————
Leave All Groups
➤ [ `.leaveallgc` ]
———————————————
Leave All Channels
➤ [ `.leaveallch` ]
———————————————
"""

enhelp12 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Photo Editor ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**With the following commands, you can design the text you want on the photo**

➤ [ `.kanna` ] **⤳** (TEXT)
———————————————
➤ [ `.clyde` ] **⤳** (TEXT)
———————————————
➤ [ `.write` ] **⤳** (TEXT)
———————————————
➤ [ `.mind` ] **⤳** (TEXT)
———————————————
➤ [ `.trump` ] **⤳** (TEXT)
———————————————
➤ [ `.o` ] **⤳** (TEXT)
———————————————
➤ [ `.o2` ] **⤳** (TEXT)
———————————————
➤ [ `.bish` ] **⤳** (TEXT)
———————————————
➤ [ `.latex` ] **⤳** (TEXT)
———————————————
**With the following commands, you can set different filters on the photo you want**

➤ [ `.blue` ] **⤳** (Reply)
———————————————
➤ [ `.green` ] **⤳** (Reply)
———————————————
➤ [ `.red` ] **⤳** (Reply)
———————————————
➤ [ `.grey` ] **⤳** (Reply)
———————————————
➤ [ `.grey2` ] **⤳** (Reply)
———————————————
➤ [ `.sepia` ] **⤳** (Reply)
———————————————
➤ [ `.threshold` ] **⤳** (Reply)
———————————————
➤ [ `.blurple` ] **⤳** (Reply)
———————————————
➤ [ `.filter` ] **⤳** (Reply)
———————————————
**With the following commands, you can change the style and dimensions of the photo you want**

➤ [ `.bisexual` ] **⤳** (Reply)
———————————————
➤ [ `.blur` ] **⤳** (Reply)
———————————————
➤ [ `.horny` ] **⤳** (Reply)
———————————————
➤ [ `.stupid` ] **⤳** (Reply)
———————————————
➤ [ `.lesbian` ] **⤳** (Reply)
———————————————
➤ [ `.lgbt` ] **⤳** (Reply)
———————————————
➤ [ `.lolice` ] **⤳** (Reply)
———————————————
➤ [ `.non` ] **⤳** (Reply)
———————————————
➤ [ `.psexual` ] **⤳** (Reply)
———————————————
➤ [ `.pixel` ] **⤳** (Reply)
———————————————
➤ [ `.simp` ] **⤳** (Reply)
———————————————
➤ [ `.spin` ] **⤳** (Reply)
———————————————
➤ [ `.toni` ] **⤳** (Reply)
———————————————
**With the commands below, you can apply filters and fun changes to your desired photo**

➤ [ `.comrade` ] **⤳** (Reply)
———————————————
➤ [ `.gay` ] **⤳** (Reply)
———————————————
➤ [ `.glass` ] **⤳** (Reply)
———————————————
➤ [ `.jail` ] **⤳** (Reply)
———————————————
➤ [ `.wasted` ] **⤳** (Reply)
———————————————
➤ [ `.pass` ] **⤳** (Reply)
———————————————
"""

enhelp13 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ L - G Marker ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Create logo with text
➤ [ `.logo` ] **⤳** (TEXT)
———————————————
Create logo with text 2
➤ [ `.logo2` ] **⤳** (TEXT)
———————————————
Create logo with the desired text and design
➤ [ `.lg` ] **⤳** (TEXT Mode)
Mode: 1-138
———————————————
Create Gif with text
➤ [ `.gif` ] **⤳** (TEXT)
———————————————
Create Gif with text 2
➤ [ `.giff` ] **⤳** (TEXT)
———————————————
"""

enhelp14 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Compiler ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
➤ [ `.py` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.js` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.php` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.kotlin` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.go` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.java` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.lua` ] **⤳** (Code) (Reply)
———————————————
➤ [ `.exec` ] **⤳** (Code)
———————————————
"""

enhelp15 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Tools ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
File Extraction
➤ [ `.unzip` ] **⤳** (Reply)
———————————————
Rename the file
➤ [ `.rname` ] **⤳** (TEXT) (Reply)
———————————————
Virtual number Checker
➤ [ `.check` ] **⤳** (Number)
———————————————
Screenshot of the text
➤ [ `.q` ] **⤳** (Reply)
———————————————
Screenshot of the desired text
➤ [ `.qq` ] **⤳** (TEXT)
———————————————
Results of Cricket matches
➤ [ `.cricket` ] **⤳**
———————————————
Weather
➤ [ `.weather` ] **⤳** (City Name)
———————————————
Azan time
➤ [ `.azan` ] **⤳** (City Name)
———————————————
Temperature Converter
➤ [ `.t` ] **⤳** (NUM c OR f)
eg: .t 25 c
———————————————
Digital Currency Converter
➤ [ `.c` ] **⤳** (NUM Currency1 Currency2)
eg: .c 100 usdt eur
———————————————
Calculator
➤ [ `.e` ] **⤳** (Match)
eg: .e 2+2
———————————————
Get the IP of the site
➤ [ `.ip` ] **⤳** (Domain)
———————————————
Get IP information
➤ [ `.whoisip` ] **⤳** (IP)
———————————————
Link Shortener
➤ [ `.link` ] **⤳** (URL)
———————————————
Link Shortener 2
➤ [ `.link2` ] **⤳** (URL)
———————————————
Get site ping
➤ [ `.p` ] **⤳** (Domain)
———————————————
Screenshot of the site
➤ [ `.screenshot` ] **⤳** (Domain)
———————————————
Screenshot of the site 2
➤ [ `.screenshot2` ] **⤳** (Domain)
———————————————
Screenshot of the site 3
➤ [ `.screenshot3` ] **⤳** (Domain)
———————————————
Screenshot of the site 4
➤ [ `.screenshot4` ] **⤳** (Domain)
———————————————
Screenshot of the site 5
➤ [ `.shot` ] **⤳** (Domain)
———————————————
Get GitHub Account information
➤ [ `.github` ] **⤳** (Username)
———————————————
Get Project information
➤ [ `.git` ] **⤳** (TEXT)
———————————————
Search in the dictionary
➤ [ `.dict` ] **⤳** (Word)
———————————————
Copy the profile of an account
➤ [ `.clone` ] **⤳** (ID) (Reply)
———————————————
Account Creation date
➤ [ `.i` ] **⤳** (ID) (Reply)
———————————————
Self Account Creation date
➤ [ `.creation` ]
———————————————
Self Account limit status
➤ [ `.limit` ]
———————————————
Get Country information
➤ [ `.country` ] **⤳** (Name)
———————————————
Convert Sticker to Photo
➤ [ `.tp` ] **⤳** (Reply)
———————————————
Convert Photo to Sticker
➤ [ `.ts` ] **⤳** (Reply)
———————————————
Create Gif
➤ [ `.tg` ] **⤳** (Reply)
———————————————
Translate to Persian
➤ [ `.fa` ] **⤳** (TEXT)
———————————————
Translate to English
➤ [ `.en` ] **⤳** (TEXT)
———————————————
Get the movie
➤ [ `.movie` ] **⤳** (TEXT)
———————————————
Get Anime
➤ [ `.anim` ] **⤳** (TEXT)
———————————————
Create Password with the desired number of characters
➤ [ `.pass` ] **⤳** (NUM)
———————————————
Convert text to Morse code
➤ [ `.morset` ] **⤳** (TEXT)
———————————————
Convert Morse code to text
➤ [ `.unmorset` ] **⤳** (Code)
———————————————
Get the date
➤ [ `.date` ]
———————————————
Get Account information
➤ [ `.id` ] **⤳** (ID) (Reply)
———————————————
Get Message information
➤ [ `.get_message` ] **⤳** (Reply)
———————————————
Mention a User
➤ [ `.mention` ] **⤳** (ID) (Reply)
———————————————
National code Check
➤ [ `.meli` ] **⤳** (Number)
———————————————
Check bank card
➤ [ `.estelam` ] **⤳** (Number)
———————————————
Get daily News
➤ [ `.news` ] **⤳** (Category)
Category: business, entertainment, general, health, science, sports, technology
———————————————
Get Bin card
➤ [ `.ccgen` ]
———————————————
Get daily News
➤ [ `.yjc` ]
———————————————
Extract Text from Photo
➤ [ `.ocr` ] **⤳** (Reply)
———————————————
Download timed Photo
➤ [ `.dl` ] **⤳** (Reply)
———————————————
Saved Messages
➤ [ `.waitt` ] **⤳** (Reply)
———————————————
Get the time
➤ [ `.time` ]
———————————————
"""

enhelp16 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Account ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Add Admin to Self
➤ [ `.addadmin` ] **⤳** (ID) (Reply)
———————————————
Delete Admin from Self
➤ [ `.deladmin` ] **⤳** (ID) (Reply)
———————————————
Admin list
➤ [ `.adminlist` ]
———————————————
Clear Admin list
➤ [ `.clearadminlist` ]
———————————————
Get Self Account ID
➤ [ `id` ]
———————————————
Self Account limit status
➤ [ `.limit` ]
———————————————
Self Account Creation date
➤ [ `.creation` ]
———————————————
Get Self Account session information
➤ [ `.session` ]
———————————————
"""

enhelp17 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Book ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Get joke
➤ [ `.joke` ]
———————————————
Get poem
➤ [ `.poem` ]
———————————————
Get Know
➤ [ `.know` ]
———————————————
Get quote
➤ [ `.quote` ]
———————————————
Search on Wikipedia
➤ [ `.wiki` ] **⤳** (TEXT)
———————————————
Search on Google
➤ [ `.google` ] **⤳** (TEXT)
———————————————
Convert Numbers to Letters
➤ [ `.num` ] **⤳** (NUM)
———————————————
Get Name information
➤ [ `.name` ] **⤳** (Name)
———————————————
Get biography
➤ [ `.bio` ]
———————————————
Get diary
➤ [ `.memo` ]
———————————————
Get pnp
➤ [ `.pnp` ]
———————————————
Get alaki
➤ [ `.alaki` ]
———————————————
Get hadis
➤ [ `.hadis` ]
———————————————
Get story
➤ [ `.dastan` ]
———————————————
Get random name
➤ [ `.rname` ]
———————————————
Get horoscope
➤ [ `.fal` ]
———————————————
Get istikhara
➤ [ `.estekhare` ]
———————————————
Get zekr
➤ [ `.zekr` ]
———————————————
"""

enhelp18 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Fun ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Cheating at dice
➤ [ `.tas` ] **⤳** (1-6)
———————————————
Cheating at darts
➤ [ `.dart` ]
———————————————
Cheating at bowling
➤ [ `.bowling` ]
———————————————
Cheating at basketball
➤ [ `.basketball` ]
———————————————
Cheating at football
➤ [ `.football` ] **⤳** (1 OR 6)
1: Fail
4: Goal
———————————————
Get random games 1
➤ [ `.game` ]
———————————————
Get random games 2
➤ [ `.bazi` ]
———————————————
Get random games 3
➤ [ `.hehe` ]
———————————————
**Other hobbies**

➤ [ `.moon` ]
———————————————
➤ [ `.clock` ]
———————————————
➤ [ `.thunder` ]
———————————————
➤ [ `.earth` ]
———————————————
➤ [ `.heart` ]
———————————————
➤ [ `.love` ]
———————————————
➤ [ `.santet` ]
———————————————
➤ [ `.nah` ]
———————————————
➤ [ `.ajg` ]
———————————————
➤ [ `.babi` ]
———————————————
➤ [ `.tank` ]
———————————————
➤ [ `.y` ]
———————————————
➤ [ `.awk` ]
———————————————
➤ [ `.tembak` ]
———————————————
➤ [ `.heli` ]
———————————————
➤ [ `.gabut` ]
———————————————
➤ [ `.syg` ]
———————————————
➤ [ `.dino` ]
———————————————
➤ [ `.hack` ]
———————————————
➤ [ `.fuck` ]
———————————————
➤ [ `.koc` ]
———————————————
➤ [ `.charging` ]
———————————————
➤ [ `.gang` ]
———————————————
➤ [ `.hypo` ]
———————————————
➤ [ `.ding` ]
———————————————
➤ [ `.wtf` ]
———————————————
➤ [ `.call` ]
———————————————
➤ [ `.bomb` ]
———————————————
➤ [ `.brain` ]
———————————————
➤ [ `.ahh` ]
———————————————
➤ [ `.hmm` ]
———————————————
"""

enhelp19 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Market ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
The price of goods in the Iranian market (BaSalam)
➤ [ `.price` ] **⤳** (TEXT)
———————————————
The price of goods in the Iranian market (Torob)
➤ [ `.qeymat` ] **⤳** (TEXT)
———————————————
Digital Currencies symbols list
➤ [ `.cryptolist` ]
———————————————
Digital Currency price
➤ [ `.crypto` ] **⤳** (Name)
———————————————
Digital Currency converter
➤ [ `.c` ] **⤳** (NUM Currency1 Currency2)
eg: .c 100 usdt eur
———————————————
Tron price
➤ [ `.trx` ]
———————————————
Currency price list
➤ [ `.arz` ]
———————————————
Check bank card
➤ [ `.estelam` ] **⤳** (Number)
———————————————
Get Digital Currency transaction information
➤ [ `.tara` ] **⤳** (TransLink)
———————————————
"""

enhelp20 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Sticker - Gif ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Create Sticker with text
➤ [ `.sticker` ] **⤳** (TEXT)
———————————————
Get Sticker information
➤ [ `.stickerinfo` ] **⤳** (Reply)
———————————————
Create Sticker with error code
➤ [ `.error` ] **⤳** (Code)
eg: .error 404
———————————————
Minimize Stickers and Pictures
➤ [ `.tiny` ] **⤳** (Reply)
———————————————
Convert Photo to Sticker
➤ [ `.ts` ] **⤳** (Reply)
———————————————
Create Gif
➤ [ `.tg` ] **⤳** (Reply)
———————————————
**Get random Gifs**

➤ [ `.palm` ]
———————————————
➤ [ `.wink` ]
———————————————
➤ [ `.hug` ]
———————————————
➤ [ `.pat` ]
———————————————
"""

enhelp21 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ AI ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**Textual AI**

➤ [ `.gpt3` ] **⤳** (TEXT)
———————————————
➤ [ `.gpt4` ] **⤳** (TEXT)
———————————————
➤ [ `.bard` ] **⤳** (TEXT)
———————————————
➤ [ `.asq` ] **⤳** (TEXT)
———————————————
➤ [ `.messi` ] **⤳** (TEXT)
———————————————
➤ [ `.ronaldo` ] **⤳** (TEXT)
———————————————
➤ [ `.ilon` ] **⤳** (TEXT)
———————————————
**Audio AI**

➤ [ `.` ] **⤳** (TEXT) Women
———————————————
➤ [ `/` ] **⤳** (TEXT) Man
———————————————
➤ [ `.voice` ] **⤳** (TEXT)
———————————————
➤ [ `.crush` ] **⤳** (TEXT)
———————————————
➤ [ `.wo` ] **⤳** (TEXT) Women
———————————————
➤ [ `.ma` ] **⤳** (TEXT) Man
———————————————
➤ [ `.v` ] **⤳** (TEXT)
———————————————
Get ID list
➤ [ `.vl` ]
———————————————
Set desired accent with ID
➤ [ `.sv` ] **⤳** (Mode)
———————————————
**Visual AI**

➤ [ `.pgpt` ] **⤳** (TEXT)
———————————————
"""

enhelp22 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Photo ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Create color
➤ [ `.color` ] **⤳** (Color)
———————————————
**Get random photos of animals**

➤ [ `.pikachu` ]
———————————————
➤ [ `.whale` 
———————————————
➤ [ `.foxx` ]
———————————————
➤ [ `.doggg` ]
———————————————
➤ [ `.rpanda` ]
———————————————
➤ [ `.raccoon` ]
———————————————
➤ [ `.panda` ]
———————————————
➤ [ `.koala` ]
———————————————
➤ [ `.kangroo` ]
———————————————
➤ [ `.fox` ]
———————————————
➤ [ `.dogg` ]
———————————————
➤ [ `.birdd` ]
———————————————
➤ [ `.catt` ]
———————————————
➤ [ `.bird` ]
———————————————
➤ [ `.dog` ]
———————————————
➤ [ `.cat` ]
———————————————
➤ [ `.robo` ] **⤳** (1-999999)
———————————————
**Get random +18 photos**

➤ [ `.couple` ]
———————————————
➤ [ `.ayang` ]
———————————————
➤ [ `.boob` ]
———————————————
➤ [ `.nude` ]
———————————————
➤ [ `.nude2` ]
———————————————
**Photo Search**

➤ [ `.pic` ]
———————————————
➤ [ `.bing` ]
———————————————
➤ [ `.uns` ]
———————————————
➤ [ `.photo` ]
———————————————
➤ [ `.photos` ]
———————————————
"""

enhelp23 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ Music ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**Search and download music with the following commands**

➤ [ `.music` ] **⤳** (TEXT)
———————————————
➤ [ `.youtube` ] **⤳** (TEXT)
———————————————
➤ [ `.musicc` ] **⤳** (TEXT)
———————————————
➤ [ `.remix` ] **⤳** (TEXT)
———————————————
➤ [ `.demo` ] **⤳** (TEXT)
———————————————
➤ [ `.classic` ] **⤳** (TEXT)
———————————————
➤ [ `.ahang` ] **⤳** (TEXT)
———————————————
➤ [ `.melo` ] **⤳** (TEXT)
———————————————
➤ [ `.global` ] **⤳** (TEXT)
———————————————
"""

enhelp24 = """
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**[ System ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
Self On
[ ➤ `.on` ]
———————————————
Self Off
[ ➤ `.off` ]
———————————————
Restart Self
[ ➤ `.restart` ]
———————————————
Emergency shutdown Self
➤ [ `.shutdown` ]
———————————————
Get Self ping
➤ [ `.ping` ]
———————————————
Self Status
➤ [ `self` ]
———————————————
Get Self stats
➤ [ `.on_off_status` ]
———————————————
Processor information
➤ [ `.cpu` ]
———————————————
Memory information
➤ [ `.memory` ]
———————————————
System information
➤ [ `.system-inf` ]
———————————————
"""

openpanelbot = InlineKeyboardMarkup(
     [
         [
             InlineKeyboardButton("Panel", callback_data='openpanel')
         ]
     ]
)

# ================= TITAN PANEL UI =================
TITAN_PANEL_VERSION = "2.0"
TITAN_SELFSZ_VERSION = "2.0"

def build_titan_panel_keyboard(user_id, language="fa"):
     """Build the inline keyboard attached directly below the Titan identity card."""
     suffix = str(user_id)

     if language == "en":
          rows = [
               [InlineKeyboardButton('𝗚𝗹𝗼𝗯𝗮𝗹 - 𝗣𝗲𝗿𝘀𝗼𝗻𝗮𝗹', callback_data=f'global_person2-{suffix}')],
               [InlineKeyboardButton('𝗣𝗿𝗼𝗳𝗶𝗹𝗲', callback_data=f'profile2-{suffix}')],
               [
                    InlineKeyboardButton('𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿', callback_data=f'downloader2-{suffix}'),
                    InlineKeyboardButton('𝗨𝗽𝗹𝗼𝗮𝗱𝗲𝗿', callback_data=f'uploader2-{suffix}')
               ],
               [
                    InlineKeyboardButton('𝗧𝗲𝘅𝘁 𝗠𝗼𝗱𝗲', callback_data=f'text_mode2-{suffix}'),
                    InlineKeyboardButton('𝗔𝗰𝘁𝗶𝗼𝗻 𝗠𝗼𝗱𝗲', callback_data=f'action_mode2-{suffix}')
               ],
               [
                    InlineKeyboardButton('𝗪𝗲𝗯𝗵𝗼𝗼𝗸', callback_data=f'webhook2-{suffix}'),
                    InlineKeyboardButton('𝗟𝗼𝗰𝗸𝘀', callback_data=f'locks2-{suffix}'),
                    InlineKeyboardButton('𝗖𝗿𝗼𝗻 𝗝𝗼𝗯', callback_data=f'cronjob2-{suffix}')
               ],
               [
                    InlineKeyboardButton('𝗔𝗻𝘁𝗶 𝗟𝗼𝗴𝗶𝗻', callback_data=f'antilogin2-{suffix}'),
                    InlineKeyboardButton('𝗧𝗮𝗯𝗰𝗵𝗶', callback_data=f'tabchi2-{suffix}')
               ],
               [
                    InlineKeyboardButton('𝗣𝗵𝗼𝘁𝗼 𝗘𝗱𝗶𝘁𝗼𝗿', callback_data=f'photo_editor2-{suffix}'),
                    InlineKeyboardButton('𝗟 - 𝗚 𝗠𝗮𝗿𝗸𝗲𝗿', callback_data=f'marker2-{suffix}')
               ],
               [
                    InlineKeyboardButton('𝗖𝗼𝗺𝗽𝗶𝗹𝗲𝗿', callback_data=f'compiler2-{suffix}'),
                    InlineKeyboardButton('𝗧𝗼𝗼𝗹𝘀', callback_data=f'tools2-{suffix}'),
                    InlineKeyboardButton('𝗔𝗰𝗰𝗼𝘂𝗻𝘁', callback_data=f'account2-{suffix}')
               ],
               [
                    InlineKeyboardButton('𝗕𝗼𝗼𝗸', callback_data=f'book2-{suffix}'),
                    InlineKeyboardButton('𝗙𝘂𝗻', callback_data=f'fun2-{suffix}'),
                    InlineKeyboardButton('𝗠𝗮𝗿𝗸𝗲𝘁', callback_data=f'market2-{suffix}')
               ],
               [
                    InlineKeyboardButton('𝗦𝘁𝗶𝗰𝗸𝗲𝗿 - 𝗚𝗶𝗳', callback_data=f'photo_gif2-{suffix}'),
                    InlineKeyboardButton('𝗔𝗜', callback_data=f'ai2-{suffix}')
               ],
               [
                    InlineKeyboardButton('𝗣𝗵𝗼𝘁𝗼', callback_data=f'photo2-{suffix}'),
                    InlineKeyboardButton('𝗠𝘂𝘀𝗶𝗰', callback_data=f'music2-{suffix}')
               ],
               [InlineKeyboardButton('𝗦𝘆𝘀𝘁𝗲𝗺', callback_data=f'system2-{suffix}')],
               [InlineKeyboardButton('● 𝗖𝗹𝗼𝘀𝗲 𝗣𝗮𝗻𝗲𝗹 ●', callback_data=f'close2-{suffix}')],
          ]
     else:
          rows = [
               [InlineKeyboardButton('سراسری - شخصی', callback_data=f'global_person1-{suffix}')],
               [InlineKeyboardButton('پروفایل', callback_data=f'profile1-{suffix}')],
               [
                    InlineKeyboardButton('دانلودر', callback_data=f'downloader1-{suffix}'),
                    InlineKeyboardButton('آپلودر', callback_data=f'uploader1-{suffix}')
               ],
               [
                    InlineKeyboardButton('حالت متن', callback_data=f'text_mode1-{suffix}'),
                    InlineKeyboardButton('حالت اکشن', callback_data=f'action_mode1-{suffix}')
               ],
               [
                    InlineKeyboardButton('وبهوک', callback_data=f'webhook1-{suffix}'),
                    InlineKeyboardButton('قفل ها', callback_data=f'locks1-{suffix}'),
                    InlineKeyboardButton('کرون جاب', callback_data=f'cronjob1-{suffix}')
               ],
               [
                    InlineKeyboardButton('آنتی لاگین', callback_data=f'antilogin1-{suffix}'),
                    InlineKeyboardButton('تبچی', callback_data=f'tabchi1-{suffix}')
               ],
               [
                    InlineKeyboardButton('ویرایشگر عکس', callback_data=f'photo_editor1-{suffix}'),
                    InlineKeyboardButton('گیف و لوگو ساز', callback_data=f'marker1-{suffix}')
               ],
               [
                    InlineKeyboardButton('کامپایلر', callback_data=f'compiler1-{suffix}'),
                    InlineKeyboardButton('ابزار ها', callback_data=f'tools1-{suffix}'),
                    InlineKeyboardButton('اکانت', callback_data=f'account1-{suffix}')
               ],
               [
                    InlineKeyboardButton('کتاب', callback_data=f'book1-{suffix}'),
                    InlineKeyboardButton('سرگرمی', callback_data=f'fun1-{suffix}'),
                    InlineKeyboardButton('بازار', callback_data=f'market1-{suffix}')
               ],
               [
                    InlineKeyboardButton('استیکر - گیف', callback_data=f'photo_gif1-{suffix}'),
                    InlineKeyboardButton('هوش مصنوعی', callback_data=f'ai1-{suffix}')
               ],
               [
                    InlineKeyboardButton('عکس', callback_data=f'photo1-{suffix}'),
                    InlineKeyboardButton('موزیک', callback_data=f'music1-{suffix}')
               ],
               [InlineKeyboardButton('تنظیمات سیستم', callback_data=f'system1-{suffix}')],
               [InlineKeyboardButton('● بستن پنل ●', callback_data=f'close1-{suffix}')],
          ]

     return InlineKeyboardMarkup(rows)


# ================= TITAN PAGINATED HELP =================
# Telegram photo captions cannot hold very long help sections. Instead of
# summarizing/removing commands, every long section is split into clean pages.
# The TiTaN card stays as the same message; only caption/buttons change.

def _titan_help_sections():
     return {
          "gp": {"fa": ("سراسری - شخصی", fahelp1), "en": ("Global - Personal", enhelp1)},
          "profile": {"fa": ("پروفایل", fahelp2), "en": ("Profile", enhelp2)},
          "downloader": {"fa": ("دانلودر", fahelp3), "en": ("Downloader", enhelp3)},
          "uploader": {"fa": ("آپلودر", fahelp4), "en": ("Uploader", enhelp4)},
          "textmode": {"fa": ("حالت متن", fahelp5), "en": ("Text Mode", enhelp5)},
          "actionmode": {"fa": ("حالت اکشن", fahelp6), "en": ("Action Mode", enhelp6)},
          "webhook": {"fa": ("وبهوک", fahelp7), "en": ("Webhook", enhelp7)},
          "locks": {"fa": ("قفل ها", fahelp8), "en": ("Locks", enhelp8)},
          "cronjob": {"fa": ("کرون جاب", fahelp9), "en": ("Cron Job", enhelp9)},
          "antilogin": {"fa": ("آنتی لاگین", fahelp10), "en": ("Anti Login", enhelp10)},
          "tabchi": {"fa": ("تبچی", fahelp11), "en": ("Tabchi", enhelp11)},
          "photoeditor": {"fa": ("ویرایشگر عکس", fahelp12), "en": ("Photo Editor", enhelp12)},
          "marker": {"fa": ("گیف و لوگو ساز", fahelp13), "en": ("Logo/GIF Maker", enhelp13)},
          "compiler": {"fa": ("کامپایلر", fahelp14), "en": ("Compiler", enhelp14)},
          "tools": {"fa": ("ابزار ها", fahelp15), "en": ("Tools", enhelp15)},
          "account": {"fa": ("اکانت", fahelp16), "en": ("Account", enhelp16)},
          "book": {"fa": ("کتاب", fahelp17), "en": ("Book", enhelp17)},
          "fun": {"fa": ("سرگرمی", fahelp18), "en": ("Fun", enhelp18)},
          "market": {"fa": ("بازار", fahelp19), "en": ("Market", enhelp19)},
          "photogif": {"fa": ("استیکر - گیف", fahelp20), "en": ("Sticker - GIF", enhelp20)},
          "ai": {"fa": ("هوش مصنوعی", fahelp21), "en": ("AI", enhelp21)},
          "photo": {"fa": ("عکس", fahelp22), "en": ("Photo", enhelp22)},
          "music": {"fa": ("موزیک", fahelp23), "en": ("Music", enhelp23)},
          "system": {"fa": ("تنظیمات سیستم", fahelp24), "en": ("System", enhelp24)},
     }


_TITAN_HELP_ACTIONS = {
     "global_person1": ("fa", "gp"), "global_person2": ("en", "gp"),
     "profile1": ("fa", "profile"), "profile2": ("en", "profile"),
     "downloader1": ("fa", "downloader"), "downloader2": ("en", "downloader"),
     "uploader1": ("fa", "uploader"), "uploader2": ("en", "uploader"),
     "text_mode1": ("fa", "textmode"), "text_mode2": ("en", "textmode"),
     "action_mode1": ("fa", "actionmode"), "action_mode2": ("en", "actionmode"),
     "webhook1": ("fa", "webhook"), "webhook2": ("en", "webhook"),
     "locks1": ("fa", "locks"), "locks2": ("en", "locks"),
     "cronjob1": ("fa", "cronjob"), "cronjob2": ("en", "cronjob"),
     "antilogin1": ("fa", "antilogin"), "antilogin2": ("en", "antilogin"),
     "tabchi1": ("fa", "tabchi"), "tabchi2": ("en", "tabchi"),
     "photo_editor1": ("fa", "photoeditor"), "photo_editor2": ("en", "photoeditor"),
     "marker1": ("fa", "marker"), "marker2": ("en", "marker"),
     "compiler1": ("fa", "compiler"), "compiler2": ("en", "compiler"),
     "tools1": ("fa", "tools"), "tools2": ("en", "tools"),
     "account1": ("fa", "account"), "account2": ("en", "account"),
     "book1": ("fa", "book"), "book2": ("en", "book"),
     "fun1": ("fa", "fun"), "fun2": ("en", "fun"),
     "market1": ("fa", "market"), "market2": ("en", "market"),
     "photo_gif1": ("fa", "photogif"), "photo_gif2": ("en", "photogif"),
     "ai1": ("fa", "ai"), "ai2": ("en", "ai"),
     "photo1": ("fa", "photo"), "photo2": ("en", "photo"),
     "music1": ("fa", "music"), "music2": ("en", "music"),
     "system1": ("fa", "system"), "system2": ("en", "system"),
}


def _titan_split_long_line(line, max_len=560):
     line = str(line)
     if len(line) <= max_len:
          return [line]
     parts = []
     while len(line) > max_len:
          cut = line.rfind(" ", 0, max_len)
          if cut < max_len // 2:
               cut = max_len
          parts.append(line[:cut].rstrip())
          line = line[cut:].lstrip()
     if line:
          parts.append(line)
     return parts


def _titan_paginate_help_text(raw_text, title, lang="fa", body_limit=690):
     lines = []
     for line in str(raw_text or "").strip().splitlines():
          for part in _titan_split_long_line(line.rstrip(), 560):
               lines.append(part)
     chunks, current, current_len = [], [], 0
     for line in lines:
          add_len = len(line) + 1
          if current and current_len + add_len > body_limit:
               chunks.append("\n".join(current).rstrip())
               current, current_len = [], 0
          current.append(line)
          current_len += add_len
     if current:
          chunks.append("\n".join(current).rstrip())
     if not chunks:
          chunks = ["—"]

     total = len(chunks)
     pages = []
     for index, chunk in enumerate(chunks, start=1):
          if lang == "fa":
               header = f"╭━━━ ⚡ TiTaN Help Center ━━━╮\n┃ بخش: {title}\n┃ صفحه: {index} از {total}\n╰━━━━━━━━━━━━━━━━━━━━━━╯"
               footer = "━━━━━━━━━━━━━━\nبرای ادامه از دکمه‌های صفحه‌بندی استفاده کن."
          else:
               header = f"╭━━━ ⚡ TiTaN Help Center ━━━╮\n┃ Section: {title}\n┃ Page: {index}/{total}\n╰━━━━━━━━━━━━━━━━━━━━━━╯"
               footer = "━━━━━━━━━━━━━━\nUse pagination buttons to continue."
          page = f"{header}\n\n{chunk}\n\n{footer}"
          # Absolute safety: if decorative header made it too long, shrink body further.
          if len(page) > 950:
               overflow = len(page) - 950
               safe_chunk = chunk[:-overflow-5].rstrip() + "\n…"
               page = f"{header}\n\n{safe_chunk}\n\n{footer}"
          pages.append(page)
     return pages


def _titan_paginated_keyboard(lang, key, page, total, user_id):
     uid = str(user_id)
     rows = []
     if total > 1:
          prev_cb = f"hpg-{lang}-{key}-{page-1}-{uid}" if page > 0 else "outside"
          next_cb = f"hpg-{lang}-{key}-{page+1}-{uid}" if page < total - 1 else "outside"
          if lang == "fa":
               rows.append([
                    InlineKeyboardButton("⬅ قبلی", callback_data=prev_cb),
                    InlineKeyboardButton(f"{page+1}/{total}", callback_data="outside"),
                    InlineKeyboardButton("بعدی ➡", callback_data=next_cb),
               ])
          else:
               rows.append([
                    InlineKeyboardButton("⬅ Prev", callback_data=prev_cb),
                    InlineKeyboardButton(f"{page+1}/{total}", callback_data="outside"),
                    InlineKeyboardButton("Next ➡", callback_data=next_cb),
               ])
     back_cb = f"back1-{uid}" if lang == "fa" else f"back2-{uid}"
     close_cb = f"close1-{uid}" if lang == "fa" else f"close2-{uid}"
     if lang == "fa":
          rows.append([
               InlineKeyboardButton("🔙 بازگشت", callback_data=back_cb),
               InlineKeyboardButton("✖ بستن پنل", callback_data=close_cb),
          ])
     else:
          rows.append([
               InlineKeyboardButton("🔙 Back", callback_data=back_cb),
               InlineKeyboardButton("✖ Close", callback_data=close_cb),
          ])
     return InlineKeyboardMarkup(rows)


async def _titan_show_help_page(client, call, lang, key, page, user_id):
     sections = _titan_help_sections()
     title, raw_text = sections[key][lang]
     pages = _titan_paginate_help_text(raw_text, title, lang=lang)
     page = max(0, min(int(page), len(pages) - 1))
     await _titan_edit_inline_or_chat(
          client,
          call,
          text=pages[page],
          reply_markup=_titan_paginated_keyboard(lang, key, page, len(pages), user_id)
     )


async def send_titan_panel(client, chat_id, user=None, language="fa"):
     """Generate a fresh Titan card and attach the self/helper controls to it."""
     if user is None:
          user = await client.get_users(chat_id)

     titan_card_path = await render_titan_user_card_cached(client, user)

     await client.send_photo(
          chat_id,
          photo=titan_card_path,
          reply_markup=build_titan_panel_keyboard(user.id, language=language)
     )


def _titan_caption_safe(text):
     """Return text if it fits Telegram photo caption limit, otherwise None."""
     text = str(text or "")
     return text if len(text) <= 950 else None


async def _titan_edit_inline_or_chat(client, call, text, reply_markup=None):
     """Show panel sections WITHOUT summarizing their content.

     Telegram photo captions have a hard limit (~1024 chars). Therefore:
     - Short section text: edit the card photo caption, card stays visible.
     - Long section text: delete the photo message and send the FULL original
       text message with the existing buttons. No features are summarized.
     - Normal text messages: edit with full text.
     - Inline messages: try full text first for long sections; if Telegram does
       not allow converting media to text, fall back to full caption only when it fits.
     """
     full_text = str(text or "")
     caption_text = _titan_caption_safe(full_text)

     if call.inline_message_id:
          if caption_text is not None:
               try:
                    return await client.edit_inline_caption(
                         inline_message_id=call.inline_message_id,
                         caption=caption_text,
                         reply_markup=reply_markup
                    )
               except Exception:
                    pass
          # For long inline sections, attempt to convert to full text.
          # This is the only way to avoid losing commands due to caption limit.
          try:
               return await client.edit_inline_text(
                    inline_message_id=call.inline_message_id,
                    text=full_text,
                    reply_markup=reply_markup
               )
          except Exception:
               # Last safe fallback: do not summarize silently; show clear reason.
               fallback = "**این بخش طولانی‌تر از محدودیت کپشن تلگرام است. پنل را داخل پیوی Helper باز کن تا متن کامل نمایش داده شود.**"
               try:
                    return await client.edit_inline_caption(
                         inline_message_id=call.inline_message_id,
                         caption=fallback,
                         reply_markup=reply_markup
                    )
               except Exception:
                    return await client.edit_inline_text(
                         inline_message_id=call.inline_message_id,
                         text=fallback,
                         reply_markup=reply_markup
                    )

     if call.message:
          if getattr(call.message, "photo", None):
               if caption_text is not None:
                    return await client.edit_message_caption(
                         call.message.chat.id,
                         call.message.id,
                         caption=caption_text,
                         reply_markup=reply_markup
                    )
               # Long section: remove the card photo and show complete text like the original panel.
               try:
                    await call.message.delete()
               except Exception:
                    pass
               return await client.send_message(
                    call.message.chat.id,
                    full_text,
                    reply_markup=reply_markup
               )

          return await client.edit_message_text(
               call.message.chat.id,
               call.message.id,
               text=full_text,
               reply_markup=reply_markup
          )


async def _titan_close_panel(client, call, fallback_text="**● پنل راهنما بسته شد ●**"):
     """Close panel. Normal photo messages are deleted with their card.

     Telegram does not provide chat_id/message_id for inline callback messages,
     so true deletion is only possible for normal messages. For inline messages
     we remove buttons and replace the caption/text with a closed notice.
     """
     if getattr(call, "message", None):
          try:
               await call.message.delete()
               return
          except Exception as exc:
               print(f"{Fore.YELLOW}TITAN close delete failed: {exc}{Fore.RESET}")
     if getattr(call, "inline_message_id", None):
          try:
               return await client.edit_inline_caption(
                    inline_message_id=call.inline_message_id,
                    caption=fallback_text,
                    reply_markup=None
               )
          except Exception:
               return await client.edit_inline_text(
                    inline_message_id=call.inline_message_id,
                    text=fallback_text,
                    reply_markup=None
               )


_TITAN_INLINE_URL_CACHE = {}
_TITAN_INLINE_FILE_ID_CACHE = {}

async def _titan_cached_photo_file_id(client, user):
     """Create/reuse Telegram cached photo file_id for inline results.

     Inline panel in Saved Messages/groups/channels is sent by self.py through
     inline mode. Inline photo results are most reliable when we answer with a
     Telegram cached photo file_id instead of depending on public image hosts.
     We upload the generated card once to the user's private helper chat, grab
     its file_id, delete that temporary message, then reuse the file_id.
     """
     card_path = await render_titan_user_card_cached(client, user)
     try:
          stat_key = f"{card_path}:{int(os.path.getmtime(card_path))}:{os.path.getsize(card_path)}"
     except Exception:
          stat_key = card_path
     if stat_key in _TITAN_INLINE_FILE_ID_CACHE:
          return _TITAN_INLINE_FILE_ID_CACHE[stat_key]

     sent = await client.send_photo(user.id, photo=card_path)
     file_id = None
     try:
          if getattr(sent, "photo", None):
               file_id = getattr(sent.photo, "file_id", None)
     except Exception:
          file_id = None
     try:
          await sent.delete()
     except Exception:
          try:
               await client.delete_messages(user.id, sent.id)
          except Exception:
               pass
     if not file_id:
          raise RuntimeError("Could not obtain Telegram cached photo file_id")
     _TITAN_INLINE_FILE_ID_CACHE[stat_key] = file_id
     print(f"{Fore.GREEN}TITAN inline cached photo_file_id created{Fore.RESET}")
     return file_id


def _upload_public_image_sync(card_path):
     """Upload a generated card to a public image URL for inline mode.

     InlineQueryResultPhoto requires an HTTPS URL. We try multiple public hosts
     so inline panel does not fall back to a text-only error when one host fails.
     """
     errors_list = []

     # 1) Telegraph
     try:
          from telegraph import upload_file
          uploaded = upload_file(card_path)
          if uploaded:
               return "https://telegra.ph" + uploaded[0]
          errors_list.append("Telegraph returned empty result")
     except Exception as exc:
          errors_list.append(f"Telegraph: {exc}")

     # 2) 0x0.st — returns a direct URL as plain text
     try:
          with open(card_path, "rb") as f:
               res = requests.post("https://0x0.st", files={"file": f}, timeout=45)
          if res.ok and res.text.strip().startswith("https://"):
               return res.text.strip()
          errors_list.append(f"0x0.st: HTTP {res.status_code} {res.text[:120]}")
     except Exception as exc:
          errors_list.append(f"0x0.st: {exc}")

     # 3) tmpfiles.org — JSON URL, convert to direct /dl/ link
     try:
          with open(card_path, "rb") as f:
               res = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=45)
          if res.ok:
               data = res.json()
               url = data.get("data", {}).get("url")
               if url:
                    return url.replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/")
          errors_list.append(f"tmpfiles: HTTP {res.status_code} {res.text[:120]}")
     except Exception as exc:
          errors_list.append(f"tmpfiles: {exc}")

     raise RuntimeError(" | ".join(errors_list))


async def _titan_inline_photo_url(client, user):
     """Upload cached TiTaN card PNG for inline-mode usage in any chat."""
     card_path = await render_titan_user_card_cached(client, user)
     try:
          stat_key = f"{card_path}:{int(os.path.getmtime(card_path))}:{os.path.getsize(card_path)}"
     except Exception:
          stat_key = card_path
     if stat_key in _TITAN_INLINE_URL_CACHE:
          return _TITAN_INLINE_URL_CACHE[stat_key]

     url = await asyncio.to_thread(_upload_public_image_sync, card_path)
     _TITAN_INLINE_URL_CACHE[stat_key] = url
     print(f"{Fore.GREEN}TITAN inline card uploaded: {url}{Fore.RESET}")
     return url


keyboard_idk = ReplyKeyboardMarkup(
     [
         [
             ("Add Admin"),
             ("Delete Admin"),
             ("Admin List")
         ],
         [
             ("Add Owner"),
             ("Delete Owner"),
             ("Owner List")
         ]
     ],
one_time_keyboard=True,resize_keyboard=True)

@app.on_inline_query()
async def answer(client, inline_query):
     chat_id = inline_query.from_user.id
     AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = {chat_id} LIMIT 1")
     if AdminUser is not None:
          if inline_query.query.strip().lower() in ["panel", "help", "helper"] or inline_query.query.strip() in ["پنل", "راهنما"]:
               try:
                    user = await client.get_users(inline_query.from_user.id)
                    try:
                         cached_file_id = await _titan_cached_photo_file_id(client, user)
                         await inline_query.answer(
                              results=[
                                   InlineQueryResultCachedPhoto(
                                        title="TiTaN SelfSaz Panel",
                                        description="Dynamic TiTaN identity card panel",
                                        photo_file_id=cached_file_id,
                                        caption="TiTaN SelfSaz Panel",
                                        reply_markup=build_titan_panel_keyboard(user.id, language="fa")
                                   )
                              ],
                              cache_time=1,
                              is_personal=True
                         )
                    except Exception as cached_exc:
                         print(f"{Fore.YELLOW}TITAN cached inline photo failed, trying public URL: {cached_exc}{Fore.RESET}")
                         photo_url = await _titan_inline_photo_url(client, user)
                         await inline_query.answer(
                              results=[
                                   InlineQueryResultPhoto(
                                        title="TiTaN SelfSaz Panel",
                                        description="Dynamic TiTaN identity card panel",
                                        photo_url=photo_url,
                                        thumb_url=photo_url,
                                        caption="TiTaN SelfSaz Panel",
                                        reply_markup=build_titan_panel_keyboard(user.id, language="fa")
                                   )
                              ],
                              cache_time=1,
                              is_personal=True
                         )
               except Exception as exc:
                    print(f"{Fore.YELLOW}TITAN inline panel generation failed: {exc}{Fore.RESET}")
                    # Last-resort fallback: do NOT show a useless error-only result.
                    # Selecting this result leaves a button in the target chat; pressing it
                    # sends the real local photo card with send_photo in that same chat.
                    await inline_query.answer(
                         results=[
                              InlineQueryResultArticle(
                                   title="TiTaN Panel Backup",
                                   input_message_content=InputTextMessageContent("**TiTaN panel is ready. Tap the button below to open the card here.**"),
                                   description="Open TiTaN card in this chat",
                                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚜️ Open TiTaN Card", callback_data='openpanel')]])
                              ),
                         ],
                         cache_time=1,
                         is_personal=True
                    )

          if inline_query.query == "coinprice":
               s = requests.get('https://api.nobitex.ir/market/stats?srcCurrency=usdt,trx,ton,btc,shib,eth,etc,usdt,ada,bch,ltc,bnb&dstCurrency=irt,rls,usdt')
               s = s.text
               js = json.loads(s)
               byusdt = js['stats']['usdt-irt']['bestBuy']
               sellusdt = js['stats']['usdt-irt']['bestSell']
               bytrx = js['stats']['trx-irt']['bestBuy']
               selltrx = js['stats']['trx-irt']['bestSell']
               byton = js['stats']['ton-irt']['bestBuy']
               sellton = js['stats']['ton-irt']['bestSell']
               byshib = js['stats']['shib-usdt']['bestBuy']
               sellshib = js['stats']['shib-usdt']['bestSell']
               bybit = js['stats']['btc-usdt']['bestBuy']
               sellbit = js['stats']['btc-usdt']['bestSell']
               byet = js['stats']['eth-usdt']['bestBuy']
               sellet = js['stats']['eth-usdt']['bestSell']
               byetc = js['stats']['etc-usdt']['bestBuy']
               selletc = js['stats']['etc-usdt']['bestSell']
               byada = js['stats']['ada-usdt']['bestBuy']
               sellada = js['stats']['ada-usdt']['bestSell']
               bybch = js['stats']['bch-usdt']['bestBuy']
               sellbch = js['stats']['bch-usdt']['bestSell']
               byltc = js['stats']['ltc-usdt']['bestBuy']
               sellltc = js['stats']['ltc-usdt']['bestSell']
               bybnb = js['stats']['bnb-usdt']['bestBuy']
               sellbnb = js['stats']['bnb-usdt']['bestSell']

               coind = InlineKeyboardMarkup(
                    [
                         [
                              InlineKeyboardButton("Currency", callback_data="outside"),
                              InlineKeyboardButton("Best Buy", callback_data="outside"),
                              InlineKeyboardButton("Best Sell", callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("USDT", callback_data="outside"),
                              InlineKeyboardButton("☫%s" % byusdt, callback_data="outside"),
                              InlineKeyboardButton("☫%s" % sellusdt, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("TRX", callback_data="outside"),
                              InlineKeyboardButton("☫%s" % bytrx, callback_data="outside"),
                              InlineKeyboardButton("☫%s" % selltrx, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("TON", callback_data="outside"),
                              InlineKeyboardButton("☫%s" % byton, callback_data="outside"),
                              InlineKeyboardButton("☫%s" % sellton, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("SHIB", callback_data="outside"),
                              InlineKeyboardButton("$%s" % byshib, callback_data="outside"),
                              InlineKeyboardButton("$%s" % sellshib, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("BTC", callback_data="outside"),
                              InlineKeyboardButton("$%s" % bybit, callback_data="outside"),
                              InlineKeyboardButton("$%s" % sellbit, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("ETH", callback_data="outside"),
                              InlineKeyboardButton("$%s" % byet, callback_data="outside"),
                              InlineKeyboardButton("$%s" % sellet, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("ETC", callback_data="outside"),
                              InlineKeyboardButton("$%s" % byetc, callback_data="outside"),
                              InlineKeyboardButton("$%s" % selletc, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("ADA", callback_data="outside"),
                              InlineKeyboardButton("$%s" % byada, callback_data="outside"),
                              InlineKeyboardButton("$%s" % sellada, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("BCH", callback_data="outside"),
                              InlineKeyboardButton("$%s" % bybch, callback_data="outside"),
                              InlineKeyboardButton("$%s" % sellbch, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("LTC", callback_data="outside"),
                              InlineKeyboardButton("$%s" % byltc, callback_data="outside"),
                              InlineKeyboardButton("$%s" % sellltc, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("BNB", callback_data="outside"),
                              InlineKeyboardButton("$%s" % bybnb, callback_data="outside"),
                              InlineKeyboardButton("$%s" % sellbnb, callback_data="outside")
                         ],
                         [
                              InlineKeyboardButton("Close ×", callback_data=f'Close-{inline_query.from_user.id}')
                         ]
                    ]
               )

               await inline_query.answer(
                    results=[
                         InlineQueryResultArticle(
                              title="Coin price",
                              input_message_content=InputTextMessageContent("➣ **Currency price list**"),
                              url="https://t.me/KING_MEMBEER",
                              description="ᴄʀɪᴛᴜs",
                              thumb_url="https://t.me/KING_MEMBEER/33",
                              reply_markup=coind
                         ),
                    ],
                    cache_time=1
               )

@app.on_callback_query()
async def call(app, call):
     AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1")

     mark1 = InlineKeyboardMarkup(
          [
               [
                    InlineKeyboardButton('سراسری - شخصی',callback_data=f'global_person1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('پروفایل',callback_data=f'profile1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('دانلودر',callback_data=f'downloader1-{call.from_user.id}'), 
                    InlineKeyboardButton('آپلودر',callback_data=f'uploader1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('حالت متن',callback_data=f'text_mode1-{call.from_user.id}'),
                    InlineKeyboardButton('حالت اکشن',callback_data=f'action_mode1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('وبهوک',callback_data=f'webhook1-{call.from_user.id}'),
                    InlineKeyboardButton('قفل ها',callback_data=f'locks1-{call.from_user.id}'),
                    InlineKeyboardButton('کرون جاب',callback_data=f'cronjob1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('آنتی لاگین',callback_data=f'antilogin1-{call.from_user.id}'),
                    InlineKeyboardButton('تبچی',callback_data=f'tabchi1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('ویرایشگر عکس',callback_data=f'photo_editor1-{call.from_user.id}'),
                    InlineKeyboardButton('گیف و لوگو ساز',callback_data=f'marker1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('کامپایلر',callback_data=f'compiler1-{call.from_user.id}'),
                    InlineKeyboardButton('ابزار ها',callback_data=f'tools1-{call.from_user.id}'),
                    InlineKeyboardButton('اکانت',callback_data=f'account1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('کتاب',callback_data=f'book1-{call.from_user.id}'),
                    InlineKeyboardButton('سرگرمی',callback_data=f'fun1-{call.from_user.id}'),
                    InlineKeyboardButton('بازار',callback_data=f'market1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('استیکر - گیف',callback_data=f'photo_gif1-{call.from_user.id}'),
                    InlineKeyboardButton('هوش مصنوعی',callback_data=f'ai1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('عکس',callback_data=f'photo1-{call.from_user.id}'),
                    InlineKeyboardButton('موزیک',callback_data=f'music1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('تنظیمات سیستم',callback_data=f'system1-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('● بستن پنل ●',callback_data=f'close1-{call.from_user.id}')
               ]
          ]
     )

     mark2 = InlineKeyboardMarkup(
          [
               [
                    InlineKeyboardButton('𝗚𝗹𝗼𝗯𝗮𝗹 - 𝗣𝗲𝗿𝘀𝗼𝗻𝗮𝗹',callback_data=f'global_person2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗣𝗿𝗼𝗳𝗶𝗹𝗲',callback_data=f'profile2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗗𝗼𝘄𝗻𝗹𝗼𝗮𝗱𝗲𝗿',callback_data=f'downloader2-{call.from_user.id}'), 
                    InlineKeyboardButton('𝗨𝗽𝗹𝗼𝗮𝗱𝗲𝗿',callback_data=f'uploader2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗧𝗲𝘅𝘁 𝗠𝗼𝗱𝗲',callback_data=f'text_mode2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗔𝗰𝘁𝗶𝗼𝗻 𝗠𝗼𝗱𝗲',callback_data=f'action_mode2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗪𝗲𝗯𝗵𝗼𝗼𝗸',callback_data=f'webhook2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗟𝗼𝗰𝗸𝘀',callback_data=f'locks2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗖𝗿𝗼𝗻 𝗝𝗼𝗯',callback_data=f'cronjob2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗔𝗻𝘁𝗶 𝗟𝗼𝗴𝗶𝗻',callback_data=f'antilogin2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗧𝗮𝗯𝗰𝗵𝗶',callback_data=f'tabchi2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗣𝗵𝗼𝘁𝗼 𝗘𝗱𝗶𝘁𝗼𝗿',callback_data=f'photo_editor2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗟 - 𝗚 𝗠𝗮𝗿𝗸𝗲𝗿',callback_data=f'marker2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗖𝗼𝗺𝗽𝗶𝗹𝗲𝗿',callback_data=f'compiler2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗧𝗼𝗼𝗹𝘀',callback_data=f'tools2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗔𝗰𝗰𝗼𝘂𝗻𝘁',callback_data=f'account2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗕𝗼𝗼𝗸',callback_data=f'book2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗙𝘂𝗻',callback_data=f'fun2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗠𝗮𝗿𝗸𝗲𝘁',callback_data=f'market2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗦𝘁𝗶𝗰𝗸𝗲𝗿 - 𝗚𝗶𝗳',callback_data=f'photo_gif2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗔𝗜',callback_data=f'ai2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗣𝗵𝗼𝘁𝗼',callback_data=f'photo2-{call.from_user.id}'),
                    InlineKeyboardButton('𝗠𝘂𝘀𝗶𝗰',callback_data=f'music2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('𝗦𝘆𝘀𝘁𝗲𝗺',callback_data=f'system2-{call.from_user.id}')
               ],
               [
                    InlineKeyboardButton('● 𝗖𝗹𝗼𝘀𝗲 𝗣𝗮𝗻𝗲𝗹 ●',callback_data=f'close2-{call.from_user.id}')
               ]
          ]
     )

     dast1 = InlineKeyboardMarkup(
          [
               [
                    InlineKeyboardButton("● بازگشت ●", callback_data=f'back1-{call.from_user.id}')
               ]
          ]
     )

     dast2 = InlineKeyboardMarkup(
          [
               [
                    InlineKeyboardButton("● 𝗕𝗮𝗰𝗸 ●", callback_data=f'back2-{call.from_user.id}')
               ]
          ]
     )

     if call.data == "openpanel":
          if AdminUser is None:
               await call.answer("دسترسی غیر مجاز 🚫", show_alert=False)
               return
          try:
               user = await app.get_users(call.from_user.id)
               if call.message:
                    try:
                         await call.message.delete()
                    except Exception:
                         pass
               target_chat_id = call.message.chat.id if call.message else call.from_user.id
               await send_titan_panel(app, target_chat_id, user=user, language="fa")
               await call.answer()
          except Exception as exc:
               print(f"{Fore.YELLOW}TITAN callback panel generation failed: {exc}{Fore.RESET}")
               await call.answer("خطا در ساخت پنل", show_alert=True)
          return

     if call.data != "outside":
          try:
               _target_user_id = int(call.data.split("-")[-1])
          except Exception:
               _target_user_id = call.from_user.id
          if AdminUser is not None and int(call.from_user.id) == int(_target_user_id):
               _action = call.data.split("-")[0]

               # Paginated TiTaN help sections: prevents Telegram caption limit
               # while keeping all commands visible across pages.
               if _action in _TITAN_HELP_ACTIONS:
                    _lang, _key = _TITAN_HELP_ACTIONS[_action]
                    await _titan_show_help_page(app, call, _lang, _key, 0, call.from_user.id)
                    return

               if _action == "hpg":
                    _parts = call.data.split("-")
                    if len(_parts) >= 5:
                         await _titan_show_help_page(app, call, _parts[1], _parts[2], int(_parts[3]), call.from_user.id)
                         return
     
               if call.data.split("-")[0] == "persian":
                    await _titan_edit_inline_or_chat(app, call, text=f"**سلام {call.from_user.first_name} به راهنمای اولترا سلف خوش آمدید. لطفا بخش مورد نظر خود را انتخاب کنید:**", reply_markup=mark1)

               elif call.data.split("-")[0] == "english":
                    await _titan_edit_inline_or_chat(app, call, text=f"**Hello {call.from_user.first_name} Welcome to Ultra Self help.\nPlease select the section you want:**", reply_markup=mark2)

               elif call.data.split("-")[0] == "back1":
                    await _titan_edit_inline_or_chat(app, call, text=f"**سلام {call.from_user.first_name} به راهنمای اولترا سلف خوش آمدید. لطفا بخش مورد نظر خود را انتخاب کنید:**", reply_markup=mark1)

               elif call.data.split("-")[0] == "back2":
                    await _titan_edit_inline_or_chat(app, call, text=f"**Hello {call.from_user.first_name} Welcome to Ultra Self help.\nPlease select the section you want:**", reply_markup=mark2)

               elif call.data.split("-")[0] == "global_person1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp1, reply_markup=dast1)

               elif call.data.split("-")[0] == "profile1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp2, reply_markup=dast1)

               elif call.data.split("-")[0] == "downloader1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp3, reply_markup=dast1)

               elif call.data.split("-")[0] == "uploader1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp4, reply_markup=dast1)

               elif call.data.split("-")[0] == "text_mode1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp5, reply_markup=dast1)

               elif call.data.split("-")[0] == "action_mode1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp6, reply_markup=dast1)

               elif call.data.split("-")[0] == "webhook1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp7, reply_markup=dast1)

               elif call.data.split("-")[0] == "locks1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp8, reply_markup=dast1)

               elif call.data.split("-")[0] == "cronjob1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp9, reply_markup=dast1)

               elif call.data.split("-")[0] == "antilogin1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp10, reply_markup=dast1)

               elif call.data.split("-")[0] == "tabchi1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp11, reply_markup=dast1)

               elif call.data.split("-")[0] == "photo_editor1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp12, reply_markup=dast1)

               elif call.data.split("-")[0] == "marker1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp13, reply_markup=dast1)

               elif call.data.split("-")[0] == "compiler1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp14, reply_markup=dast1)

               elif call.data.split("-")[0] == "tools1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp15, reply_markup=dast1)

               elif call.data.split("-")[0] == "account1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp16, reply_markup=dast1)

               elif call.data.split("-")[0] == "book1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp17, reply_markup=dast1)

               elif call.data.split("-")[0] == "fun1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp18, reply_markup=dast1)

               elif call.data.split("-")[0] == "market1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp19, reply_markup=dast1)

               elif call.data.split("-")[0] == "photo_gif1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp20, reply_markup=dast1)

               elif call.data.split("-")[0] == "ai1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp21, reply_markup=dast1)

               elif call.data.split("-")[0] == "photo1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp22, reply_markup=dast1)

               elif call.data.split("-")[0] == "music1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp23, reply_markup=dast1)

               elif call.data.split("-")[0] == "system1":
                    await _titan_edit_inline_or_chat(app, call, text=fahelp24, reply_markup=dast1)

               elif call.data.split("-")[0] == "global_person2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp1, reply_markup=dast2)

               elif call.data.split("-")[0] == "profile2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp2, reply_markup=dast2)

               elif call.data.split("-")[0] == "downloader2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp3, reply_markup=dast2)

               elif call.data.split("-")[0] == "uploader2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp4, reply_markup=dast2)

               elif call.data.split("-")[0] == "text_mode2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp5, reply_markup=dast2)

               elif call.data.split("-")[0] == "action_mode2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp6, reply_markup=dast2)

               elif call.data.split("-")[0] == "webhook2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp7, reply_markup=dast2)

               elif call.data.split("-")[0] == "locks2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp8, reply_markup=dast2)

               elif call.data.split("-")[0] == "cronjob2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp9, reply_markup=dast2)

               elif call.data.split("-")[0] == "antilogin2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp10, reply_markup=dast2)

               elif call.data.split("-")[0] == "tabchi2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp11, reply_markup=dast2)

               elif call.data.split("-")[0] == "photo_editor2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp12, reply_markup=dast2)

               elif call.data.split("-")[0] == "marker2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp13, reply_markup=dast2)

               elif call.data.split("-")[0] == "compiler2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp14, reply_markup=dast2)

               elif call.data.split("-")[0] == "tools2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp15, reply_markup=dast2)

               elif call.data.split("-")[0] == "account2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp16, reply_markup=dast2)

               elif call.data.split("-")[0] == "book2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp17, reply_markup=dast2)

               elif call.data.split("-")[0] == "fun2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp18, reply_markup=dast2)

               elif call.data.split("-")[0] == "market2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp19, reply_markup=dast2)

               elif call.data.split("-")[0] == "photo_gif2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp20, reply_markup=dast2)

               elif call.data.split("-")[0] == "ai2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp21, reply_markup=dast2)

               elif call.data.split("-")[0] == "photo2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp22, reply_markup=dast2)

               elif call.data.split("-")[0] == "music2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp23, reply_markup=dast2)

               elif call.data.split("-")[0] == "system2":
                    await _titan_edit_inline_or_chat(app, call, text=enhelp24, reply_markup=dast2)

               elif call.data.split("-")[0] == "close1":
                    await _titan_close_panel(app, call, "**● پنل راهنما بسته شد ●**")

               elif call.data.split("-")[0] == "close2":
                    await _titan_close_panel(app, call, "**● Helper Panel Closed ●**")

               elif call.data.split("-")[0] == "Close":
                    await _titan_close_panel(app, call, "**● Closed ●**")
          else:
               await call.answer("دسترسی غیر مجاز 🚫", show_alert=False)
     else:
          await call.answer("این دکمه نمایشی است", show_alert=True)

@app.on_message(filters.private&filters.command("restart"), group=1)
async def updates(app, m:Message):
     OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{m.chat.id}' LIMIT 1")
     if OwnerUser is not None:
          await app.send_message(m.chat.id, "**Helper Restart was successful**")
          python = sys.executable
          os.execl(python, python, *sys.argv)
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
    
@app.on_message(filters.private&filters.command("ownerpanel"))
async def owner_panel(app, m:Message):
     OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{m.chat.id}' LIMIT 1")
     if OwnerUser is not None:
          await app.send_message(m.chat.id, "**QuiteCreateCliBot Panel Owner**", reply_markup=keyboard_idk)
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

@app.on_message(filters.command("panel"))
async def updates(app, m:Message):
     AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{m.from_user.id}' LIMIT 1")
     if AdminUser is not None:
          try:
               user = await app.get_users(m.from_user.id)
               await send_titan_panel(app, m.chat.id, user=user, language="fa")
          except Exception as exc:
               print(f"{Fore.YELLOW}TITAN panel generation failed: {exc}{Fore.RESET}")
               await app.send_message(m.chat.id, "خطا در ساخت کارت پنل TiTaN")
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.from_user.id}' LIMIT 1")
          raise StopPropagation
    
@app.on_message(filters.text & filters.regex(r"(?i)^(panel|help|helper|پنل|راهنما)$"), group=-5)
async def titan_panel_text_trigger(app, m:Message):
     AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{m.from_user.id}' LIMIT 1")
     if AdminUser is not None:
          try:
               user = await app.get_users(m.from_user.id)
               await send_titan_panel(app, m.chat.id, user=user, language="fa")
          except Exception as exc:
               print(f"{Fore.YELLOW}TITAN text panel generation failed: {exc}{Fore.RESET}")
               await app.send_message(m.chat.id, "خطا در ساخت کارت پنل TiTaN")
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.from_user.id}' LIMIT 1")
          raise StopPropagation

@app.on_message(filters.private&filters.command("start"))
async def updates(app, m:Message):
     AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{m.chat.id}' LIMIT 1")
     if AdminUser is not None:
          await app.send_message(m.chat.id, f"𝑯𝒆𝒍𝒍𝒐 {m.from_user.first_name}\n𝑾𝒆𝒍𝒄𝒐𝒎𝒆 𝑻𝒐 𝑯𝒆𝒍𝒑𝒆𝒓 𝑩𝒐𝒕 💛\n𝑭𝒐𝒓 𝒈𝒆𝒕 𝑷𝒂𝒏𝒆𝒍 𝒕𝒚𝒑𝒆 ( `help` 𝑶𝒓 `panel` 𝑶𝒓 `پنل` )\n     ", reply_markup=openpanelbot)
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
     else:
          await m.delete()
   #______________________________Owner Panel________________________

Back = ReplyKeyboardMarkup(
     [
          [
               ("Back")
          ]
     ],resize_keyboard=True
)

@app.on_message(filters.private)
async def updates(app, m:Message):
 OwnerUser = get_data(f"SELECT * FROM ownerlist WHERE id = '{m.chat.id}' LIMIT 1")
 if OwnerUser is not None:
     user = get_data(f"SELECT * FROM user WHERE id = '{m.chat.id}' LIMIT 1")
     OwnerList = get_datas("SELECT * FROM ownerlist")
     AdminList = get_datas("SELECT * FROM adminlist")
     text = m.text

     if text == "Back":
          await app.send_message(m.chat.id, "**QuiteCreateCliBot Panel Owner**", reply_markup=keyboard_idk)
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

     elif text == "Add Admin":
          await app.send_message(m.chat.id, "**Send Me User ID**:", reply_markup=Back)
          update_data(f"UPDATE user SET step = 'addadmin' WHERE id = '{m.chat.id}' LIMIT 1")

     elif user["step"] == "addadmin":
          if text.isdigit():
               user_id = int(text.strip())
               if get_data(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is None:
                    await app.send_message(m.chat.id, f"Successfull\nUser [ `{user_id}` ] Added to Admin List")
                    update_data(f"INSERT INTO adminlist(id) VALUES({user_id})")
               else:
                    await app.send_message(m.chat.id, "This user in the Admin list")
          else:
               await app.send_message(m.chat.id, "Invalid entry! Only sending numbers is allowed")

     elif text == "Delete Admin":
          await app.send_message(m.chat.id, "**Send Me User ID**:", reply_markup=Back)
          update_data(f"UPDATE user SET step = 'deladmin' WHERE id = '{m.chat.id}' LIMIT 1")

     elif user["step"] == "deladmin":
          if text.isdigit():
               user_id = int(text.strip())
               if get_data(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(m.chat.id, f"Successfull\nUser [ `{user_id}` ] Deleted From User List")
                    update_data(f"DELETE FROM adminlist WHERE id = '{user_id}' LIMIT 1")
               else:
                    await app.send_message(m.chat.id, f"This user not in Admin list")
          else:
               await app.send_message(m.chat.id, "Invalid entry! Only sending numbers is allowed")
             
     elif text == "Admin List":
          s = ""
          if AdminList:
               for index, user in enumerate(AdminList, start=1):
                    s += f"֍ {index} -> `{user[0]}`\n"
               await app.send_message(m.chat.id, f"**Admin List:**\n{s}")
          else:
               await app.send_message(m.chat.id, f"**Admin List is Empty**")
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

     elif text == "Add Owner":
          await app.send_message(m.chat.id, "**Send Me User ID**:", reply_markup=Back)
          update_data(f"UPDATE user SET step = 'addowner' WHERE id = '{m.chat.id}' LIMIT 1")

     elif user["step"] == "addowner":
          if text.isdigit():
               user_id = int(text.strip())
               if get_data(f"SELECT * FROM ownerlist WHERE id = '{user_id}' LIMIT 1") is None:
                    if get_data(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None:
                         await app.send_message(m.chat.id, f"Successfull\nUser [ `{user_id}` ] Added to Owner List")
                         update_data(f"INSERT INTO ownerlist(id) VALUES({user_id})")
                    else:
                         await app.send_message(m.chat.id, "ابتدا کاربر مورد نظر را به لیست ادمین اضافه کنید!")
               else:
                    await app.send_message(m.chat.id, "This user in the Owner list")
          else:
               await app.send_message(m.chat.id, "Invalid entry! Only sending numbers is allowed")

     elif text == "Delete Owner":
          await app.send_message(m.chat.id, "**Send Me User ID**:", reply_markup=Back)
          update_data(f"UPDATE user SET step = 'delowner' WHERE id = '{m.chat.id}' LIMIT 1")

     elif user["step"] == "delowner":
          if text.isdigit():
               user_id = int(text.strip())
               if get_data(f"SELECT * FROM ownerlist WHERE id = '{user_id}' LIMIT 1") is not None:
                    await app.send_message(m.chat.id, f"Successfull\nUser [ `{user_id}` ] Deleted From User List")
                    update_data(f"DELETE FROM ownerlist WHERE id = '{user_id}' LIMIT 1")
               else:
                    await app.send_message(m.chat.id, f"This user not in Owner list")
          else:
               await app.send_message(m.chat.id, "Invalid entry! Only sending numbers is allowed")
             
     elif text == "Owner List":
          s = ""
          if OwnerList:
               for index, user in enumerate(OwnerList, start=1):
                    s += f"֍ {index} -> `{user[0]}`\n"
               await app.send_message(m.chat.id, f"**Owner List:**\n{s}")
          else:
               await app.send_message(m.chat.id, f"**Owner List is Empty**")
          update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")

#================== Run ===================#
def _flood_wait_seconds(exc):
     value = getattr(exc, "value", None) or getattr(exc, "x", None)
     if value is None:
          import re
          match = re.search(r"wait of (\d+) seconds", str(exc))
          value = int(match.group(1)) if match else 60
     return max(1, int(value))

async def start_client_safely(client, label):
     while True:
          try:
               await client.start()
               return
          except errors.FloodWait as e:
               wait_time = _flood_wait_seconds(e) + 5
               print(f"{Fore.RED}[{label}] Telegram FLOOD_WAIT: sleeping {wait_time} seconds instead of crashing Railway...{Fore.RESET}")
               await asyncio.sleep(wait_time)
          except Exception:
               print(f"{Fore.RED}[{label}] Startup failed with non-FloodWait error:{Fore.RESET}")
               import traceback
               print(traceback.format_exc())
               raise

async def main():
     await start_client_safely(app, "helper")
     print(Fore.YELLOW + "Started...")
     try:
          await idle()
     finally:
          try:
               await app.stop()
          except Exception:
               pass

if __name__ == "__main__":
     app.run(main())
