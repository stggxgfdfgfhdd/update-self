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
FIX_VERSION = "2026-08-25-titan-hybrid-buttons-v8-7"
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
  
# ================= SLEEK COMPACT HELP TEXTS (ALL COMMANDS PRESERVED) =================

# ================= MINIMAL 2-COLUMN GRID HELP TEXTS =================

fahelp1 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: سراسری - شخصی
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔇 سکوت کاربر       │ 🔊 رفع سکوت
   `.mute`          │    `.unmute`

🧹 پاکسازی سکوت     │ 🚫 بلاک کاربر
   `.allunmute`     │    `.block`

🔓 رفع بلاک         │ ☠️ افزودن دشمن
   `.unblock`       │    `.setenemy`

🗑 حذف دشمن        │ 🧹 پاکسازی دشمن
   `.delenemy`      │    `.clearenemy`

❤️ افزودن عشق       │ 💔 حذف عشق
   `.setlove`       │    `.dellove`

🧹 پاکسازی عشق      │ 💬 منشی خودکار
   `.clearlove`     │    `.monshi`

🔕 خاموشی منشی      │ 🌙 حالت آفلاین
   `.monshioff`     │    `.afk`

☀️ لغو آفلاین       │ 🔔 هشدار تگ
   `.unafk`         │    `.tagalert`

📢 ساخت کانال       │ 👥 ساخت گروه
   `.creatchannel`  │    `.creatgroup`

👑 ساخت سوپرگروه    │ ⚡ اسپم پیام
   `.creatsupergroup`│   `.spam`

🐢 اسپم آرام        │ 👻 اسپم مخفی
   `.slowspam`      │    `.statspam`

🚀 اسپم سریع        │ 🥇 پیام اول چت
   `.fastspam`      │    `.firstcom`

💬 ارسال پیام اول   │ ⏰ ارسال زماندار
   `.first_message` │    `.text_time`

📸 عکس زماندار      │ ⏱ زماندار ریپلی
   `.photo_time`    │    `.text_send_time`

🖼 عکس ریپلی زمان   │ 🤖 پاسخ خودکار
   `.photo_send_time`│   `.answer`

➕ افزودن پاسخ      │ ➖ حذف پاسخ
   `.addan`         │    `.delan`

📋 لیست پاسخ‌ها     │ 🧹 پاکسازی پاسخ
   `.anlist`        │    `.anclear`

👋 خوشامدگویی       │ ➕ تنظیم خوشامد
   `.welcome`       │    `.welcome_add`

👁 نمایش خوشامد     │ 🔄 ریست خوشامد
   `.welcome_show`  │    `.welcome_reset`

⛔ بن کاربر         │ ❇️ آنبن کاربر
   `.ban`           │    `.unban`

🔇 میوت گروه        │ 🔊 آنمیوت گروه
   `.setmute`       │    `.delmute`

🖼 عکس گروه         │ 📝 نام گروه
   `.setchatphoto`  │    `.setchattitle`

📄 بیو گروه         │ 🔗 یوزرنیم گروه
   `.setchatbio`    │    `.setchatusername`

📌 پین پیام         │ 📍 آنپین پیام
   `.pin`           │    `.unpin`

📍 آنپین همه        │ 🗑 حذف کانال
   `.unpinall`      │    `.deletechannel`

🗑 حذف گروه         │ 🧹 پاکسازی کاربر
   `.deletegroup`   │    `.delallmsguser`

⏳ اسلومود چت       │ ❌ حذف پیام‌ها
   `.slowmod`       │    `.delete`

👮 لیست ادمین‌ها    │ 📣 تگ سراسری
   `.tadmin`        │    `.tagall`

🛑 لغو عملیات       │ 🗑 حذف تاریخچه
   `.cancel`        │    `.delethistory`

🗑 حذف تک پیام      │
   `.del`           │"""

enhelp1 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Global - Personal
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔇 Mute User        │ 🔊 Unmute User
   `.mute`          │    `.unmute`

🧹 Clear Mute       │ 🚫 Block User
   `.allunmute`     │    `.block`

🔓 Unblock User     │ ☠️ Set Enemy
   `.unblock`       │    `.setenemy`

🗑 Del Enemy        │ 🧹 Clear Enemy
   `.delenemy`      │    `.clearenemy`

❤️ Set Love         │ 💔 Del Love
   `.setlove`       │    `.dellove`

🧹 Clear Love       │ 💬 Auto Monshi
   `.clearlove`     │    `.monshi`

🔕 Monshi Off       │ 🌙 Offline AFK
   `.monshioff`     │    `.afk`

☀️ UnAFK Mode       │ 🔔 Tag Alert
   `.unafk`         │    `.tagalert`

📢 Create Channel   │ 👥 Create Group
   `.creatchannel`  │    `.creatgroup`

👑 Supergroup       │ ⚡ Spam Messages
   `.creatsupergroup`│   `.spam`

🐢 Slow Spam        │ 👻 Stat Spam
   `.slowspam`      │    `.statspam`

🚀 Fast Spam        │ 🥇 First Comment
   `.fastspam`      │    `.firstcom`

💬 First Message    │ ⏰ Timed Text
   `.first_message` │    `.text_time`

📸 Timed Photo      │ ⏱ Reply Timed Msg
   `.photo_time`    │    `.text_send_time`

🖼 Reply Photo Time │ 🤖 Auto Answer
   `.photo_send_time`│   `.answer`

➕ Add Answer       │ ➖ Del Answer
   `.addan`         │    `.delan`

📋 Answer List      │ 🧹 Clear Answers
   `.anlist`        │    `.anclear`

👋 Welcome Msg      │ ➕ Set Welcome
   `.welcome`       │    `.welcome_add`

👁 Show Welcome     │ 🔄 Reset Welcome
   `.welcome_show`  │    `.welcome_reset`

⛔ Ban User         │ ❇️ Unban User
   `.ban`           │    `.unban`

🔇 Set Chat Mute    │ 🔊 Del Chat Mute
   `.setmute`       │    `.delmute`

🖼 Set Chat Photo   │ 📝 Set Chat Title
   `.setchatphoto`  │    `.setchattitle`

📄 Set Chat Bio     │ 🔗 Set Username
   `.setchatbio`    │    `.setchatusername`

📌 Pin Message      │ 📍 Unpin Message
   `.pin`           │    `.unpin`

📍 Unpin All        │ 🗑 Delete Channel
   `.unpinall`      │    `.deletechannel`

🗑 Delete Group     │ 🧹 Del User Msgs
   `.deletegroup`   │    `.delallmsguser`

⏳ Slowmode         │ ❌ Delete Count
   `.slowmod`       │    `.delete`

👮 Admin List       │ 📣 Tag All Members
   `.tadmin`        │    `.tagall`

🛑 Cancel Operation │ 🗑 Clear History
   `.cancel`        │    `.delethistory`

🗑 Delete Message   │
   `.del`           │"""

fahelp2 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: پروفایل
╰━━━━━━━━━━━━━━━━━━━━━━╯

👤 نام اول          │ 👥 نام خانوادگی
   `.setname`       │    `.setlastname`

📝 بیوگرافی پروفایل │ 🔤 فونت خودکار نام
   `.setbio`        │    `.fontname`

⏰ ساعت اسم (مدل ۱) │ ⏰ ساعت اسم (مدل ۲)
   `.timename`      │    `.2timename`

🕒 ساعت بیو (مدل ۱) │ 🕒 ساعت بیو (مدل ۲)
   `.timebio`       │    `.2timebio`

🕒 ساعت بیو (مدل ۳) │ 🕒 ساعت بیو (مدل ۴)
   `.3timebio`      │    `.4timebio`

🕒 ساعت بیو (مدل ۵) │ 🕒 ساعت بیو (مدل ۶)
   `.5timebio`      │    `.6timebio`

🖼 تنظیم پروفایل    │ 🗑 حذف پروفایل
   `.setprofile`    │    `.delprofile`

🤖 پروفایل خودکار ۱ │ 🤖 پروفایل خودکار ۲
   `.autopic`       │    `.2autopic`

🤖 پروفایل خودکار ۳ │ 🤖 پروفایل خودکار ۴
   `.3autopic`      │    `.4autopic`"""

enhelp2 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Profile
╰━━━━━━━━━━━━━━━━━━━━━━╯

👤 Set First Name   │ 👥 Set Last Name
   `.setname`       │    `.setlastname`

📝 Set Biography    │ 🔤 Auto Font Name
   `.setbio`        │    `.fontname`

⏰ Clock on Name 1  │ ⏰ Clock on Name 2
   `.timename`      │    `.2timename`

🕒 Clock on Bio 1   │ 🕒 Clock on Bio 2
   `.timebio`       │    `.2timebio`

🕒 Clock on Bio 3   │ 🕒 Clock on Bio 4
   `.3timebio`      │    `.4timebio`

🕒 Clock on Bio 5   │ 🕒 Clock on Bio 6
   `.5timebio`      │    `.6timebio`

🖼 Set Profile Photo│ 🗑 Del Profile Photo
   `.setprofile`    │    `.delprofile`

🤖 Auto Profile 1   │ 🤖 Auto Profile 2
   `.autopic`       │    `.2autopic`

🤖 Auto Profile 3   │ 🤖 Auto Profile 4
   `.3autopic`      │    `.4autopic`"""

fahelp3 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: دانلودر
╰━━━━━━━━━━━━━━━━━━━━━━╯

📸 اطلاعات اینستا   │ 📥 دانلود اینستاگرام
   `.iginfo`        │    `.igdl`

🌐 دانلود همه‌کاره   │ 🎥 دانلود یوتیوب
   `.down`          │    `.youtube`

📱 جستجوی برنامه    │ 📦 دانلود مستقیم نصبی
   `.app`           │    `.apk`"""

enhelp3 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Downloader
╰━━━━━━━━━━━━━━━━━━━━━━╯

📸 Instagram Info   │ 📥 Instagram DL
   `.iginfo`        │    `.igdl`

🌐 Universal DL     │ 🎥 YouTube DL
   `.down`          │    `.youtube`

📱 App Search       │ 📦 Direct APK DL
   `.app`           │    `.apk`"""

fahelp4 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: آپلودر
╰━━━━━━━━━━━━━━━━━━━━━━╯

☁️ آپلود در نکو    │ 📄 آپلود تلگراف
   `.neko`          │    `.telegraph`"""

enhelp4 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Uploader
╰━━━━━━━━━━━━━━━━━━━━━━╯

☁️ Upload to Neko   │ 📄 Upload Telegraph
   `.neko`          │    `.telegraph`"""

fahelp5 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: حالت متن
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔲 متن بولد (ضخیم)  │ 🙈 متن اسپویلر
   `.bold`          │    `.spoiler`

✍️ متن ایتالیک (کج) │ 💻 فونت کدنویسی
   `.italic`        │    `.code`

➖ خط زیرین متن     │ <s> خط روی متن </s>
   `.underline`     │    `.strike`

😀 ایموجی خودکار    │ 💬 نقل قول خودکار
   `.emoji`         │    `.quote`

📢 منشن خودکار      │ 💖 تنظیم ری‌اکشن
   `.mention`       │    `.setreact`

🗑 حذف ری‌اکشن      │ 📋 لیست ری‌اکشن‌ها
   `.delreact`      │    `.reactlist`

🪜 متن نردبانی شیک  │
   `.lad`           │"""

enhelp5 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Text Mode
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔲 Bold Text Mode   │ 🙈 Spoiler Mode
   `.bold`          │    `.spoiler`

✍️ Italic Text Mode │ 💻 Code Font Mode
   `.italic`        │    `.code`

➖ Underline Mode   │ <s> Strike Mode </s>
   `.underline`     │    `.strike`

😀 Auto Emoji       │ 💬 Auto Quote
   `.emoji`         │    `.quote`

📢 Auto Mention     │ 💖 Set Reaction
   `.mention`       │    `.setreact`

🗑 Del Reaction     │ 📋 Reaction List
   `.delreact`      │    `.reactlist`

🪜 Ladder Text Style│
   `.lad`           │"""

fahelp6 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: حالت اکشن
╰━━━━━━━━━━━━━━━━━━━━━━╯

⌨️ در حال تایپ...   │ 🎮 در حال بازی...
   `.typing`        │    `.playing`

📹 ضبط ویدیو...     │ 🎭 انتخاب استیکر...
   `.record_vid`    │    `.choose_sticker`

📤 آپلود ویدیو...   │ 📄 آپلود فایل...
   `.upload_vid`    │    `.upload_doc`

🎵 آپلود صدا...     │ 🎙 ضبط وویس...
   `.upload_audio`  │    `.speaking`

🟢 آنلاین دائمی     │ ⚫️ آفلاین دائمی
   `.online`        │    `.offline`"""

enhelp6 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Action Mode
╰━━━━━━━━━━━━━━━━━━━━━━╯

⌨️ Typing Action    │ 🎮 Playing Game
   `.typing`        │    `.playing`

📹 Recording Video  │ 🎭 Choosing Sticker
   `.record_vid`    │    `.choose_sticker`

📤 Uploading Video  │ 📄 Uploading Doc
   `.upload_vid`    │    `.upload_doc`

🎵 Uploading Audio  │ 🎙 Recording Voice
   `.upload_audio`  │    `.speaking`

🟢 Always Online    │ ⚫️ Always Offline
   `.online`        │    `.offline`"""

fahelp7 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: وبهوک
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔗 تنظیم وبهوک      │ 🗑 حذف وبهوک
   `.setwebhook`    │    `.delwebhook`

🧹 حذف آپدیت‌ها     │ ℹ️ اطلاعات وبهوک
   `.delupdate`     │    `.webhookinfo`

🤖 اطلاعات کامل ربات│
   `.botinfo`       │"""

enhelp7 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Webhook
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔗 Set Webhook      │ 🗑 Delete Webhook
   `.setwebhook`    │    `.delwebhook`

🧹 Delete Updates   │ ℹ️ Webhook Info
   `.delupdate`     │    `.webhookinfo`

🤖 Telegram Bot Info│
   `.botinfo`       │"""

fahelp8 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: قفل‌ها
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔒 قفل امنیتی پیوی  │ 🛡 جوین اجباری منشی
   `.pvlock`        │    `.monshi2`

📖 راهنمای قفل هلپر │ 📋 لیست قفل‌های گروه
   `.hlock`         │    `.locks`

🔐 قفل کردن آیتم    │ 🔓 باز کردن آیتم
   `.lock`          │    `.unlock`

🔒 قفل همه موارد    │ 🔓 باز کردن همه
   `.lock all`      │    `.unlock all`"""

enhelp8 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Locks
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔒 PV Security Lock │ 🛡 Monshi2 Forced Join
   `.pvlock`        │    `.monshi2`

📖 Helper Locks Info│ 📋 Group Locks List
   `.hlock`         │    `.locks`

🔐 Lock Specific    │ 🔓 Unlock Specific
   `.lock`          │    `.unlock`

🔒 Lock All Items   │ 🔓 Unlock All Items
   `.lock all`      │    `.unlock all`"""

fahelp9 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: کرون جاب
╰━━━━━━━━━━━━━━━━━━━━━━╯

⏱ اجرای کرون جاب   │
   `.cron`          │"""

enhelp9 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Cron Job
╰━━━━━━━━━━━━━━━━━━━━━━╯

⏱ Execute Cron Job  │
   `.cron`          │"""

fahelp10 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: آنتی لاگین
╰━━━━━━━━━━━━━━━━━━━━━━╯

🛡 سیستم ضد ورود غیرمجاز
   `.antilog`       │"""

enhelp10 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Anti Login
╰━━━━━━━━━━━━━━━━━━━━━━╯

🛡 Anti-Login Protection
   `.antilog`       │"""

fahelp11 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: تبچی
╰━━━━━━━━━━━━━━━━━━━━━━╯

📊 وضعیت کلی تبچی   │ 📩 ارسال خودکار پیوی
   `.tabchi status` │    `.tabchipv`

👥 ارسال خودکار گروه│ 🖼 بنر تبلیغاتی پیوی
   `.tabchigp`      │    `.setbannerpv`

🖼 بنر تبلیغاتی گروه│ ⏱ تایمر ارسال پیوی
   `.setbannergp`   │    `.settimerpv`

⏱ تایمر ارسال گروه │ 📤 ارسال دستی پیوی
   `.settimergp`    │    `.sendpv`

📤 ارسال دستی گروه  │ 👤 بنر فرستنده تبلیغ
   `.sendgp`        │    `.setbannersender`

📢 ارسال سراسری     │ 🔗 دریافت لینک دعوت
   `.sendall`       │    `.invitelink`

🚪 عضویت در لینک    │ 🚶 خروج از لینک
   `.join`          │    `.leave`

🏃 لفت از همه گروه‌ها│ 🏃 لفت از همه کانال‌ها
   `.leaveallgc`    │    `.leaveallch`"""

enhelp11 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Tabchi
╰━━━━━━━━━━━━━━━━━━━━━━╯

📊 Tabchi Status    │ 📩 Auto Send in PV
   `.tabchi status` │    `.tabchipv`

👥 Auto Send in GP  │ 🖼 Set Banner PV
   `.tabchigp`      │    `.setbannerpv`

🖼 Set Banner GP    │ ⏱ Timer PV Send
   `.setbannergp`   │    `.settimerpv`

⏱ Timer GP Send    │ 📤 Manual Send PV
   `.settimergp`    │    `.sendpv`

📤 Manual Send GP   │ 👤 Sender Banner
   `.sendgp`        │    `.setbannersender`

📢 Send All Users   │ 🔗 Get Invite Link
   `.sendall`       │    `.invitelink`

🚪 Join Chat Link   │ 🚶 Leave Chat Link
   `.join`          │    `.leave`

🏃 Leave All Groups │ 🏃 Leave All Channels
   `.leaveallgc`    │    `.leaveallch`"""

