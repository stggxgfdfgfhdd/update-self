#============ TiTaN Dedicated Join Helper ============#
# Purpose: only Forced Join / Monshi2 inline panels and membership verification.
# This file is intentionally isolated from the main helper panel bot.

from pyrogram import Client, filters, idle, errors
from pyrogram.types import (
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    Message,
)
from colorama import Fore
import os
import json
import base64
import hashlib
import asyncio
import time
from urllib.parse import unquote

FIX_VERSION = "2026-08-18-dedicated-join-helper-final-v4-8-inline-only"
print(f"{Fore.GREEN}TiTaN Join Helper version: {FIX_VERSION}{Fore.RESET}")


def _env(name, default=""):
    return str(os.environ.get(name, default)).strip().strip('"').strip("'").strip()


API_ID = int(_env("API_ID", "0") or 0)
API_HASH = _env("API_HASH", "")
JOIN_HELPER_BOT_TOKEN = _env("JOIN_HELPER_BOT_TOKEN", _env("FORCED_JOIN_BOT_TOKEN", ""))

if not JOIN_HELPER_BOT_TOKEN:
    print(f"{Fore.RED}JOIN_HELPER_BOT_TOKEN is not set. Add it in Railway Variables.{Fore.RESET}")

app = Client("JoinHelper", api_id=API_ID, api_hash=API_HASH, bot_token=JOIN_HELPER_BOT_TOKEN)

_FORCED_JOIN_CACHE = {}  # token -> {payload, time}
_CACHE_TTL = 60 * 60 * 12


def _cleanup_cache():
    now = int(time.time())
    expired = [k for k, v in _FORCED_JOIN_CACHE.items() if now - v.get("time", now) > _CACHE_TTL]
    for k in expired:
        _FORCED_JOIN_CACHE.pop(k, None)


def _cache_key(payload):
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:18]


def _decode_base64_text(token):
    token = str(token or "")
    token += "=" * (-len(token) % 4)
    return base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")


def _parse_fj2_query(query, from_user_id):
    """Parse compact query from self.py.

    Format:
    fj2|USER_ID|c:channel1,c:channel2,g:group|t:BASE64_TEXT|p:PHOTO_URL
    """
    payload = {
        "u": int(from_user_id),
        "t": "🔐 عضویت اجباری فعال است. لطفاً عضو لینک‌های زیر شوید و سپس تأیید عضویت را بزنید.",
        "r": [],
    }
    photo_url = None
    parts = str(query or "").split("|")
    if len(parts) > 1 and str(parts[1]).isdigit():
        payload["u"] = int(parts[1])

    compact_items = parts[2].split(",") if len(parts) > 2 and parts[2] else []
    reqs = []
    for raw in compact_items:
        if not raw or ":" not in raw:
            continue
        bits = raw.split(":", 2)
        kind_code = bits[0]
        ref = bits[1].strip().lstrip("@") if len(bits) > 1 else ""
        title = ref
        if len(bits) > 2 and bits[2]:
            try:
                decoded_title = _decode_base64_text(bits[2]).strip()
                if decoded_title:
                    title = decoded_title
            except Exception as exc:
                print(f"{Fore.YELLOW}JoinHelper title decode warning: {exc}{Fore.RESET}")
        if not ref:
            continue
        reqs.append({
            "type": "channel" if kind_code == "c" else "group",
            "username": ref,
            "title": title,
            "url": f"https://t.me/{ref}" if not ref.startswith("-") else "https://t.me/",
        })
    payload["r"] = reqs

    for extra in parts[3:]:
        if extra.startswith("t:"):
            try:
                custom = _decode_base64_text(extra[2:]).strip()
                if custom:
                    payload["t"] = custom
            except Exception as exc:
                print(f"{Fore.YELLOW}JoinHelper text decode warning: {exc}{Fore.RESET}")
        elif extra.startswith("p:"):
            try:
                url = unquote(extra[2:]).strip()
                if url.startswith("http"):
                    payload["p"] = url
                    photo_url = url
            except Exception as exc:
                print(f"{Fore.YELLOW}JoinHelper photo url decode warning: {exc}{Fore.RESET}")
    return payload, photo_url


def _button_title(item):
    return item.get("title") or item.get("username") or "Join"


def _keyboard(payload):
    _cleanup_cache()
    token = _cache_key(payload)
    _FORCED_JOIN_CACHE[token] = {"payload": payload, "time": int(time.time())}

    rows = []
    current = []
    for item in payload.get("r", []):
        title = _button_title(item)
        icon = "📢" if item.get("type") == "channel" else "👥"
        url = item.get("url") or "https://t.me/"
        current.append(InlineKeyboardButton(f"{icon} {title} ↗", url=url))
        if len(current) == 2:
            rows.append(current)
            current = []
    if current:
        rows.append(current)
    rows.append([InlineKeyboardButton("✅ تأیید عضویت", callback_data=f"fjv-{token}")])
    return InlineKeyboardMarkup(rows)


async def _missing_memberships(user_id, payload):
    missing = []
    for item in payload.get("r", []):
        ref = item.get("username") or item.get("id")
        if not ref:
            continue
        chat_ref = ref if str(ref).startswith("-") else f"@{str(ref).lstrip('@')}"
        try:
            member = await app.get_chat_member(chat_ref, int(user_id))
            status = str(getattr(member, "status", "")).lower()
            if any(x in status for x in ["left", "banned", "kicked"]):
                missing.append(item)
        except Exception as exc:
            print(f"{Fore.YELLOW}JoinHelper membership check failed for {chat_ref}/{user_id}: {exc}{Fore.RESET}")
            missing.append(item)
    return missing


