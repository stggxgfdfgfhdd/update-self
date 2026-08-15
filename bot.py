#=============== In The Name Of God ===============#
# Source Name: Ultra Self Creator
# Source Version: 1.4.3
# Developer: @Code_Sheild
# © 2024 Ultra Self LLC. All rights reserved.
#==================== Import ======================#
from colorama import Fore
from pyrogram import Client, filters, idle, errors
from pyrogram.types import *
from functools import wraps
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import subprocess
import html
import zipfile
import pymysql
import shutil
import signal
import re
import os
import traceback
FIX_VERSION = "2026-08-07-self-startup-deepfix-v8"
print(f"{Fore.GREEN}Ultra Self worker fix version: {FIX_VERSION}{Fore.RESET}")

# MySQL Database - Try EVERY possible Railway variable name
import os as _os
from urllib.parse import urlparse as _urlparse

def _env(name, default=""):
    """Read config from Railway environment variables with fallback."""
    return _os.environ.get(name, str(default))

def _normalize_channel_id(value):
    """Accept @channel, channel, https://t.me/channel, or numeric channel id."""
    value = str(value or "").strip()
    value = value.replace("https://t.me/", "").replace("http://t.me/", "").replace("t.me/", "")
    value = value.split("?")[0].strip().strip("/")
    if value.startswith("@"):
        value = value[1:]
    return value

print(f"{Fore.CYAN}{'='*60}")
print(f"{Fore.CYAN}MySQL Environment Variables Check:")
for _k in sorted(_os.environ.keys()):
    if any(_needle in _k.upper() for _needle in ["MYSQL", "DB_", "DATABASE", "DBHOST"]):
        _v = _os.environ[_k]
        _masked = "***" + _v[-4:] if len(_v) > 6 else "***" if _v else "(empty)"
        print(f"{Fore.CYAN}  {_k} = {_masked}")
print(f"{Fore.CYAN}{'='*60}{Fore.RESET}")

_db_url = _env("DATABASE_URL", "")
_parsed = False
if _db_url:
    try:
        if _db_url.startswith("mysql://") or _db_url.startswith("mysql+"):
            # Strip mysql+ prefix if present
            clean_url = _db_url.replace("mysql+pymysql://", "mysql://").replace("mysql+mysqldb://", "mysql://")
            _p = _urlparse(clean_url)
            DBHost = _p.hostname or "localhost"
            DBPort = _p.port or 3306
            DBName = _p.path.lstrip("/") or ""
            DBUser = _p.username or "root"
            DBPass = _p.password or ""
            if DBName and DBHost != "localhost":
                _parsed = True
                print(f"{Fore.GREEN}✓ Connected via DATABASE_URL: {DBHost}:{DBPort}/{DBName}{Fore.RESET}")
    except Exception as _e:
        print(f"{Fore.YELLOW}DATABASE_URL parse failed: {_e}{Fore.RESET}")

if not _parsed:
    DBHost = _env("MYSQLHOST", _env("MYSQL_HOST", ""))
    DBPort = int(_env("MYSQLPORT", _env("MYSQL_PORT", "3306")))
    DBName = _env("MYSQLDATABASE", _env("MYSQL_DATABASE", ""))
    DBUser = _env("MYSQLUSER", _env("MYSQL_USERNAME", _env("MYSQL_USER", "root")))
    DBPass = _env("MYSQLPASSWORD", _env("MYSQL_PASSWORD", ""))
    if DBHost and DBName and DBHost != "localhost":
        _parsed = True
        print(f"{Fore.GREEN}✓ Connected via MYSQL* vars: {DBHost}:{DBPort}/{DBName}{Fore.RESET}")

if not _parsed:
    DBHost = _env("RAILWAY_MYSQL_HOST", "")
    DBPort = int(_env("RAILWAY_MYSQL_PORT", "3306"))
    DBName = _env("RAILWAY_MYSQL_DATABASE", "")
    DBUser = _env("RAILWAY_MYSQL_USERNAME", "root")
    DBPass = _env("RAILWAY_MYSQL_PASSWORD", "")
    if DBHost and DBName:
        _parsed = True
        print(f"{Fore.GREEN}✓ Connected via RAILWAY_MYSQL* vars: {DBHost}:{DBPort}/{DBName}{Fore.RESET}")

if not _parsed or DBHost == "localhost":
    print(f"{Fore.RED}{'='*60}")
    print(f"{Fore.RED} MySQL NOT configured correctly!")
    print(f"{Fore.RED}Current values:")
    print(f"{Fore.RED}  DBHost = {DBHost}")
    print(f"{Fore.RED}  DBPort = {DBPort}")
    print(f"{Fore.RED}  DBName = {DBName}")
    print(f"{Fore.RED}  DBUser = {DBUser}")
    print(f"{Fore.RED}{'='*60}{Fore.RESET}")

Admin = int(_env("ADMIN_ID", "00000"))                          # Admin ID
Token = _env("BOT_TOKEN", "00000")                              # Bot Token
API_ID = int(_env("API_ID", "00000"))                           # API ID
API_HASH = _env("API_HASH", "00000")                            # API HASH
Channel_ID = _normalize_channel_id(_env("CHANNEL_ID", "00000"))  # Channel Username / Link / ID
Helper_ID = _env("HELPER_ID", "00000")                          # Helper Username

# Card info
CardNumber = _env("CARD_NUMBER", "00000")                       # Card Number
CardName = _env("CARD_NAME", "00000")                           # Card Name

HelperDBHost = DBHost
HelperDBPort = DBPort
HelperDBName = DBName
HelperDBUser = DBUser
HelperDBPass = DBPass
#==================== Create =====================#
if not os.path.isdir("sessions"):
    os.mkdir("sessions")
if not os.path.isdir("selfs"):
    os.mkdir("selfs")
if not os.path.isfile("source/Self.zip"):
    print(f"{Fore.RED}WARNING: source/Self.zip not found! Self activation will fail.")
    print(f"{Fore.RED}Make sure 'source/Self.zip' is in your repository.{Fore.RESET}")

_config_errors = []
if Admin == 0:
    _config_errors.append("ADMIN_ID is not set (still 0)")
if Token == "00000":
    _config_errors.append("BOT_TOKEN is not set")
if API_ID == 0:
    _config_errors.append("API_ID is not set (still 0)")
if API_HASH == "00000":
    _config_errors.append("API_HASH is not set")
if not _parsed or DBHost == "localhost" or not DBName:
    _config_errors.append(f"MySQL not configured! DBHost={DBHost}, DBName={DBName}")
    _config_errors.append("Please set DATABASE_URL in Railway Variables (format: mysql://user:pass@host:port/db)")
if _config_errors:
    print(f"{Fore.RED}{'='*50}")
    print(f"{Fore.RED}Configuration Errors (set these in Railway Variables):")
    for err in _config_errors:
        print(f"{Fore.RED}  ✗ {err}")
    print(f"{Fore.RED}{'='*50}{Fore.RESET}")
#===================== App =======================#
app = Client("Bot", api_id=API_ID, api_hash=API_HASH, bot_token=Token)

scheduler = AsyncIOScheduler()

temp_Client = {}
lock = asyncio.Lock()

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
    """Add missing columns to old Railway tables without deleting any data."""
    rows = get_datas(f"SHOW COLUMNS FROM `{table_name}` LIKE '{column_name}'")
    if not rows:
        print(f"{Fore.YELLOW}[DB Migration] Adding missing column `{column_name}` to `{table_name}`...{Fore.RESET}")
        update_data(f"ALTER TABLE `{table_name}` ADD COLUMN `{column_name}` {column_definition}")

def ensure_user(chat_id):
    """Create/fix a user row and always return all keys used by the bot."""
    user = get_data(f"SELECT * FROM user WHERE id = '{chat_id}' LIMIT 1")
    if user is None:
        update_data(f"INSERT INTO user(id) VALUES({chat_id})")
        user = get_data(f"SELECT * FROM user WHERE id = '{chat_id}' LIMIT 1")
    defaults = {
        "step": "none",
        "phone": None,
        "amount": 0,
        "expir": 0,
        "account": "unverified",
        "self": "inactive",
        "pid": None,
    }
    for key, value in defaults.items():
        if key not in user:
            user[key] = value
    return user

def _short_dir_listing(path):
    try:
        return ", ".join(sorted(os.listdir(path))[:30])
    except Exception as e:
        return f"<cannot list {path}: {e}>"

def prepare_self_directory(user_id):
    """Prepare selfs/self-{user_id} from source/Self.zip or from source/ files.

    Railway sometimes deploys without the binary Self.zip if it was not uploaded correctly.
    In that case, fall back to copying the source/ directory directly.
    """
    target = os.path.join("selfs", f"self-{user_id}")
    if os.path.isdir(target):
        shutil.rmtree(target, ignore_errors=True)
    os.makedirs(target, exist_ok=True)

    candidates = [
        os.path.join(os.getcwd(), "source", "Self.zip"),
        os.path.join("source", "Self.zip"),
        os.path.join(os.getcwd(), "Self.zip"),
        "Self.zip",
    ]
    zip_path = next((p for p in candidates if os.path.isfile(p)), None)
    if zip_path:
        print(f"{Fore.GREEN}[Self Prepare] Extracting {zip_path} -> {target}{Fore.RESET}")
        with zipfile.ZipFile(zip_path, "r") as extract:
            extract.extractall(target)
    else:
        source_dir = os.path.join(os.getcwd(), "source")
        if os.path.isfile(os.path.join(source_dir, "self.py")):
            print(f"{Fore.YELLOW}[Self Prepare] source/Self.zip not found; copying source directory -> {target}{Fore.RESET}")
            shutil.copytree(
                source_dir,
                target,
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("Self.zip", "__pycache__", "*.pyc")
            )
        else:
            raise FileNotFoundError(
                "Self source not found. Expected source/Self.zip or source/self.py. "
                f"cwd={os.getcwd()} | root files=[{_short_dir_listing(os.getcwd())}] | "
                f"source files=[{_short_dir_listing(source_dir)}]"
            )

    if not os.path.isfile(os.path.join(target, "self.py")):
        raise FileNotFoundError(
            f"self.py was not found after preparing self directory. target={target} | "
            f"target files=[{_short_dir_listing(target)}]"
        )
    return target

