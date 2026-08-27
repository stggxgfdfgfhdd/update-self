import re
#============ In The Name Of God ============#
# Source Name: Ultra Self
# Developer: @IVGalaxy
# © 2024 Ultra Self LLC. All rights reserved.
#================== Import ==================#
from pyrogram import Client, filters, idle, errors, StopPropagation, enums
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
FIX_VERSION = "2026-08-25-titan-ssot-v8-4"
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
                                                   **[ هوش مصنوعی Pro ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**هوش مصنوعی متنی - فقط یک دستور**
موتور: MajidAPI GPT 3.5 Turbo
➤ [ `.ai` ] **⤳** (TEXT)
مثال:
➤ `.ai یک متن تبلیغاتی حرفه‌ای بنویس`
———————————————
**حافظه و یادگیری AI**
آموزش دادن به هوش مصنوعی
➤ [ `.ai learn` ] **⤳** (TEXT)
مثال:
➤ `.ai learn اسم کانال من TiTaN است`
———————————————
دیدن حافظه
➤ [ `.ai memory` ]
———————————————
حذف یک حافظه
➤ [ `.ai forget 2` ]
———————————————
حذف کل حافظه
➤ [ `.ai forget all` ]
———————————————
پاک کردن تاریخچه چت، بدون حذف حافظه
➤ [ `.ai reset` ]
———————————————
**هوش مصنوعی صوتی**
تبدیل متن به صوت با صدای پیش‌فرض
➤ [ `.tts` ] **⤳** (TEXT)
———————————————
صدای زن فارسی
➤ [ `.ttsf` ] **⤳** (TEXT)
———————————————
صدای مرد فارسی
➤ [ `.ttsm` ] **⤳** (TEXT)
———————————————
تغییر صدای ویس با MajidAPI
➤ [ `.vc` ] **⤳** (Speaker) (Reply Voice)
مثال:
➤ `.vc ataran`
➤ `.vc list`
———————————————
لیست صداهای TTS
➤ [ `.vl` ]
———————————————
تنظیم صدای پیش‌فرض
➤ [ `.sv` ] **⤳** (Voice ID)
مثال: `.sv fa-female`
———————————————
**هوش مصنوعی تصویری**
ساخت عکس با MajidAPI
➤ [ `.pgpt` ] **⤳** (TEXT)
مثال:
➤ `.pgpt گربه سایبرپانک در تهران بارانی`
———————————————
**Variable لازم**
`MAJIDAPI_TOKEN`
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
**[ AI Pro ]**
▬▬▬▬▬▬▬▬▬▬▬▬▬▬
**Text AI - single command**
Engine: MajidAPI GPT 3.5 Turbo
➤ [ `.ai` ] **⤳** (TEXT)
Example:
➤ `.ai Write a premium channel bio`
———————————————
**AI Memory / Learning**
Teach the AI
➤ [ `.ai learn` ] **⤳** (TEXT)
Example:
➤ `.ai learn My channel name is TiTaN`
———————————————
Show memory
➤ [ `.ai memory` ]
———————————————
Forget one memory
➤ [ `.ai forget 2` ]
———————————————
Clear all memory
➤ [ `.ai forget all` ]
———————————————
Reset chat history, keep memory
➤ [ `.ai reset` ]
———————————————
**AI Voice**
Text-to-speech default voice
➤ [ `.tts` ] **⤳** (TEXT)
———————————————
Persian female voice
➤ [ `.ttsf` ] **⤳** (TEXT)
———————————————
Persian male voice
➤ [ `.ttsm` ] **⤳** (TEXT)
———————————————
Voice changer with MajidAPI
➤ [ `.vc` ] **⤳** (Speaker) (Reply Voice)
Example:
➤ `.vc ataran`
➤ `.vc list`
———————————————
Voice IDs
➤ [ `.vl` ]
———————————————
Set default voice
➤ [ `.sv` ] **⤳** (Voice ID)
Example: `.sv fa-female`
———————————————
**AI Image**
Generate image with MajidAPI
➤ [ `.pgpt` ] **⤳** (TEXT)
Example:
➤ `.pgpt cyberpunk cat in rainy Tehran`
———————————————
**Required Variable**
`MAJIDAPI_TOKEN`
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
               [InlineKeyboardButton('𝗠𝗼𝗻𝘀𝗵𝗶𝟮 𝗣𝗿𝗼', callback_data=f'monshi2_panel2-{suffix}')],
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
               [InlineKeyboardButton('مدیریت Monshi2 Pro', callback_data=f'monshi2_panel1-{suffix}')],
               [InlineKeyboardButton('تنظیمات سیستم', callback_data=f'system1-{suffix}')],
               [InlineKeyboardButton('● بستن پنل ●', callback_data=f'close1-{suffix}')],
          ]

     return InlineKeyboardMarkup(rows)


