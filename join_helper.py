#============ TiTaN Dedicated Join Helper ============#
# Purpose: only Forced Join / Monshi2 inline panels and membership verification.
# This file is intentionally isolated from the main helper panel bot.

from pyrogram import Client, filters, idle, errors
from pyrogram.types import (
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InlineQueryResultCachedPhoto,
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

FIX_VERSION = "2026-08-18-dedicated-join-helper-final-v5-0-monshi2-pro"
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
    # Photo file_id is not needed for the verify token identity.
    clean = dict(payload or {})
    clean.pop("photo_file_id", None)
    raw = json.dumps(clean, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:18]


def _decode_base64_text(token):
    token = str(token or "")
    token += "=" * (-len(token) % 4)
    return base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")


def _decode_fj_payload(token):
    return json.loads(_decode_base64_text(token))


def _clip_text(text, limit):
    text = str(text or "")
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def _parse_fj2_query(query, from_user_id):
    """Backward-compatible compact query parser.

    Format:
    fj2|USER_ID|c:channel1,c:channel2,g:group|t:BASE64_TEXT|p:PHOTO_URL
    """
    payload = {
        "u": int(from_user_id),
        "t": "🔐 عضویت اجباری فعال است. لطفاً عضو لینک‌های زیر شوید و سپس تأیید عضویت را بزنید.",
        "nt": "شما هنوز کامل جوین چنل ها نشده اید",
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


def _parse_fj3_query(query):
    """Parse token-based query created by v4.9 self.py.

    Format: fj3|USER_ID|TOKEN
    Full text/list/photo is already stored in _FORCED_JOIN_CACHE by /fjcfg and /fjphoto.
    """
    parts = str(query or "").split("|", 2)
    if len(parts) < 3:
        raise ValueError("invalid fj3 query")
    user_id = int(parts[1])
    token = parts[2].strip()
    cached = _FORCED_JOIN_CACHE.get(token)
    if not cached or not cached.get("payload"):
        raise ValueError(f"fj3 config not ready for token={token}")
    payload = dict(cached["payload"])
    payload["u"] = user_id
    payload["_token"] = token
    if not payload.get("r"):
        raise ValueError(f"fj3 config has no requirements token={token}")
    return payload, payload.get("p")


def _button_title(item):
    return item.get("title") or item.get("username") or "Join"


def _keyboard(payload):
    _cleanup_cache()
    token = str((payload or {}).get("_token") or _cache_key(payload))
    payload["_token"] = token
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


@app.on_message(filters.private & filters.text & filters.regex(r"^/fjcfg\s+"))
async def store_fj_config(client, message: Message):
    """Receive full forced-join config from the self account.

    /fjcfg TOKEN BASE64_JSON
    This avoids Telegram inline-query length limits and keeps full custom text.
    """
    try:
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3:
            return
        token = parts[1].strip()
        payload = _decode_fj_payload(parts[2].strip())
        payload["_token"] = token
        existing = _FORCED_JOIN_CACHE.get(token, {}).get("payload") or {}
        for keep_key in ["photo_file_id", "source_chat_id", "source_message_id"]:
            if existing.get(keep_key) and not payload.get(keep_key):
                payload[keep_key] = existing.get(keep_key)
        _FORCED_JOIN_CACHE[token] = {"payload": payload, "time": int(time.time())}
        print(f"{Fore.GREEN}JoinHelper stored fj3 config: token={token}, items={len(payload.get('r', []))}, text_len={len(payload.get('t', ''))}{Fore.RESET}")
    except Exception as exc:
        print(f"{Fore.RED}JoinHelper /fjcfg store failed: {exc}{Fore.RESET}")


@app.on_message(filters.private & filters.photo)
async def store_fj_photo(client, message: Message):
    """Receive configured forced-join photo from self account.

    Caption: /fjphoto TOKEN
    The bot stores its own photo file_id and later uses InlineQueryResultCachedPhoto.
    """
    caption = (message.caption or "").strip()
    if not caption.startswith("/fjphoto"):
        return
    try:
        parts = caption.split(maxsplit=1)
        if len(parts) < 2:
            return
        token = parts[1].strip()
        file_id = message.photo.file_id
        cached = _FORCED_JOIN_CACHE.get(token) or {"payload": {}, "time": int(time.time())}
        payload = cached.get("payload") or {}
        payload["photo_file_id"] = file_id
        _FORCED_JOIN_CACHE[token] = {"payload": payload, "time": int(time.time())}
        print(f"{Fore.GREEN}JoinHelper stored fj3 photo: token={token}, file_id={file_id[:24]}...{Fore.RESET}")
    except Exception as exc:
        print(f"{Fore.RED}JoinHelper /fjphoto store failed: {exc}{Fore.RESET}")


@app.on_message(filters.private & filters.text & filters.regex(r"^/fjmsg\s+"))
async def store_fj_message(client, message: Message):
    """Receive final panel message id from self so success verify can delete it.

    /fjmsg TOKEN CHAT_ID MESSAGE_ID
    """
    try:
        parts = (message.text or "").split(maxsplit=3)
        if len(parts) < 4:
            return
        token = parts[1].strip()
        chat_id = int(parts[2])
        msg_id = int(parts[3])
        cached = _FORCED_JOIN_CACHE.get(token) or {"payload": {}, "time": int(time.time())}
        payload = cached.get("payload") or {}
        payload["_token"] = token
        payload["source_chat_id"] = chat_id
        payload["source_message_id"] = msg_id
        _FORCED_JOIN_CACHE[token] = {"payload": payload, "time": int(time.time())}
        print(f"{Fore.GREEN}JoinHelper stored fj3 panel message: token={token}, chat={chat_id}, msg={msg_id}{Fore.RESET}")
    except Exception as exc:
        print(f"{Fore.RED}JoinHelper /fjmsg store failed: {exc}{Fore.RESET}")


async def _notify_owner(payload, text):
    owner = payload.get("owner") or payload.get("owner_id")
    if not owner:
        return False
    try:
        await app.send_message(int(owner), text)
        return True
    except Exception as exc:
        print(f"{Fore.YELLOW}JoinHelper notify owner failed: {exc}{Fore.RESET}")
        return False


@app.on_inline_query()
async def inline_handler(client, inline_query):
    query = inline_query.query or ""
    if not (query.startswith("fj2|") or query.startswith("fj3|")):
        # This dedicated bot should not answer unrelated inline queries.
        await inline_query.answer(results=[], cache_time=1, is_personal=True)
        return

    try:
        print(f"{Fore.CYAN}JoinHelper inline query from {inline_query.from_user.id}: {query[:220]}{Fore.RESET}")
        if query.startswith("fj3|"):
            payload, photo_url = _parse_fj3_query(query)
        else:
            payload, photo_url = _parse_fj2_query(query, inline_query.from_user.id)

        keyboard = _keyboard(payload)
        rows_count = len(getattr(keyboard, "inline_keyboard", []) or [])
        photo_file_id = payload.get("photo_file_id")
        print(f"{Fore.CYAN}JoinHelper built panel: items={len(payload.get('r', []))}, rows={rows_count}, photo={'cached' if photo_file_id else ('url' if photo_url else 'no')}, text_len={len(payload.get('t', ''))}{Fore.RESET}")
        text = payload.get("t") or "🔐 عضویت اجباری فعال است."

        if photo_file_id:
            result = InlineQueryResultCachedPhoto(
                photo_file_id=photo_file_id,
                title="🔐 Forced Join",
                description="Join required channels/groups",
                caption=_clip_text(text, 1024),
                reply_markup=keyboard,
            )
            await inline_query.answer(results=[result], cache_time=1, is_personal=True)
            return

        if photo_url:
            result = InlineQueryResultPhoto(
                title="🔐 Forced Join",
                description="Join required channels/groups",
                photo_url=photo_url,
                thumb_url=photo_url,
                caption=_clip_text(text, 1024),
                reply_markup=keyboard,
            )
            await inline_query.answer(results=[result], cache_time=1, is_personal=True)
            return

        result = InlineQueryResultArticle(
            title="🔐 Forced Join",
            description="Join required channels/groups",
            input_message_content=InputTextMessageContent(_clip_text(text, 4096)),
            reply_markup=keyboard,
        )
        await inline_query.answer(results=[result], cache_time=1, is_personal=True)
    except Exception as exc:
        # Do not return a no-button fallback article. The self account will see no
        # results and warn admin instead, preventing broken plain prompts.
        print(f"{Fore.RED}JoinHelper inline build failed; returning no results: {exc}{Fore.RESET}")
        await inline_query.answer(results=[], cache_time=1, is_personal=True)


@app.on_callback_query(filters.regex(r"^fjv-"))
async def verify_callback(client, call):
    token = call.data.split("-", 1)[1]
    cached = _FORCED_JOIN_CACHE.get(token)
    if not cached:
        await call.answer("❌ درخواست منقضی شده؛ دوباره پیام بدهید.", show_alert=True)
        return

    payload = cached["payload"]
    payload["_token"] = token
    target_uid = payload.get("u")
    if target_uid and int(target_uid) != int(call.from_user.id):
        await call.answer("❌ این دکمه برای شما نیست.", show_alert=True)
        return

    missing = await _missing_memberships(call.from_user.id, payload)
    if missing:
        text = payload.get("nt") or "شما هنوز کامل جوین چنل ها نشده اید"
        await call.answer("❌ عضویت کامل نیست", show_alert=True)
        await _notify_owner(payload, f"/fjstat fail {call.from_user.id} {token}")
        reply_markup = _keyboard(payload)  # Keep all buttons visible.
        try:
            if getattr(call, "inline_message_id", None):
                try:
                    await client.edit_inline_caption(
                        inline_message_id=call.inline_message_id,
                        caption=_clip_text(text, 1024),
                        reply_markup=reply_markup,
                    )
                except Exception:
                    await client.edit_inline_text(
                        inline_message_id=call.inline_message_id,
                        text=_clip_text(text, 4096),
                        reply_markup=reply_markup,
                    )
            elif getattr(call, "message", None):
                try:
                    await client.edit_message_caption(call.message.chat.id, call.message.id, caption=_clip_text(text, 1024), reply_markup=reply_markup)
                except Exception:
                    await client.edit_message_text(call.message.chat.id, call.message.id, _clip_text(text, 4096), reply_markup=reply_markup)
        except Exception as exc:
            print(f"{Fore.YELLOW}JoinHelper failed verify edit failed: {exc}{Fore.RESET}")
        return

    # Success
    success_text = payload.get("st") or "✅ عضویت شما تأیید شد"
    await call.answer("✅ عضویت تأیید شد", show_alert=True)
    await _notify_owner(payload, f"/fjstat success {call.from_user.id} {token}")

    delete_success = str(payload.get("delete_success", "on")).lower() == "on"
    chat_id = payload.get("source_chat_id")
    msg_id = payload.get("source_message_id")
    if delete_success and chat_id and msg_id:
        # Ask the userbot/self account to delete its own inline-result message.
        await _notify_owner(payload, f"/fjdelete {chat_id} {msg_id} {token}")
        return

    # Fallback if deletion is disabled or message id was not registered.
    try:
        if getattr(call, "inline_message_id", None):
            try:
                await client.edit_inline_caption(
                    inline_message_id=call.inline_message_id,
                    caption=_clip_text(success_text, 1024),
                    reply_markup=None,
                )
            except Exception:
                await client.edit_inline_text(
                    inline_message_id=call.inline_message_id,
                    text=_clip_text(success_text, 4096),
                    reply_markup=None,
                )
        elif getattr(call, "message", None):
            try:
                await client.edit_message_caption(call.message.chat.id, call.message.id, caption=_clip_text(success_text, 1024), reply_markup=None)
            except Exception:
                await client.edit_message_text(call.message.chat.id, call.message.id, _clip_text(success_text, 4096), reply_markup=None)
    except Exception as exc:
        print(f"{Fore.YELLOW}JoinHelper success edit failed: {exc}{Fore.RESET}")


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