async def cleanup_login_client(chat_id):
    """Safely disconnect and remove temporary login client without hiding the original error."""
    async with lock:
        client = temp_Client.get(chat_id, {}).get("client")
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass
        temp_Client.pop(chat_id, None)

async def wait_for_self_ready(process, self_dir, timeout=None):
    """Wait until self.py confirms it really started.

    Checking only `process.poll() is None` is not enough: a process can be alive
    but stuck before Pyrogram starts. self.py creates ready.flag after app.start().
    """
    timeout = int(_env("SELF_START_TIMEOUT", "35") if timeout is None else timeout)
    ready_file = os.path.join(self_dir, "ready.flag")
    for _ in range(timeout):
        if os.path.isfile(ready_file) and process.poll() is None:
            return True
        if process.poll() is not None:
            return False
        await asyncio.sleep(1)
    if process.poll() is None:
        try:
            process.terminate()
        except Exception:
            pass
    return False

def helper_getdata(query):
    with pymysql.connect(host=HelperDBHost, port=HelperDBPort, database=HelperDBName, user=HelperDBUser, password=HelperDBPass) as connect:
        db = connect.cursor()
        db.execute(query)
        result = db.fetchone()
        return result

def helper_updata(query):
    with pymysql.connect(host=HelperDBHost, port=HelperDBPort, database=HelperDBName, user=HelperDBUser, password=HelperDBPass) as connect:
        db = connect.cursor()
        db.execute(query)
        connect.commit()