# ================= TITAN UNIFIED HELP & PAGINATION ENGINE (SSOT) =================
_PAGE_SIZE = 7

_TITAN_CATEGORIES = [
    ("gp", "سراسری - شخصی", "Global - Personal"),
    ("profile", "پروفایل", "Profile"),
    ("downloader", "دانلودر", "Downloader"),
    ("uploader", "آپلودر", "Uploader"),
    ("textmode", "حالت متن", "Text Mode"),
    ("actionmode", "حالت اکشن", "Action Mode"),
    ("webhook", "وبهوک", "Webhook"),
    ("locks", "قفل ها", "Locks"),
    ("cronjob", "کرون جاب", "Cron Job"),
    ("antilogin", "آنتی لاگین", "Anti Login"),
    ("tabchi", "تبچی", "Tabchi"),
    ("photoeditor", "ویرایشگر عکس", "Photo Editor"),
    ("marker", "گیف و لوگو ساز", "Logo/GIF Maker"),
    ("compiler", "کامپایلر", "Compiler"),
    ("tools", "ابزار ها", "Tools"),
    ("account", "اکانت", "Account"),
    ("book", "کتاب", "Book"),
    ("fun", "سرگرمی", "Fun"),
    ("market", "بازار", "Market"),
    ("photogif", "استیکر - گیف", "Sticker - GIF"),
    ("ai", "هوش مصنوعی", "AI"),
    ("photo", "عکس", "Photo"),
    ("music", "موزیک", "Music"),
    ("system", "تنظیمات سیستم", "System"),
]

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

_TITAN_FA_CMD_MAP = {
    "ping": "پینگ", "session": "سلف", "timename": "ست تایم", "timebio": "تایم بیو",
    "ai": "هوش", "monshi2": "منشی۲", "monshi": "منشی", "monshioff": "خاموشی منشی",
    "weather": "آب و هوا", "azan": "اذان", "qeymat": "قیمت", "price": "قیمت باسلام",
    "crypto": "قیمت ارز", "trx": "ترون", "tara": "تارا", "tts": "صدا", "ttsf": "صدای زن",
    "ttsm": "صدای مرد", "pgpt": "ساخت عکس", "vc": "تغییر صدا", "pvlock": "قفل پیوی",
    "block": "بلاک", "unblock": "آنبلاک", "locks": "قفل ها", "spam": "اسپم",
    "fastspam": "اسپم سریع", "cancel": "لغو", "tagall": "تگ همه", "del": "حذف",
    "down": "دانلود اینستا", "down2": "دانلود مدیا", "unsplash": "عکس رندوم",
    "qq": "کووت", "bkp": "بکاپ", "afk": "اف کی", "unafk": "آن اف کی",
    "invitelink": "لینک دعوت", "leaveallch": "خروج از کانال ها", "leaveallgc": "خروج از گروه ها",
    "tiny": "کوچک کننده متن", "packinfo": "اطلاعات استیکر", "telegraph": "تلگراف",
    "shutdown": "خاموش", "online": "آنلاین", "offline": "آفلاین", "antilog": "آنتی لاگین",
    "love": "قلب", "setenemy": "دشمن ست", "delenemy": "حذف دشمن", "clearenemy": "پاکسازی دشمن",
    "enemylist": "لیست دشمن", "setlove": "عشق ست", "dellove": "حذف عشق", "clearlove": "پاکسازی عشق",
    "lovelist": "لیست عشق", "check": "استعلام شماره", "shot": "اسکرین شات",
    "link": "کوتاه لینک", "github": "گیت هاب", "git": "گیت", "dict": "دیکشنری",
    "mute": "سکوت کاربر", "unmute": "حذف سکوت کاربر", "allunmute": "پاکسازی لیست سکوت",
    "bold": "حالت بولد", "spoiler": "حالت اسپویلر", "italic": "حالت کج نویس",
    "font": "فونت", "underline": "خط زیرین", "strike": "خط روی متن",
}