@app.on_inline_query()
async def inline_handler(client, inline_query):
    query = inline_query.query or ""
    if not query.startswith("fj2|"):
        # This dedicated bot should not answer unrelated inline queries.
        await inline_query.answer(results=[], cache_time=1, is_personal=True)
        return

    try:
        print(f"{Fore.CYAN}JoinHelper inline query from {inline_query.from_user.id}: {query[:220]}{Fore.RESET}")
        payload, photo_url = _parse_fj2_query(query, inline_query.from_user.id)
        keyboard = _keyboard(payload)
        rows_count = len(getattr(keyboard, "inline_keyboard", []) or [])
        print(f"{Fore.CYAN}JoinHelper built panel: items={len(payload.get('r', []))}, rows={rows_count}, photo={'yes' if photo_url else 'no'}{Fore.RESET}")
        text = payload.get("t") or "🔐 عضویت اجباری فعال است."

        # Prefer article for maximum reliability. If a valid public photo URL is provided,
        # use photo result; if it fails, fall back to article with the same buttons.
        if photo_url:
            try:
                result = InlineQueryResultPhoto(
                    title="🔐 Forced Join",
                    description="Join required channels/groups",
                    photo_url=photo_url,
                    thumb_url=photo_url,
                    caption=text,
                    reply_markup=keyboard,
                )
                await inline_query.answer(results=[result], cache_time=1, is_personal=True)
                return
            except Exception as exc:
                print(f"{Fore.YELLOW}JoinHelper photo result failed, using article: {exc}{Fore.RESET}")

        result = InlineQueryResultArticle(
            title="🔐 Forced Join",
            description="Join required channels/groups",
            input_message_content=InputTextMessageContent(text),
            reply_markup=keyboard,
        )
        await inline_query.answer(results=[result], cache_time=1, is_personal=True)
    except Exception as exc:
        print(f"{Fore.RED}JoinHelper inline build failed: {exc}{Fore.RESET}")
        # Final emergency response; should rarely happen.
        await inline_query.answer(
            results=[InlineQueryResultArticle(
                title="🔐 Forced Join",
                description="Try again",
                input_message_content=InputTextMessageContent("🔐 عضویت اجباری فعال است؛ لطفاً دوباره پیام بدهید."),
            )],
            cache_time=1,
            is_personal=True,
        )


@app.on_callback_query(filters.regex(r"^fjv-"))
async def verify_callback(client, call):
    token = call.data.split("-", 1)[1]
    cached = _FORCED_JOIN_CACHE.get(token)
    if not cached:
        await call.answer("❌ درخواست منقضی شده؛ دوباره پیام بدهید.", show_alert=True)
        return

    payload = cached["payload"]
    target_uid = payload.get("u")
    if target_uid and int(target_uid) != int(call.from_user.id):
        await call.answer("❌ این دکمه برای شما نیست.", show_alert=True)
        return

    missing = await _missing_memberships(call.from_user.id, payload)
    if missing:
        names = "\n".join([f"• {_button_title(x)}" for x in missing])
        text = f"❌ عضویت کامل نیست\n\nموارد باقی‌مانده:\n{names}"
        await call.answer("❌ عضویت کامل نیست", show_alert=True)
    else:
        text = "✅ عضویت تأیید شد\n🔓 دسترسی شما فعال شد. اکنون می‌توانید پیام ارسال کنید."
        await call.answer("✅ عضویت تأیید شد", show_alert=True)

    try:
        if getattr(call, "inline_message_id", None):
            try:
                await client.edit_inline_caption(inline_message_id=call.inline_message_id, caption=text, reply_markup=None)
            except Exception:
                await client.edit_inline_text(inline_message_id=call.inline_message_id, text=text, reply_markup=None)
        elif getattr(call, "message", None):
            await client.edit_message_text(call.message.chat.id, call.message.id, text, reply_markup=None)
    except Exception as exc:
        print(f"{Fore.YELLOW}JoinHelper verify edit failed: {exc}{Fore.RESET}")


@app.on_message(filters.private & filters.command("start"))
async def start_message(client, message: Message):
    await message.reply_text("🔐 TiTaN Join Helper is online.")


def _flood_wait_seconds(exc):
    value = getattr(exc, "value", None) or getattr(exc, "x", None)
    try:
        return max(1, int(value))
    except Exception:
        return 60


async def start_client_safely(client, label):
    while True:
        try:
            await client.start()
            return
        except errors.FloodWait as e:
            wait_time = _flood_wait_seconds(e) + 5
            print(f"{Fore.RED}[{label}] Telegram FLOOD_WAIT: sleeping {wait_time}s...{Fore.RESET}")
            await asyncio.sleep(wait_time)
        except Exception:
            raise


async def main():
    await start_client_safely(app, "join-helper")
    print(Fore.YELLOW + "Join Helper Started..." + Fore.RESET)
    try:
        await idle()
    finally:
        try:
            await app.stop()
        except Exception:
            pass


if __name__ == "__main__":
    app.run(main())