update_data("""
CREATE TABLE IF NOT EXISTS bot(
status varchar(10) DEFAULT 'ON'
) default charset=utf8mb4;
""")
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
CREATE TABLE IF NOT EXISTS block(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")
helper_updata("""
CREATE TABLE IF NOT EXISTS ownerlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")
helper_updata("""
CREATE TABLE IF NOT EXISTS adminlist(
id bigint PRIMARY KEY
) default charset=utf8mb4;
""")

#================== DB Migration ==================#
ensure_column("bot", "status", "varchar(10) DEFAULT 'ON'")
ensure_column("user", "step", "varchar(150) DEFAULT 'none'")
ensure_column("user", "phone", "varchar(150) DEFAULT NULL")
ensure_column("user", "amount", "bigint DEFAULT '0'")
ensure_column("user", "expir", "bigint DEFAULT '0'")
ensure_column("user", "account", "varchar(50) DEFAULT 'unverified'")
ensure_column("user", "self", "varchar(50) DEFAULT 'inactive'")
ensure_column("user", "pid", "bigint DEFAULT NULL")

update_data("UPDATE `bot` SET status = 'ON' WHERE status IS NULL")
update_data("UPDATE `user` SET step = 'none' WHERE step IS NULL")
update_data("UPDATE `user` SET amount = 0 WHERE amount IS NULL")
update_data("UPDATE `user` SET expir = 0 WHERE expir IS NULL")
update_data("UPDATE `user` SET account = 'unverified' WHERE account IS NULL")
update_data("UPDATE `user` SET self = 'inactive' WHERE self IS NULL")
print(f"{Fore.GREEN}✓ Database schema checked/migrated successfully{Fore.RESET}")

bot = get_data("SELECT * FROM bot")
if bot is None:
    update_data("INSERT INTO bot() VALUES()")

OwnerUser = helper_getdata(f"SELECT * FROM ownerlist WHERE id = '{Admin}' LIMIT 1")
if OwnerUser is None:
    helper_updata(f"INSERT INTO ownerlist(id) VALUES({Admin})")

AdminUser = helper_getdata(f"SELECT * FROM adminlist WHERE id = '{Admin}' LIMIT 1")
if AdminUser is None:
    helper_updata(f"INSERT INTO adminlist(id) VALUES({Admin})")

def add_admin(user_id):
    if helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is None:
        helper_updata(f"INSERT INTO adminlist(id) VALUES({user_id})")

def delete_admin(user_id):
    if helper_getdata(f"SELECT * FROM adminlist WHERE id = '{user_id}' LIMIT 1") is not None:
        helper_updata(f"DELETE FROM adminlist WHERE id = '{user_id}' LIMIT 1")

async def _safe_answer_callback(call, text=None, show_alert=False):
    """Answer callback queries without crashing if Telegram says it was already answered/expired."""
    try:
        await call.answer(text=text, show_alert=show_alert)
    except Exception:
        pass

async def _safe_send_admin_error(title, exc):
    """Send a short error report to admin and print full traceback in Railway logs."""
    tb = traceback.format_exc()
    print(f"{Fore.RED}[{title}] {exc}{Fore.RESET}")
    print(tb)
    try:
        await app.send_message(Admin, f"⚠️ خطای ربات در بخش {title}:\n```\n{tb[-3500:]}\n```")
    except Exception:
        pass

def checker(func):
    @wraps(func)
    async def wrapper(c, m, *args, **kwargs):
        is_callback = hasattr(m, "data") and hasattr(m, "from_user")
        chat_id = m.chat.id if hasattr(m, "chat") else m.from_user.id

        if get_data(f"SELECT * FROM user WHERE id = '{chat_id}' LIMIT 1") is None:
            update_data(f"INSERT INTO user(id) VALUES({chat_id})")

        bot = get_data("SELECT * FROM bot")
        if bot is None:
            update_data("INSERT INTO bot() VALUES()")
            bot = get_data("SELECT * FROM bot")

        block = get_data(f"SELECT * FROM block WHERE id = '{chat_id}' LIMIT 1")
        if block is not None and chat_id != Admin:
            if is_callback:
                await _safe_answer_callback(m, "شما از ربات مسدود شده‌اید", True)
            return

        # Forced-join check. Admin must never be blocked by this check.
        # If CHANNEL_ID is wrong or bot is not admin in the channel, do NOT break all buttons;
        # log the problem and allow the bot to continue.
        if chat_id != Admin and Channel_ID and Channel_ID != "00000":
            try:
                await app.get_chat_member(Channel_ID, chat_id)
            except errors.UserNotParticipant:
                if is_callback:
                    await _safe_answer_callback(m, "ابتدا در کانال عضو شوید و سپس /start را بزنید", True)
                await app.send_message(chat_id, "لطفا برای استفاده از ربات ابتدا در کانال زیر عضو شوید\nبعد از عضویت روی /start کلیک کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="عضویت در کانال", url=f"https://t.me/{Channel_ID}")
                        ]
                    ]
                ))
                return
            except Exception as e:
                print(f"{Fore.YELLOW}[JoinCheck Warning] CHANNEL_ID={Channel_ID} -> {type(e).__name__}: {e}{Fore.RESET}")

        if bot["status"] == "OFF" and chat_id != Admin:
            if is_callback:
                await _safe_answer_callback(m, "ربات در حال حاضر خاموش است!", True)
            else:
                await app.send_message(chat_id, "ربات در حال حاضر خاموش است!")
            return

        try:
            return await func(c, m, *args, **kwargs)
        except errors.MessageNotModified:
            # User clicked a button that would show the same text again; not a real error.
            if is_callback:
                await _safe_answer_callback(m)
            return
        except Exception as e:
            if is_callback:
                await _safe_answer_callback(m, "خطایی رخ داد؛ گزارش برای مدیر ارسال شد", True)
            else:
                try:
                    await app.send_message(chat_id, "خطایی رخ داد؛ گزارش برای مدیر ارسال شد")
                except Exception:
                    pass
            await _safe_send_admin_error("handler/button", e)
            return
    return wrapper

async def expirdec(user_id):
    user = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
    user_expir = user["expir"]
    if user_expir > 0:
        user_upexpir = user_expir - 1
        update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
    else:
        job = scheduler.get_job(str(user_id))
        if job:
            scheduler.remove_job(str(user_id))
        if user_id != Admin:
            delete_admin(user_id)
        if os.path.isdir(f"selfs/self-{user_id}"):
            pid = user["pid"]
            os.kill(pid, signal.SIGKILL)
            await asyncio.sleep(1)
            shutil.rmtree(f"selfs/self-{user_id}")
        if os.path.isfile(f"sessions/{user_id}.session"):
            async with Client(f"sessions/{user_id}") as user_client:
                await user_client.log_out()
            if os.path.isfile(f"sessions/{user_id}.session"):
                os.remove(f"sessions/{user_id}.session")
        if os.path.isfile(f"sessions/{user_id}.session-journal"):
            os.remove(f"sessions/{user_id}.session-journal")
        await app.send_message(user_id, "کاربر گرامی اشتراک سلف شما به پایان رسید. برای خرید مجدد اشتراک به قسمت خرید اشتراک مراجعه کنید")
        update_data(f"UPDATE user SET self = 'inactive' WHERE id = '{user_id}' LIMIT 1")
        update_data(f"UPDATE user SET pid = NULL WHERE id = '{user_id}' LIMIT 1")

async def setscheduler(user_id):
    job = scheduler.get_job(str(user_id))
    if not job:
        scheduler.add_job(expirdec, "interval", hours=24, args=[user_id], id=str(user_id))

Main = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="حساب من", callback_data="MyAccount")
        ],
        [
            InlineKeyboardButton(text="خرید اشتراک", callback_data="BuySub")
        ],
        [
            InlineKeyboardButton(text="بها", callback_data="Price"),
            InlineKeyboardButton(text="کیف پول", callback_data="Wallet")
        ],
        [
            InlineKeyboardButton(text="احراز هویت", callback_data="AccVerify"),
            InlineKeyboardButton(text="اطلاعات اشتراک", callback_data="Subinfo")
        ],
        [
            InlineKeyboardButton(text="سوالات متداول", url="https://t.me/Code_shield"),
            InlineKeyboardButton(text="سلف چیست؟", callback_data="WhatSelf")
        ],
        [
            InlineKeyboardButton(text="پشتیبانی", callback_data="Support")
        ]
    ]
)

@app.on_message(filters.private, group=-1)
async def update(c, m):
    ensure_user(m.chat.id)

@app.on_message(filters.private&filters.command("start"))
@checker
async def update(c, m):
    await app.send_message(m.chat.id, f"سلام کاربر {html.escape(m.chat.first_name)} به سلف ساز TiTaN Self خوش آمدید!", reply_markup=Main)
    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
    async with lock:
        if m.chat.id in temp_Client:
            del temp_Client[m.chat.id]
    if os.path.isfile(f"sessions/{m.chat.id}.session") and not os.path.isfile(f"sessions/{m.chat.id}.session-journal"):
        os.remove(f"sessions/{m.chat.id}.session")

@app.on_callback_query()
@checker
async def call(c, call):
    global temp_Client
    user = ensure_user(call.from_user.id)
    phone_number = user["phone"]
    account_status = "تایید شده" if user["account"] == "verified" else "تایید نشده"
    expir = user["expir"] or 0
    amount = user["amount"] or 0
    chat_id = call.from_user.id
    m_id = call.message.id
    data = call.data
    print(f"{Fore.CYAN}[Callback] user={chat_id} data={data}{Fore.RESET}")
    username = f"@{call.from_user.username}" if call.from_user.username else "وجود ندارد"

    if data == "MyAccount":
        await app.edit_message_text(chat_id, m_id, "اطلاعات حساب کاربری شما در TiTaN به شرح زیر می باشد:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="نام شما", callback_data="text"),
                    InlineKeyboardButton(text=f"{call.from_user.first_name}", callback_data="text")
                ],
                [
                    InlineKeyboardButton(text="آیدی شما", callback_data="text"),
                    InlineKeyboardButton(text=f"{call.from_user.id}", callback_data="text")
                ],
                [
                    InlineKeyboardButton(text="یوزرنیم شما", callback_data="text"),
                    InlineKeyboardButton(text=f"{username}", callback_data="text")
                ],
                [
                    InlineKeyboardButton(text="موجودی شما", callback_data="text"),
                    InlineKeyboardButton(text=f"{amount} تومان", callback_data="text")
                ],
                [
                    InlineKeyboardButton(text="وضعیت حساب شما", callback_data="text"),
                    InlineKeyboardButton(text=f"{account_status}", callback_data="text")
                ],
                [
                    InlineKeyboardButton(text="----------------", callback_data="text")
                ],
                [
                    InlineKeyboardButton(text=f"انقضای شما ({expir}) روز", callback_data="text")
                ],
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "BuySub" or data == "Back2":
        if user["phone"] is None:
            await app.delete_messages(chat_id, m_id)
            await app.send_message(chat_id, "لطفا با استفاده از دکمه زیر شماره خود را به اشتراک بگذارید", reply_markup=ReplyKeyboardMarkup(
                [
                    [
                        KeyboardButton(text="اشتراک گذاری شماره", request_contact=True)
                    ]
                ],resize_keyboard=True
            ))
            update_data(f"UPDATE user SET step = 'contact' WHERE id = '{call.from_user.id}' LIMIT 1")
        else:
            if user["account"] == "verified":
                if not os.path.isfile(f"sessions/{chat_id}.session-journal"):
                    await app.edit_message_text(chat_id, m_id, "مدت زمان اشتراک را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text="1 ماهه معادل 20000 تومان", callback_data="Login-30-20000")
                            ],
                            [
                                InlineKeyboardButton(text="2 ماهه معادل 45000 تومان", callback_data="Login-60-45000")
                            ],
                            [
                                InlineKeyboardButton(text="3 ماهه معادل 65000 تومان", callback_data="Login-90-65000")
                            ],
                            [
                                InlineKeyboardButton(text="4 ماهه معادل 85000 تومان", callback_data="Login-120-85000")
                            ],
                            [
                                InlineKeyboardButton(text="5 ماهه معادل 110000 تومان", callback_data="Login-150-110000")
                            ],
                            [
                                InlineKeyboardButton(text="6 ماهه معادل 130000 تومان", callback_data="Login-180-130000")
                            ],
                            [
                                InlineKeyboardButton(text="برگشت", callback_data="Back")
                            ]
                        ]
                    ))
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
                    async with lock:
                        if chat_id in temp_Client:
                            del temp_Client[chat_id]
                    if os.path.isfile(f"sessions/{chat_id}.session") and not os.path.isfile(f"sessions/{chat_id}.session-journal"):
                        os.remove(f"sessions/{chat_id}.session")
                else:
                    await app.answer_callback_query(call.id, text="اشتراک سلف برای شما فعال است!", show_alert=True)
            else:
                await app.edit_message_text(chat_id, m_id, "برای خرید اشتراک ابتدا باید احراز هویت کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="احراز هویت", callback_data="AccVerify")
                        ],
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data.split("-")[0] == "Login":
        expir_count = data.split("-")[1]
        cost = data.split("-")[2]
        if int(amount) >= int(cost):
            mess = await app.edit_message_text(chat_id, m_id, "در حال پردازش...")
            async with lock:
                if chat_id not in temp_Client:
                    temp_Client[chat_id] = {}
                temp_Client[chat_id]["client"] = Client(f"sessions/{chat_id}", api_id=API_ID, api_hash=API_HASH, device_model="ULTRA-SELF", system_version="Linux")
                temp_Client[chat_id]["number"] = phone_number
                await temp_Client[chat_id]["client"].connect()
            try:
                await app.edit_message_text(chat_id, mess.id, "کد تایید 5 رقمی را با فرمت زیر ارسال کنید:\n1.2.3.4.5", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2")
                        ]
                    ]
                ))
                async with lock:
                    temp_Client[chat_id]["response"] = await temp_Client[chat_id]["client"].send_code(temp_Client[chat_id]["number"])
                update_data(f"UPDATE user SET step = 'login1-{expir_count}-{cost}' WHERE id = '{call.from_user.id}' LIMIT 1")

            except errors.BadRequest:
                await app.edit_message_text(chat_id, mess.id, "اتصال ناموفق بود! لطفا دوباره تلاش کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")

            except errors.PhoneNumberInvalid:
                await app.edit_message_text(chat_id, mess.id, "این شماره نامعتبر است!", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")

            except errors.PhoneNumberBanned:
                await app.edit_message_text(chat_id, mess.id, "این اکانت محدود است!", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")

            except Exception:
                async with lock:
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")
        else:
            await app.edit_message_text(chat_id, m_id, "موجودی حساب شما برای خرید این اشتراک کافی نیست", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="افزایش موجودی", callback_data="Wallet")
                    ],
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back2")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "Price":
        await app.edit_message_text(chat_id, m_id, """**
֍ بَهاء سلف عبارت است از : 

» 1 ماهه: 20000 تومان

» 2 ماهه: 45000 تومان

» 3 ماهه: 65000 تومان

» 4 ماهه 85000 تومان

» 5 ماهه: 110000 تومان

» 6 ماهه: 130000 تومان
**""", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "Wallet" or data == "Back3":
        await app.edit_message_text(chat_id, m_id, f"موجودی شما: {amount} تومان\nیکی از گزینه های زیر را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="خرید موجودی", callback_data="BuyAmount"),
                    InlineKeyboardButton(text="انتقال موجودی", callback_data="TransferAmount")
                ],
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
    
    elif data == "BuyAmount":
        if user["account"] == "verified":
            await app.edit_message_text(chat_id, m_id, "میزان موجودی مورد نظر خود را برای شارژ حساب وارد کنید:\nحداقل موجودی قابل خرید 10000 تومان است!", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back3")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'buyamount1' WHERE id = '{call.from_user.id}' LIMIT 1")
        else:
            await app.edit_message_text(chat_id, m_id, "برای خرید موجودی ابتدا باید احراز هویت کنید", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="احراز هویت", callback_data="AccVerify")
                    ],
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back3")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
    
    elif data.split("-")[0] == "AcceptAmount":
        user_id = int(data.split("-")[1])
        count = int(data.split("-")[2])
        user_amount = get_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
        user_upamount = int(user_amount["amount"]) + int(count)
        update_data(f"UPDATE user SET amount = '{user_upamount}' WHERE id = '{user_id}' LIMIT 1")
        await app.edit_message_text(Admin, m_id, f"تایید انجام شد\nمبلغ {count} تومان به حساب کاربر [ {user_id} ] انتقال یافت\nموجودی جدید کاربر: {user_upamount} تومان")
        await app.send_message(user_id, f"درخواست شما برای افزایش موجودی تایید شد\nمبلغ {count} تومان به حساب شما انتقال یافت\nموجودی جدید شما: {user_upamount} تومان")
    
    elif data.split("-")[0] == "RejectAmount":
        user_id = int(data.split("-")[1])
        await app.edit_message_text(Admin, m_id, "درخواست کاربر مورد نظر برای افزایش موجودی رد شد")
        await app.send_message(user_id, "درخواست شما برای افزایش موجودی رد شد")
    
    elif data == "TransferAmount":
        if user["account"] == "verified":
            await app.edit_message_text(chat_id, m_id, "آیدی عددی کاربری که قصد انتقال موجودی به او را دارید ارسال کنید:", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back3")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'transferam1' WHERE id = '{call.from_user.id}' LIMIT 1")
        else:
            await app.edit_message_text(chat_id, m_id, "برای انتقال موجودی ابتدا باید احراز هویت کنید", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="احراز هویت", callback_data="AccVerify")
                    ],
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back3")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
    
    elif data == "AccVerify":
        if user["account"] != "verified":
            await app.edit_message_text(chat_id, m_id, """**
به بخش احراز هویت خوش آمدید.
نکات :
1) شماره کارت و نام صاحب کارت کاملا مشخص باشد.
2) لطفا تاریخ اعتبار و Cvv2 کارت خود را بپوشانید!
3) اسکرین شات و عکس از کارت از داخل موبایل بانک قابل قبول نیستند
4) فقط با کارتی که احراز هویت میکنید میتوانید خرید انجام بدید و اگر با کارت دیگری اقدام کنید تراکنش ناموفق میشود و هزینه از سمت خودِ بانک به شما بازگشت داده میشود.
5) در صورتی که توانایی ارسال عکس از کارت را ندارید تنها راه حل ارسال عکس از کارت ملی یا شناسنامه صاحب کارت است.