def _titan_parse_help_items(raw_text, lang="fa"):
    lines = [l.strip() for l in str(raw_text or "").splitlines() if l.strip()]
    items = []
    current_desc = []
    for l in lines:
        if set(l) <= set("▬—-─ ") or l.startswith("**["):
            continue
        if "➤" in l or "[ `" in l or "[`." in l or "[." in l:
            desc = " ".join(current_desc).strip()
            cmd_line = l
            if lang == "fa":
                def repl(m):
                    c = m.group(1).lstrip(".")
                    fa_c = _TITAN_FA_CMD_MAP.get(c.lower(), c)
                    return f"`{fa_c}` یا `.{c}`"
                cmd_line = re.sub(r"`\.([A-Za-z0-9_]+)`", repl, cmd_line)
            items.append((desc, cmd_line))
            current_desc = []
        else:
            clean = l.replace("**", "").replace("`", "").strip()
            if clean and len(clean) < 140:
                current_desc.append(clean)
    if not items and lines:
        for l in lines:
            if not (set(l) <= set("▬—-─ ") or l.startswith("**[")):
                items.append(("", l))
    return items

def _titan_get_registry():
    global _COMMAND_REGISTRY_CACHE
    if "_COMMAND_REGISTRY_CACHE" in globals() and _COMMAND_REGISTRY_CACHE:
        return _COMMAND_REGISTRY_CACHE
    registry = {}
    for idx, (cat_key, fa_title, en_title) in enumerate(_TITAN_CATEGORIES, start=1):
        fa_raw = globals().get(f"fahelp{idx}", "")
        en_raw = globals().get(f"enhelp{idx}", "")
        registry[cat_key] = {
            "fa_title": fa_title,
            "en_title": en_title,
            "fa_items": _titan_parse_help_items(fa_raw, "fa"),
            "en_items": _titan_parse_help_items(en_raw, "en"),
        }
    _COMMAND_REGISTRY_CACHE = registry
    return registry

_COMMAND_REGISTRY_CACHE = None

def _titan_render_help_page(lang, cat_key, page):
    reg = _titan_get_registry()
    cat_data = reg.get(cat_key, {"fa_title": cat_key, "en_title": cat_key, "fa_items": [], "en_items": []})
    items = cat_data["fa_items"] if lang == "fa" else cat_data["en_items"]
    title = cat_data["fa_title"] if lang == "fa" else cat_data["en_title"]
    total_pages = max(1, (len(items) + _PAGE_SIZE - 1) // _PAGE_SIZE)
    page = max(0, min(int(page), total_pages - 1))
    start = page * _PAGE_SIZE
    chunk = items[start:start + _PAGE_SIZE]

    lines = []
    if lang == "fa":
        lines.append("╭━━━ ⚡ TiTaN Help Center ━━━╮")
        lines.append(f"┃ بخش: {title}")
        lines.append(f"┃ صفحه: {page+1} از {total_pages} (تعداد دستورات: {len(items)})")
        lines.append("╰━━━━━━━━━━━━━━━━━━━━━━╯\n")
        for i, (desc, cmd) in enumerate(chunk, start=start+1):
            if desc:
                lines.append(f"<b>{i}.</b> {desc}\n{cmd}")
            else:
                lines.append(f"<b>{i}.</b> {cmd}")
            lines.append("━━━━━━━━━━━━━━")
    else:
        lines.append("╭━━━ ⚡ TiTaN Help Center ━━━╮")
        lines.append(f"┃ Section: {title}")
        lines.append(f"┃ Page: {page+1}/{total_pages} (Total: {len(items)})")
        lines.append("╰━━━━━━━━━━━━━━━━━━━━━━╯\n")
        for i, (desc, cmd) in enumerate(chunk, start=start+1):
            if desc:
                lines.append(f"<b>{i}.</b> {desc}\n{cmd}")
            else:
                lines.append(f"<b>{i}.</b> {cmd}")
            lines.append("━━━━━━━━━━━━━━")
    return "\n".join(lines).rstrip("━\n "), total_pages, page


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


def _titan_language_keyboard(user_id):
    uid = str(user_id)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇮🇷 فارسی", callback_data=f"persian-{uid}"),
            InlineKeyboardButton("🇬🇧 English", callback_data=f"english-{uid}"),
        ],
        [
            InlineKeyboardButton("✖ بستن / Close", callback_data=f"close1-{uid}"),
        ]
    ])