fahelp12 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: ویرایشگر عکس
╰━━━━━━━━━━━━━━━━━━━━━━╯

👧 توییت کانّا       │ 🤖 توییت کلاید
   `.kanna`         │    `.clyde`

📝 نوشتن روی کاغذ   │ 💭 توییت نظر
   `.write`         │    `.mind`

👔 توییت ترامپ      │ 📜 دستخط تیتان ۱
   `.trump`         │    `.o`

📜 دستخط تیتان ۲    │ 💬 توییت دیسکورد
   `.o2`            │    `.bish`

📐 فرمول لاتک       │ 🔵 فیلتر آبی
   `.latex`         │    `.blue`

🟢 فیلتر سبز        │ 🔴 فیلتر قرمز
   `.green`         │    `.red`

⚪️ فیلتر خاکستری ۱  │ ⚪️ فیلتر خاکستری ۲
   `.grey`          │    `.grey2`

📜 فیلتر سپیا       │ 🔲 فیلتر ترشولد
   `.sepia`         │    `.threshold`

🟣 فیلتر بلورپل     │ 💡 فیلتر نوری
   `.blurple`       │    `.filter`

🌈 افکت بای‌سکشوال  │ 🌫 افکت تاری/مات
   `.bisexual`      │    `.blur`

😈 افکت شاخ دار     │ 🤪 افکت احمق
   `.horny`         │    `.stupid`

👩‍❤️‍👩 افکت لزبین      │ 🏳️‍🌈 افکت رنگین‌کمان
   `.lesbian`       │    `.lgbt`

👮 افکت پلیس انیمه  │ 👤 افکت بدون چهره
   `.lolice`        │    `.non`

💖 افکت پان‌سکشوال   │ 👾 افکت پیکسلی
   `.psexual`       │    `.pixel`

🥺 افکت سیمپ        │ 🌀 افکت چرخشی
   `.simp`          │    `.spin`

🦾 تونی استارک      │ ☭ رفیق کمونیست
   `.toni`          │    `.comrade`

👨‍❤️‍👨 افکت گی          │ 🪟 افکت شیشه‌ای
   `.gay`           │    `.glass`

⛓ افکت زندان        │ ☠️ افکت بازی جی‌تی‌ای
   `.jail`          │    `.wasted`

🛂 افکت پاسپورت     │
   `.pass`          │"""

enhelp12 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Photo Editor
╰━━━━━━━━━━━━━━━━━━━━━━╯

👧 Kanna Tweet      │ 🤖 Clyde Tweet
   `.kanna`         │    `.clyde`

📝 Write on Paper   │ 💭 Change My Mind
   `.write`         │    `.mind`

👔 Trump Tweet      │ 📜 Titan Note 1
   `.trump`         │    `.o`

📜 Titan Note 2     │ 💬 Discord Tweet
   `.o2`            │    `.bish`

📐 LaTeX Math Formula│ 🔵 Blue Filter
   `.latex`         │    `.blue`

🟢 Green Filter     │ 🔴 Red Filter
   `.green`         │    `.red`

⚪️ Grey Filter 1    │ ⚪️ Grey Filter 2
   `.grey`          │    `.grey2`

📜 Sepia Filter     │ 🔲 Threshold Filter
   `.sepia`         │    `.threshold`

🟣 Blurple Filter   │ 💡 Light Filter
   `.blurple`       │    `.filter`

🌈 Bisexual Effect  │ 🌫 Blur Effect
   `.bisexual`      │    `.blur`

😈 Horny Effect     │ 🤪 Stupid Effect
   `.horny`         │    `.stupid`

👩‍❤️‍👩 Lesbian Effect    │ 🏳️‍🌈 LGBT Effect
   `.lesbian`       │    `.lgbt`

👮 Lolice Effect    │ 👤 None Effect
   `.lolice`        │    `.non`

💖 Psexual Effect   │ 👾 Pixel Effect
   `.psexual`       │    `.pixel`

🥺 Simp Effect      │ 🌀 Spin Effect
   `.simp`          │    `.spin`

🦾 Toni Stark Effect│ ☭ Comrade Effect
   `.toni`          │    `.comrade`

👨‍❤️‍👨 Gay Effect       │ 🪟 Glass Effect
   `.gay`           │    `.glass`

⛓ Jail Effect       │ ☠️ GTA Wasted Effect
   `.jail`          │    `.wasted`

🛂 Passport Photo   │
   `.pass`          │"""

fahelp13 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: گیف و لوگو ساز
╰━━━━━━━━━━━━━━━━━━━━━━╯

🎨 ساخت لوگو گرافیکی│ 🎨 ساخت لوگو مدل ۲
   `.logo`          │    `.logo2`

🖌 ساخت لوگو سفارشی │ 🎬 ساخت گیف متنی ۱
   `.lg`            │    `.gif`

🎬 ساخت گیف متنی ۲  │
   `.giff`          │"""

enhelp13 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Logo & GIF Maker
╰━━━━━━━━━━━━━━━━━━━━━━╯

🎨 Graphic Logo 1   │ 🎨 Graphic Logo 2
   `.logo`          │    `.logo2`

🖌 Custom Logo Maker│ 🎬 Animated Text GIF 1
   `.lg`            │    `.gif`

🎬 Animated Text GIF 2│
   `.giff`          │"""

fahelp14 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: کامپایلر
╰━━━━━━━━━━━━━━━━━━━━━━╯

🐍 اجرای کد پایتون  │ 🟨 اجرای جاوااسکریپت
   `.py`            │    `.js`

🐘 اجرای پی‌اچ‌پی     │ 📱 اجرای کد کاتلین
   `.php`           │    `.kotlin`

🔷 اجرای زبان گو     │ ☕️ اجرای کد جاوا
   `.go`            │    `.java`

🌙 اجرای کد لوآ      │ ⚡️ اجرای مستقیم شل
   `.lua`           │    `.exec`"""

enhelp14 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Compiler
╰━━━━━━━━━━━━━━━━━━━━━━╯

🐍 Execute Python   │ 🟨 Execute JavaScript
   `.py`            │    `.js`

🐘 Execute PHP      │ 📱 Execute Kotlin
   `.php`           │    `.kotlin`

🔷 Execute Golang   │ ☕️ Execute Java
   `.go`            │    `.java`

🌙 Execute Lua      │ ⚡️ Execute Terminal
   `.lua`           │    `.exec`"""

fahelp15 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: ابزارها
╰━━━━━━━━━━━━━━━━━━━━━━╯

📦 استخراج زیپ      │ ✏️ تغییر نام فایل
   `.unzip`         │    `.rname`

📱 استعلام شماره    │ 💬 ساخت کووت تلگرام
   `.check`         │    `.q`

💭 ساخت کووت پیشرفته│ 🏏 نتیجه زنده ورزشی
   `.qq`            │    `.cricket`

🌤 وضعیت آب و هوا   │ 🕋 اذان و اوقات شرعی
   `.weather`       │    `.azan`

🌡 تبدیل دما c/f    │ 💱 تبدیل لحظه‌ای ارز
   `.t`             │    `.c`

🧮 ماشین حساب ریاضی │ 🌐 اطلاعات آی‌پی
   `.e`             │    `.ip`

🔍 هوایز و مشخصات سرور│ 🔗 کوتاه کننده لینک ۱
   `.whoisip`       │    `.link`

🔗 کوتاه کننده لینک ۲│ 📶 تست پینگ سرور
   `.link2`         │    `.ping`

📸 اسکرین‌شات سایت ۱ │ 📸 اسکرین‌شات سایت ۲
   `.shot`          │    `.screenshot`

📸 اسکرین‌شات سایت ۳ │ 📸 اسکرین‌شات سایت ۴
   `.screenshot2`   │    `.screenshot3`

📸 اسکرین‌شات سایت ۵ │ 🐙 جستجوی گیت‌هاب
   `.screenshot4`   │    `.github`

📁 مخزن سورس گیت    │ 📖 دیکشنری و ترجمه
   `.git`           │    `.dict`

👥 کلون اکانت تلگرام│ 👤 مشخصات پروفایل
   `.clone`         │    `.i`

📅 تاریخ ساخت اکانت │ ⚠️ بررسی لیمیت اکانت
   `.creation`      │    `.limit`

🌍 مشخصات کشور      │ 🖼 تصویر به استیکر
   `.country`       │    `.ts`

🎭 استیکر به تصویر  │ 🇮🇷 ترجمه به فارسی
   `.tg`            │    `.fa`

🇬🇧 ترجمه به انگلیسی │ 🎬 جستجوی فیلم سینمایی
   `.en`            │    `.movie`

🍿 جستجوی انیمیشن   │ 🔑 ساخت پسورد امن
   `.anim`          │    `.pass`

📡 تبدیل به کد مورس │ 📡 رمزگشایی کد مورس
   `.morset`        │    `.unmorset`

🗓 تاریخ شمسی و میلادی│ 🆔 شناسه عددی تلگرام
   `.date`          │    `.id`

📩 دریافت مشخصات پیام│ 📣 منشن کاربر با ایدی
   `.get_message`   │    `.mention`

🇮🇷 استعلام کدملی    │ 🔍 استعلامات عمومی
   `.meli`          │    `.estelam`

📰 اخبار سراسری روز │ 💳 ساخت کارت تست
   `.news`          │    `.ccgen`

📡 اخبار خبرگزاری YJC│ 👁 متن خوان OCR تصویر
   `.yjc`           │    `.ocr`

📥 دانلود مستقیم فایل│ ⏳ پیام انتظار دانلود
   `.dl`            │    `.waitt`

⏰ نمایش ساعت دقیق  │ 🔞 عکس خاص مدل ۱
   `.time`          │    `.nude`

🔞 عکس خاص مدل ۲    │ 🔞 عکس خاص مدل ۳
   `.nude2`         │    `.nude3`

🔥 رسانه اختصاصی    │ 💃 رسانه یانگ
   `.boob`          │    `.ayang`

🎲 تست شانس تصادفی  │
   `.chance`        │"""

enhelp15 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Tools
╰━━━━━━━━━━━━━━━━━━━━━━╯

📦 Extract ZIP File │ ✏️ Rename File
   `.unzip`         │    `.rname`

📱 Number Check     │ 💬 Create Quotly
   `.check`         │    `.q`

💭 Advanced Quotly  │ 🏏 Live Cricket Score
   `.qq`            │    `.cricket`

🌤 Weather Forecast │ 🕋 Azan & Prayer Time
   `.weather`       │    `.azan`

🌡 Temperature Calc │ 💱 Currency Converter
   `.t`             │    `.c`

🧮 Math Calculator  │ 🌐 IP Info Lookup
   `.e`             │    `.ip`

🔍 Whois Server Info│ 🔗 Short URL Link 1
   `.whoisip`       │    `.link`

🔗 Short URL Link 2 │ 📶 Server Ping Test
   `.link2`         │    `.ping`

📸 Web Screenshot 1 │ 📸 Web Screenshot 2
   `.shot`          │    `.screenshot`

📸 Web Screenshot 3 │ 📸 Web Screenshot 4
   `.screenshot2`   │    `.screenshot3`

📸 Web Screenshot 5 │ 🐙 GitHub User Info
   `.screenshot4`   │    `.github`

📁 Git Repository   │ 📖 Word Dictionary
   `.git`           │    `.dict`

👥 Clone Account    │ 👤 Account Full Info
   `.clone`         │    `.i`

📅 Account Creation │ ⚠️ Check Account Limits
   `.creation`      │    `.limit`

🌍 Country Info     │ 🖼 Photo to Sticker
   `.country`       │    `.ts`

🎭 Sticker to Photo │ 🇮🇷 Translate Persian
   `.tg`            │    `.fa`

🇬🇧 Translate English│ 🎬 Search Movie
   `.en`            │    `.movie`

🍿 Search Animation │ 🔑 Password Generator
   `.anim`          │    `.pass`

📡 Text to Morse    │ 📡 Decode Morse Code
   `.morset`        │    `.unmorset`

🗓 Gregorian Date   │ 🆔 Numeric User ID
   `.date`          │    `.id`

📩 Get Message Info │ 📣 Mention with ID
   `.get_message`   │    `.mention`

🇮🇷 National ID Check│ 🔍 General Price Inquiry
   `.meli`          │    `.estelam`

📰 News Headlines   │ 💳 Test Credit Card Gen
   `.news`          │    `.ccgen`

📡 YJC News Feed    │ 👁 Image Text OCR
   `.yjc`           │    `.ocr`

📥 Direct Link DL   │ ⏳ Download Wait Msg
   `.dl`            │    `.waitt`

⏰ Exact Clock Time │ 🔞 Special Photo 1
   `.time`          │    `.nude`

🔞 Special Photo 2   │ 🔞 Special Photo 3
   `.nude2`         │    `.nude3`

🔥 Special Media    │ 💃 Ayang Media
   `.boob`          │    `.ayang`

🎲 Random Chance    │
   `.chance`        │"""

fahelp16 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: اکانت
╰━━━━━━━━━━━━━━━━━━━━━━╯

➕ افزودن ادمین سلف │ ➖ حذف ادمین سلف
   `.addadmin`      │    `.deladmin`

📋 لیست ادمین‌ها    │ 🧹 پاکسازی ادمین‌ها
   `.adminlist`     │    `.clearadminlist`

🆔 شناسه کاربری     │ ⚠️ بررسی لیمیت
   `.id`            │    `.limit`

📅 تاریخ ساخت اکانت │ 🟢 وضعیت اتصال سلف
   `.creation`      │    `.session`"""

enhelp16 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Account
╰━━━━━━━━━━━━━━━━━━━━━━╯

➕ Add Helper Admin │ ➖ Del Helper Admin
   `.addadmin`      │    `.deladmin`

📋 Helper Admin List│ 🧹 Clear All Admins
   `.adminlist`     │    `.clearadminlist`

🆔 Numeric User ID  │ ⚠️ Check Limits
   `.id`            │    `.limit`

📅 Account Creation │ 🟢 Self ON Status
   `.creation`      │    `.session`"""

fahelp17 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: کتاب و اطلاعات
╰━━━━━━━━━━━━━━━━━━━━━━╯

😂 ارسال جوک جالب   │ 📜 شعر و ابیات زیبا
   `.joke`          │    `.poem`

💡 آیا می‌دانید؟     │ 💬 سخنان بزرگان
   `.know`          │    `.quote`

📚 جستجو در ویکی‌پدیا│ 🔍 جستجو در گوگل
   `.wiki`          │    `.google`

🔢 عدد تصادفی رندوم │ 🔤 پیشنهاد نام زیبا
   `.num`           │    `.name`

📝 بیوگرافی پیشنهادی│ 📌 یادداشت سریع
   `.bio`           │    `.memo`

🎭 شوخی و طنز روز   │ 🌀 متن‌های رندوم
   `.pnp`           │    `.alaki`

📖 حدیث روز         │ 📚 داستان کوتاه زیبا
   `.hadis`         │    `.dastan`

✏️ تغییر نام مستعار │ 🥠 فال حافظ با معنی
   `.rname`         │    `.fal`

📿 استخاره آنلاین   │ 🤲 ذکر ایام هفته
   `.estekhare`     │    `.zekr`"""

enhelp17 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Book & Info
╰━━━━━━━━━━━━━━━━━━━━━━╯

😂 Funny Jokes      │ 📜 Beautiful Poems
   `.joke`          │    `.poem`

💡 Did You Know?    │ 💬 Famous Quotes
   `.know`          │    `.quote`

📚 Search Wikipedia │ 🔍 Search Google
   `.wiki`          │    `.google`

🔢 Random Number    │ 🔤 Name Suggestions
   `.num`           │    `.name`

📝 Biography Ideas  │ 📌 Quick Notes
   `.bio`           │    `.memo`

🎭 Daily Humors     │ 🌀 Random Text Gen
   `.pnp`           │    `.alaki`

📖 Daily Hadith     │ 📚 Short Stories
   `.hadis`         │    `.dastan`

✏️ Rename Nickname  │ 🥠 Hafez Horoscope
   `.rname`         │    `.fal`

📿 Online Estekhare │ 🤲 Daily Prayers
   `.estekhare`     │    `.zekr`"""

fahelp18 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: سرگرمی و ایموجی
╰━━━━━━━━━━━━━━━━━━━━━━╯

🎲 پرتاب تاس شانس   │ 🎯 پرتاب دارت
   `.tas`           │    `.dart`

🎳 پرتاب بولینگ     │ 🏀 پرتاب بسکتبال
   `.bowling`       │    `.basketball`

⚽️ شوت فوتبال       │ 🎮 بازی‌های تلگرامی
   `.football`      │    `.game`

🕹 اجرای بازی‌ها     │ 😂 انیمیشن خنده
   `.bazi`          │    `.hehe`

🌕 انیمیشن ماه      │ 🕰 انیمیشن ساعت
   `.moon`          │    `.clock`

⚡️ انیمیشن رعدوبرق  │ 🌍 انیمیشن کره زمین
   `.thunder`       │    `.earth`

❤️ انیمیشن قلب متحرک│ 💖 قلب‌های عاشقانه
   `.heart`         │    `.love`

🧙‍♂️ جادوی متنی       │ 🙅‍♂️ پاسخ نه متحرک
   `.santet`        │    `.nah`