لطفا عکس از کارتی که میخواهید با آن خرید انجام دهید ارسال کنید.
**""", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'accverify' WHERE id = '{call.from_user.id}' LIMIT 1")
        else:
            await app.answer_callback_query(call.id, "حساب شما تایید شده است!", show_alert=True)
    
    elif data.split("-")[0] == "AcceptVerify":
        user_id = int(data.split("-")[1])
        update_data(f"UPDATE user SET account = 'verified' WHERE id = '{user_id}' LIMIT 1")
        await app.edit_message_text(Admin, m_id, f"حساب کاربر [ {user_id} ] تایید شد")
        await app.send_message(user_id, "حساب کاربری شما تایید شد و اکنون می توانید بدون محدودیت از ربات استفاده کنید")
    
    elif data.split("-")[0] == "RejectVerify":
        user_id = int(data.split("-")[1])
        await app.edit_message_text(Admin, m_id, "درخواست کاربر مورد نظر برای تایید حساب کاربری رد شد")
        await app.send_message(user_id, "درخواست شما برای تایید حساب کاربری رد شد")

    elif data == "Subinfo" or data == "Back4":
        if os.path.isfile(f"sessions/{chat_id}.session-journal"):
            substatus = "فعال" if user["self"] == "active" else "غیرفعال"
            await app.edit_message_text(chat_id, m_id, f"وضعیت اشتراک: {substatus}\nشماره اکانت: {phone_number}\nانقضا: {expir} روز", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="خرید انقضا", callback_data="BuyExpir"),
                        InlineKeyboardButton(text="انتقال انقضا", callback_data="TransferExpir")
                    ],
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back")
                    ]
                ]
            ))
        else:
            await app.answer_callback_query(call.id, text="شما اشتراک فعالی ندارید!", show_alert=True)
    
    elif data == "BuyExpir":
        if user["account"] == "verified":
            await app.edit_message_text(chat_id, m_id, "میزان انقضای مورد نظر خود را برای افزایش وارد کنید:\nهزینه هر یک روز انقضا 1000 تومان است", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back4")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'buyexpir1' WHERE id = '{call.from_user.id}' LIMIT 1")
        else:
            await app.edit_message_text(chat_id, m_id, "برای خرید انقضا ابتدا باید احراز هویت کنید", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="احراز هویت", callback_data="AccVerify")
                    ],
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back4")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
    
    elif data.split("-")[0] == "AcceptExpir":
        user_id = int(data.split("-")[1])
        count = int(data.split("-")[2])
        user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
        user_upexpir = int(user_expir["expir"]) + int(count)
        update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
        await app.edit_message_text(Admin, m_id, f"تایید انجام شد\n{count} روز به انقضای کاربر [ {user_id} ] افزوده شد\nانقضای جدید کاربر: {user_upexpir} روز")
        await app.send_message(user_id, f"درخواست شما برای افزایش انقضا تایید شد\n{count} روز به انقضای شما افزوده شد\nانقضای جدید شما: {user_upexpir} روز")
    
    elif data.split("-")[0] == "RejectExpir":
        user_id = int(data.split("-")[1])
        await app.edit_message_text(Admin, m_id, "درخواست کاربر مورد نظر برای افزایش انقضا رد شد")
        await app.send_message(user_id, "درخواست شما برای افزایش انقضا رد شد")

    elif data == "TransferExpir":
        if user["account"] == "verified":
            await app.edit_message_text(chat_id, m_id, "آیدی عددی کاربری که قصد انتقال انقضا به او را دارید ارسال کنید:", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back4")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'transferex1' WHERE id = '{call.from_user.id}' LIMIT 1")
        else:
            await app.edit_message_text(chat_id, m_id, "برای انتقال انقضا ابتدا باید احراز هویت کنید", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="احراز هویت", callback_data="AccVerify")
                    ],
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back4")
                    ]
                ]
            ))
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "WhatSelf":
        await app.edit_message_text(chat_id, m_id, """**
سلف به رباتی گفته میشه که روی اکانت شما نصب میشه و امکانات خاصی رو در اختیارتون میزاره ، لازم به ذکر هست که نصب شدن بر روی اکانت شما به معنی وارد شدن ربات به اکانت شما هست ( به دلیل دستور گرفتن و انجام فعالیت ها )
از جمله امکاناتی که در اختیار شما قرار میدهد شامل موارد زیر است:

❈ گذاشتن ساعت با فونت های مختلف بر روی بیو ، اسم
❈ قابلیت تنظیم حالت خوانده شدن خودکار پیام ها
❈ تنظیم حالت پاسخ خودکار
❈ پیام انیمیشنی
❈ منشی هوشمند
❈ دریافت پنل و تنظیمات اکانت هوشمند
❈ دو زبانه بودن دستورات و جواب ها
❈ تغییر نام و کاور فایل ها
❈ اعلان پیام ادیت و حذف شده در پیوی
❈ ذخیره پروفایل های جدید و اعلان حذف پروفایل مخاطبین

و امکاناتی دیگر که میتوانید با مراجعه به بخش راهنما آن ها را ببینید و مطالعه کنید!