async def _titan_plain_edit_kwargs():
    try:
        return {"parse_mode": enums.ParseMode.HTML}
    except Exception:
        return {"parse_mode": None}


async def _titan_show_paginated_text(client, call, text, reply_markup=None):
    full_text = str(text or "")
    if len(full_text) > 950:
        full_text = full_text[:920].rstrip() + "\n…"
    plain_kwargs = await _titan_plain_edit_kwargs()

    if getattr(call, "inline_message_id", None):
        try:
            return await client.edit_inline_caption(
                inline_message_id=call.inline_message_id,
                caption=full_text,
                reply_markup=reply_markup,
                **plain_kwargs,
            )
        except Exception:
            try:
                return await client.edit_inline_text(
                    inline_message_id=call.inline_message_id,
                    text=full_text,
                    reply_markup=reply_markup,
                    **plain_kwargs,
                )
            except Exception as e:
                print(f"TITAN inline edit error: {e}")
                return

    if getattr(call, "message", None):
        if getattr(call.message, "photo", None):
            try:
                return await client.edit_message_caption(
                    call.message.chat.id,
                    call.message.id,
                    caption=full_text,
                    reply_markup=reply_markup,
                    **plain_kwargs,
                )
            except Exception:
                try:
                    await call.message.delete()
                except Exception:
                    pass
                return await client.send_message(
                    call.message.chat.id,
                    full_text,
                    reply_markup=reply_markup,
                    **plain_kwargs,
                )
        try:
            return await client.edit_message_text(
                call.message.chat.id,
                call.message.id,
                text=full_text,
                reply_markup=reply_markup,
                **plain_kwargs,
            )
        except Exception:
            return await client.send_message(
                call.message.chat.id,
                full_text,
                reply_markup=reply_markup,
                **plain_kwargs,
            )


async def _titan_show_help_page(client, call, lang, key, page, user_id):
    text, total_pages, page = _titan_render_help_page(lang, key, page)
    await _titan_show_paginated_text(
        client,
        call,
        text=text,
        reply_markup=_titan_paginated_keyboard(lang, key, page, total_pages, user_id)
    )


async def send_titan_panel(client, chat_id, user=None, language="fa"):
    """Generate a fresh Titan card and show language choice before panel."""
    if user is None:
        user = await client.get_users(chat_id)

    titan_card_path = await render_titan_user_card_cached(client, user)

    await client.send_photo(
        chat_id,
        photo=titan_card_path,
        caption="زبان پنل را انتخاب کن / Choose panel language:",
        reply_markup=_titan_language_keyboard(user.id)
    )


def _titan_caption_safe(text):
    text = str(text or "")
    return text if len(text) <= 950 else None


async def _titan_edit_inline_or_chat(client, call, text, reply_markup=None):
    return await _titan_show_paginated_text(client, call, text, reply_markup=reply_markup)