🤬 شوخی فان ۱       │ 🤬 شوخی فان ۲
   `.ajg`           │    `.babi`

🚜 شلیک تانک جنگی   │ 👍 تایید سریع
   `.tank`          │    `.y`

😹 خنده متحرک       │ 🔫 شلیک گلوله
   `.awk`           │    `.tembak`

🚁 پرواز هلیکوپتر   │ 🛋 متن بیکاری
   `.heli`          │    `.gabut`

💑 متن عشقم         │ 🦖 دایناسور متحرک
   `.syg`           │    `.dino`

💻 شبیه‌ساز هک      │ 🤬 شوخی طنز
   `.hack`          │    `.fuck`

🔥 طنز متنی         │ 🔋 شارژ باتری متحرک
   `.koc`           │    `.charging`

🕶 انیمیشن گنگستر   │ 🌀 انیمیشن هایپو
   `.gang`          │    `.hypo`

🔔 انیمیشن دینگ     │ ❓ انیمیشن وات
   `.ding`          │    `.wtf`

📞 انیمیشن تماس     │ 💣 انیمیشن انفجار بمب
   `.call`          │    `.bomb`

🧠 انیمیشن مغز فعال │ 🥱 انیمیشن آخ
   `.brain`         │    `.ahh`

🤔 انیمیشن هوم      │
   `.hmm`           │"""

enhelp18 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Fun & Games
╰━━━━━━━━━━━━━━━━━━━━━━╯

🎲 Lucky Dice Roll  │ 🎯 Target Dart
   `.tas`           │    `.dart`

🎳 Bowling Game     │ 🏀 Basketball Shot
   `.bowling`       │    `.basketball`

⚽️ Football Goal    │ 🎮 Telegram Games
   `.football`      │    `.game`

🕹 Play Online Games│ 😂 Laugh Animation
   `.bazi`          │    `.hehe`

🌕 Moon Animation   │ 🕰 Clock Animation
   `.moon`          │    `.clock`

⚡️ Thunder Storm    │ 🌍 Earth Globe Spin
   `.thunder`       │    `.earth`

❤️ Animated Heart   │ 💖 Love Heart Beat
   `.heart`         │    `.love`

🧙‍♂️ Magic Prank      │ 🙅‍♂️ Animated Nah
   `.santet`        │    `.nah`

🤬 Prank Text 1     │ 🤬 Prank Text 2
   `.ajg`           │    `.babi`

🚜 War Tank Cannon  │ 👍 Quick Yes
   `.tank`          │    `.y`

😹 Awkward Laugh    │ 🔫 Gun Shoot
   `.awk`           │    `.tembak`

🚁 Fly Helicopter   │ 🛋 Boredom Mood
   `.heli`          │    `.gabut`

💑 My Darling Text  │ 🦖 Animated Dino
   `.syg`           │    `.dino`

💻 Fake Hack Prank  │ 🤬 Joke Prank
   `.hack`          │    `.fuck`

🔥 Fun Animation    │ 🔋 Charging Battery
   `.koc`           │    `.charging`

🕶 Gangster Mood    │ 🌀 Hypo Animation
   `.gang`          │    `.hypo`

🔔 Ding Bell        │ ❓ WTF Animation
   `.ding`          │    `.wtf`

📞 Incoming Call    │ 💣 Bomb Explosion
   `.call`          │    `.bomb`

🧠 Active Brain     │ 🥱 Ahh Animation
   `.brain`         │    `.ahh`

🤔 Thinking Hmm     │
   `.hmm`           │"""

fahelp19 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: بازار و ارز
╰━━━━━━━━━━━━━━━━━━━━━━╯

🛍 قیمت کالا در باسلام│ 🛒 قیمت کالا در ترب
   `.price`         │    `.qeymat`

📊 لیست تمام رمزارزها│ 🪙 قیمت لحظه‌ای کریپتو
   `.cryptolist`    │    `.crypto`

💱 ماشین حساب تبدیل ارز│ 🔴 قیمت و شبکه ترون
   `.c`             │    `.trx`

📈 قیمت ارزهای نوبیتکس│ 🔍 استعلام قیمت عمومی
   `.arz`           │    `.estelam`

⚡️ پیگیری تراکنش تارا│
   `.tara`          │"""

enhelp19 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Market & Crypto
╰━━━━━━━━━━━━━━━━━━━━━━╯

🛍 Basalam Store Price│ 🛒 Torob Market Price
   `.price`         │    `.qeymat`

📊 Crypto Coins List │ 🪙 Real-time Coin Price
   `.cryptolist`    │    `.crypto`

💱 Currency Converter│ 🔴 TRON Network & Info
   `.c`             │    `.trx`

📈 Nobitex Exchange  │ 🔍 General Inquiries
   `.arz`           │    `.estelam`

⚡️ TRON Tara Tracker │
   `.tara`          │"""

fahelp20 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: استیکر و گیف
╰━━━━━━━━━━━━━━━━━━━━━━╯

🎨 تبدیل متن به استیکر│ 📦 اطلاعات پک استیکر
   `.sticker`       │    `.stickerinfo`

⚠️ استیکر ارور ویندوز│ 🔬 متن فوق ریز تینی
   `.error`         │    `.tiny`

🖼 تبدیل عکس به استیکر│ 🎭 تبدیل استیکر به عکس
   `.ts`            │    `.tg`

🤦‍♂️ ری‌اکشن دست رو صورت│ 😉 ری‌اکشن چشمک انیمه
   `.palm`          │    `.wink`

🤗 ری‌اکشن بغل و آغوش│ 💆‍♂️ ری‌اکشن نوازش
   `.hug`           │    `.pat`"""

enhelp20 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Sticker & GIF
╰━━━━━━━━━━━━━━━━━━━━━━╯

🎨 Text to Sticker   │ 📦 Sticker Pack Info
   `.sticker`       │    `.stickerinfo`

⚠️ Windows Error Msg │ 🔬 Superscript Tiny Text
   `.error`         │    `.tiny`

🖼 Photo to Sticker  │ 🎭 Sticker to Photo
   `.ts`            │    `.tg`

🤦‍♂️ Facepalm Action   │ 😉 Anime Wink Action
   `.palm`          │    `.wink`

🤗 Anime Hug Action  │ 💆‍♂️ Anime Pat Action
   `.hug`           │    `.pat`"""

fahelp21 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: هوش مصنوعی
╰━━━━━━━━━━━━━━━━━━━━━━╯

🤖 هوش مصنوعی پیشرفته│ 🧠 آموزش و یادگیری AI
   `.ai`            │    `.ai learn`

💾 مشاهده حافظه AI  │ 🗑 فراموشی حافظه AI
   `.ai memory`     │    `.ai forget`

🔄 ریست چت هوش مصنوعی│ ⚡️ روت مدل سریع
   `.ai reset`      │    `.ai /fast`

🎯 روت مدل دقیق     │ 💻 روت مدل کدنویسی
   `.ai /smart`     │    `.ai /code`

🎙 تبدیل متن به صدا │ 👩 تبدیل صدا با لحن زن
   `.tts`           │    `.ttsf`

👨 تبدیل صدا با لحن مرد│ 🗣 وویس صوتی سریع
   `.ttsm`          │    `.v`

📋 لیست صداهای هوشمند│ ⚙️ تنظیم صدای پیش‌فرض
   `.vl`            │    `.sv`

🎨 ساخت عکس با هوش  │ 🎭 تغییر دهنده صدا
   `.pgpt`          │    `.vc`

🌐 مدل جی‌پی‌تی ۳.۵  │ 🌐 مدل جی‌پی‌تی ۴
   `.gpt3`          │    `.gpt4`

🌐 دستیار هوش بارد  │ 🤖 هوش مصنوعی لئو مسی
   `.bard`          │    `.messi`

🤖 هوش رونالدو      │ 🚀 هوش ایلان ماسک
   `.ronaldo`       │    `.ilon`"""

enhelp21 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: AI Assistant
╰━━━━━━━━━━━━━━━━━━━━━━╯

🤖 9Router Text AI   │ 🧠 AI Knowledge Teach
   `.ai`            │    `.ai learn`

💾 AI Memory Viewer  │ 🗑 Forget Memory Item
   `.ai memory`     │    `.ai forget`

🔄 Reset AI Context  │ ⚡️ Fast AI Route
   `.ai reset`      │    `.ai /fast`

🎯 Smart AI Route    │ 💻 Code Expert Route
   `.ai /smart`     │    `.ai /code`

🎙 Neural TTS Voice  │ 👩 Female Neural Voice
   `.tts`           │    `.ttsf`

👨 Male Neural Voice │ 🗣 Quick Voice Note
   `.ttsm`          │    `.v`

📋 List All Voices   │ ⚙️ Set Default Voice
   `.vl`            │    `.sv`

🎨 AI Image Creator  │ 🎭 Smart Voice Changer
   `.pgpt`          │    `.vc`

🌐 GPT-3.5 Engine    │ 🌐 GPT-4.0 Engine
   `.gpt3`          │    `.gpt4`

🌐 Google Bard AI    │ 🤖 Leo Messi Persona
   `.bard`          │    `.messi`

🤖 C. Ronaldo Persona│ 🚀 Elon Musk Persona
   `.ronaldo`       │    `.ilon`"""

fahelp22 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: عکس و حیوانات
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔞 عکس خاص مدل ۱    │ 🔞 عکس خاص مدل ۲
   `.nude`          │    `.nude2`

🔞 عکس خاص مدل ۳    │ 🔥 رسانه خاص اختصاصی
   `.nude3`         │    `.boob`

💃 رسانه یانگ زیبا  │ 💑 تصویر دونفره عاشقانه
   `.ayang`         │    `.couple`

🤖 چهره ربات تصادفی │ 🎨 پس‌زمینه تک‌رنگ
   `.robo`          │    `.color`

🔍 جستجوی عکس متنی │ 🌐 جستجوی عکس در بینگ
   `.pic`           │    `.bing`

🖼 عکس‌های آنسپلش   │ 📷 عکس رندوم روز
   `.uns`           │    `.photo`

📸 گالری عکس رندوم  │ ⚡️ عکس پیکاچو
   `.photos`        │    `.pikachu`

🐋 عکس نهنگ اقیانوس │ 🦊 عکس روباه وحشی ۱
   `.whale`         │    `.fox`

🦊 عکس روباه مدل ۲   │ 🐶 عکس سگ بامزه ۱
   `.foxx`          │    `.dog`

🐕 عکس سگ مدل ۲     │ 🐕 عکس سگ مدل ۳
   `.dogg`          │    `.doggg`

🐼 عکس خرس پاندا ۱  │ 🐼 عکس خرس پاندا ۲
   `.panda`         │    `.rpanda`

🦝 عکس راکون بامزه  │ 🐨 عکس کوآلای استرالیا
   `.raccoon`       │    `.koala`

🦘 عکس کانگورو جهنده│ 🐦 عکس پرندگان زیبا ۱
   `.kangroo`       │    `.bird`

🕊 عکس پرنده مدل ۲  │ 🐱 عکس گربه ملوس ۱
   `.birdd`         │    `.cat`

🐈 عکس گربه مدل ۲   │
   `.catt`          │"""

enhelp22 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Photo & Animals
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔞 Special Photo 1   │ 🔞 Special Photo 2
   `.nude`          │    `.nude2`

🔞 Special Photo 3   │ 🔥 Exclusive Media
   `.nude3`         │    `.boob`

💃 Ayang Media      │ 💑 Romantic Couple
   `.ayang`         │    `.couple`

🤖 Random Robot Face │ 🎨 Solid Color Screen
   `.robo`          │    `.color`

🔍 Search Any Photo  │ 🌐 Bing Photo Search
   `.pic`           │    `.bing`

🖼 Unsplash Photos   │ 📷 Random HD Photo
   `.uns`           │    `.photo`

📸 Photo Gallery     │ ⚡️ Pikachu Photo
   `.photos`        │    `.pikachu`

🐋 Ocean Whale Photo │ 🦊 Wild Fox Photo 1
   `.whale`         │    `.fox`

🦊 Wild Fox Photo 2  │ 🐶 Cute Puppy Dog 1
   `.foxx`          │    `.dog`

🐕 Cute Dog Photo 2  │ 🐕 Cute Dog Photo 3
   `.dogg`          │    `.doggg`

🐼 Giant Panda 1     │ 🐼 Giant Panda 2
   `.panda`         │    `.rpanda`

🦝 Cute Raccoon      │ 🐨 Australian Koala
   `.raccoon`       │    `.koala`

🦘 Jumping Kangaroo  │ 🐦 Beautiful Bird 1
   `.kangroo`       │    `.bird`

🕊 Bird Photo 2     │ 🐱 Sweet Cat Photo 1
   `.birdd`         │    `.cat`

🐈 Cat Photo 2      │
   `.catt`          │"""

fahelp23 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: موزیک
╰━━━━━━━━━━━━━━━━━━━━━━╯

🎵 جستجوی موزیک تلگرام│ 🎥 دریافت موزیک یوتیوب
   `.music`         │    `.youtube`

🎶 دیتابیس موزیک ۲   │ 🎛 دانلود موزیک ریمیکس
   `.musicc`        │    `.remix`

🎼 دانلود دمو کوتاه │ 🎻 موزیک‌های کلاسیک
   `.demo`          │    `.classic`

🎤 دانلود آهنگ روز   │ 🎧 سرچ ویس و ملوبات
   `.ahang`         │    `.melo`

🌍 سرچ موزیک بین‌المللی│
   `.global`        │"""

enhelp23 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: Music
╰━━━━━━━━━━━━━━━━━━━━━━╯

🎵 Search TG Music   │ 🎥 YouTube Music Track
   `.music`         │    `.youtube`

🎶 Music Database 2  │ 🎛 Remix Songs Track
   `.musicc`        │    `.remix`

🎼 Short Demo Track  │ 🎻 Classical Tracks
   `.demo`          │    `.classic`

🎤 Popular Songs     │ 🎧 Melobot Voice Search
   `.ahang`         │    `.melo`

🌍 Global Music Track│
   `.global`        │"""

fahelp24 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇮🇷 بخش: تنظیمات سیستم
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔄 ری‌استارت سلف‌بات │ 🛑 خاموش کردن سلف
   `.restart`       │    `.shutdown`

📶 تست پینگ و سرعت  │ 🟢 وضعیت آنلاین سلف
   `.ping`          │    `self`

📊 وضعیت ماژول‌ها    │ 💻 درصد مصرف CPU
   `.on_off_status` │    `.cpu`

🧠 درصد مصرف RAM سرور│ 🖥 مشخصات کامل سرور
   `.memory`        │    `.system-inf`"""

enhelp24 = """╭━━━ ⚡ TiTaN SelfSaz ━━━╮
┃ 🇬🇧 Section: System
╰━━━━━━━━━━━━━━━━━━━━━━╯

🔄 Restart Self Bot  │ 🛑 Shutdown Self Bot
   `.restart`       │    `.shutdown`

📶 Ping Response Time│ 🟢 Self ON Status
   `.ping`          │    `self`

📊 Modules Status    │ 💻 Server CPU Usage
   `.on_off_status` │    `.cpu`