❈ لازم به ذکر است که امکاناتی که در بالا گفته شده تنها ذره ای از امکانات سلف میباشد .
**""", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data == "Support":
        await app.edit_message_text(chat_id, m_id, "پیام خود را ارسال کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="Back")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'support' WHERE id = '{call.from_user.id}' LIMIT 1")

    elif data.split("-")[0] == "Reply":
        exit = data.split("-")[1]
        getuser = await app.get_users(exit)
        await app.send_message(Admin, f"پیام خود را برای کاربر [ {html.escape(getuser.first_name)} ] ارسال کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="صفحه اصلی", callback_data="Back"),
                    InlineKeyboardButton(text="پنل مدیریت", callback_data="Panel")
                ]
            ]
        ))
        update_data(f"UPDATE user SET step = 'ureply-{exit}' WHERE id = '{Admin}' LIMIT 1")

    elif data.split("-")[0] == "Block":
        exit = data.split("-")[1]
        getuser = await app.get_users(exit)
        block = get_data(f"SELECT * FROM block WHERE id = '{exit}' LIMIT 1")
        if block is None:
            await app.send_message(exit, "کاربر محترم شما به دلیل نقض قوانین از ربات مسدود شدید")
            await app.send_message(Admin, f"کاربر [ {html.escape(getuser.first_name)} ] از ربات بلاک شد")
            update_data(f"INSERT INTO block(id) VALUES({exit})")
        else:
            await app.send_message(Admin, f"کاربر [ {html.escape(getuser.first_name)} ] از قبل بلاک است")

    elif data == "Back":
        await app.edit_message_text(chat_id, m_id, f"سلام کاربر {html.escape(call.from_user.first_name)} به سلف ساز Ultra Self خوش آمدید!", reply_markup=Main)
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{call.from_user.id}' LIMIT 1")
        async with lock:
            if chat_id in temp_Client:
                del temp_Client[chat_id]
    
    elif data == "text":
        await app.answer_callback_query(call.id, text="این دکمه نمایشی است", show_alert=True)

    # Stop Telegram's loading spinner for all buttons that edited/sent a message but did not answer explicitly.
    await _safe_answer_callback(call)

@app.on_message(filters.contact)
@checker
async def update(c, m):
    user = ensure_user(m.chat.id)
    if user["step"] == "contact":
        phone_number = str(m.contact.phone_number)
        if not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"
        contact_id = m.contact.user_id
        if m.contact and m.chat.id == contact_id:
            mess = await app.send_message(m.chat.id, "شماره شما تایید شد", reply_markup=ReplyKeyboardRemove())
            update_data(f"UPDATE user SET phone = '{phone_number}' WHERE id = '{m.chat.id}' LIMIT 1")
            await asyncio.sleep(1)
            await app.delete_messages(m.chat.id, mess.id)
            await app.send_message(m.chat.id, f"سلام کاربر {html.escape(m.chat.first_name)} به سلف ساز Ultra Self خوش آمدید!", reply_markup=Main)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(m.chat.id, "لطفا از دکمه اشتراک گذاری شماره استفاده کنید!")

@app.on_message(filters.private)
@checker
async def update(c, m):
    global temp_Client
    user = ensure_user(m.chat.id)
    username = f"@{m.from_user.username}" if m.from_user.username else "وجود ندارد"
    phone_number = user["phone"]
    expir = user["expir"]
    amount = user["amount"]
    chat_id = m.chat.id
    text = m.text
    m_id = m.id

    if user["step"].split("-")[0] == "login1":
        if re.match(r'^\d\.\d\.\d\.\d\.\d$', text):
            code = ''.join(re.findall(r'\d', text))
            expir_count = user["step"].split("-")[1]
            cost = user["step"].split("-")[2]

            mess = await app.send_message(chat_id, "در حال پردازش...")
            try:
                async with lock:
                    await temp_Client[chat_id]["client"].sign_in(temp_Client[chat_id]["number"], temp_Client[chat_id]["response"].phone_code_hash, code)
                    await temp_Client[chat_id]["client"].disconnect()
                    if chat_id in temp_Client:
                        del temp_Client[chat_id]
                mess = await app.edit_message_text(chat_id, mess.id, "لاگین با موفقیت انجام شد")
                mess = await app.edit_message_text(chat_id, mess.id, "در حال فعالسازی سلف...\n(ممکن است چند لحظه طول بکشد)")
                self_dir = prepare_self_directory(m.chat.id)
                error_log_path = os.path.join(self_dir, "error.log")
                with open(error_log_path, "w") as error_log_file:
                    process = subprocess.Popen(["python3", "-u", "-W", "ignore::SyntaxWarning", "self.py", str(m.chat.id), str(API_ID), API_HASH, Helper_ID], cwd=self_dir, stdout=error_log_file, stderr=subprocess.STDOUT)
                if await wait_for_self_ready(process, self_dir):
                    if os.path.isfile(error_log_path):
                        os.remove(error_log_path)
                    await app.edit_message_text(chat_id, mess.id, f"سلف با موفقیت برای اکانت شما فعال شد\nمدت زمان اشتراک: {expir_count} روز", reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text="برگشت", callback_data="Back")
                            ]
                        ]
                    ))
                    upamount = int(amount) - int(cost)
                    update_data(f"UPDATE user SET amount = '{upamount}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET expir = '{expir_count}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET self = 'active' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET pid = '{process.pid}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                    add_admin(m.chat.id)
                    await setscheduler(m.chat.id)
                    await app.send_message(Admin, f"#گزارش_خرید_اشتراک\n\nآیدی کاربر: `{m.chat.id}`\nشماره کاربر: {phone_number}\nقیمت اشتراک: {cost} تومان\nمدت زمان اشتراک: {expir_count} روز")
                else:
                    error_output = ""
                    if os.path.isfile(error_log_path):
                        with open(error_log_path, "r", encoding="utf-8", errors="ignore") as ef:
                            error_output = ef.read()
                    if not error_output.strip():
                        error_output = "self.py did not create ready.flag before timeout. The process exited or was not fully started. Check Railway logs and source files."
                    await app.send_message(Admin, f"⚠️ خطا در فعالسازی سلف کاربر `{m.chat.id}`:\n```\n{error_output[:3500]}\n```")
                    await app.edit_message_text(chat_id, mess.id, "در فعالسازی سلف برای اکانت شما مشکلی رخ داد! هیچ مبلغی از حساب شما کسر نشد\nلطفا دوباره امتحان کنید و در صورتی که مشکل ادامه داشت با پشتیبانی تماس بگیرید", reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text="برگشت", callback_data="Back")
                            ]
                        ]
                    ))
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                    if os.path.isfile(f"sessions/{chat_id}.session"):
                        os.remove(f"sessions/{chat_id}.session")
                    if os.path.isdir(f"selfs/self-{chat_id}"):
                        shutil.rmtree(f"selfs/self-{chat_id}", ignore_errors=True)

            except errors.SessionPasswordNeeded:
                await app.edit_message_text(chat_id, mess.id, "رمز تایید دو مرحله ای برای اکانت شما فعال است\nرمز را وارد کنید:", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("برگشت", callback_data="Back2")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'login2-{expir_count}-{cost}' WHERE id = '{m.chat.id}' LIMIT 1")

            except errors.BadRequest:
                await app.edit_message_text(chat_id, mess.id, "کد نامعتبر است!")
            except errors.PhoneCodeInvalid:
                await app.edit_message_text(chat_id, mess.id, "کد نامعتبر است!")
            except errors.PhoneCodeExpired:
                await app.edit_message_text(chat_id, mess.id, "کد منقضی شده است! لطفا عملیات ورود را دوباره تکرار کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back2")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                await cleanup_login_client(chat_id)
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")
            
            except Exception:
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                await cleanup_login_client(chat_id)
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")
                if os.path.isdir(f"selfs/self-{chat_id}"):
                    shutil.rmtree(f"selfs/self-{chat_id}", ignore_errors=True)
                raise
        else:
            await app.send_message(chat_id, "فرمت نامعتبر است! لطفا کد را با فرمت ذکر شده وارد کنید:")
    
    elif user["step"].split("-")[0] == "login2":
        password = text.strip()
        expir_count = user["step"].split("-")[1]
        cost = user["step"].split("-")[2]

        mess = await app.send_message(chat_id, "در حال پردازش...")
        try:
            async with lock:
                await temp_Client[chat_id]["client"].check_password(password)
                await temp_Client[chat_id]["client"].disconnect()
                if chat_id in temp_Client:
                    del temp_Client[chat_id]
            mess = await app.edit_message_text(chat_id, mess.id, "لاگین با موفقیت انجام شد")
            mess = await app.edit_message_text(chat_id, mess.id, "در حال فعالسازی سلف...\n(ممکن است چند لحظه طول بکشد)")
            # Always prepare a fresh self source. Supports both source/Self.zip and source/self.py fallback.
            self_dir = prepare_self_directory(m.chat.id)
            error_log_path = os.path.join(self_dir, "error.log")
            with open(error_log_path, "w") as error_log_file:
                process = subprocess.Popen(["python3", "-u", "-W", "ignore::SyntaxWarning", "self.py", str(m.chat.id), str(API_ID), API_HASH, Helper_ID], cwd=self_dir, stdout=error_log_file, stderr=subprocess.STDOUT)
            if await wait_for_self_ready(process, self_dir):
                if os.path.isfile(error_log_path):
                    os.remove(error_log_path)
                await app.edit_message_text(chat_id, mess.id, f"سلف با موفقیت برای اکانت شما فعال شد\nمدت زمان اشتراک: {expir_count} روز", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back")
                        ]
                    ]
                ))
                upamount = int(amount) - int(cost)
                update_data(f"UPDATE user SET amount = '{upamount}' WHERE id = '{m.chat.id}' LIMIT 1")
                update_data(f"UPDATE user SET expir = '{expir_count}' WHERE id = '{m.chat.id}' LIMIT 1")
                update_data(f"UPDATE user SET self = 'active' WHERE id = '{m.chat.id}' LIMIT 1")
                update_data(f"UPDATE user SET pid = '{process.pid}' WHERE id = '{m.chat.id}' LIMIT 1")
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                add_admin(m.chat.id)
                await setscheduler(m.chat.id)
                await app.send_message(Admin, f"#گزارش_خرید_اشتراک\n\nآیدی کاربر: `{m.chat.id}`\nشماره کاربر: {phone_number}\nقیمت اشتراک: {cost} تومان\nمدت زمان اشتراک: {expir_count} روز")
            else:
                error_output = ""
                if os.path.isfile(error_log_path):
                    with open(error_log_path, "r", encoding="utf-8", errors="ignore") as ef:
                        error_output = ef.read()
                if not error_output.strip():
                    error_output = "self.py did not create ready.flag before timeout. The process exited or was not fully started. Check Railway logs and source files."
                await app.send_message(Admin, f"⚠️ خطا در فعالسازی سلف کاربر `{m.chat.id}`:\n```\n{error_output[:3500]}\n```")
                await app.edit_message_text(chat_id, mess.id, "در فعالسازی سلف برای اکانت شما مشکلی رخ داد! هیچ مبلغی از حساب شما کسر نشد\nلطفا دوباره امتحان کنید و در صورتی که مشکل ادامه داشت با پشتیبانی تماس بگیرید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                if os.path.isfile(f"sessions/{chat_id}.session"):
                    os.remove(f"sessions/{chat_id}.session")
                if os.path.isdir(f"selfs/self-{chat_id}"):
                    shutil.rmtree(f"selfs/self-{chat_id}", ignore_errors=True)

        except errors.BadRequest:
            await app.edit_message_text(chat_id, mess.id, "رمز نادرست است!\nرمز را وارد کنید:", reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="برگشت", callback_data="Back2")
                    ]
                ]
            ))

        except Exception:
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
            await cleanup_login_client(chat_id)
            if os.path.isfile(f"sessions/{chat_id}.session"):
                os.remove(f"sessions/{chat_id}.session")
            if os.path.isdir(f"selfs/self-{chat_id}"):
                shutil.rmtree(f"selfs/self-{chat_id}", ignore_errors=True)
            raise

    elif user["step"] == "buyamount1":
        if text.isdigit():
            count = text.strip()
            if int(count) >= 10000:
                await app.send_message(chat_id, f"فاکتور افزایش موجودی به مبلغ {count} تومان ایجاد شد\n\nشماره کارت: `{CardNumber}`\nبه نام {CardName}\nمبلغ قابل پرداخت: {count} تومان\n\nبعد از پرداخت رسید تراکنش را در همین قسمت ارسال کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back3")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'buyamount2-{count}' WHERE id = '{m.chat.id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "حداقل موجودی قابل خرید 10000 تومان است!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "buyamount2":
        if m.photo:
            count = int(user["step"].split("-")[1])
            mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
            await app.send_message(Admin, f"""