def _monshi2_helper_panel_text(lang="fa", section="main"):
    if lang == "en":
        texts = {
            "main": """**Monshi2 Pro Management**\n\nThis helper panel shows ready-to-copy commands. Actual Monshi2 settings are stored inside the running self account.\n\n• Main Switch: `.monshi2 on` / `.monshi2 off`\n• Mode Switch: `.monshi2 mode photo` / `text` / `user`\n• Test Verification: `.monshi2 test`\n• Settings Status: `.monshi2`""",
            "config": """**Monshi2 Pro Config Guide**\n\n• Cooldown: `.monshi2 cooldown 60`\n• Auto Delete Card: `.monshi2 delete on/off`\n• Block Non-Members: `.monshi2 block on/off`\n• Allowed Channels: `.monshi2 allow @ch1 @ch2`""",
            "links": """**Monshi2 Pro Links Guide**\n\n• Set Primary Channel: `.monshi2 link @channel`\n• Set Channel + Link: `.monshi2 link @channel https://t.me/invite`\n• View Links: `.monshi2 links`""",
            "text": """**Monshi2 Pro Text / Template**\n\n• Set Custom Text: `.monshi2 settext Your text`\n• Preview Text: `.monshi2 text`\n• Reset Default: `.monshi2 resettext`""",
            "users": """**Monshi2 Pro User Management**\n\n• Whitelist User: `.monshi2 user 12345678`\n• Remove User: `.monshi2 deluser 12345678`\n• User List: `.monshi2 users`""",
            "stats": """**Monshi2 Pro Stats**\n\nUse `.monshi2 stats` inside self chat to view detailed operational counters.\n\nStats include blocked PV messages, panels sent, cooldown skipped, verify success/failed, and deleted panels.""",
        }
    else:
        texts = {
            "main": """**پنل مدیریت Monshi2 Pro**\n\nاین بخش دستورات آماده کپی را نمایش می‌دهد. تنظیمات اصلی داخل اکانت سلف فعال و ذخیره می‌شوند.\n\n• سوئیچ اصلی: `.monshi2 on` یا `.monshi2 off`\n• حالت نمایش: `.monshi2 mode photo` / `text` / `user`\n• تست پنل عضویت: `.monshi2 test`\n• وضعیت کامل: `.monshi2`""",
            "config": """**تنظیمات پیشرفته Monshi2 Pro**\n\n• زمان کول‌داون: `.monshi2 cooldown 60`\n• حذف خودکار کارت: `.monshi2 delete on/off`\n• بلاک کاربران غیرعضو: `.monshi2 block on/off`\n• کانال‌های مجاز: `.monshi2 allow @ch1 @ch2`""",
            "links": """**مدیریت لینک‌های کانال Monshi2**\n\n• تنظیم کانال اصلی: `.monshi2 link @channel`\n• تنظیم کانال + لینک خصوصی: `.monshi2 link @channel https://t.me/invite`\n• مشاهده لیست: `.monshi2 links`""",
            "text": """**شخصی‌سازی متن هشدار Monshi2**\n\n• تنظیم متن دلخواه: `.monshi2 settext متن مورد نظر`\n• مشاهده پیش‌نمایش متن: `.monshi2 text`\n• بازنشانی پیش‌فرض: `.monshi2 resettext`""",
            "users": """**مدیریت کاربران و استثناها**\n\n• وایت‌لیست کاربر: `.monshi2 user 12345678`\n• حذف کاربر: `.monshi2 deluser 12345678`\n• مشاهده لیست: `.monshi2 users`""",
            "stats": """**آمار عملکرد Monshi2 Pro**\n\nبرای مشاهده شمارنده‌های عملیاتی از دستور `.monshi2 stats` داخل سلف استفاده کن.\n\nآمارها شامل پیام‌های بلاک‌شده، پنل‌های ارسالی، رد شده با کول‌داون، تأیید موفق/ناموفق و پنل‌های حذف‌شده است.""",
        }
    return texts.get(section, texts["main"])


def _monshi2_helper_panel_keyboard(user_id, lang="fa", section="main"):
    suffix = str(user_id)
    if lang == "en":
        rows = [
            [InlineKeyboardButton("⚙️ Config Guide", callback_data=f"monshi2_config2-{suffix}"), InlineKeyboardButton("🔗 Links Guide", callback_data=f"monshi2_links2-{suffix}")],
            [InlineKeyboardButton("📝 Text Guide", callback_data=f"monshi2_text2-{suffix}"), InlineKeyboardButton("👥 Users Guide", callback_data=f"monshi2_users2-{suffix}")],
            [InlineKeyboardButton("📊 Stats Guide", callback_data=f"monshi2_stats2-{suffix}")],
            [InlineKeyboardButton("🔙 Back to Panel", callback_data=f"back2-{suffix}")],
        ]
    else:
        rows = [
            [InlineKeyboardButton("⚙️ راهنمای تنظیمات", callback_data=f"monshi2_config1-{suffix}"), InlineKeyboardButton("🔗 راهنمای لینک‌ها", callback_data=f"monshi2_links1-{suffix}")],
            [InlineKeyboardButton("📝 شخصی‌سازی متن", callback_data=f"monshi2_text1-{suffix}"), InlineKeyboardButton("👥 مدیریت کاربران", callback_data=f"monshi2_users1-{suffix}")],
            [InlineKeyboardButton("📊 آمار عملیاتی", callback_data=f"monshi2_stats1-{suffix}")],
            [InlineKeyboardButton("🔙 بازگشت به پنل", callback_data=f"back1-{suffix}")],
        ]
    if section != "main":
        rows.append([InlineKeyboardButton("🔙 Monshi2", callback_data=f"monshi2_panel{2 if lang == 'en' else 1}-{suffix}")])
    return InlineKeyboardMarkup(rows)


async def _titan_close_panel(client, call, fallback_text="**● پنل راهنما بسته شد ●**"):
    if getattr(call, "message", None):
        try:
            return await call.message.delete()
        except Exception:
            pass
    try:
        return await _titan_show_paginated_text(client, call, fallback_text, reply_markup=None)
    except Exception:
        pass