🧠 Server RAM Usage  │ 🖥 Full System Hardware
   `.memory`        │    `.system-inf`"""



# ================= TITAN COMMANDS POPUP & BUTTONS DATABASE =================
# Comprehensive script to build the Hybrid Inline Button + 2-Column Grid Titan Panel in helper.py
import re

def build_data():
    # Define complete command database for all 24 categories
    # Structure: cat_key -> list of (cmd_id, fa_btn, en_btn, syntax, fa_popup, en_popup)
    DB = {
        "gp": [
            ("mute", "🔇 سکوت", "🔇 Mute", ".mute", "سکوت کردن کاربر در گروه\nنحوه استفاده: ریپلی روی پیام کاربر با .mute", "Mute user in group\nUsage: Reply to user with .mute"),
            ("unmute", "🔊 لغو سکوت", "🔊 Unmute", ".unmute", "لغو سکوت کاربر در گروه\nنحوه استفاده: ریپلی روی پیام کاربر با .unmute", "Unmute user in group\nUsage: Reply to user with .unmute"),
            ("allunmute", "🧹 پاکسازی سکوت", "🧹 Clear Mutes", ".allunmute", "پاکسازی لیست تمام کاربران میوت‌شده در چت", "Clear all muted users list in current chat"),
            ("block", "🚫 بلاک کاربر", "🚫 Block User", ".block", "مسدود کردن کاربر\nنحوه استفاده: ریپلی یا ارسال با ایدی عددی", "Block user from contacting you\nUsage: Reply or with ID"),
            ("unblock", "🔓 آنبلاک کاربر", "🔓 Unblock User", ".unblock", "رفع مسدودی کاربر در تلگرام", "Unblock user on Telegram"),
            ("setenemy", "☠️ ثبت دشمن", "☠️ Set Enemy", ".setenemy", "افزودن کاربر به لیست دشمنان (با ریپلی یا ایدی)", "Add user to enemy list (Reply or ID)"),
            ("delenemy", "🗑 حذف دشمن", "🗑 Del Enemy", ".delenemy", "حذف کاربر از لیست دشمنان", "Remove user from enemy list"),
            ("clearenemy", "🧹 پاکسازی دشمن", "🧹 Clear Enemies", ".clearenemy", "پاکسازی کامل لیست دشمنان", "Clear entire enemy list"),
            ("setlove", "❤️ ثبت عشق", "❤️ Set Love", ".setlove", "افزودن کاربر به لیست عشق (با ریپلی یا ایدی)", "Add user to love list (Reply or ID)"),
            ("dellove", "💔 حذف عشق", "💔 Del Love", ".dellove", "حذف کاربر از لیست عشق", "Remove user from love list"),
            ("clearlove", "🧹 پاکسازی عشق", "🧹 Clear Loves", ".clearlove", "پاکسازی کامل لیست عشق", "Clear entire love list"),
            ("monshi", "💬 منشی خودکار", "💬 Auto Monshi", ".monshi", "تنظیم متن منشی خودکار: .monshi متن", "Set auto monshi text: .monshi text"),
            ("monshioff", "🔕 خاموشی منشی", "🔕 Monshi Off", ".monshioff", "غیرفعال‌سازی منشی خودکار پیام‌ها", "Disable auto monshi responder"),
            ("afk", "🌙 حالت آفلاین", "🌙 AFK Mode", ".afk", "تنظیم پیام وضعیت آفلاین: .afk متن", "Set offline AFK message: .afk text"),
            ("unafk", "☀️ لغو آفلاین", "☀️ UnAFK", ".unafk", "خروج از وضعیت آفلاینی و فعال شدن اکانت", "Turn off AFK offline mode"),
            ("tagalert", "🔔 هشدار تگ", "🔔 Tag Alert", ".tagalert", "هشدار هنگام تگ شدن در گروه‌ها: .tagalert on/off", "Alert on mentions in chats: .tagalert on/off"),
            ("creatchannel", "📢 ساخت کانال", "📢 New Channel", ".creatchannel", "ساخت سریع کانال تلگرام: .creatchannel نام", "Create Telegram channel: .creatchannel name"),
            ("creatgroup", "👥 ساخت گروه", "👥 New Group", ".creatgroup", "ساخت سریع گروه تلگرام: .creatgroup نام", "Create Telegram group: .creatgroup name"),
            ("creatsupergroup", "👑 سوپرگروه", "👑 Supergroup", ".creatsupergroup", "تبدیل یا ساخت سوپرگروه: .creatsupergroup نام", "Create supergroup: .creatsupergroup name"),
            ("spam", "⚡️ اسپم پیام", "⚡️ Spam", ".spam", "ارسال اسپم: .spam تعداد متن", "Send spam: .spam count text"),
            ("slowspam", "🐢 اسپم آرام", "🐢 Slow Spam", ".slowspam", "اسپم با تاخیر زمانی آرام: .slowspam تعداد متن", "Send slow spam: .slowspam count text"),
            ("statspam", "👻 اسپم مخفی", "👻 Stat Spam", ".statspam", "ارسال اسپم همراه با حذف فوری: .statspam تعداد متن", "Spam with instant auto delete: .statspam count text"),
            ("fastspam", "🚀 اسپم سریع", "🚀 Fast Spam", ".fastspam", "ارسال اسپم فوق سریع و متوالی: .fastspam تعداد متن", "High-speed spam: .fastspam count text"),
            ("firstcom", "🥇 کامنت اول", "🥇 First Comment", ".firstcom", "ارسال خودکار کامنت اول کانال‌ها: .firstcom on/off", "Auto first comment on channels: .firstcom on/off"),
            ("first_message", "💬 متن کامنت اول", "💬 First Msg Text", ".first_message", "تنظیم متن کامنت اول کانال: .first_message متن", "Set first comment text: .first_message text"),
            ("text_time", "⏰ متن زماندار", "⏰ Timed Text", ".text_time", "ارسال متن در ساعت مشخص: .text_time HH:MM", "Send scheduled text: .text_time HH:MM"),
            ("photo_time", "📸 عکس زماندار", "📸 Timed Photo", ".photo_time", "ارسال عکس در ساعت مشخص: .photo_time HH:MM", "Send scheduled photo: .photo_time HH:MM"),
            ("text_send_time", "⏱ ریپلی زماندار", "⏱ Timed Reply", ".text_send_time", "ارسال ریپلی متنی زمانبندی‌شده", "Send timed reply message"),
            ("photo_send_time", "🖼 عکس ریپلی", "🖼 Timed Reply Pic", ".photo_send_time", "ارسال ریپلی تصویری زمانبندی‌شده", "Send timed reply photo"),
            ("answer", "🤖 پاسخ خودکار", "🤖 Auto Answer", ".answer", "فعال/غیرفعال کردن پاسخ خودکار: .answer on/off", "Toggle auto answer: .answer on/off"),
            ("addan", "➕ افزودن پاسخ", "➕ Add Answer", ".addan", "افزودن پاسخ خودکار: .addan سوال:جواب", "Add auto answer: .addan Q:A"),
            ("delan", "➖ حذف پاسخ", "➖ Del Answer", ".delan", "حذف پاسخ خودکار: .delan جواب", "Delete auto answer: .delan Answer"),
            ("anlist", "📋 لیست پاسخ‌ها", "📋 Answer List", ".anlist", "مشاهده لیست تمام پاسخ‌های خودکار فعال", "View list of all auto answers"),
            ("anclear", "🧹 پاکسازی پاسخ", "🧹 Clear Answers", ".anclear", "پاکسازی و حذف کامل لیست پاسخ‌های خودکار", "Clear all auto answers list"),
            ("welcome", "👋 خوشامدگویی", "👋 Welcome", ".welcome", "فعال‌سازی خوشامدگویی به اعضا: .welcome on/off", "Toggle welcome message: .welcome on/off"),
            ("welcome_add", "➕ تنظیم خوشامد", "➕ Set Welcome", ".welcome_add", "تنظیم متن خوشامدگویی: .welcome_add متن", "Set welcome text: .welcome_add text"),
            ("welcome_show", "👁 نمایش خوشامد", "👁 Show Welcome", ".welcome_show", "مشاهده متن پیام خوشامدگویی فعلی", "View current welcome message text"),
            ("welcome_reset", "🔄 ریست خوشامد", "🔄 Reset Welcome", ".welcome_reset", "بازنشانی متن خوشامدگویی به پیش‌فرض", "Reset welcome text to default"),
            ("ban", "⛔️ بن کاربر", "⛔️ Ban User", ".ban", "اخراج و بن کاربر از گروه (با ریپلی یا ایدی)", "Ban user from group (Reply or ID)"),
            ("unban", "❇️ آنبن کاربر", "❇️ Unban User", ".unban", "لغو بن و اجازه ورود کاربر (با ریپلی یا ایدی)", "Unban user in group (Reply or ID)"),
            ("setmute", "🔇 میوت چت", "🔇 Mute Chat", ".setmute", "بی‌صدا کردن کاربر در چت گروه (با ریپلی)", "Mute user in current chat (Reply)"),
            ("delmute", "🔊 آنمیوت چت", "🔊 Unmute Chat", ".delmute", "رفع بی‌صدایی کاربر در گروه (با ریپلی)", "Unmute user in current chat (Reply)"),
            ("setchatphoto", "🖼 عکس گروه", "🖼 Set Chat Photo", ".setchatphoto", "تنظیم عکس گروه یا کانال (با ریپلی روی عکس)", "Set group/channel photo (Reply to photo)"),
            ("setchattitle", "📝 نام گروه", "📝 Set Title", ".setchattitle", "تغییر نام گروه یا کانال: .setchattitle متن", "Set group title: .setchattitle text"),
            ("setchatbio", "📄 بیو گروه", "📄 Set Bio", ".setchatbio", "تغییر بیوگرافی چت: .setchatbio متن", "Set chat description: .setchatbio text"),
            ("setchatusername", "🔗 یوزرنیم چت", "🔗 Set Username", ".setchatusername", "تنظیم یوزرنیم عمومی چت: .setchatusername یوزر", "Set public chat username: .setchatusername username"),
            ("pin", "📌 پین پیام", "📌 Pin Msg", ".pin", "سنجاق و پین کردن پیام (با ریپلی روی پیام)", "Pin message in chat (Reply to msg)"),
            ("unpin", "📍 آنپین پیام", "📍 Unpin Msg", ".unpin", "برداشتن پین پیام (با ریپلی روی پیام)", "Unpin message in chat (Reply to msg)"),
            ("unpinall", "📍 آنپین همه", "📍 Unpin All", ".unpinall", "حذف تمام پیام‌های سنجاق‌شده در گروه", "Unpin all messages in chat"),
            ("deletechannel", "🗑 حذف کانال", "🗑 Del Channel", ".deletechannel", "حذف دائمی کانال: .deletechannel یوزرنیم", "Delete Telegram channel: .deletechannel username"),
            ("deletegroup", "🗑 حذف گروه", "🗑 Del Group", ".deletegroup", "حذف دائمی گروه: .deletegroup یوزرنیم", "Delete Telegram group: .deletegroup username"),
            ("delallmsguser", "🧹 پاکسازی پیام‌ها", "🧹 Del User Msgs", ".delallmsguser", "حذف تمام پیام‌های یک کاربر در چت (با ریپلی)", "Delete all messages of user in group (Reply)"),
            ("slowmod", "⏳ اسلومود چت", "⏳ Slowmode", ".slowmod", "تنظیم اسلومود چت: .slowmod ثانیه", "Set chat slowmode: .slowmod seconds"),
            ("delete", "❌ حذف چندتایی", "❌ Delete Count", ".delete", "حذف تعداد مشخص پیام: .delete تعداد", "Delete message count: .delete count"),
            ("tadmin", "👮 مدیران چت", "👮 Admins List", ".tadmin", "مشاهده لیست کامل ادمین‌های گروه", "View chat administrators list"),
            ("tagall", "📣 منشن همه", "📣 Tag All", ".tagall", "تگ و منشن کردن تمام اعضای گروه: .tagall متن", "Mention all group members: .tagall text"),
            ("cancel", "🛑 لغو دستورات", "🛑 Cancel", ".cancel", "لغو و متوقف کردن فرآیند تگ یا اسپم فعال", "Cancel active tagall or spam process"),
            ("delethistory", "🗑 حذف تاریخچه", "🗑 Clear History", ".delethistory", "پاکسازی کامل تاریخچه پیام‌های چت", "Clear chat message history"),
            ("del", "🗑 حذف تک پیام", "🗑 Delete Msg", ".del", "حذف سریع پیام مورد نظر (با ریپلی روی پیام)", "Quick delete message (Reply to msg)"),
        ],
        "profile": [
            ("setname", "👤 نام اول", "👤 First Name", ".setname", "تنظیم نام حساب کاربری: .setname متن", "Set profile first name: .setname text"),
            ("setlastname", "👥 نام خانوادگی", "👥 Last Name", ".setlastname", "تنظیم نام خانوادگی حساب: .setlastname متن", "Set profile last name: .setlastname text"),
            ("setbio", "📝 بیوگرافی", "📝 Biography", ".setbio", "تنظیم متن بیوگرافی پروفایل: .setbio متن", "Set profile biography: .setbio text"),
            ("fontname", "🔤 فونت خودکار", "🔤 Auto Font", ".fontname", "اعمال فونت شیک خودکار روی نام: .fontname on/off", "Auto font on name: .fontname on/off"),
            ("timename", "⏰ ساعت اسم ۱", "⏰ Clock Name 1", ".timename", "ساعت دیجیتال خودکار روی نام ۱: .timename on/off", "Auto digital clock on name 1: .timename on/off"),
            ("2timename", "⏰ ساعت اسم ۲", "⏰ Clock Name 2", ".2timename", "ساعت دیجیتال روی نام مدل ۲: .2timename on/off", "Auto clock on name mode 2: .2timename on/off"),
            ("timebio", "🕒 ساعت بیو ۱", "🕒 Clock Bio 1", ".timebio", "ساعت خودکار روی بیو مدل ۱: .timebio on/off", "Auto clock on bio mode 1: .timebio on/off"),
            ("2timebio", "🕒 ساعت بیو ۲", "🕒 Clock Bio 2", ".2timebio", "ساعت خودکار روی بیو مدل ۲: .2timebio on/off", "Auto clock on bio mode 2: .2timebio on/off"),
            ("3timebio", "🕒 ساعت بیو ۳", "🕒 Clock Bio 3", ".3timebio", "ساعت خودکار روی بیو مدل ۳: .3timebio on/off", "Auto clock on bio mode 3: .3timebio on/off"),
            ("4timebio", "🕒 ساعت بیو ۴", "🕒 Clock Bio 4", ".4timebio", "ساعت خودکار روی بیو مدل ۴: .4timebio on/off", "Auto clock on bio mode 4: .4timebio on/off"),
            ("5timebio", "🕒 ساعت بیو ۵", "🕒 Clock Bio 5", ".5timebio", "ساعت خودکار روی بیو مدل ۵: .5timebio on/off", "Auto clock on bio mode 5: .5timebio on/off"),
            ("6timebio", "🕒 ساعت بیو ۶", "🕒 Clock Bio 6", ".6timebio", "ساعت خودکار روی بیو مدل ۶: .6timebio on/off", "Auto clock on bio mode 6: .6timebio on/off"),
            ("setprofile", "🖼 تنظیم عکس", "🖼 Set Profile", ".setprofile", "تنظیم عکس پروفایل (با ریپلی روی عکس)", "Set profile photo (Reply to photo)"),
            ("delprofile", "🗑 حذف عکس", "🗑 Del Profile", ".delprofile", "حذف آخرین عکس پروفایل اکانت", "Delete current profile photo"),
            ("autopic", "🤖 پروفایل خودکار ۱", "🤖 Auto Pic 1", ".autopic", "تغییر خودکار عکس پروفایل با زمان مدل ۱", "Auto dynamic profile photo mode 1"),
            ("2autopic", "🤖 پروفایل خودکار ۲", "🤖 Auto Pic 2", ".2autopic", "تغییر خودکار عکس پروفایل با زمان مدل ۲", "Auto dynamic profile photo mode 2"),
            ("3autopic", "🤖 پروفایل خودکار ۳", "🤖 Auto Pic 3", ".3autopic", "تغییر خودکار عکس پروفایل با زمان مدل ۳", "Auto dynamic profile photo mode 3"),
            ("4autopic", "🤖 پروفایل خودکار ۴", "🤖 Auto Pic 4", ".4autopic", "تغییر خودکار عکس پروفایل با زمان مدل ۴", "Auto dynamic profile photo mode 4"),
        ],
        "downloader": [
            ("iginfo", "📸 مشخصات اینستا", "📸 Insta Info", ".iginfo", "دریافت اطلاعات پیج اینستاگرام: .iginfo یوزرنیم", "Get Instagram user profile info: .iginfo user"),
            ("igdl", "📥 دانلود اینستا", "📥 Insta DL", ".igdl", "دانلود پست و ریلز اینستاگرام: .igdl لینک", "Download Instagram post/reel: .igdl URL"),
            ("down", "🌐 دانلود همه‌کاره", "🌐 Universal DL", ".down", "دانلود مدیا از شبکه‌های اجتماعی: .down لینک", "Download social media media: .down URL"),
            ("youtube", "🎥 دانلود یوتیوب", "🎥 YouTube DL", ".youtube", "جستجو و دانلود از یوتیوب: .youtube نام_ویدیو", "Search & DL from YouTube: .youtube name"),
            ("app", "📱 جستجوی اپلیکیشن", "📱 App Search", ".app", "جستجوی برنامه در استور: .app نام", "Search app store: .app name"),
            ("apk", "📦 دانلود مستقیم APK", "📦 Direct APK DL", ".apk", "دانلود مستقیم فایل نصبی: .apk نام", "Download APK directly: .apk name"),
        ],
        "uploader": [
            ("neko", "☁️ آپلود نکو", "☁️ Neko Upload", ".neko", "آپلود فایل در سرور نکو (با ریپلی روی فایل)", "Upload file to Neko server (Reply)"),
            ("telegraph", "📄 آپلود تلگراف", "📄 Telegraph", ".telegraph", "آپلود عکس در تلگراف (با ریپلی روی عکس)", "Upload photo to Telegraph (Reply)"),
        ],
        "textmode": [
            ("bold", "🔲 متن بولد", "🔲 Bold Text", ".bold", "حالت متن ضخیم: .bold on/off", "Bold text mode: .bold on/off"),
            ("spoiler", "🙈 متن اسپویلر", "🙈 Spoiler Text", ".spoiler", "حالت متن مخفی: .spoiler on/off", "Spoiler text mode: .spoiler on/off"),
            ("italic", "✍️ متن ایتالیک", "✍️ Italic Text", ".italic", "حالت متن کج: .italic on/off", "Italic text mode: .italic on/off"),
            ("code", "💻 فونت کد", "💻 Code Font", ".code", "حالت فونت کدنویسی: .code on/off", "Monospace code font: .code on/off"),
            ("underline", "➖ خط زیرین", "➖ Underline", ".underline", "حالت خط زیر متن: .underline on/off", "Underline text mode: .underline on/off"),
            ("strike", "<s> خط روی متن </s>", "<s> Strike </s>", ".strike", "حالت خط روی متن: .strike on/off", "Strikethrough text mode: .strike on/off"),
            ("emoji", "😀 ایموجی خودکار", "😀 Auto Emoji", ".emoji", "افزودن خودکار ایموجی به پیام: .emoji on/off", "Auto emoji on messages: .emoji on/off"),
            ("quote", "💬 نقل قول خودکار", "💬 Auto Quote", ".quote", "حالت نقل قول: .quote on/off", "Auto quote text mode: .quote on/off"),
            ("mention", "📢 منشن خودکار", "📢 Auto Mention", ".mention", "حالت منشن کردن: .mention on/off", "Auto mention mode: .mention on/off"),
            ("setreact", "💖 تنظیم ری‌اکشن", "💖 Set Reaction", ".setreact", "تنظیم ری‌اکشن خودکار: .setreact ایموجی (با ریپلی)", "Set auto reaction: .setreact emoji (Reply)"),
            ("delreact", "🗑 حذف ری‌اکشن", "🗑 Del Reaction", ".delreact", "حذف ری‌اکشن تنظیم‌شده روی پیام", "Delete configured reaction (Reply)"),
            ("reactlist", "📋 لیست ری‌اکشن‌ها", "📋 Reaction List", ".reactlist", "مشاهده لیست ری‌اکشن‌های فعال", "View list of active reactions"),
            ("lad", "🪜 متن نردبانی", "🪜 Ladder Text", ".lad", "نوشتن متن به صورت نردبانی: .lad متن", "Create ladder style text: .lad text"),
        ],
        "actionmode": [
            ("typing", "⌨️ تایپینگ", "⌨️ Typing", ".typing", "اکشن در حال نوشتن...: .typing on/off", "Typing action state: .typing on/off"),
            ("playing", "🎮 بازی", "🎮 Playing", ".playing", "اکشن در حال بازی...: .playing on/off", "Playing game action: .playing on/off"),
            ("record_vid", "📹 ضبط ویدیو", "📹 Record Video", ".record_vid", "اکشن ضبط ویدیو: .record_vid on/off", "Recording video action: .record_vid on/off"),
            ("choose_sticker", "🎭 انتخاب استیکر", "🎭 Sticker", ".choose_sticker", "اکشن انتخاب استیکر: .choose_sticker on/off", "Choosing sticker action: .choose_sticker on/off"),
            ("upload_vid", "📤 آپلود ویدیو", "📤 Upload Video", ".upload_vid", "اکشن آپلود ویدیو: .upload_vid on/off", "Uploading video action: .upload_vid on/off"),
            ("upload_doc", "📄 آپلود فایل", "📄 Upload Doc", ".upload_doc", "اکشن آپلود سند و فایل: .upload_doc on/off", "Uploading doc action: .upload_doc on/off"),
            ("upload_audio", "🎵 آپلود صدا", "🎵 Upload Audio", ".upload_audio", "اکشن آپلود صوت و موزیک: .upload_audio on/off", "Uploading audio action: .upload_audio on/off"),
            ("speaking", "🎙 ضبط وویس", "🎙 Recording Voice", ".speaking", "اکشن ضبط صدا: .speaking on/off", "Recording voice note: .speaking on/off"),
            ("online", "🟢 آنلاین دائم", "🟢 Always Online", ".online", "حالت آنلاین همیشگی سلف: .online on/off", "Always online status: .online on/off"),
            ("offline", "⚫️ آفلاین دائم", "⚫️ Always Offline", ".offline", "حالت آفلاین همیشگی سلف: .offline on/off", "Always offline status: .offline on/off"),
        ],
        "webhook": [
            ("setwebhook", "🔗 تنظیم وبهوک", "🔗 Set Webhook", ".setwebhook", "تنظیم وبهوک ربات: .setwebhook توکن لینک", "Set bot webhook: .setwebhook Token URL"),
            ("delwebhook", "🗑 حذف وبهوک", "🗑 Del Webhook", ".delwebhook", "حذف وبهوک ربات: .delwebhook توکن", "Delete bot webhook: .delwebhook Token"),
            ("delupdate", "🧹 حذف آپدیت‌ها", "🧹 Del Updates", ".delupdate", "حذف آپدیت‌های معلق ربات: .delupdate توکن", "Delete pending updates: .delupdate Token"),
            ("webhookinfo", "ℹ️ مشخصات وبهوک", "ℹ️ Webhook Info", ".webhookinfo", "دریافت وضعیت و مشخصات وبهوک: .webhookinfo توکن", "Get webhook status info: .webhookinfo Token"),
            ("botinfo", "🤖 اطلاعات کامل ربات", "🤖 Bot Info", ".botinfo", "مشخصات فنی و وضعیت ربات: .botinfo توکن", "Get full Telegram bot info: .botinfo Token"),
        ],
        "locks": [
            ("pvlock", "🔒 قفل پیوی", "🔒 PV Lock", ".pvlock", "قفل امنیتی پیوی سلف‌بات: .pvlock on/off", "PV security protection lock: .pvlock on/off"),
            ("monshi2", "🛡 جوین اجباری", "🛡 Forced Join", ".monshi2", "منشی عضویت اجباری ۲: .monshi2 on/off", "Monshi2 forced channel join: .monshi2 on/off"),
            ("hlock", "📖 راهنمای قفل", "📖 Locks Guide", ".hlock", "مشاهده راهنمای کامل قفل‌های هلپر", "View complete helper locks guide"),
            ("locks", "📋 لیست قفل‌ها", "📋 All Locks", ".locks", "مشاهده لیست تمام قفل‌های چت گروه", "View all group chat locks status"),
            ("lock", "🔐 قفل آیتم", "🔐 Lock Item", ".lock", "قفل کردن مورد دلخواه: .lock نام_قفل", "Lock specific item: .lock item_name"),
            ("unlock", "🔓 باز کردن آیتم", "🔓 Unlock Item", ".unlock", "باز کردن قفل مورد: .unlock نام_قفل", "Unlock specific item: .unlock item_name"),
            ("lock_all", "🔒 قفل همه موارد", "🔒 Lock All", ".lock all", "قفل کردن تمامی دسترسی‌های گروه", "Lock all group permissions"),
            ("unlock_all", "🔓 باز کردن همه", "🔓 Unlock All", ".unlock all", "باز کردن تمامی قفل‌های گروه", "Unlock all group permissions"),
        ],
        "cronjob": [
            ("cron", "⏱ اجرای کرون جاب", "⏱ Run Cron Job", ".cron", "اجرای زمانبندی کرون جاب: .cron لینک زمان", "Run scheduled cron job: .cron URL Time"),
        ],
        "antilogin": [
            ("antilog", "🛡 آنتی لاگین", "🛡 Anti-Login", ".antilog", "سیستم امنیتی ضد ورود غیرمجاز سشن: .antilog on/off", "Anti unauthorized login security: .antilog on/off"),
        ],
        "tabchi": [
            ("tabchi_status", "📊 وضعیت تبچی", "📊 Tabchi Status", ".tabchi status", "مشاهده گزارش و وضعیت تبچی تبلیغاتی", "View Tabchi status summary"),
            ("tabchipv", "📩 ارسال پیوی", "📩 PV Auto Send", ".tabchipv", "ارسال خودکار در پیوی‌ها: .tabchipv on/off", "Auto send in PV: .tabchipv on/off"),
            ("tabchigp", "👥 ارسال گروه", "👥 GP Auto Send", ".tabchigp", "ارسال خودکار در گروه‌ها: .tabchigp on/off", "Auto send in Groups: .tabchigp on/off"),
            ("setbannerpv", "🖼 بنر پیوی", "🖼 Set Banner PV", ".setbannerpv", "تنظیم بنر تبلیغاتی پیوی: .setbannerpv متن", "Set PV ad banner: .setbannerpv text"),
            ("setbannergp", "🖼 بنر گروه", "🖼 Set Banner GP", ".setbannergp", "تنظیم بنر تبلیغاتی گروه: .setbannergp متن", "Set GP ad banner: .setbannergp text"),
            ("settimerpv", "⏱ تایمر پیوی", "⏱ PV Timer", ".settimerpv", "ثانیه تاخیر ارسال پیوی: .settimerpv ثانیه", "Set PV send timer: .settimerpv sec"),
            ("settimergp", "⏱ تایمر گروه", "⏱ GP Timer", ".settimergp", "ثانیه تاخیر ارسال گروه: .settimergp ثانیه", "Set GP send timer: .settimergp sec"),
            ("sendpv", "📤 ارسال دستی پیوی", "📤 Send PV", ".sendpv", "ارسال فوری بنر به چت‌های پیوی", "Send banner manually to PVs"),
            ("sendgp", "📤 ارسال دستی گروه", "📤 Send GP", ".sendgp", "ارسال فوری بنر به گروه‌ها", "Send banner manually to groups"),
            ("setbannersender", "👤 بنر فرستنده", "👤 Sender Banner", ".setbannersender", "تنظیم بنر فرستنده تبلیغاتی: .setbannersender متن", "Set sender ad banner: .setbannersender text"),
            ("sendall", "📢 ارسال به همه", "📢 Send All", ".sendall", "ارسال سراسری به مخاطبان: .sendall یوزر", "Send broadcast to all: .sendall user"),
            ("invitelink", "🔗 لینک دعوت", "🔗 Invite Link", ".invitelink", "دریافت لینک دعوت چت", "Get group invite link"),
            ("join", "🚪 عضویت در لینک", "🚪 Join Link", ".join", "عضویت در گروه با لینک: .join لینک", "Join chat via link: .join link"),
            ("leave", "🚶 خروج از لینک", "🚶 Leave Link", ".leave", "خروج از گروه با لینک: .leave لینک", "Leave chat via link: .leave link"),
            ("leaveallgc", "🏃 خروج از همه گروه‌ها", "🏃 Leave Groups", ".leaveallgc", "خروج سراسری از تمام گروه‌های تلگرام", "Leave all Telegram groups"),
            ("leaveallch", "🏃 خروج از همه کانال‌ها", "🏃 Leave Channels", ".leaveallch", "خروج سراسری از تمام کانال‌های تلگرام", "Leave all Telegram channels"),
        ],
        "photoeditor": [
            ("kanna", "👧 توییت کانّا", "👧 Kanna Tweet", ".kanna", "توییت انیمه کانّا: .kanna متن", "Kanna anime tweet: .kanna text"),
            ("clyde", "🤖 توییت کلاید", "🤖 Clyde Tweet", ".clyde", "توییت ربات کلاید دیسکورد: .clyde متن", "Discord Clyde bot tweet: .clyde text"),
            ("write", "📝 نوشتن روی کاغذ", "📝 Note Paper", ".write", "نوشتن متن روی برگه کاغذ: .write متن", "Write text on paper note: .write text"),
            ("mind", "💭 میم تغییر نظر", "💭 Change Mind", ".mind", "میم تغییر نظر Change My Mind: .mind متن", "Change My Mind meme: .mind text"),
            ("trump", "👔 توییت ترامپ", "👔 Trump Tweet", ".trump", "توییت فیک دونالد ترامپ: .trump متن", "Donald Trump tweet: .trump text"),
            ("o", "📜 دستخط تیتان ۱", "📜 Titan Note 1", ".o", "دستخط ویژه استایل تیتان: .o متن", "Titan handwritten note 1: .o text"),
            ("o2", "📜 دستخط تیتان ۲", "📜 Titan Note 2", ".o2", "دستخط استایل تیتان مدل دوم: .o2 متن", "Titan handwritten note 2: .o2 text"),
            ("bish", "💬 توییت دیسکورد", "💬 Discord Tweet", ".bish", "توییت شیک استایل دیسکورد: .bish متن", "Discord style tweet: .bish text"),
            ("latex", "📐 فرمول لاتک", "📐 LaTeX Math", ".latex", "رندر فرمول ریاضی با زبان لاتک: .latex فرمول", "Render LaTeX math equation: .latex eq"),
            ("blue", "🔵 فیلتر آبی", "🔵 Blue Filter", ".blue", "اعمال فیلتر تم آبی روی تصویر (با ریپلی)", "Apply blue filter to photo (Reply)"),
            ("green", "🟢 فیلتر سبز", "🟢 Green Filter", ".green", "اعمال فیلتر تم سبز روی تصویر (با ریپلی)", "Apply green filter to photo (Reply)"),
            ("red", "🔴 فیلتر قرمز", "🔴 Red Filter", ".red", "اعمال فیلتر تم قرمز روی تصویر (با ریپلی)", "Apply red filter to photo (Reply)"),
            ("grey", "⚪️ فیلتر خاکستری ۱", "⚪️ Grey Filter 1", ".grey", "فیلتر سیاه‌سفید روی تصویر (با ریپلی)", "Apply black & white filter (Reply)"),
            ("grey2", "⚪️ فیلتر خاکستری ۲", "⚪️ Grey Filter 2", ".grey2", "فیلتر سیاه‌سفید مدل دوم (با ریپلی)", "Apply grey filter mode 2 (Reply)"),
            ("sepia", "📜 فیلتر سپیا", "📜 Sepia Filter", ".sepia", "اعمال فیلتر نوستالژیک سپیا (با ریپلی)", "Apply vintage sepia filter (Reply)"),
            ("threshold", "🔲 فیلتر ترشولد", "🔲 Threshold", ".threshold", "فیلتر کنتراست شدید سیاه و سفید (با ریپلی)", "Apply threshold filter (Reply)"),
            ("blurple", "🟣 فیلتر بنفش", "🟣 Blurple", ".blurple", "اعمال فیلتر بنفش بلورپل دیسکورد (با ریپلی)", "Apply blurple filter (Reply)"),
            ("filter", "💡 فیلتر نوری", "💡 Light Filter", ".filter", "اعمال فیلتر نوری جذاب روی عکس (با ریپلی)", "Apply light filter to photo (Reply)"),
            ("bisexual", "🌈 افکت بای‌سکشوال", "🌈 Bisexual Effect", ".bisexual", "افکت رنگین بای‌سکشوال روی چهره (با ریپلی)", "Apply bisexual face effect (Reply)"),
            ("blur", "🌫 افکت تاری", "🌫 Blur Effect", ".blur", "مات و بلور کردن تصویر (با ریپلی)", "Blur photo (Reply)"),
            ("horny", "😈 افکت شاخ دار", "😈 Horny Effect", ".horny", "افکت شاخ کارتونی روی چهره (با ریپلی)", "Apply horn effect to face (Reply)"),
            ("stupid", "🤪 افکت احمق", "🤪 Stupid Effect", ".stupid", "افکت طنز چهره احمق (با ریپلی)", "Apply stupid face effect (Reply)"),
            ("lesbian", "👩‍❤️‍👩 افکت لزبین", "👩‍❤️‍👩 Lesbian Effect", ".lesbian", "افکت رنگی لزبین روی چهره (با ریپلی)", "Apply lesbian color effect (Reply)"),
            ("lgbt", "🏳️‍🌈 افکت رنگین‌کمان", "🏳️‍🌈 LGBT Effect", ".lgbt", "افکت رنگین‌کمانی روی تصویر (با ریپلی)", "Apply rainbow LGBT effect (Reply)"),
            ("lolice", "👮 پلیس انیمه", "👮 Lolice Effect", ".lolice", "افکت پلیس لولی انیمه (با ریپلی)", "Apply lolice anime effect (Reply)"),
            ("non", "👤 بدون چهره", "👤 No Face", ".non", "افکت محو کردن چهره روی عکس (با ریپلی)", "Apply no-face effect (Reply)"),
            ("psexual", "💖 پان‌سکشوال", "💖 Psexual Effect", ".psexual", "افکت رنگی پان‌سکشوال روی چهره (با ریپلی)", "Apply pansexual effect (Reply)"),
            ("pixel", "👾 افکت پیکسلی", "👾 Pixel Effect", ".pixel", "پیکسلی و شطرنجی کردن عکس (با ریپلی)", "Pixelate photo effect (Reply)"),
            ("simp", "🥺 افکت سیمپ", "🥺 Simp Effect", ".simp", "افکت چهره مظلوم سیمپ (با ریپلی)", "Apply simp face effect (Reply)"),
            ("spin", "🌀 افکت چرخشی", "🌀 Spin Effect", ".spin", "افکت چرخش و سرگیجه تصویر (با ریپلی)", "Apply spin rotation effect (Reply)"),
            ("toni", "🦾 تونی استارک", "🦾 Toni Stark", ".toni", "افکت مرد آهنی تونی استارک (با ریپلی)", "Apply Iron Man Toni Stark effect (Reply)"),
            ("comrade", "☭ رفیق کمونیست", "☭ Comrade Effect", ".comrade", "افکت پرچم سرخ شوروی (با ریپلی)", "Apply Soviet comrade effect (Reply)"),
            ("gay", "👨‍❤️‍👨 افکت گی", "👨‍❤️‍👨 Gay Effect", ".gay", "افکت رنگین روی چهره (با ریپلی)", "Apply gay color effect (Reply)"),
            ("glass", "🪟 افکت شیشه‌ای", "🪟 Glass Effect", ".glass", "افکت بافت شیشه روی عکس (با ریپلی)", "Apply glass texture effect (Reply)"),
            ("jail", "⛓ افکت زندان", "⛓ Jail Effect", ".jail", "افکت میله‌های زندان روی چهره (با ریپلی)", "Apply jail bars effect (Reply)"),
            ("wasted", "☠️ افکت جی‌تی‌ای", "☠️ Wasted GTA", ".wasted", "افکت باخت بازی GTA Wasted (با ریپلی)", "Apply GTA Wasted effect (Reply)"),
            ("pass", "🛂 افکت پاسپورت", "🛂 Passport Photo", ".pass", "افکت فریم پاسپورت روی عکس (با ریپلی)", "Apply passport photo frame (Reply)"),
        ],
        "marker": [
            ("logo", "🎨 ساخت لوگو ۱", "🎨 Logo Maker 1", ".logo", "ساخت لوگو گرافیکی: .logo متن", "Create graphic logo 1: .logo text"),
            ("logo2", "🎨 ساخت لوگو ۲", "🎨 Logo Maker 2", ".logo2", "ساخت لوگو گرافیکی مدل دوم: .logo2 متن", "Create graphic logo 2: .logo2 text"),
            ("lg", "🖌 لوگو سفارشی", "🖌 Custom Logo", ".lg", "ساخت لوگو با استایل دلخواه: .lg متن مدل", "Create custom logo: .lg text mode"),
            ("gif", "🎬 ساخت گیف ۱", "🎬 Text GIF 1", ".gif", "ساخت گیف متحرک متنی: .gif متن", "Create text animated GIF 1: .gif text"),
            ("giff", "🎬 ساخت گیف ۲", "🎬 Text GIF 2", ".giff", "ساخت گیف متحرک مدل دوم: .giff متن", "Create text animated GIF 2: .giff text"),
        ],
        "compiler": [
            ("py", "🐍 کامپایل پایتون", "🐍 Python Code", ".py", "اجرای آنلاین کد پایتون (با ریپلی روی کد)", "Run Python code online (Reply)"),
            ("js", "🟨 کامپایل جاوااسکریپت", "🟨 JavaScript Code", ".js", "اجرای کد جاوااسکریپت Node.js (با ریپلی)", "Run JavaScript Node.js code (Reply)"),
            ("php", "🐘 کامپایل پی‌اچ‌پی", "🐘 PHP Code", ".php", "اجرای آنلاین کد PHP (با ریپلی)", "Run PHP code online (Reply)"),
            ("kotlin", "📱 کامپایل کاتلین", "📱 Kotlin Code", ".kotlin", "اجرای آنلاین کد Kotlin (با ریپلی)", "Run Kotlin code online (Reply)"),
            ("go", "🔷 کامپایل زبان گو", "🔷 Golang Code", ".go", "اجرای آنلاین کد Golang (با ریپلی)", "Run Golang code online (Reply)"),
            ("java", "☕️ کامپایل جاوا", "☕️ Java Code", ".java", "اجرای آنلاین کد Java (با ریپلی)", "Run Java code online (Reply)"),
            ("lua", "🌙 کامپایل لوآ", "🌙 Lua Code", ".lua", "اجرای آنلاین کد Lua (با ریپلی)", "Run Lua code online (Reply)"),
            ("exec", "⚡️ اجرای شل لینوکس", "⚡️ Shell Exec", ".exec", "اجرای مستقیم دستور در سرور لینوکس: .exec دستور", "Execute direct shell command: .exec command"),
        ],
        "tools": [
            ("unzip", "📦 استخراج زیپ", "📦 Unzip Archive", ".unzip", "استخراج فایل‌های فشرده ZIP (با ریپلی)", "Extract ZIP archive (Reply)"),
            ("rname", "✏️ تغییر نام فایل", "✏️ Rename File", ".rname", "تغییر نام فایل یا آهنگ: .rname نام", "Rename file/audio: .rname name"),
            ("check", "📱 استعلام شماره", "📱 Number Check", ".check", "استعلام اپراتور و کشور شماره: .check شماره", "Check virtual phone number: .check number"),
            ("q", "💬 ساخت کووت", "💬 Quotly Sticker", ".q", "ساخت استیکر کووت از پیام (با ریپلی)", "Create quotly sticker (Reply)"),
            ("qq", "💭 کووت پیشرفته", "💭 Custom Quote", ".qq", "ساخت کووت با متن دلخواه: .qq متن", "Create advanced quotly: .qq text"),
            ("cricket", "🏏 نتیجه زنده", "🏏 Cricket Score", ".cricket", "مشاهده نتایج زنده ورزشی", "View live sports match scores"),
            ("weather", "🌤 وضعیت آب و هوا", "🌤 Weather Forecast", ".weather", "پیش‌بینی آب و هوای شهر: .weather شهر", "Weather forecast: .weather city"),
            ("azan", "🕋 اوقات شرعی", "🕋 Azan Times", ".azan", "اوقات شرعی و اذان: .azan شهر", "Prayer & Azan times: .azan city"),
            ("t", "🌡 تبدیل دما", "🌡 Temperature", ".t", "تبدیل دما سانتیگراد/فارنهایت: .t عدد c/f", "Temperature converter: .t num c/f"),
            ("c", "💱 تبدیل ارز", "💱 Currency Calc", ".c", "ماشین حساب تبدیل ارزها: .c مقدار ارز۱ ارز۲", "Currency converter calculator: .c amount cur1 cur2"),
            ("e", "🧮 ماشین حساب", "🧮 Calculator", ".e", "محاسبه عبارات ریاضی: .e عبارت", "Evaluate math equation: .e eq"),
            ("ip", "🌐 اطلاعات آی‌پی", "🌐 IP Info", ".ip", "استعلام آی‌پی و دامین: .ip آدرس", "IP & domain lookup: .ip domain"),
            ("whoisip", "🔍 هوایز سرور", "🔍 Whois Server", ".whoisip", "اطلاعات هاست و سرور: .whoisip آی‌پی", "Server whois info: .whoisip IP"),
            ("link", "🔗 کوتاه لینک ۱", "🔗 Short Link 1", ".link", "کوتاه کننده لینک اینترنتی: .link آدرس", "Shorten URL 1: .link URL"),
            ("link2", "🔗 کوتاه لینک ۲", "🔗 Short Link 2", ".link2", "کوتاه کننده لینک مدل دوم: .link2 آدرس", "Shorten URL 2: .link2 URL"),
            ("p", "📶 پینگ هاست", "📶 Ping Host", ".p", "تست پینگ هاست و دامنه: .p آدرس", "Ping host/domain: .p domain"),
            ("ping", "⚡️ پینگ سرور", "⚡️ Server Ping", ".ping", "تست سرعت و پینگ ربات سلف: .ping", "Server response ping: .ping"),
            ("shot", "📸 اسکرین‌شات ۱", "📸 Screenshot 1", ".shot", "عکس از وب‌سایت: .shot آدرس", "Web screenshot: .shot URL"),
            ("screenshot", "📸 اسکرین‌شات ۲", "📸 Screenshot 2", ".screenshot", "اسکرین‌شات کامل وب‌سایت: .screenshot آدرس", "Full web screenshot: .screenshot URL"),
            ("screenshot2", "📸 اسکرین‌شات ۳", "📸 Screenshot 3", ".screenshot2", "اسکرین‌شات با کیفیت بالا: .screenshot2 آدرس", "HQ screenshot: .screenshot2 URL"),
            ("screenshot3", "📸 اسکرین‌شات ۴", "📸 Screenshot 3", ".screenshot3", "اسکرین‌شات موبایل سایت: .screenshot3 آدرس", "Mobile screenshot: .screenshot3 URL"),
            ("screenshot4", "📸 اسکرین‌شات ۵", "📸 Screenshot 4", ".screenshot4", "اسکرین‌شات تبلت سایت: .screenshot4 آدرس", "Tablet screenshot: .screenshot4 URL"),
            ("github", "🐙 جستجوی گیت‌هاب", "🐙 GitHub User", ".github", "مشخصات پروفایل گیت‌هاب: .github یوزر", "GitHub user profile: .github user"),
            ("git", "📁 مخزن سورس گیت", "📁 Git Repo", ".git", "جستجوی ریپازیتوری در گیت‌هاب: .git نام", "Search GitHub repos: .git name"),
            ("dict", "📖 دیکشنری لغات", "📖 Dictionary", ".dict", "ترجمه و معنی لغات: .dict کلمه", "Word dictionary translation: .dict word"),
            ("clone", "👥 کلون اکانت", "👥 Clone Profile", ".clone", "کپی کامل پروفایل، نام و بیو اکانت (با ریپلی)", "Clone profile, name and bio (Reply)"),
            ("i", "👤 مشخصات اکانت", "👤 Account Info", ".i", "اطلاعات کامل اکانت تلگرام (با ریپلی)", "Full Telegram account info (Reply)"),
            ("creation", "📅 تاریخ ساخت", "📅 Creation Date", ".creation", "تخمین سال و تاریخ ساخت اکانت تلگرام", "Estimate Telegram account creation date"),
            ("limit", "⚠️ بررسی لیمیت", "⚠️ Check Limit", ".limit", "بررسی لیمیت دیلیت اکانت تلگرام", "Check Telegram account deletion limit"),
            ("country", "🌍 مشخصات کشور", "🌍 Country Info", ".country", "اطلاعات جغرافیایی کشورها: .country نام", "Geographic country info: .country name"),
            ("ts", "🖼 تصویر به استیکر", "🖼 Photo to Sticker", ".ts", "تبدیل عکس به استیکر تلگرام (با ریپلی)", "Convert photo to sticker (Reply)"),
            ("tg", "🎭 استیکر به تصویر", "🎭 Sticker to Photo", ".tg", "تبدیل استیکر تلگرام به عکس (با ریپلی)", "Convert sticker to photo (Reply)"),
            ("fa", "🇮🇷 ترجمه به فارسی", "🇮🇷 To Persian", ".fa", "ترجمه متن به فارسی روان: .fa متن", "Translate text to Persian: .fa text"),
            ("en", "🇬🇧 ترجمه به انگلیسی", "🇬🇧 To English", ".en", "ترجمه متن به انگلیسی: .en متن", "Translate text to English: .en text"),
            ("movie", "🎬 جستجوی فیلم", "🎬 Movie Search", ".movie", "مشخصات و ژانر فیلم و سریال: .movie نام", "Search movie info: .movie name"),
            ("anim", "🍿 جستجوی انیمه", "🍿 Anime Search", ".anim", "مشخصات انیمیشن و انیمه: .anim نام", "Search anime info: .anim name"),
            ("pass", "🔑 ساخت پسورد", "🔑 Password Gen", ".pass", "تولید پسورد تصادفی امن: .pass تعداد", "Generate secure random password: .pass length"),
            ("morset", "📡 تبدیل به مورس", "📡 Text to Morse", ".morset", "تبدیل متن به کد مورس: .morset متن", "Convert text to Morse code: .morset text"),
            ("unmorset", "📡 رمزگشایی مورس", "📡 Decode Morse", ".unmorset", "ترجمه کد مورس به متن: .unmorset کد", "Decode Morse code to text: .unmorset code"),
            ("date", "🗓 تاریخ روز", "🗓 Date Info", ".date", "نمایش تقویم روز شمسی، قمری و میلادی", "Show solar, lunar and gregorian date"),
            ("id", "🆔 ایدی عددی", "🆔 Numeric ID", ".id", "دریافت شناسه عددی تلگرام (با ریپلی)", "Get numeric Telegram ID (Reply)"),
            ("get_message", "📩 اطلاعات پیام", "📩 Message Info", ".get_message", "دریافت متادیتای فنی پیام (با ریپلی)", "Get message raw metadata (Reply)"),
            ("mention", "📣 منشن با ایدی", "📣 Mention ID", ".mention", "منشن کاربر با ایدی عددی: .mention ایدی", "Mention user with numeric ID: .mention ID"),
            ("meli", "🇮🇷 استعلام کدملی", "🇮🇷 National ID", ".meli", "بررسی صحت کدملی ایرانی: .meli کدملی", "Validate Iranian national ID: .meli code"),
            ("estelam", "🔍 استعلامات عمومی", "🔍 Inquiries", ".estelam", "استعلام نرخ و قیمت‌ها: .estelam عدد", "General inquiries: .estelam num"),
            ("news", "📰 اخبار روز", "📰 News", ".news", "دریافت سرتیتر اخبار روز: .news دسته‌بندی", "Daily news headlines: .news category"),
            ("ccgen", "💳 ساخت کارت تست", "💳 Test CC Gen", ".ccgen", "تولید کارت اعتباری تستی معتبر", "Generate test credit card number"),
            ("yjc", "📡 اخبار YJC", "📡 YJC News", ".yjc", "آخرین اخبار خبرگزاری باشگاه خبرنگاران", "Latest YJC news headlines"),
            ("ocr", "👁 متن خوان OCR", "👁 Image OCR", ".ocr", "استخراج متن از روی تصویر (با ریپلی)", "Extract text from photo OCR (Reply)"),
            ("dl", "📥 دانلود مستقیم", "📥 Direct DL", ".dl", "دانلود مستقیم فایل از لینک: .dl لینک", "Download file directly from URL: .dl link"),
            ("waitt", "⏳ پیام انتظار", "⏳ Wait Msg", ".waitt", "ارسال پیام انیمیشنی در حال دانلود", "Send downloading wait animation"),
            ("time", "⏰ ساعت دقیق", "⏰ Clock Time", ".time", "نمایش ساعت رسمی تهران و جهانی", "Display exact official clock time"),
            ("nude", "🔞 عکس خاص ۱", "🔞 Special Pic 1", ".nude", "ارسال تصویر اختصاصی مدل ۱", "Send special photo 1"),
            ("nude2", "🔞 عکس خاص ۲", "🔞 Special Pic 2", ".nude2", "ارسال تصویر اختصاصی مدل ۲", "Send special photo 2"),
            ("nude3", "🔞 عکس خاص ۳", "🔞 Special Pic 3", ".nude3", "ارسال تصویر اختصاصی مدل ۳", "Send special photo 3"),
            ("boob", "🔥 رسانه خاص", "🔥 Special Media", ".boob", "ارسال رسانه اختصاصی ویژه", "Send exclusive special media"),
            ("ayang", "💃 رسانه یانگ", "💃 Ayang Media", ".ayang", "ارسال رسانه اختصاصی یانگ", "Send Ayang special media"),
            ("chance", "🎲 تست شانس", "🎲 Random Chance", ".chance", "محاسبه درصد شانس تصادفی", "Calculate random luck percentage"),
        ],
        "account": [
            ("addadmin", "➕ افزودن ادمین", "➕ Add Admin", ".addadmin", "افزودن ادمین کمکی به سلف: .addadmin ایدی", "Add helper admin: .addadmin ID"),
            ("deladmin", "➖ حذف ادمین", "➖ Del Admin", ".deladmin", "حذف ادمین کمکی از سلف: .deladmin ایدی", "Delete helper admin: .deladmin ID"),
            ("adminlist", "📋 لیست ادمین‌ها", "📋 Admin List", ".adminlist", "مشاهده لیست تمام ادمین‌های مجاز سلف", "View list of all authorized admins"),
            ("clearadminlist", "🧹 پاکسازی ادمین‌ها", "🧹 Clear Admins", ".clearadminlist", "حذف تمامی ادمین‌های کمکی سلف", "Clear all helper admins list"),
            ("id", "🆔 شناسه کاربری", "🆔 User ID", ".id", "دریافت شناسه عددی اکانت کاربری", "Get numeric account user ID"),
            ("limit", "⚠️ بررسی لیمیت", "⚠️ Check Limit", ".limit", "بررسی لیمیت دیلیت اکانت تلگرام", "Check account deletion limits"),
            ("creation", "📅 تاریخ ساخت", "📅 Creation Date", ".creation", "تخمین تاریخ ساخت اکانت تلگرام", "Estimate account creation date"),
            ("session", "🟢 وضعیت سلف", "🟢 Self Status", ".session", "بررسی وضعیت روشن بودن سلف‌بات: .session", "Check self ON status: .session"),
        ],
        "book": [
            ("joke", "😂 ارسال جوک", "😂 Jokes", ".joke", "ارسال جوک و لطیفه‌های طنز روز", "Send funny jokes"),
            ("poem", "📜 ابیات شعر", "📜 Poems", ".poem", "ارسال اشعار ناب و زیبای فارسی", "Send beautiful poems"),
            ("know", "💡 آیا می‌دانید؟", "💡 Did You Know?", ".know", "دانستنی‌های علمی و جالب روز", "Send scientific facts & trivia"),
            ("quote", "💬 سخنان بزرگان", "💬 Quotes", ".quote", "سخنان و جملات انگیزشی بزرگان", "Send famous philosophical quotes"),
            ("wiki", "📚 ویکی‌پدیا", "📚 Wikipedia", ".wiki", "جستجوی مقاله در دانشنامه ویکی‌پدیا: .wiki متن", "Search Wikipedia article: .wiki text"),
            ("google", "🔍 سرچ گوگل", "🔍 Google Search", ".google", "جستجوی مستقیم در موتور گوگل: .google متن", "Search on Google directly: .google text"),
            ("num", "🔢 عدد رندوم", "🔢 Random Number", ".num", "تولید عدد تصادفی رندوم: .num سقف_عدد", "Generate random number: .num max"),
            ("name", "🔤 پیشنهاد نام", "🔤 Name Ideas", ".name", "پیشنهاد نام‌های زیبا و اصیل: .name نام", "Suggest beautiful names: .name name"),
            ("bio", "📝 بیوگرافی زیبا", "📝 Bio Suggestions", ".bio", "پیشنهاد متن‌های جذاب برای بیوگرافی", "Suggest attractive biography texts"),
            ("memo", "📌 یادداشت موقت", "📌 Quick Notes", ".memo", "ثبت و یادآوری یادداشت: .memo متن", "Save quick note: .memo text"),
            ("pnp", "🎭 طنز روز", "🎭 Daily Humor", ".pnp", "متن‌های کوتاه طنز و شوخی روز", "Send short daily humors"),
            ("alaki", "🌀 متن‌های رندوم", "🌀 Random Text", ".alaki", "ارسال متن‌های رندوم و تصادفی", "Send funny random texts"),
            ("hadis", "📖 حدیث روز", "📖 Daily Hadith", ".hadis", "ارسال احادیث گرانقدر معنوی", "Send daily holy Hadith"),
            ("dastan", "📚 داستان کوتاه", "📚 Short Story", ".dastan", "ارسال داستان‌های کوتاه و آموزنده", "Send short moral stories"),
            ("rname", "✏️ نام مستعار", "✏️ Rename Nickname", ".rname", "تغییر نام و عنوان سفارشی", "Rename custom nickname"),
            ("fal", "🥠 فال حافظ", "🥠 Hafez Horoscope", ".fal", "فال حافظ همراه با تعبیر غزل", "Get Hafez horoscope with meaning"),
            ("estekhare", "📿 استخاره آنلاین", "📿 Online Estekhare", ".estekhare", "استخاره آنلاین با قرآن کریم", "Online Quranic Estekhare"),
            ("zekr", "🤲 ذکر ایام هفته", "🤲 Daily Prayers", ".zekr", "مشاهده ذکر و دعای مخصوص امروز", "View daily prayer & Zekr"),
        ],
        "fun": [
            ("tas", "🎲 پرتاب تاس", "🎲 Dice Roll", ".tas", "پرتاب تاس با شماره دلخواه: .tas ۱-۶", "Roll dice with number: .tas 1-6"),
            ("dart", "🎯 پرتاب دارت", "🎯 Dart Target", ".dart", "پرتاب دارت متحرک به سمت هدف", "Throw target dart animation"),
            ("bowling", "🎳 پرتاب بولینگ", "🎳 Bowling", ".bowling", "پرتاب توپ بولینگ متحرک", "Roll bowling ball animation"),
            ("basketball", "🏀 پرتاب بسکتبال", "🏀 Basketball", ".basketball", "پرتاب توپ بسکتبال درون سبد", "Shoot basketball shot animation"),
            ("football", "⚽️ شوت فوتبال", "⚽️ Football Goal", ".football", "شوت کردن توپ فوتبال درون دروازه", "Football penalty goal animation"),
            ("game", "🎮 بازی تلگرام", "🎮 TG Games", ".game", "ارسال مینی‌گیم‌های تلگرام", "Send interactive Telegram games"),
            ("bazi", "🕹 بازی آنلاین", "🕹 Online Games", ".bazi", "اجرای بازی‌های آنلاین HTML5", "Play online HTML5 games"),
            ("hehe", "😂 انیمیشن خنده", "😂 Laugh Anim", ".hehe", "ارسال انیمیشن خنده‌های بامزه", "Send laughing animation"),
            ("moon", "🌕 انیمیشن ماه", "🌕 Moon Anim", ".moon", "انیمیشن مراحل تغییرات ماه", "Moon phase change animation"),
            ("clock", "🕰 انیمیشن ساعت", "🕰 Clock Anim", ".clock", "انیمیشن تیک‌تاک ساعت عقربه‌ای", "Ticking clock animation"),
            ("thunder", "⚡️ رعدوبرق", "⚡️ Thunder Storm", ".thunder", "انیمیشن صاعقه و رعدوبرق", "Thunder storm animation"),
            ("earth", "🌍 کره زمین", "🌍 Earth Globe", ".earth", "انیمیشن چرخش سیاره زمین", "Spinning earth globe animation"),
            ("heart", "❤️ انیمیشن قلب", "❤️ Heart Anim", ".heart", "انیمیشن تپش قلب سرخ", "Beating red heart animation"),
            ("love", "💖 قلب‌های عاشقانه", "💖 Love Hearts", ".love", "ارسال پترن‌های متحرک قلبی", "Animated love hearts pattern"),
            ("santet", "🧙‍♂️ جادوگری طنز", "🧙‍♂️ Magic Prank", ".santet", "شبیه‌ساز سحر و جادوگری طنز", "Magic prank simulation"),
            ("nah", "🙅‍♂️ انیمیشن نه", "🙅‍♂️ Nah Anim", ".nah", "انیمیشن طنز مخالفت و نه گفتن", "Funny 'Nah' animation"),
            ("ajg", "🤬 شوخی طنز ۱", "🤬 Prank 1", ".ajg", "متن‌های شوخی و کل‌کل مدل ۱", "Fun prank text mode 1"),
            ("babi", "🤬 شوخی طنز ۲", "🤬 Prank 2", ".babi", "متن‌های شوخی و کل‌کل مدل ۲", "Fun prank text mode 2"),
            ("tank", "🚜 شلیک تانک", "🚜 War Tank", ".tank", "انیمیشن شلیک گلوله تانک جنگی", "War tank cannon shoot animation"),
            ("y", "👍 تایید بله", "👍 Quick Yes", ".y", "انیمیشن و پیام تایید سریع", "Quick yes confirmation animation"),
            ("awk", "😹 خنده عجیب", "😹 Awkward Laugh", ".awk", "انیمیشن خنده عجیب و بامزه", "Awkward laughing animation"),
            ("tembak", "🔫 شلیک اسلحه", "🔫 Gun Shoot", ".tembak", "انیمیشن شلیک گلوله اسلحه", "Gun shoot bullet animation"),
            ("heli", "🚁 پرواز هلیکوپتر", "🚁 Helicopter", ".heli", "انیمیشن پرواز هلیکوپتر در آسمان", "Helicopter flying animation"),
            ("gabut", "🛋 متن بیکاری", "🛋 Boredom Mood", ".gabut", "متن‌های طنز در وصف بیکاری", "Funny boredom texts"),
            ("syg", "💑 پیام عشقم", "💑 Darling Love", ".syg", "ارسال پیام‌های رمانتیک عاشقانه", "Send romantic love messages"),
            ("dino", "🦖 دایناسور گوگل", "🦖 Google Dino", ".dino", "انیمیشن بازی دایناسور گوگل", "Google Dino game animation"),
            ("hack", "💻 شبیه‌ساز هک", "💻 Fake Hack", ".hack", "شبیه‌ساز هک ترمینال هکرها", "Terminal hacker simulation"),
            ("fuck", "🤬 شوخی طنز ۳", "🤬 Prank 3", ".fuck", "شوخی‌های متنی طنز", "Funny text pranks"),
            ("koc", "🔥 شوخی متحرک", "🔥 Fun Prank", ".koc", "انیمیشن‌های شوخی متحرک", "Animated fun pranks"),
            ("charging", "🔋 شارژ باتری", "🔋 Battery Charge", ".charging", "انیمیشن شارژ شدن باتری گوشی", "Phone battery charging animation"),
            ("gang", "🕶 مود گنگستر", "🕶 Gangster Mood", ".gang", "انیمیشن استایل گنگستری", "Gangster animation mood"),
            ("hypo", "🌀 انیمیشن هایپو", "🌀 Hypo Anim", ".hypo", "انیمیشن‌های هیپنوتیزم و چرخش", "Hypnotic spinning animation"),
            ("ding", "🔔 زنگ دینگ", "🔔 Ding Bell", ".ding", "انیمیشن به صدا درآمدن زنگ", "Ringing bell animation"),
            ("wtf", "❓ علامت سوال وات", "❓ WTF Anim", ".wtf", "انیمیشن تعجب شدید و WTF", "Shocking WTF animation"),
            ("call", "📞 انیمیشن تماس", "📞 Phone Call", ".call", "انیمیشن زنگ خوردن تلفن", "Phone call ringing animation"),
            ("bomb", "💣 انفجار بمب", "💣 Bomb Explosion", ".bomb", "انیمیشن شمارش معکوس و انفجار بمب", "Bomb countdown explosion animation"),
            ("brain", "🧠 مغز متفکر", "🧠 Active Brain", ".brain", "انیمیشن فعالیت سلول‌های مغز", "Active brain cells animation"),
            ("ahh", "🥱 انیمیشن آخ", "🥱 Ahh Anim", ".ahh", "انیمیشن خستگی و خمیازه", "Tired yawning animation"),
            ("hmm", "🤔 انیمیشن هوم", "🤔 Thinking", ".hmm", "انیمیشن تفکر عمیق و تمرکز", "Deep thinking animation"),
        ],
        "market": [
            ("price", "🛍 قیمت باسلام", "🛍 Basalam Price", ".price", "استعلام قیمت محصولات در باسلام: .price نام_کالا", "Inquire item price on Basalam: .price name"),
            ("qeymat", "🛒 قیمت ترب", "🛒 Torob Price", ".qeymat", "استعلام کمترین قیمت کالا در ترب: .qeymat نام_کالا", "Inquire lowest price on Torob: .qeymat name"),
            ("cryptolist", "📊 لیست رمزارزها", "📊 Crypto Coins", ".cryptolist", "مشاهده لیست تمام ارزهای دیجیتال برتر", "View list of top crypto coins"),
            ("crypto", "🪙 قیمت کریپتو", "🪙 Crypto Price", ".crypto", "قیمت لحظه‌ای رمزارز: .crypto btc/eth/trx", "Real-time coin price: .crypto btc/eth/trx"),
            ("c", "💱 تبدیل ارزها", "💱 Currency Calc", ".c", "ماشین حساب تبدیل ارز: .c مقدار ارز۱ ارز۲", "Currency converter calculator: .c amount cur1 cur2"),
            ("trx", "🔴 شبکه ترون", "🔴 TRON Coin", ".trx", "مشخصات، قیمت و اطلاعات شبکه TRON", "TRON coin price and network info"),
            ("arz", "📈 صرافی نوبیتکس", "📈 Nobitex Prices", ".arz", "نرخ لحظه‌ای ارزهای دیجیتال در نوبیتکس", "Nobitex cryptocurrency market rates"),
            ("estelam", "🔍 استعلام قیمت", "🔍 General Price", ".estelam", "استعلام عمومی نرخ‌ها: .estelam عدد", "General price inquiry: .estelam num"),
            ("tara", "⚡️ تراکنش تارا", "⚡️ TRON Tracker", ".tara", "پیگیری و رصد تراکنش شبکه ترون: .tara هش", "Track TRON TRC20 transaction: .tara hash"),
        ],
        "photogif": [
            ("sticker", "🎨 متن به استیکر", "🎨 Text to Sticker", ".sticker", "تبدیل فوری متن به استیکر: .sticker متن", "Convert text to Telegram sticker: .sticker text"),
            ("stickerinfo", "📦 اطلاعات استیکر", "📦 Pack Info", ".stickerinfo", "دریافت اطلاعات و لینک پک استیکر (با ریپلی)", "Get sticker pack info & link (Reply)"),
            ("error", "⚠️ استیکر ارور", "⚠️ Windows Error", ".error", "تولید استیکر دیالوگ ارور ویندوز: .error متن", "Create Windows error sticker: .error text"),
            ("tiny", "🔬 متن فوق ریز", "🔬 Tiny Text", ".tiny", "تبدیل متن به حروف سوپراسکریپت ریز (با ریپلی)", "Convert text to tiny superscript (Reply)"),
            ("ts", "🖼 عکس به استیکر", "🖼 Photo to Sticker", ".ts", "تبدیل عکس به فرمت استیکر وب‌پی (با ریپلی)", "Convert photo to sticker format (Reply)"),
            ("tg", "🎭 استیکر به عکس", "🎭 Sticker to Photo", ".tg", "تبدیل استیکر به تصویر عادی (با ریپلی)", "Convert sticker to normal photo (Reply)"),
            ("palm", "🤦‍♂️ دست رو صورت", "🤦‍♂️ Facepalm", ".palm", "ری‌اکشن انیمه فیس‌پالم (با ریپلی)", "Facepalm anime reaction (Reply)"),
            ("wink", "😉 چشمک انیمه", "😉 Anime Wink", ".wink", "ری‌اکشن چشمک انیمیشنی (با ریپلی)", "Anime wink reaction (Reply)"),
            ("hug", "🤗 بغل و آغوش", "🤗 Anime Hug", ".hug", "ری‌اکشن بغل کردن انیمه (با ریپلی)", "Anime hug reaction (Reply)"),
            ("pat", "💆‍♂️ نوازش انیمه", "💆‍♂️ Anime Pat", ".pat", "ری‌اکشن نوازش سر انیمه (با ریپلی)", "Anime head pat reaction (Reply)"),
        ],
        "ai": [
            ("ai", "🤖 هوش متنی", "🤖 9Router Text AI", ".ai", "گفتگو با هوش مصنوعی متنی: .ai سوال", "Chat with advanced 9Router AI: .ai question"),
            ("ai_learn", "🧠 آموزش به هوش", "🧠 AI Learn", ".ai learn", "آموزش دانش جدید به حافظه هوش: .ai learn متن", "Teach new knowledge to AI memory: .ai learn text"),
            ("ai_memory", "💾 حافظه هوش", "💾 AI Memory", ".ai memory", "مشاهده اطلاعات ذخیره‌شده در حافظه", "View stored AI long-term memory"),
            ("ai_forget", "🗑 فراموشی حافظه", "🗑 AI Forget", ".ai forget", "پاکسازی موردی حافظه هوش: .ai forget شماره", "Forget specific AI memory: .ai forget index"),
            ("ai_reset", "🔄 ریست گفتگو", "🔄 AI Reset", ".ai reset", "پاکسازی تاریخچه گفتگو و ریست چت", "Reset AI chat conversation history"),
            ("ai_fast", "⚡️ روت سریع", "⚡️ Fast AI Route", ".ai /fast", "پاسخگویی با سرعت بالا: .ai /fast سوال", "High speed response AI route: .ai /fast prompt"),
            ("ai_smart", "🎯 روت دقیق", "🎯 Smart AI Route", ".ai /smart", "تحلیل عمیق و هوشمند: .ai /smart سوال", "Deep analytical smart route: .ai /smart prompt"),
            ("ai_code", "💻 روت کدنویسی", "💻 Code Route", ".ai /code", "تولید و عیب‌یابی کدهای برنامه‌نویسی: .ai /code سوال", "Expert coding & debugging route: .ai /code prompt"),
            ("tts", "🎙 صدا پیش‌فرض", "🎙 Default Voice", ".tts", "تبدیل متن به وویس طبیعی: .tts متن", "Convert text to natural voice: .tts text"),
            ("ttsf", "👩 صدای زن", "👩 Female Voice", ".ttsf", "تبدیل متن به وویس خانم: .ttsf متن", "Convert text to female voice: .ttsf text"),
            ("ttsm", "👨 صدای مرد", "👨 Male Voice", ".ttsm", "تبدیل متن به وویس آقا: .ttsm متن", "Convert text to male voice: .ttsm text"),
            ("v", "🗣 وویس سریع", "🗣 Quick Voice", ".v", "تبدیل سریع متن به صوت: .v متن", "Quick voice note generator: .v text"),
            ("vl", "📋 لیست صداها", "📋 Voice List", ".vl", "مشاهده لیست گویندگان هوشمند", "View list of all neural voices"),
            ("sv", "⚙️ تنظیم صدا", "⚙️ Set Voice", ".sv", "تنظیم صدای پیش‌فرض: .sv کد_صدا", "Set default neural voice: .sv voice_code"),
            ("pgpt", "🎨 ساخت عکس AI", "🎨 AI Image Gen", ".pgpt", "ساخت عکس با هوش مصنوعی: .pgpt متن_پرامپت", "Generate AI image: .pgpt prompt"),
            ("vc", "🎭 تغییر دهنده صدا", "🎭 Voice Changer", ".vc", "افکت‌گذاری روی وویس: .vc شماره (با ریپلی)", "Voice changer effects: .vc number (Reply)"),
            ("gpt3", "🌐 موتور GPT 3.5", "🌐 GPT 3.5 Engine", ".gpt3", "پاسخگویی با مدل هوش GPT-3.5", "AI query with GPT-3.5 engine"),
            ("gpt4", "🌐 موتور GPT 4.0", "🌐 GPT 4.0 Engine", ".gpt4", "پاسخگویی با مدل هوش GPT-4.0", "AI query with GPT-4.0 engine"),
            ("bard", "🌐 گوگل بارد", "🌐 Google Bard", ".bard", "دستیار هوش مصنوعی Google Bard", "Query Google Bard assistant"),
            ("messi", "🤖 هوش لئو مسی", "🤖 Leo Messi AI", ".messi", "شخصیت هوش مصنوعی لیونل مسی", "Chat with Leo Messi persona"),
            ("ronaldo", "🤖 هوش رونالدو", "🤖 C. Ronaldo AI", ".ronaldo", "شخصیت هوش مصنوعی کریستیانو رونالدو", "Chat with Cristiano Ronaldo persona"),
            ("ilon", "🚀 هوش ایلان ماسک", "🚀 Elon Musk AI", ".ilon", "شخصیت هوش مصنوعی ایلان ماسک", "Chat with Elon Musk persona"),
        ],
        "photo": [
            ("nude", "🔞 عکس خاص ۱", "🔞 Photo 1", ".nude", "ارسال تصویر اختصاصی مدل ۱", "Send special photo 1"),
            ("nude2", "🔞 عکس خاص ۲", "🔞 Photo 2", ".nude2", "ارسال تصویر اختصاصی مدل ۲", "Send special photo 2"),
            ("nude3", "🔞 عکس خاص ۳", "🔞 Photo 3", ".nude3", "ارسال تصویر اختصاصی مدل ۳", "Send special photo 3"),
            ("boob", "🔥 رسانه خاص", "🔥 Special Media", ".boob", "ارسال رسانه اختصاصی ویژه", "Send exclusive special media"),
            ("ayang", "💃 رسانه یانگ", "💃 Ayang Media", ".ayang", "ارسال رسانه اختصاصی یانگ", "Send Ayang special media"),
            ("couple", "💑 عکس دونفره", "💑 Romantic Couple", ".couple", "ارسال عکس‌های رمانتیک دونفره", "Send romantic couple photos"),
            ("robo", "🤖 چهره ربات", "🤖 Robot Face", ".robo", "تولید چهره رباتی تصادفی: .robo شماره", "Generate random robot avatar: .robo num"),
            ("color", "🎨 پس‌زمینه رنگی", "🎨 Color Screen", ".color", "تولید پس‌زمینه رنگی: .color نام_رنگ", "Generate solid color photo: .color name"),
            ("pic", "🔍 جستجوی عکس", "🔍 Search Photo", ".pic", "جستجوی تصویر با کلیدواژه: .pic متن", "Search photos by keyword: .pic text"),
            ("bing", "🌐 عکس بینگ", "🌐 Bing Photos", ".bing", "جستجوی تصویر در موتور بینگ: .bing متن", "Search Bing images: .bing text"),
            ("uns", "🖼 عکس آنسپلش", "🖼 Unsplash", ".uns", "عکس‌های باکیفیت Unsplash: .uns متن", "Search Unsplash HD photos: .uns text"),
            ("photo", "📷 عکس تصادفی", "📷 Random Photo", ".photo", "ارسال عکس رندوم و باکیفیت روز", "Send random high-quality photo"),
            ("photos", "📸 گالری رندوم", "📸 Photo Gallery", ".photos", "ارسال مجموعه تصاویر تصادفی", "Send random photo gallery"),
            ("pikachu", "⚡️ عکس پیکاچو", "⚡️ Pikachu", ".pikachu", "ارسال تصاویر پیکاچو کارتونی", "Send cute Pikachu photos"),
            ("whale", "🐋 عکس نهنگ", "🐋 Ocean Whale", ".whale", "ارسال تصاویر شگفت‌انگیز نهنگ‌ها", "Send ocean whale photos"),
            ("fox", "🦊 روباه وحشی ۱", "🦊 Wild Fox 1", ".fox", "ارسال تصاویر روباه در طبیعت", "Send wild fox photos 1"),
            ("foxx", "🦊 روباه مدل ۲", "🦊 Wild Fox 2", ".foxx", "ارسال تصاویر روباه مدل دوم", "Send wild fox photos 2"),
            ("dog", "🐶 سگ بامزه ۱", "🐶 Cute Dog 1", ".dog", "ارسال تصاویر سگ‌های بامزه", "Send cute dog photos 1"),
            ("dogg", "🐕 سگ مدل ۲", "🐕 Dog 2", ".dogg", "ارسال تصاویر سگ‌های نژاددار", "Send cute dog photos 2"),
            ("doggg", "🐕 سگ مدل ۳", "🐕 Dog 3", ".doggg", "ارسال تصاویر سگ‌ها در طبیعت", "Send cute dog photos 3"),
            ("panda", "🐼 خرس پاندا ۱", "🐼 Giant Panda 1", ".panda", "ارسال تصاویر خرس‌های پاندا", "Send giant panda photos 1"),
            ("rpanda", "🐼 پاندا قرمز", "🐼 Red Panda", ".rpanda", "ارسال تصاویر پاندای سرخ", "Send cute red panda photos"),
            ("raccoon", "🦝 راکون بامزه", "🦝 Cute Raccoon", ".raccoon", "ارسال تصاویر راکون‌های جنگلی", "Send cute raccoon photos"),
            ("koala", "🐨 کوآلا استرالیا", "🐨 Australian Koala", ".koala", "ارسال تصاویر کوآلا روی درخت", "Send cute koala photos"),
            ("kangroo", "🦘 کانگورو جهنده", "🦘 Kangaroo", ".kangroo", "ارسال تصاویر کانگوروهای استرالیا", "Send jumping kangaroo photos"),
            ("bird", "🐦 پرندگان ۱", "🐦 Bird 1", ".bird", "ارسال عکس پرندگان خوش‌رنگ", "Send beautiful bird photos 1"),
            ("birdd", "🕊 پرندگان ۲", "🕊 Bird 2", ".birdd", "ارسال عکس پرندگان شکاری و زیبا", "Send beautiful bird photos 2"),
            ("cat", "🐱 گربه ملوس ۱", "🐱 Cute Cat 1", ".cat", "ارسال تصاویر گربه‌های خانگی", "Send cute cat photos 1"),
            ("catt", "🐈 گربه مدل ۲", "🐈 Cat 2", ".catt", "ارسال تصاویر گربه‌های نژاددار", "Send cute cat photos 2"),
        ],
        "music": [
            ("music", "🎵 دانلود موزیک", "🎵 Search Music", ".music", "جستجو و دانلود آهنگ از تلگرام: .music نام", "Search & download TG music: .music name"),
            ("youtube", "🎥 موزیک یوتیوب", "🎥 YouTube Music", ".youtube", "دریافت صوت موزیک از یوتیوب: .youtube نام", "Audio from YouTube: .youtube name"),
            ("musicc", "🎶 سرچ موزیک ۲", "🎶 Music DB 2", ".musicc", "جستجوی موزیک در دیتابیس دوم: .musicc نام", "Search music database 2: .musicc name"),
            ("remix", "🎛 دانلود ریمیکس", "🎛 Remix Songs", ".remix", "دانلود آهنگ‌های شاد و ریمیکس: .remix نام", "Download remix songs: .remix name"),
            ("demo", "🎼 دمو موزیک", "🎼 Music Demo", ".demo", "دانلود دمو و پیش‌نمایش آهنگ: .demo نام", "Download song preview demo: .demo name"),
            ("classic", "🎻 موزیک کلاسیک", "🎻 Classical", ".classic", "دانلود قطعات آرامش‌بخش و کلاسیک", "Download classical instrumental music"),
            ("ahang", "🎤 ترانه روز", "🎤 Persian Songs", ".ahang", "دانلود ترانه‌های روز و پاپ ایرانی: .ahang نام", "Download trending songs: .ahang name"),
            ("melo", "🎧 ملوبات وویس", "🎧 Melobot Voice", ".melo", "جستجو و دریافت وویس موزیک: .melo نام", "Melobot voice song search: .melo name"),
            ("global", "🌍 موزیک بین‌الملل", "🌍 Global Music", ".global", "جستجوی آهنگ‌های محبوب خارجی: .global نام", "Search global international music: .global name"),
        ],
        "system": [
            ("restart", "🔄 ری‌استارت سلف", "🔄 Restart Self", ".restart", "راه‌اندازی مجدد سرویس سلف‌بات", "Restart self-bot server process"),
            ("shutdown", "🛑 خاموش کردن", "🛑 Shutdown", ".shutdown", "خاموش کردن و توقف کامل سلف‌بات", "Turn off self-bot process completely"),
            ("ping", "📶 تست پینگ", "📶 Ping Speed", ".ping", "تست زمان پاسخگویی و پینگ سرور", "Server response time & ping test"),
            ("self", "🟢 وضعیت اتصال", "🟢 Self Status", "self", "بررسی آنلاین بودن سرور و اکانت سلف", "Check self connection & ON status"),
            ("on_off_status", "📊 وضعیت ماژول‌ها", "📊 Modules Status", ".on_off_status", "مشاهده وضعیت روشن/خاموش بودن امکانات", "View on/off status of all modules"),
            ("cpu", "💻 مصرف پردازنده", "💻 CPU Usage", ".cpu", "درصد مصرف لحظه‌ای پردازنده CPU سرور", "Current server CPU usage percentage"),
            ("memory", "🧠 مصرف رم", "🧠 RAM Usage", ".memory", "درصد مصرف حافظه رم RAM سرور", "Current server RAM memory usage"),
            ("system_inf", "🖥 مشخصات لینوکس", "🖥 Hardware Info", ".system-inf", "مشخصات کامل سیستم‌عامل، کرنل و سخت‌افزار", "Full Linux hardware & system specs"),
        ],
    }
    return DB

print("Data builder verified successfully!")

_TITAN_COMMANDS_DB = build_data()

_TITAN_COMMANDS_MAP = {}
for _ck, _items in _TITAN_COMMANDS_DB.items():
    for _cid, _f_lbl, _e_lbl, _syn, _f_pop, _e_pop in _items:
        _TITAN_COMMANDS_MAP[_cid] = {
            "fa_label": _f_lbl, "en_label": _e_lbl,
            "syntax": _syn, "fa_popup": _f_pop, "en_popup": _e_pop
        }

def _titan_category_keyboard(cat_key, lang, user_id):
    uid = str(user_id)
    cmd_list = _TITAN_COMMANDS_DB.get(cat_key, [])
    rows = []
    for i in range(0, len(cmd_list), 2):
        row = []
        for item in cmd_list[i:i+2]:
            cid = item[0]
            label = item[1] if lang == "fa" else item[2]
            row.append(InlineKeyboardButton(label, callback_data=f"cmd:{lang}:{cid}:{uid}"))
        rows.append(row)
    back_btn = "● بازگشت ●" if lang == "fa" else "● 𝗕𝗮𝗰𝗸 ●"
    back_cb = f"back1-{uid}" if lang == "fa" else f"back2-{uid}"
    rows.append([InlineKeyboardButton(back_btn, callback_data=back_cb)])
    return InlineKeyboardMarkup(rows)


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


# ================= TITAN HYBRID INTERACTIVE PANEL (BUTTONS + POPUPS) =================

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


async def _titan_edit_inline_or_chat(client, call, text, reply_markup=None):
    """Sleek, robust renderer for Titan photo card & buttons."""
    full_text = str(text or "")
    caption_text = full_text if len(full_text) <= 950 else None

    if getattr(call, "inline_message_id", None):
        if caption_text is not None:
            try:
                return await client.edit_inline_caption(
                    inline_message_id=call.inline_message_id,
                    caption=caption_text,
                    reply_markup=reply_markup,
                )
            except Exception:
                pass
        try:
            return await client.edit_inline_text(
                inline_message_id=call.inline_message_id,
                text=full_text,
                reply_markup=reply_markup,
            )
        except Exception:
            try:
                return await client.edit_inline_caption(
                    inline_message_id=call.inline_message_id,
                    caption=full_text[:950],
                    reply_markup=reply_markup,
                )
            except Exception as e:
                print(f"TITAN inline edit error: {e}")
        return

    if getattr(call, "message", None):
        if getattr(call.message, "photo", None):
            if caption_text is not None:
                try:
                    return await client.edit_message_caption(
                        call.message.chat.id,
                        call.message.id,
                        caption=caption_text,
                        reply_markup=reply_markup,
                    )
                except Exception:
                    pass
            try:
                await call.message.delete()
            except Exception:
                pass
            return await client.send_message(
                call.message.chat.id,
                full_text,
                reply_markup=reply_markup,
            )
        try:
            return await client.edit_message_text(
                call.message.chat.id,
                call.message.id,
                text=full_text,
                reply_markup=reply_markup,
            )
        except Exception:
            return await client.send_message(
                call.message.chat.id,
                full_text,
                reply_markup=reply_markup,
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
            [InlineKeyboardButton("● 𝗕𝗮𝗰𝗸 ●", callback_data=f"back2-{suffix}")],
        ]
    else:
        rows = [
            [InlineKeyboardButton("⚙️ راهنمای تنظیمات", callback_data=f"monshi2_config1-{suffix}"), InlineKeyboardButton("🔗 راهنمای لینک‌ها", callback_data=f"monshi2_links1-{suffix}")],
            [InlineKeyboardButton("📝 شخصی‌سازی متن", callback_data=f"monshi2_text1-{suffix}"), InlineKeyboardButton("👥 مدیریت کاربران", callback_data=f"monshi2_users1-{suffix}")],
            [InlineKeyboardButton("📊 آمار عملیاتی", callback_data=f"monshi2_stats1-{suffix}")],
            [InlineKeyboardButton("● بازگشت ●", callback_data=f"back1-{suffix}")],
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
        return await _titan_edit_inline_or_chat(client, call, fallback_text, reply_markup=None)
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

    # Handle Command Popup Buttons
    if call.data.startswith("cmd:"):
        parts = call.data.split(":")
        lang = parts[1] if len(parts) > 1 else "fa"
        cid = parts[2] if len(parts) > 2 else ""
        target_uid = parts[3] if len(parts) > 3 else "0"
        if int(call.from_user.id) != int(target_uid):
            await call.answer("دسترسی غیر مجاز 🚫", show_alert=False)
            return
        info = _TITAN_COMMANDS_MAP.get(cid)
        if info:
            syntax = info["syntax"]
            if lang == "fa":
                popup = f"📌 دستور: {syntax}\n\nℹ️ راهنما:\n{info['fa_popup']}"
            else:
                popup = f"📌 Command: {syntax}\n\nℹ️ Usage:\n{info['en_popup']}"
            await call.answer(popup[:200], show_alert=True)
        else:
            await call.answer("دستور یافت نشد.", show_alert=True)
        return

    uid = str(call.from_user.id)

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
            action = call.data.split("-")[0]

            # 1. Main Persian Panel
            if action in ["persian", "back1"]:
                try:
                    user = await app.get_users(call.from_user.id)
                    await _titan_edit_inline_or_chat(
                        app,
                        call,
                        text=f"**سلام {user.first_name} به راهنمای اولترا سلف خوش آمدید. لطفا بخش مورد نظر خود را انتخاب کنید:**",
                        reply_markup=build_titan_panel_keyboard(call.from_user.id, language="fa")
                    )
                except Exception:
                    await _titan_edit_inline_or_chat(
                        app,
                        call,
                        text="**به راهنمای اولترا سلف خوش آمدید. لطفا بخش مورد نظر خود را انتخاب کنید:**",
                        reply_markup=build_titan_panel_keyboard(call.from_user.id, language="fa")
                    )
                await call.answer()
                return

            # 2. Main English Panel
            if action in ["english", "back2"]:
                try:
                    user = await app.get_users(call.from_user.id)
                    await _titan_edit_inline_or_chat(
                        app,
                        call,
                        text=f"**Hello {user.first_name} Welcome to Ultra Self help.\nPlease select the section you want:**",
                        reply_markup=build_titan_panel_keyboard(call.from_user.id, language="en")
                    )
                except Exception:
                    await _titan_edit_inline_or_chat(
                        app,
                        call,
                        text="**Welcome to Ultra Self help.\nPlease select the section you want:**",
                        reply_markup=build_titan_panel_keyboard(call.from_user.id, language="en")
                    )
                await call.answer()
                return

            # 3. Persian Category Handlers with Interactive Buttons
            fa_action_to_cat = {
                "global_person1": ("gp", fahelp1), "profile1": ("profile", fahelp2), "downloader1": ("downloader", fahelp3),
                "uploader1": ("uploader", fahelp4), "text_mode1": ("textmode", fahelp5), "action_mode1": ("actionmode", fahelp6),
                "webhook1": ("webhook", fahelp7), "locks1": ("locks", fahelp8), "cronjob1": ("cronjob", fahelp9),
                "antilogin1": ("antilogin", fahelp10), "tabchi1": ("tabchi", fahelp11), "photo_editor1": ("photoeditor", fahelp12),
                "marker1": ("marker", fahelp13), "compiler1": ("compiler", fahelp14), "tools1": ("tools", fahelp15),
                "account1": ("account", fahelp16), "book1": ("book", fahelp17), "fun1": ("fun", fahelp18),
                "market1": ("market", fahelp19), "photo_gif1": ("photogif", fahelp20), "ai1": ("ai", fahelp21),
                "photo1": ("photo", fahelp22), "music1": ("music", fahelp23), "system1": ("system", fahelp24),
            }
            if action in fa_action_to_cat:
                cat_k, h_txt = fa_action_to_cat[action]
                kb = _titan_category_keyboard(cat_k, "fa", call.from_user.id)
                await _titan_edit_inline_or_chat(app, call, text=h_txt, reply_markup=kb)
                await call.answer()
                return

            # 4. English Category Handlers with Interactive Buttons
            en_action_to_cat = {
                "global_person2": ("gp", enhelp1), "profile2": ("profile", enhelp2), "downloader2": ("downloader", enhelp3),
                "uploader2": ("uploader", enhelp4), "text_mode2": ("textmode", enhelp5), "action_mode2": ("actionmode", enhelp6),
                "webhook2": ("webhook", enhelp7), "locks2": ("locks", enhelp8), "cronjob2": ("cronjob", enhelp9),
                "antilogin2": ("antilogin", enhelp10), "tabchi2": ("tabchi", enhelp11), "photo_editor2": ("photoeditor", enhelp12),
                "marker2": ("marker", enhelp13), "compiler2": ("compiler", enhelp14), "tools2": ("tools", enhelp15),
                "account2": ("account", enhelp16), "book2": ("book", enhelp17), "fun2": ("fun", enhelp18),
                "market2": ("market", enhelp19), "photo_gif2": ("photogif", enhelp20), "ai2": ("ai", enhelp21),
                "photo2": ("photo", enhelp22), "music2": ("music", enhelp23), "system2": ("system", enhelp24),
            }
            if action in en_action_to_cat:
                cat_k, h_txt = en_action_to_cat[action]
                kb = _titan_category_keyboard(cat_k, "en", call.from_user.id)
                await _titan_edit_inline_or_chat(app, call, text=h_txt, reply_markup=kb)
                await call.answer()
                return

            # 5. Monshi2 Handlers
            if action.startswith("monshi2_"):
                lang = "en" if action.endswith("2") else "fa"
                base = action[:-1] if action[-1:] in ["1", "2"] else action
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
                await _titan_edit_inline_or_chat(
                    app,
                    call,
                    text=_monshi2_helper_panel_text(lang, section),
                    reply_markup=_monshi2_helper_panel_keyboard(call.from_user.id, lang, section)
                )
                await call.answer()
                return

            # 6. Close Handlers
            if action in ["close1", "close2", "Close"]:
                close_text = "**● پنل راهنما بسته شد ●**" if action == "close1" else "**● Helper Panel Closed ●**"
                await _titan_close_panel(app, call, close_text)
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