مدیر گرامی درخواست افزایش موجودی جدید دارید

نام کاربر: {html.escape(m.chat.first_name)}
آیدی کاربر: `{m.chat.id}`
یوزرنیم کاربر: {username}
مبلغ درخواستی کاربر: {count} تومان
""", reply_to_message_id=mess.id, reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("تایید", callback_data=f"AcceptAmount-{chat_id}-{count}"),
                        InlineKeyboardButton("رد کردن", callback_data=f"RejectAmount-{chat_id}")
                    ]
                ]
            ))
            await app.send_message(chat_id, "رسید تراکنش شما ارسال شد. لطفا منتظر تایید توسط مدیر باشید", reply_to_message_id=m_id)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عکس مجاز است")
    
    elif user["step"] == "transferam1":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                if user_id != m.chat.id:
                    await app.send_message(chat_id, "میزان موجودی مورد نظر خود را برای انتقال وارد کنید:\nحداقل موجودی قابل ارسال 10000 تومان است")
                    update_data(f"UPDATE user SET step = 'transferam2-{user_id}' WHERE id = '{m.chat.id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "شما نمی توانید به خودتان موجودی انتقال دهید!")
            else:
                await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif user["step"].split("-")[0] == "transferam2":
        if text.isdigit():
            user_id = int(user["step"].split("-")[1])
            count = text.strip()
            if int(amount) >= int(count):
                if int(count) >= 10000:
                    user_amount = get_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
                    upamount = int(amount) - int(count)
                    user_upamount = int(user_amount["amount"]) + int(count)
                    update_data(f"UPDATE user SET amount = '{upamount}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET amount = '{user_upamount}' WHERE id = '{user_id}' LIMIT 1")
                    await app.send_message(chat_id, f"مبلغ {count} تومان از حساب شما کسر شد و به حساب کاربر [ {user_id} ] انتقال یافت\nموجودی جدید شما: {upamount} تومان", reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text="برگشت", callback_data="Back3")
                            ]
                        ]
                    ))
                    await app.send_message(user_id, f"مبلغ {count} تومان از حساب کاربر [ {m.chat.id} ] به حساب شما انتقال یافت\nموجودی جدید شما: {user_upamount} تومان")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "حداقل موجودی قابل ارسال 10000 تومان است!")
            else:
                await app.send_message(chat_id, "موجودی شما کافی نیست!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"] == "accverify":
        if m.photo:
            mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
            await app.send_message(Admin, f"""
مدیر گرامی درخواست تایید حساب کاربری دارید

نام کاربر: {html.escape(m.chat.first_name)}
آیدی کاربر: `{m.chat.id}`
یوزرنیم کاربر: {username}
""", reply_to_message_id=mess.id, reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("تایید", callback_data=f"AcceptVerify-{chat_id}"),
                        InlineKeyboardButton("رد کردن", callback_data=f"RejectVerify-{chat_id}")
                    ]
                ]
            ))
            await app.send_message(chat_id, "درخواست شما برای تایید حساب کاربری ارسال شد. لطفا منتظر تایید توسط مدیر باشید", reply_to_message_id=m_id)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عکس مجاز است")

    elif user["step"] == "buyexpir1":
        if text.isdigit():
            count = int(text.strip())
            if int(count) > 0:
                await app.send_message(chat_id, f"فاکتور افزایش انقضا به مدت {count} روز ایجاد شد\n\nشماره کارت: `{CardNumber}`\nبه نام {CardName}\nمبلغ قابل پرداخت: {count*1000} تومان\n\nبعد از پرداخت رسید تراکنش را در همین قسمت ارسال کنید", reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text="برگشت", callback_data="Back4")
                        ]
                    ]
                ))
                update_data(f"UPDATE user SET step = 'buyexpir2-{count}' WHERE id = '{m.chat.id}' LIMIT 1")
            else:
                await app.send_message(chat_id, "حداقل انقضای قابل خرید 1 روز است!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "buyexpir2":
        if m.photo:
            count = int(user["step"].split("-")[1])
            mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
            await app.send_message(Admin, f"""
مدیر گرامی درخواست افزایش انقضای جدید دارید

نام کاربر: {html.escape(m.chat.first_name)}
آیدی کاربر: `{m.chat.id}`
یوزرنیم کاربر: {username}
تعداد روز های درخواستی کاربر: {count} روز
""", reply_to_message_id=mess.id, reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("تایید", callback_data=f"AcceptExpir-{chat_id}-{count}"),
                        InlineKeyboardButton("رد کردن", callback_data=f"RejectExpir-{chat_id}")
                    ]
                ]
            ))
            await app.send_message(chat_id, "رسید تراکنش شما ارسال شد. لطفا منتظر تایید توسط مدیر باشید", reply_to_message_id=m_id)
            update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عکس مجاز است")
        
    elif user["step"] == "transferex1":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                if user_id != m.chat.id:
                    if os.path.isfile(f"sessions/{user_id}.session-journal"):
                        await app.send_message(chat_id, "میزان انقضای مورد نظر خود را برای انتقال وارد کنید:\nحداقل باید 10 روز انقضا برای شما باقی بماند!")
                        update_data(f"UPDATE user SET step = 'transferex2-{user_id}' WHERE id = '{m.chat.id}' LIMIT 1")
                    else:
                        await app.send_message(chat_id, "اشتراک سلف برای این کاربر فعال نیست!")
                else:
                    await app.send_message(chat_id, "شما نمی توانید به خودتان انقضا انتقال دهید!")
            else:
                await app.send_message(chat_id, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif user["step"].split("-")[0] == "transferex2":
        if text.isdigit():
            user_id = int(user["step"].split("-")[1])
            count = text.strip()
            if int(expir) >= int(count):
                if int(expir) - int(count) >= 10:
                    user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
                    upexpir = int(expir) - int(count)
                    user_upexpir = int(user_expir["expir"]) + int(count)
                    update_data(f"UPDATE user SET expir = '{upexpir}' WHERE id = '{m.chat.id}' LIMIT 1")
                    update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
                    await app.send_message(chat_id, f"{count} روز از انقضای شما کسر شد و به کاربر [ {user_id} ] انتقال یافت\nانقضای جدید شما: {upexpir} روز", reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(text="برگشت", callback_data="Back4")
                            ]
                        ]
                    ))
                    await app.send_message(user_id, f"{count} روز از انقضای کاربر [ {m.chat.id} ] به شما انتقال یافت\nانقضای جدید شما: {user_upexpir} روز")
                    update_data(f"UPDATE user SET step = 'none' WHERE id = '{m.chat.id}' LIMIT 1")
                else:
                    await app.send_message(chat_id, "حداقل باید 10 روز انقضا برای شما باقی بماند!")
            else:
                await app.send_message(chat_id, "انقضای شما کافی نیست!")
        else:
            await app.send_message(chat_id, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"] == "support":
        mess = await app.forward_messages(from_chat_id=chat_id, chat_id=Admin, message_ids=m_id)
        await app.send_message(Admin, f"""
مدیر گرامی پیام ارسال شده جدید دارید