@app.on_message(filters.text & filters.regex(r"(?i)^(panel|help|helper|پنل|راهنما)$"), group=-100)
async def direct_panel_trigger(client, message: Message):
    AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{message.from_user.id}' LIMIT 1")
    if AdminUser is None:
        return
    try:
        user = await client.get_users(message.from_user.id)
        await send_titan_panel(client, message.chat.id, user=user)
    except Exception:
        text = "زبان پنل را انتخاب کن / Choose panel language:"
        await client.send_message(message.chat.id, text, reply_markup=_titan_language_keyboard(message.from_user.id))
    update_data(f"UPDATE user SET step = 'none' WHERE id = '{message.from_user.id}' LIMIT 1")
    raise StopPropagation


@app.on_callback_query()
async def call(app, call):
    AdminUser = get_data(f"SELECT * FROM adminlist WHERE id = '{call.from_user.id}' LIMIT 1")
    if AdminUser is None:
        await call.answer("دسترسی غیر مجاز 🚫", show_alert=False)
        return

    if call.data == "openpanel":
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
            print(f"TITAN callback panel generation failed: {exc}")
            await call.answer("خطا در ساخت پنل", show_alert=True)
        return

    if call.data != "outside":
        try:
            _target_user_id = int(call.data.split("-")[-1])
        except Exception:
            _target_user_id = call.from_user.id

        if int(call.from_user.id) == int(_target_user_id):
            _action = call.data.split("-")[0]

            if _action == "persian" or _action == "back1":
                await _titan_show_paginated_text(
                    app,
                    call,
                    text="╭━━━ ⚡ TiTaN SelfSaz ━━━╮\n┃ 🇮🇷 پنل راهنمای اولترا سلف\n┃ لطفاً بخش مورد نظر را انتخاب کنید:\n╰━━━━━━━━━━━━━━━━━━━━━━╯",
                    reply_markup=build_titan_panel_keyboard(call.from_user.id, language="fa")
                )
                await call.answer()
                return

            if _action == "english" or _action == "back2":
                await _titan_show_paginated_text(
                    app,
                    call,
                    text="╭━━━ ⚡ TiTaN SelfSaz ━━━╮\n┃ 🇬🇧 TiTaN SelfSaz Help Center\n┃ Please select a section:\n╰━━━━━━━━━━━━━━━━━━━━━━╯",
                    reply_markup=build_titan_panel_keyboard(call.from_user.id, language="en")
                )
                await call.answer()
                return

            if _action in _TITAN_HELP_ACTIONS:
                _lang, _key = _TITAN_HELP_ACTIONS[_action]
                await _titan_show_help_page(app, call, _lang, _key, 0, call.from_user.id)
                await call.answer()
                return

            if _action == "hpg":
                _parts = call.data.split("-")
                if len(_parts) >= 5:
                    await _titan_show_help_page(app, call, _parts[1], _parts[2], int(_parts[3]), call.from_user.id)
                    await call.answer()
                    return

            if _action.startswith("monshi2_"):
                lang = "en" if _action.endswith("2") else "fa"
                base = _action[:-1] if _action[-1:] in ["1", "2"] else _action
                section = "main"
                if base == "monshi2_config":
                    section = "config"
                elif base == "monshi2_links":
                    section = "links"
                elif base == "monshi2_text":
                    section = "text"
                elif base == "monshi2_users":
                    section = "users"
                elif base == "monshi2_stats":
                    section = "stats"
                await _titan_show_paginated_text(
                    app,
                    call,
                    text=_monshi2_helper_panel_text(lang, section),
                    reply_markup=_monshi2_helper_panel_keyboard(call.from_user.id, lang, section)
                )
                await call.answer()
                return

            if _action == "close1":
                await _titan_close_panel(app, call, "**● پنل راهنما بسته شد ●**")
                await call.answer()
                return

            if _action == "close2":
                await _titan_close_panel(app, call, "**● Helper Panel Closed ●**")
                await call.answer()
                return

            if _action == "Close":
                await _titan_close_panel(app, call, "**● Closed ●**")
                await call.answer()
                return

        else:
            await call.answer("دسترسی غیر مجاز 🚫", show_alert=False)
            return
    else:
        await call.answer("—", show_alert=False)
        return

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