نام کاربر: {html.escape(m.chat.first_name)}
آیدی کاربر: `{m.chat.id}`
یوزرنیم کاربر: {username}
""", reply_to_message_id=mess.id, reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("پاسخ", callback_data=f"Reply-{chat_id}"),
                    InlineKeyboardButton("بلاک", callback_data=f"Block-{chat_id}")
                ]
            ]
        ))
        await app.send_message(chat_id, "پیام شما ارسال شد و در اسرع وقت به آن پاسخ داده خواهد شد", reply_to_message_id=m_id)

    elif user["step"].split("-")[0] == "ureply":
        exit = user["step"].split("-")[1]
        mess = await app.copy_message(from_chat_id=Admin, chat_id=exit, message_id=m_id)
        await app.send_message(exit, "کاربر گرامی پیام ارسال شده جدید از پشتیبانی دارید", reply_to_message_id=mess.id)
        await app.send_message(Admin, "پیام شما ارسال شد پیام دیگری ارسال یا روی یکی از گزینه های زیر کلیک کنید:", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="صفحه اصلی", callback_data="Back"),
                    InlineKeyboardButton(text="پنل مدیریت", callback_data="Panel")
                ]
            ]
        ))
#===================== Panel ======================#
Panel = ReplyKeyboardMarkup(
    [
        [
            ("آمار 📊")
        ],
        [
            ("ارسال همگانی ✉️"),
            ("فوروارد همگانی ✉️")
        ],
        [
            ("بلاک کاربر 🚫"),
            ("آنبلاک کاربر ✅️")
        ],
        [
            ("افزودن موجودی ➕"),
            ("کسر موجودی ➖")
        ],
        [
            ("افزودن زمان اشتراک ➕"),
            ("کسر زمان اشتراک ➖")
        ],
        [
            ("فعال کردن سلف 🔵"),
            ("غیرفعال کردن سلف 🔴")
        ],
        [
            ("روشن کردن ربات 🔵"),
            ("خاموش کردن ربات 🔴")
        ],
        [
            ("صفحه اصلی 🏠")
        ]
    ],resize_keyboard=True
)

AdminBack = ReplyKeyboardMarkup(
    [
        [
            ("برگشت ↪️")
        ]
    ],resize_keyboard=True
)

@app.on_message(filters.private&filters.user(Admin)&filters.command("panel"), group=1)
async def update(c, m):
    await app.send_message(Admin, "مدیر گرامی به پنل مدیریت TiTaN Self خوش آمدید!", reply_markup=Panel)
    update_data(f"UPDATE user SET step = 'none' WHERE id = '{Admin}' LIMIT 1")
    async with lock:
        if Admin in temp_Client:
            del temp_Client[Admin]

@app.on_callback_query(filters.user(Admin) & filters.regex(r"^(Panel|AdminBack|DeleteSub-\d+|AcceptDelSub-\d+)$"), group=-1)
async def call(c, call):
    data = call.data
    m_id = call.message.id
    print(f"{Fore.CYAN}[Admin Callback] user={call.from_user.id} data={data}{Fore.RESET}")
    if data == "Panel":
        await app.send_message(Admin, "مدیر گرامی به پنل مدیریت TiTaN Self خوش آمدید!", reply_markup=Panel)
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{Admin}' LIMIT 1")
        async with lock:
            if Admin in temp_Client:
                del temp_Client[Admin]
    
    elif data.split("-")[0] == "DeleteSub":
        user_id = int(data.split("-")[1])
        await app.edit_message_text(Admin, m_id, "**هشدار! با این کار اشتراک کاربر مورد نظر به طور کامل حذف می شود و امکان فعالسازی دوباره از پنل مدیریت وجود ندارد\n\nاگر از این کار اطمینان دارید روی گزینه تایید و در غیر این صورت روی گزینه برگشت کلیک کنید**", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="تایید", callback_data=f"AcceptDelSub-{user_id}")
                ],
                [
                    InlineKeyboardButton(text="برگشت", callback_data="AdminBack")
                ]
            ]
        ))
    
    elif data.split("-")[0] == "AcceptDelSub":
        await app.edit_message_text(Admin, m_id, "اشتراک سلف کاربر مورد نظر به طور کامل حذف شد", reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(text="برگشت", callback_data="AdminBack")
                ]
            ]
        ))
        user_id = int(data.split("-")[1])
        if os.path.isdir(f"selfs/self-{user_id}"):
            shutil.rmtree(f"selfs/self-{user_id}")
        if os.path.isfile(f"sessions/{user_id}.session"):
            async with Client(f"sessions/{user_id}") as user_client:
                await user_client.log_out()
            if os.path.isfile(f"sessions/{user_id}.session"):
                os.remove(f"sessions/{user_id}.session")
        if os.path.isfile(f"sessions/{user_id}.session-journal"):
            os.remove(f"sessions/{user_id}.session-journal")
        update_data(f"UPDATE user SET expir = '0' WHERE id = '{user_id}' LIMIT 1")
        update_data(f"UPDATE user SET self = 'inactive' WHERE id = '{user_id}' LIMIT 1")
        update_data(f"UPDATE user SET pid = NULL WHERE id = '{user_id}' LIMIT 1")
        await app.send_message(user_id, "کاربر گرامی اشتراک سلف شما توسط مدیر حذف شد\nبرای کسب اطلاعات بیشتر و دلیل حذف اشتراک به پشتیبانی مراجعه کنید")
    
    elif data == "AdminBack":
        await app.delete_messages(Admin, m_id)
        await app.send_message(Admin, "مدیر گرامی به پنل مدیریت TiTaN Self خوش آمدید!", reply_markup=Panel)
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{Admin}' LIMIT 1")
        async with lock:
            if Admin in temp_Client:
                del temp_Client[Admin]

    await _safe_answer_callback(call)

@app.on_message(filters.private&filters.user(Admin), group=1)
async def update(c, m):
    bot = get_data("SELECT * FROM bot")
    user = ensure_user(Admin)
    text = m.text
    m_id = m.id

    if text == "برگشت ↪️":
        await app.send_message(Admin, "مدیر گرامی به پنل مدیریت TiTaN Self خوش آمدید!", reply_markup=Panel)
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{Admin}' LIMIT 1")
        async with lock:
            if Admin in temp_Client:
                del temp_Client[Admin]

    elif text == "آمار 📊":
        mess = await app.send_message(Admin, "در حال دریافت اطلاعات...")
        botinfo = await app.get_me()
        allusers = get_datas("SELECT COUNT(id) FROM user")[0][0]
        allblocks = get_datas("SELECT COUNT(id) FROM block")[0][0]
        await app.edit_message_text(Admin, mess.id, f"""
تعداد کاربران ربات: {allusers}
تعداد کاربران بلاک شده: {allblocks}
--------------------------
نام ربات: {botinfo.first_name}
آیدی ربات: `{botinfo.id}`
یوزرنیم ربات: @{botinfo.username}
""")
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{Admin}' LIMIT 1")

    elif text == "ارسال همگانی ✉️":
        await app.send_message(Admin, "پیام خود را ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'sendall' WHERE id = '{Admin}' LIMIT 1")
    
    elif user["step"] == "sendall":
        mess = await app.send_message(Admin, "در حال ارسال به همه کاربران...")
        users = get_datas(f"SELECT id FROM user")
        for user in users:
            await app.copy_message(from_chat_id=Admin, chat_id=user[0], message_id=m_id)
            await asyncio.sleep(0.1)
        await app.edit_message_text(Admin, mess.id, "پیام شما برای همه کاربران ارسال شد")
    
    elif text == "فوروارد همگانی ✉️":
        await app.send_message(Admin, "پیام خود را ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'forall' WHERE id = '{Admin}' LIMIT 1")
    
    elif user["step"] == "forall":
        mess = await app.send_message(Admin, "در حال فوروارد به همه کاربران...")
        users = get_datas(f"SELECT id FROM user")
        for user in users:
            await app.forward_messages(from_chat_id=Admin, chat_id=user[0], message_ids=m_id)
            await asyncio.sleep(0.1)
        await app.edit_message_text(Admin, mess.id, "پیام شما برای همه کاربران فوروارد شد")
    
    elif text == "بلاک کاربر 🚫":
        await app.send_message(Admin, "آیدی عددی کاربری را که می خواهید بلاک کنید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'userblock' WHERE id = '{Admin}' LIMIT 1")

    elif user["step"] == "userblock":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                block = get_data(f"SELECT * FROM block WHERE id = '{user_id}' LIMIT 1")
                if block is None:
                    await app.send_message(user_id, "کاربر محترم شما به دلیل نقض قوانین از ربات مسدود شدید")
                    await app.send_message(Admin, f"کاربر [ {user_id} ] از ربات بلاک شد")
                    update_data(f"INSERT INTO block(id) VALUES({user_id})")
                else:
                    await app.send_message(Admin, "این کاربر از قبل بلاک است")
            else:
                await app.send_message(Admin, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif text == "آنبلاک کاربر ✅️":
        await app.send_message(Admin, "آیدی عددی کاربری را که می خواهید آنبلاک کنید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'userunblock' WHERE id = '{Admin}' LIMIT 1")
    
    elif user["step"] == "userunblock":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                block = get_data(f"SELECT * FROM block WHERE id = '{user_id}' LIMIT 1")
                if block is not None:
                    await app.send_message(user_id, "کاربر عزیز شما آنبلاک شدید و اکنون می توانید از ربات استفاده کنید")
                    await app.send_message(Admin, f"کاربر [ {user_id} ] از ربات آنبلاک شد")
                    update_data(f"DELETE FROM block WHERE id = '{user_id}' LIMIT 1")
                else:
                    await app.send_message(Admin, "این کاربر از ربات بلاک نیست!")
            else:
                await app.send_message(Admin, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif text == "افزودن موجودی ➕":
        await app.send_message(Admin, "آیدی عددی کاربری که می خواهید موجودی او را افزایش دهید وارد کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'amountinc' WHERE id = '{Admin}' LIMIT 1")
    
    elif user["step"] == "amountinc":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                await app.send_message(Admin, "میزان موجودی مورد نظر خود را برای افزایش وارد کنید:")
                update_data(f"UPDATE user SET step = 'amountinc2-{user_id}' WHERE id = '{Admin}' LIMIT 1")
            else:
                await app.send_message(Admin, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "amountinc2":
        if text.isdigit():
            user_id = int(user["step"].split("-")[1])
            count = int(text.strip())
            user_amount = get_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
            user_upamount = int(user_amount["amount"]) + int(count)
            update_data(f"UPDATE user SET amount = '{user_upamount}' WHERE id = '{user_id}' LIMIT 1")
            await app.send_message(user_id, f"مبلغ {count} تومان به حساب شما انتقال یافت\nموجودی جدید شما: {user_upamount} تومان")
            await app.send_message(Admin, f"مبلغ {count} تومان به حساب کاربر [ {user_id} ] افزوده شد\nموجودی جدید کاربر: {user_upamount} تومان")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif text == "کسر موجودی ➖":
        await app.send_message(Admin, "آیدی عددی کاربری که می خواهید موجودی او را کاهش دهید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'amountdec' WHERE id = '{Admin}' LIMIT 1")
    
    elif user["step"] == "amountdec":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                await app.send_message(Admin, "میزان موجودی مورد نظر خود را برای کاهش وارد کنید:")
                update_data(f"UPDATE user SET step = 'amountdec2-{user_id}' WHERE id = '{Admin}' LIMIT 1")
            else:
                await app.send_message(Admin, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "amountdec2":
        if text.isdigit():
            user_id = int(user["step"].split("-")[1])
            count = int(text.strip())
            user_amount = get_data(f"SELECT amount FROM user WHERE id = '{user_id}' LIMIT 1")
            user_upamount = int(user_amount["amount"]) - int(count)
            update_data(f"UPDATE user SET amount = '{user_upamount}' WHERE id = '{user_id}' LIMIT 1")
            await app.send_message(user_id, f"مبلغ {count} تومان از حساب شما کسر شد\nموجودی جدید شما: {user_upamount} تومان")
            await app.send_message(Admin, f"مبلغ {count} تومان از حساب کاربر [ {user_id} ] کسر شد\nموجودی جدید کاربر: {user_upamount} تومان")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif text == "افزودن زمان اشتراک ➕":
        await app.send_message(Admin, "آیدی عددی کاربری که می خواهید زمان اشتراک او را افزایش دهید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'expirinc' WHERE id = '{Admin}' LIMIT 1")

    elif user["step"] == "expirinc":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                if os.path.isfile(f"sessions/{user_id}.session-journal"):
                    await app.send_message(Admin, "میزان انقضای مورد نظر خود را برای افزایش وارد کنید:")
                    update_data(f"UPDATE user SET step = 'expirinc2-{user_id}' WHERE id = '{Admin}' LIMIT 1")
                else:
                    await app.send_message(Admin, "اشتراک سلف برای این کاربر فعال نیست!")
            else:
                await app.send_message(Admin, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "expirinc2":
        if text.isdigit():
            user_id = int(user["step"].split("-")[1])
            count = int(text.strip())
            user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
            user_upexpir = int(user_expir["expir"]) + int(count)
            update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
            await app.send_message(user_id, f"{count} روز به انقضای شما افزوده شد\nانقضای جدید شما: {user_upexpir} روز")
            await app.send_message(Admin, f"{count} روز به انقضای کاربر [ {user_id} ] افزوده شد\nانقضای جدید کاربر: {user_upexpir} روز")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif text == "کسر زمان اشتراک ➖":
        await app.send_message(Admin, "آیدی عددی کاربری که می خواهید موجودی او را کاهش دهید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'expirdec' WHERE id = '{Admin}' LIMIT 1")
    
    elif user["step"] == "expirdec":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                if os.path.isfile(f"sessions/{user_id}.session-journal"):
                    await app.send_message(Admin, "میزان انقضای مورد نظر خود را برای کاهش وارد کنید:")
                    update_data(f"UPDATE user SET step = 'expirdec2-{user_id}' WHERE id = '{Admin}' LIMIT 1")
                else:
                    await app.send_message(Admin, "اشتراک سلف برای این کاربر فعال نیست!")
            else:
                await app.send_message(Admin, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")

    elif user["step"].split("-")[0] == "expirdec2":
        if text.isdigit():
            user_id = int(user["step"].split("-")[1])
            count = int(text.strip())
            user_expir = get_data(f"SELECT expir FROM user WHERE id = '{user_id}' LIMIT 1")
            user_upexpir = int(user_expir["expir"]) - int(count)
            update_data(f"UPDATE user SET expir = '{user_upexpir}' WHERE id = '{user_id}' LIMIT 1")
            await app.send_message(user_id, f"{count} روز از انقضای شما کسر شد\nانقضای جدید شما: {user_upexpir} روز")
            await app.send_message(Admin, f"{count} روز از انقضای کاربر [ {user_id} ] کسر شد\nانقضای جدید کاربر: {user_upexpir} روز")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif text == "فعال کردن سلف 🔵":
        await app.send_message(Admin, "آیدی عددی کاربری که می خواهید سلف او را فعال کنید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'selfactive' WHERE id = '{Admin}' LIMIT 1")
    
    elif user["step"] == "selfactive":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                if os.path.isfile(f"sessions/{user_id}.session-journal"):
                    user_data = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
                    if user_data["self"] != "active":
                        mess = await app.send_message(Admin, "در حال پردازش...\n(ممکن است چند لحظه طول بکشد)")
                        # Use fresh self.py for manual activation too.
                        self_dir = prepare_self_directory(user_id)
                        error_log_path = os.path.join(self_dir, "error.log")
                        with open(error_log_path, "w") as error_log_file:
                            process = subprocess.Popen(["python3", "-u", "-W", "ignore::SyntaxWarning", "self.py", str(user_id), str(API_ID), API_HASH, Helper_ID], cwd=self_dir, stdout=error_log_file, stderr=subprocess.STDOUT)
                        if await wait_for_self_ready(process, self_dir):
                            if os.path.isfile(error_log_path):
                                os.remove(error_log_path)
                            await app.edit_message_text(Admin, mess.id, "سلف با موفقیت برای این کاربر فعال شد")
                            update_data(f"UPDATE user SET self = 'active' WHERE id = '{user_id}' LIMIT 1")
                            update_data(f"UPDATE user SET pid = '{process.pid}' WHERE id = '{user_id}' LIMIT 1")
                            add_admin(user_id)
                            await setscheduler(user_id)
                            await app.send_message(user_id, "سلف شما توسط مدیر فعال شد")
                        else:
                            error_output = ""
                            if os.path.isfile(error_log_path):
                                with open(error_log_path, "r", encoding="utf-8", errors="ignore") as ef:
                                    error_output = ef.read()
                            if not error_output.strip():
                                error_output = "self.py did not create ready.flag before timeout. The process exited or was not fully started. Check Railway logs and source files."
                            await app.edit_message_text(Admin, mess.id, f"در فعالسازی سلف برای این کاربر مشکلی پیش آمد!\n```\n{error_output[:3500]}\n```")
                    else:
                        await app.send_message(Admin, "سلف از قبل برای این کاربر فعال است!")
                else:
                    await app.send_message(Admin, "اشتراک سلف برای این کاربر فعال نیست!")
            else:
                await app.send_message(Admin, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif text == "غیرفعال کردن سلف 🔴":
        await app.send_message(Admin, "آیدی عددی کاربری که می خواهید سلف او را غیرفعال کنید ارسال کنید:", reply_markup=AdminBack)
        update_data(f"UPDATE user SET step = 'selfinactive' WHERE id = '{Admin}' LIMIT 1")
    
    elif user["step"] == "selfinactive":
        if text.isdigit():
            user_id = int(text.strip())
            if get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1") is not None:
                if os.path.isfile(f"sessions/{user_id}.session-journal"):
                    user_data = get_data(f"SELECT * FROM user WHERE id = '{user_id}' LIMIT 1")
                    if user_data["self"] != "inactive":
                        mess = await app.send_message(Admin, "در حال پردازش...")
                        os.kill(user_data["pid"], signal.SIGKILL)
                        await app.edit_message_text(Admin, mess.id, "سلف با موفقیت برای این کاربر غیرفعال شد", reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(text="حذف اشتراک کاربر", callback_data=f"DeleteSub-{user_id}")
                                ]
                            ]
                        ))
                        update_data(f"UPDATE user SET self = 'inactive' WHERE id = '{user_id}' LIMIT 1")
                        if user_id != Admin:
                            delete_admin(user_id)
                        job = scheduler.get_job(str(user_id))
                        if job:
                            scheduler.remove_job(str(user_id))
                        await app.send_message(user_id, "سلف شما توسط مدیر غیرفعال شد")
                    else:
                        await app.send_message(Admin, "سلف از قبل برای این کاربر غیرفعال است!")
                else:
                    await app.send_message(Admin, "اشتراک سلف برای این کاربر فعال نیست!")
            else:
                await app.send_message(Admin, "چنین کاربری در ربات یافت نشد!")
        else:
            await app.send_message(Admin, "ورودی نامعتبر! فقط ارسال عدد مجاز است")
    
    elif text == "روشن کردن ربات 🔵":
        if bot["status"] != "ON":
            await app.send_message(Admin, "ربات روشن شد")
            update_data(f"UPDATE bot SET status = 'ON' LIMIT 1")
        else:
            await app.send_message(Admin, "ربات از قبل روشن است!")
    
    elif text == "خاموش کردن ربات 🔴":
        if bot["status"] != "OFF":
            await app.send_message(Admin, "ربات خاموش شد")
            update_data(f"UPDATE bot SET status = 'OFF' LIMIT 1")
        else:
            await app.send_message(Admin, "ربات از قبل خاموش است!")

    elif text == "صفحه اصلی 🏠":
        mess = await app.send_message(Admin, "به صفحه اصلی برگشتید", reply_markup=ReplyKeyboardRemove())
        await app.send_message(Admin, f"سلام کاربر {m.chat.first_name} به سلف ساز TiTaN Self خوش آمدید!", reply_markup=Main)
        update_data(f"UPDATE user SET step = 'none' WHERE id = '{Admin}' LIMIT 1")
        async with lock:
            if Admin in temp_Client:
                del temp_Client[Admin]
        await asyncio.sleep(1)
        await app.delete_messages(Admin, mess.id)

#================== Run ===================#
def _flood_wait_seconds(exc):
    """Pyrogram FloodWait exposes seconds as .value in v2; keep fallbacks for safety."""
    value = getattr(exc, "value", None) or getattr(exc, "x", None)
    if value is None:
        match = re.search(r"wait of (\d+) seconds", str(exc))
        value = int(match.group(1)) if match else 60
    return max(1, int(value))

async def start_client_safely(client, label):
    """Start Pyrogram without crashing Railway on Telegram FLOOD_WAIT.

    Telegram may rate-limit bot authorization after repeated deploys/restarts.
    Crashing makes Railway restart and makes the loop worse, so we sleep inside
    the same container until Telegram allows authorization again.
    """
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
            print(traceback.format_exc())
            raise

async def main():
    await start_client_safely(app, "worker")
    scheduler.start()
    print(Fore.YELLOW + "Started...")
    try:
        await idle()
    finally:
        try:
            scheduler.shutdown(wait=False)
        except Exception:
            pass
        try:
            await app.stop()
        except Exception:
            pass

if __name__ == "__main__":
    app.run(main())
