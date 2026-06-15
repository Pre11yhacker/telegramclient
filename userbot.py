# Telethon UserBot v3.0
import asyncio, base64, io, json, os, re, sys, time, textwrap, math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass
if hasattr(sys.stderr, 'reconfigure'):
    try: sys.stderr.reconfigure(encoding='utf-8')
    except: pass

try:
    from telethon import TelegramClient, events, errors as tlerrors, connection
    from telethon.tl.functions.messages import GetCommonChatsRequest
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.tl.types import (
        MessageEntityUrl, MessageEntityTextUrl,
        UserStatusOnline, UserStatusOffline,
        UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth,
    )
    import telethon
except ImportError:
    print("[!] telethon not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "telethon", "-q"])
    from telethon import TelegramClient, events, errors as tlerrors, connection
    from telethon.tl.functions.messages import GetCommonChatsRequest
    from telethon.tl.functions.users import GetFullUserRequest
    from telethon.tl.types import (
        MessageEntityUrl, MessageEntityTextUrl,
        UserStatusOnline, UserStatusOffline,
        UserStatusRecently, UserStatusLastWeek, UserStatusLastMonth,
    )
    import telethon

CONFIG_FILE = "ub_config.json"
SESSION_NAME = "ub_session"
VERSION = "3.1"
API_CREDENTIALS = [
    (2040, "b18441a1ff607e10a989891a5462e627"),
    (611335, "d524b414d21f4d37f08684e1e0e5a3f2"),
    (17349, "344583e45741c457fe1862106095a5eb"),
    (4, "014b35b6184100b085b0d0572f9b5103"),
    (6, "eb06d4abfb49dc3eeb1aeb98ae0f581e"),
]
running = True
afk_data = {"enabled": False, "reason": "", "since": None}
notes_data = []
start_time = datetime.now()

class GL:
    ESC = '\033'
    BG = ESC + '[48;2;7;8;12m'
    FG = ESC + '[38;2;240;244;255m'
    BLUE = ESC + '[38;2;91;164;255m'
    PURPLE = ESC + '[38;2;139;92;246m'
    GREEN = ESC + '[38;2;6;214;160m'
    RED = ESC + '[38;2;255;79;110m'
    ORANGE = ESC + '[38;2;255;179;71m'
    DIM = ESC + '[38;2;90;106;138m'
    CYAN = ESC + '[38;2;91;210;255m'
    BOLD = ESC + '[1m'
    RESET = ESC + '[0m'
    CLR = ESC + '[2J' + ESC + '[H'

    @staticmethod
    def grad(text, c1="#5ba4ff", c2="#8b5cf6"):
        chars = list(text)
        out = []
        n = len(chars)
        if n == 0: return ""
        for i, c in enumerate(chars):
            t = i / max(n - 1, 1)
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            out.append(f"{GL.ESC}[38;2;{r};{g};{b}m{c}")
        out.append(GL.RESET)
        return "".join(out)

    @staticmethod
    def box(title, lines, w=60):
        s = "-"
        t = f"{GL.BLUE}+{s * (w-2)}+{GL.RESET}"
        b = f"{GL.BLUE}+{s * (w-2)}+{GL.RESET}"
        h = f"{GL.BLUE}|{GL.RESET}  {GL.BOLD}{GL.grad(title)}{GL.DIM}  |{GL.RESET}"
        m = []
        for l in lines:
            for wl in textwrap.wrap(str(l), w-6) if l else [""]:
                pad = " " * max(0, w - 6 - len(wl))
                m.append(f"{GL.BLUE}|{GL.RESET}  {wl}{pad}{GL.BLUE}|{GL.RESET}")
        return "\n".join([t, h] + m + [b])

    @staticmethod
    def task(label, status, detail=""):
        icon = {
            "ok": f"{GL.GREEN}[+]{GL.RESET}",
            "wait": f"{GL.ORANGE}[.]{GL.RESET}",
            "err": f"{GL.RED}[x]{GL.RESET}",
            "info": f"{GL.BLUE}[i]{GL.RESET}"
        }
        i = icon.get(status, f"{GL.DIM}[-]{GL.RESET}")
        d = f" {GL.DIM}{detail}{GL.RESET}" if detail else ""
        return f"  {i} {GL.BOLD}{label}{GL.RESET}{d}"

    @staticmethod
    def logo():
        return GL.grad(r"""
    __  _   _  ____  _____  ____   _____  ____  __  ___
   / _|| | | |/ ___|| ____|/ ___| |_   _|| __ )|  \/  |
  | |_ | | | |\___ \|  _|  \___ \   | |  |  _ \| |\/| |
  |  _|| |_| | ___) | |___  ___) |  | |  | |_) | |  | |
  |_|   \___/ |____/|_____||____/   |_|  |____/|_|  |_|
        """, "#5ba4ff", "#8b5cf6")

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def make_client(aid, ahash, dev="Windows Desktop", sysver="Windows 10", appver="4.9.1 x64"):
    return TelegramClient(
        f"{SESSION_NAME}_{aid}", aid, ahash,
        device_model=dev,
        system_version=sysver,
        app_version=appver,
        lang_code="en",
        system_lang_code="en",
    )

async def try_key(aid, ahash, phone, dev, sysver, appver):
    c = make_client(aid, ahash, dev, sysver, appver)
    try:
        await c.connect()
        if await c.is_user_authorized():
            me = await c.get_me()
            save_config({"api_id": aid, "api_hash": ahash, "phone": getattr(me, "phone", "")})
            return c, True
        await c.send_code_request(phone)
        return c, True
    except:
        try: await c.disconnect()
        except: pass
        return None, False

async def do_login():
    config = load_config()
    if config and config.get("api_id"):
        c = make_client(config["api_id"], config["api_hash"])
        await c.connect()
        if await c.is_user_authorized():
            me = await c.get_me()
            print(GL.task("Session", "ok", f"authorized as {me.first_name or me.id}"))
            return c
        await c.disconnect()
    print()
    print(GL.box(" LOGIN TO TELEGRAM ", ["Enter phone with country code", "Example: +79001234567"], 56))
    print()
    phone = input(f"  {GL.BLUE}[phone]{GL.RESET} Number: ").strip()
    print()
    print(GL.task("Connecting", "wait", "trying API keys..."))
    combos = []
    for aid, ahash in API_CREDENTIALS:
        combos.append((aid, ahash, "Windows Desktop", "Windows 10", "4.9.1 x64"))
        combos.append((aid, ahash, "Samsung SM-S928B", "SDK 34", "10.14.1"))
        combos.append((aid, ahash, "iPhone 15 Pro", "iOS 18.1", "10.14.1"))
    client = None
    used = None
    for aid, ahash, dev, sv, av in combos:
        print(GL.task("", "wait", f"ID {aid} ({dev[:15]})..."), end="")
        c, ok = await try_key(aid, ahash, phone, dev, sv, av)
        if ok and c:
            client = c
            used = (aid, ahash)
            print(f"\r{GL.task('OK', 'ok', f'API ID {aid}')}")
            break
        if c:
            print(f"\r{GL.task('', 'err', f'ID {aid} blocked')}")
        else:
            print(f"\r{GL.task('', 'err', f'ID {aid} failed')}")
    if not client:
        print(f"\n  {GL.RED}[x] All API keys blocked for this network{GL.RESET}")
        print(f"  {GL.DIM}Telegram requires using a VPN or mobile hotspot{GL.RESET}")
        print(f"  {GL.DIM}or get API keys at my.telegram.org (you refused){GL.RESET}")
        input(f"\n  {GL.DIM}Press Enter to exit...{GL.RESET}")
        sys.exit(1)
    print()
    code = input(f"\n  {GL.GREEN}[code]{GL.RESET} Code from Telegram: ").strip()
    try:
        await client.sign_in(phone, code)
    except tlerrors.SessionPasswordNeededError:
        print(GL.task("2FA", "info", "password required"))
        pwd = input(f"\n  {GL.ORANGE}[2fa]{GL.RESET} 2FA Password: ")
        await client.sign_in(password=pwd)
    except tlerrors.PhoneCodeInvalidError:
        print(f"\n  {GL.RED}[x] Invalid code{GL.RESET}")
        input("Press Enter to exit...")
        sys.exit(1)
    me = await client.get_me()
    print()
    print(GL.task("Done", "ok", f"@{me.username or me.id}"))
    save_config({"api_id": used[0], "api_hash": used[1], "phone": phone})
    return client

def resolve_target(s):
    s = s.strip()
    try: return int(s)
    except: return s

def format_status(status):
    if status is None: return "unknown"
    if isinstance(status, UserStatusOnline): return "online"
    if isinstance(status, UserStatusOffline): return f"last seen {status.was_online.strftime('%Y-%m-%d %H:%M')}"
    if isinstance(status, UserStatusRecently): return "recently"
    if isinstance(status, UserStatusLastWeek): return "this week"
    if isinstance(status, UserStatusLastMonth): return "this month"
    return "unknown"

def chat_type(ch):
    from telethon.tl.types import Chat as BasicChat
    if isinstance(ch, BasicChat): return 'basic_group'
    if getattr(ch, 'forum', False): return 'forum'
    if getattr(ch, 'gigagroup', False): return 'gigagroup'
    if getattr(ch, 'megagroup', False): return 'supergroup'
    if getattr(ch, 'broadcast', False): return 'channel'
    return type(ch).__name__

def esc(s):
    if s is None: return ""
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

async def get_gifts(client, uid):
    out = []
    fallback_self = False
    try:
        from telethon.tl.functions.payments import GetSavedStarGiftsRequest
        from telethon.tl.types import DocumentAttributeSticker, InputUserSelf, StarGiftAttributeModel, StarGiftAttributePattern, StarGiftBackground
        me = await client.get_me()
        is_self = (uid == me.id)
        peer = InputUserSelf() if is_self else await client.get_entity(uid)
        r = await client(GetSavedStarGiftsRequest(peer=peer, offset='', limit=100))
        items = getattr(r, 'gifts', []) or []
        if not items and not is_self:
            r2 = await client(GetSavedStarGiftsRequest(peer=InputUserSelf(), offset='', limit=100))
            items = getattr(r2, 'gifts', []) or []
            if items: fallback_self = True
        print(GL.task("Gifts", "ok", f"{len(items)} gifts for {'self' if is_self else uid}{'(fallback bot)' if fallback_self else ''}"), flush=True)
        for g in items:
            e = {'fallback': fallback_self}
            e['id'] = str(getattr(g, 'id', ''))
            e['gift_num'] = getattr(g, 'gift_num', None)
            e['name_hidden'] = getattr(g, 'name_hidden', False)
            sg = getattr(g, 'gift', None) or getattr(g, 'star_gift', None)
            if sg:
                e['name'] = str(getattr(sg, 'title', None) or getattr(sg, 'name', None) or sg.id)
                e['stars'] = getattr(sg, 'stars', 0)
                if getattr(sg, 'limited', False): e['limited'] = True
                if getattr(sg, 'birthday', False): e['birthday'] = True
                bg = getattr(sg, 'background', None)
                if bg and isinstance(bg, StarGiftBackground):
                    e['bg_center'] = getattr(bg, 'center_color', None)
                    e['bg_edge'] = getattr(bg, 'edge_color', None)
                uv = getattr(sg, 'upgrade_variants', None)
                if uv:
                    for attr in uv:
                        if isinstance(attr, StarGiftAttributeModel):
                            e['model_name'] = getattr(attr, 'name', None)
                            e['model_rarity'] = getattr(attr, 'rarity', None)
                        elif isinstance(attr, StarGiftAttributePattern):
                            e['pattern_name'] = getattr(attr, 'name', None)
                            e['pattern_rarity'] = getattr(attr, 'rarity', None)
                sticker = getattr(sg, 'sticker', None)
                if sticker:
                    for attr in getattr(sticker, 'attributes', []):
                        if isinstance(attr, DocumentAttributeSticker) and getattr(attr, 'alt', None):
                            e['emoji'] = attr.alt
                            break
                    # Download sticker image via DC, try thumbs first, then full
                    thumbs = getattr(sticker, 'thumbs', []) or []
                    thumb_sizes = []
                    for t in thumbs:
                        tb = getattr(t, 'bytes', None)
                        if tb and isinstance(tb, bytes) and len(tb) > 100:
                            # Only embed bytes with valid image headers
                            if tb[:4] == b'\x89PNG':
                                e['sticker_b64'] = 'data:image/png;base64,' + base64.b64encode(tb).decode()
                                break
                            if tb[:2] == b'\xFF\xD8':
                                e['sticker_b64'] = 'data:image/jpeg;base64,' + base64.b64encode(tb).decode()
                                break
                            if tb[:4] == b'RIFF' and len(tb) > 12 and tb[8:12] == b'WEBP':
                                e['sticker_b64'] = 'data:image/webp;base64,' + base64.b64encode(tb).decode()
                                break
                        ts = getattr(t, 'type', '')
                        if ts in ('s', 'm', 'x'): thumb_sizes.append(ts)
                    if not e.get('sticker_b64'):
                        thumb_sizes = list(dict.fromkeys(thumb_sizes)) or ['s']
                        from telethon.tl.types import InputDocumentFileLocation
                        for ts in thumb_sizes:
                            try:
                                loc = InputDocumentFileLocation(id=sticker.id, access_hash=sticker.access_hash, file_reference=sticker.file_reference, thumb_size=ts)
                                data = await client.download_file(loc)
                                if data and len(data) > 100:
                                    if data[:4] == b'\x89PNG': fmt2 = 'image/png'
                                    elif data[:2] == b'\xFF\xD8': fmt2 = 'image/jpeg'
                                    elif data[:4] == b'RIFF' and len(data) > 12 and data[8:12] == b'WEBP': fmt2 = 'image/webp'
                                    else: fmt2 = 'image/jpeg'
                                    e['sticker_b64'] = f'data:{fmt2};base64,' + base64.b64encode(data).decode()
                                    break
                            except:
                                pass
            else:
                e['name'] = str(getattr(g, 'id', '?'))
            raw_msg = getattr(g, 'message', None)
            if raw_msg: e['message'] = raw_msg.text if hasattr(raw_msg, 'text') else str(raw_msg)
            gdate = getattr(g, 'date', None)
            if gdate:
                if isinstance(gdate, datetime): e['date'] = gdate.strftime('%Y-%m-%d %H:%M')
                elif isinstance(gdate, (int, float)): e['date'] = datetime.fromtimestamp(gdate).strftime('%Y-%m-%d %H:%M')
                else: e['date'] = str(gdate)
            from_id = getattr(g, 'from_id', None)
            if from_id:
                try:
                    sender = await client.get_entity(from_id)
                    e['sender_id'] = sender.id
                    e['sender_name'] = getattr(sender, 'first_name', '') or str(sender.id)
                    if getattr(sender, 'username', None): e['sender_username'] = '@' + sender.username
                except: pass
            out.append(e)
    except Exception as ex:
        print(GL.task("Gifts", "err", f"{ex}"), flush=True)
    return out

async def get_user_chats(client, target, limit=100):
    import asyncio
    out = []
    try:
        from telethon.tl.functions.channels import GetParticipantRequest
        from telethon.tl.functions.messages import GetFullChatRequest
        from telethon.tl.types import Chat as BasicChat
        from telethon.errors import UserNotParticipantError
        dialogs = await client.get_dialogs(limit=limit)
        print(GL.task("Chats", "info", f"scanning {len(dialogs)} dialogs for {target.id}..."), flush=True)
        sem = asyncio.Semaphore(10)
        async def check(d):
            if not (d.is_group or d.is_channel): return None
            async with sem:
                ent = d.entity
                try:
                    if isinstance(ent, BasicChat):
                        fc = await client(GetFullChatRequest(chat_id=ent.id))
                        pts = getattr(fc, 'full_chat', None)
                        if pts:
                            parts = getattr(pts, 'participants', None)
                            if parts and hasattr(parts, 'participants'):
                                ids = [getattr(p, 'user_id', None) for p in parts.participants]
                                if target.id not in ids: return None
                    else:
                        await client(GetParticipantRequest(channel=ent, participant=target.id))
                    t = chat_type(ent)
                    is_private = not bool(getattr(ent, 'username', None))
                    return {'id': ent.id, 'title': getattr(ent, 'title', '') or str(ent.id), 'type': t, 'private': is_private}
                except (UserNotParticipantError, ValueError):
                    return None
                except Exception as ex:
                    print(GL.task("Chats", "warn", f"check {getattr(ent,'title','')}: {type(ent).__name__}: {ex}"), flush=True)
                    return None
        coros = [check(d) for d in dialogs]
        all_r = await asyncio.gather(*coros)
        out = [r for r in all_r if r is not None]
        out.sort(key=lambda x: x.get('title','').lower())
        print(GL.task("Chats", "ok", f"found {len(out)} chats"), flush=True)
    except Exception as ex:
        print(GL.task("Chats", "err", f"{ex}"), flush=True)
    return out


async def get_profile_photo_b64(client, user):
    try:
        buf = io.BytesIO()
        result = await client.download_profile_photo(user, file=buf)
        if result:
            buf.seek(0)
            data = buf.read()
            if data and len(data) > 100:
                return "data:image/jpeg;base64," + base64.b64encode(data).decode()
    except: pass
    return None

async def photo_to_b64(client, msg):
    try:
        buf = io.BytesIO()
        await client.download_media(msg, file=buf)
        buf.seek(0); data = buf.read()
        if not data: return None
        return "data:image/jpeg;base64," + base64.b64encode(data).decode()
    except: return None

async def collect_messages(client, chat, user_id):
    entries = []
    stats = {'total':0,'text':0,'photo':0,'sticker':0,'video':0,'audio':0,'document':0,'links':0,'replied':0,'forwarded':0,'edited':0,'hours':Counter()}
    try:
        ce = await client.get_entity(chat)
        chat_uname = getattr(ce, 'username', None)
        chat_id_raw = getattr(ce, 'id', chat)
    except:
        chat_uname = None; chat_id_raw = chat
    async for msg in client.iter_messages(chat, from_user=user_id, limit=None):
        if getattr(msg, 'action', None) is not None: continue
        stats['total'] += 1
        mtype = 'text'; text = ''; photo_b64 = None
        if msg.sticker:
            mtype = 'sticker'; text = f"sticker {getattr(msg.sticker,'emoji','') or ''}".strip(); stats['sticker'] += 1
        elif msg.photo:
            mtype = 'photo'; text = getattr(msg,'raw_text','') or getattr(msg,'caption','') or ''
            photo_b64 = await photo_to_b64(client, msg); stats['photo'] += 1
        elif msg.video:
            mtype = 'video'; text = getattr(msg,'raw_text','') or getattr(msg,'caption','') or '[video]'; stats['video'] += 1
        elif getattr(msg,'audio',None) or getattr(msg,'voice',None):
            mtype = 'audio'; text = '[audio]'; stats['audio'] += 1
        elif msg.document:
            mtype = 'document'; text = getattr(msg,'raw_text','') or getattr(msg,'caption','') or '[document]'; stats['document'] += 1
        else:
            stats['text'] += 1; text = getattr(msg,'raw_text','') or ''
        has_link = False
        for ent in (getattr(msg,'entities',None) or []):
            if isinstance(ent,(MessageEntityUrl,MessageEntityTextUrl)): has_link = True; break
        if not has_link: has_link = bool(re.search(r'https?://|t\.me/', text))
        if has_link: stats['links'] += 1
        if msg.is_reply: stats['replied'] += 1
        if msg.forward: stats['forwarded'] += 1
        if msg.edit_date: stats['edited'] += 1
        if msg.date: stats['hours'][msg.date.hour] += 1
        raw_links = re.findall(r"https?://[^\s<>\"\\']+|t\.me/[^\s<>\"\\']+", text)
        entries.append({
            'time': msg.date.strftime('%Y-%m-%d %H:%M:%S') if msg.date else '-',
            'type': mtype, 'text': text[:400].replace('\n',' ') if text else '',
            'photo_b64': photo_b64,
            'link': (f"https://t.me/{chat_uname}/{msg.id}" if chat_uname else f"tg://privatepost?channel={chat_id_raw}&post={msg.id}"),
            'raw_links': raw_links, 'replied': msg.is_reply,
            'forwarded': bool(msg.forward), 'edited': bool(msg.edit_date), 'has_link': has_link
        })
    return entries, stats

GLASS_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700&family=JetBrains+Mono:wght@400;500;600&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#07080c;--surface:rgba(255,255,255,0.055);--surface2:rgba(255,255,255,0.035);--border:rgba(255,255,255,0.10);--border-hi:rgba(140,200,255,0.30);--a1:#5ba4ff;--a2:#8b5cf6;--a3:#06d6a0;--red:#ff4f6e;--or:#ffb347;--gr:#3dffa0;--t0:#f0f4ff;--t1:#b0bfdd;--t2:#5a6a8a;--r:16px;--rs:10px}
body{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--t0);background-image:radial-gradient(ellipse 80% 60% at 10% 10%,rgba(91,164,255,0.10) 0%,transparent 60%),radial-gradient(ellipse 60% 80% at 90% 80%,rgba(139,92,246,0.09) 0%,transparent 60%)}
.wrap{max-width:940px;margin:0 auto;padding:52px 20px 100px}
.card{background:var(--surface);border-radius:16px;border:1px solid var(--border);padding:26px 28px;margin-bottom:18px;backdrop-filter:blur(32px);box-shadow:0 8px 32px rgba(0,0,0,0.45)}
.card:hover{border-color:var(--border-hi)}
.page-header{display:flex;align-items:center;gap:20px;margin-bottom:36px;border-bottom:1px solid var(--border);padding-bottom:24px}
.page-title{font-size:28px;font-weight:700;background:linear-gradient(120deg,#fff 20%,var(--a1) 80%);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.slabel{font-size:10px;font-weight:700;letter-spacing:1.8px;text-transform:uppercase;color:var(--a1);margin-bottom:16px}
.info-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}
.info-row{padding:12px 14px;background:var(--surface2);border-radius:10px;border:1px solid var(--border)}
.info-lbl{font-size:10px;font-weight:600;color:var(--t2)}
.info-val{font-size:13px;font-weight:500;color:var(--t0);font-family:JetBrains Mono,monospace}
.info-val.hi{color:var(--a1)}
.badge{display:inline-flex;padding:5px 12px;border-radius:999px;font-size:11px;font-weight:700}
.bg{background:rgba(61,255,160,0.10);color:var(--gr);border:1px solid rgba(61,255,160,0.22)}
.bb{background:rgba(91,164,255,0.10);color:var(--a1);border:1px solid rgba(91,164,255,0.25)}
.bp{background:rgba(139,92,246,0.10);color:var(--a2);border:1px solid rgba(139,92,246,0.25)}
.bt{background:rgba(91,164,255,0.08);color:var(--a1);border:1px solid rgba(91,164,255,0.18)}
.br{background:rgba(255,79,110,0.10);color:var(--red);border:1px solid rgba(255,79,110,0.22)}
.bo{background:rgba(255,179,71,0.10);color:var(--or);border:1px solid rgba(255,179,71,0.22)}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:10px}
.stat-box{padding:16px 12px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;text-align:center}
.stat-num{font-size:26px;font-weight:700;font-family:JetBrains Mono,monospace;background:linear-gradient(135deg,var(--a1),var(--a2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.stat-lbl{font-size:9px;font-weight:700;text-transform:uppercase;color:var(--t2);margin-top:6px}
.heatmap{display:grid;grid-template-columns:repeat(24,1fr);gap:3px;margin-top:10px}
.hcol{display:flex;flex-direction:column;align-items:center;gap:3px}
.hbar{width:100%;border-radius:3px;min-height:3px}
.hhour{font-size:8px;color:var(--t2);font-family:JetBrains Mono,monospace}
.page-footer{text-align:center;margin-top:48px;color:var(--t2);font-size:11px;opacity:.4}
.page-sub{font-size:12px;color:var(--t2);margin-top:4px}
.uname-pill{display:inline-flex;padding:4px 10px;border-radius:6px;font-size:11px;font-weight:500;margin:3px 4px 3px 0;background:rgba(91,164,255,0.08);border:1px solid rgba(91,164,255,0.15);color:var(--a1)}
.uname-pill.nft{border-color:rgba(139,92,246,0.3);background:rgba(139,92,246,0.08);color:var(--a2)}
.uname-pill.dead{opacity:.3}
.log-entry{display:flex;flex-wrap:wrap;gap:8px;padding:10px 0;border-bottom:1px solid var(--border);font-size:13px}
.log-time{color:var(--a1);font-family:JetBrains Mono,monospace;font-size:11px;min-width:140px}
.log-type{color:var(--t2);min-width:60px;font-size:11px}
.log-body{flex:1;min-width:200px}
.flag{display:inline-flex;padding:2px 6px;border-radius:4px;font-size:9px;font-weight:700;background:rgba(91,164,255,0.10);color:var(--a1);margin:1px}
.flag.lock{background:rgba(255,79,110,0.10);color:var(--red)}
.flag.pub{background:rgba(61,255,160,0.10);color:var(--gr)}
.chat-item{display:flex;align-items:center;gap:8px;padding:8px 0;border-bottom:1px solid var(--border);font-size:13px}
.chat-title{flex:1}
.chat-id{color:var(--t2);font-family:JetBrains Mono,monospace;font-size:11px}
.gift{padding:10px 0;font-size:13px}
.gift-card{background:var(--surface2);border:1px solid var(--border);border-radius:16px;padding:22px;margin:12px 0;text-align:center}
.gift-card:hover{border-color:var(--border-hi)}
.gift-sticker{width:96px;height:96px;object-fit:contain;margin-bottom:8px}
.gift-emoji{font-size:72px;line-height:1.1;margin-bottom:8px}
.gift-name-row{font-size:15px;font-weight:700;color:var(--t0)}
.gift-from{font-size:12px;color:var(--t2);margin-top:4px}
.gift-msg{font-size:13px;color:var(--t1);margin-top:6px;padding:8px 10px;background:rgba(255,255,255,0.04);border-radius:8px}
.gift-date{font-size:11px;color:var(--t2);margin-top:2px}
.gift-badge{display:inline-flex;padding:1px 6px;border-radius:4px;font-size:9px;font-weight:700;margin-left:6px;vertical-align:middle}
.gift-badge.limited{background:rgba(139,92,246,0.15);color:var(--a2)}
.gift-badge.birthday{background:rgba(255,179,71,0.15);color:var(--or)}
.gift-badge.hidden{background:rgba(255,255,255,0.08);color:var(--t2)}
.gift-badge.nft{background:rgba(139,92,246,0.2);color:var(--a2);border:1px solid rgba(139,92,246,0.35)}
.gift-rare{font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.gift-rare.r0{color:#8a9bb5}
.gift-rare.r1{color:#4cd964}
.gift-rare.r2{color:#5ba4ff}
.gift-rare.r3{color:#b06aff}
.gift-rare.r4{color:#ff9500}
.gift-rare.r5{color:#ff3b30}
.gift-num{font-size:14px;font-weight:700;color:var(--a2);margin-top:4px;letter-spacing:.5px}
.gift-extra{font-size:11px;color:var(--t2);margin-top:2px}
.pp-wrap{display:flex;align-items:center;gap:20px;margin-bottom:24px}
.pp-img{width:90px;height:90px;border-radius:50%;object-fit:cover;border:2px solid var(--border-hi);flex-shrink:0}
.pp-placeholder{width:90px;height:90px;border-radius:50%;background:var(--surface2);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:32px;color:var(--t2);flex-shrink:0}
"""

def build_info_html(data):
    uid = str(data.get('id',''))
    first = esc(data.get('first_name') or '')
    last = esc(data.get('last_name') or '')
    full_name = (first + ' ' + last).strip() or uid
    phone = esc(data.get('phone') or 'hidden')
    bio = esc(data.get('bio') or '')
    online = esc(data.get('last_online') or 'unknown')
    gen = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    badges = ''
    for k,c,l in [('verified','bb','Verified'),('premium','bp','Premium'),('bot','bt','Bot'),('scam','br','Scam'),('fake','br','Fake'),('restricted','bo','Restricted')]:
        if data.get(k): badges += f'<span class="badge {c}">{l}</span>'
    if not badges: badges = '<span class="badge bg">Clean</span>'
    unames = ''
    for u in (data.get('usernames') or []):
        c = 'uname-pill' + (' nft' if u.get('nft',False) else '') + ('' if u.get('active',True) else ' dead')
        unames += f'<span class="{c}">{"NFT" if u.get("nft") else "@"}{esc(u.get("username",""))}</span>'
    if not unames: unames = '<span style="color:var(--t2)">none</span>'
    chats = ''
    for ch in (data.get('common_chats') or []):
        ch_type = ch.get('type', '')
        icons = {'channel':'📢','supergroup':'👥','group':'👥','gigagroup':'💬','forum':'🗣️','chat':'👤','megagroup':'👥','broadcast':'📢'}
        icon = icons.get(ch_type.lower(), '📁')
        acc = '<span class="flag lock">🔒</span>' if ch.get('private') else '<span class="flag pub">🌐</span>'
        chats += f'<div class="chat-item">{acc}{icon}{esc(ch_type)}<span class="chat-title">{esc(str(ch.get("title","")))}</span><span class="chat-id">{ch.get("id","")}</span></div>'
    if not chats: chats = '<p style="color:var(--t2)">no common chats</p>'
    gd = data.get('gifts') or []
    gc = len(gd) if isinstance(gd, list) else 0
    has_gift_details = bool(gd)
    gifts = ''
    if has_gift_details:
        is_fallback = any(g.get('fallback') for g in gd)
        label = ' (bot)' if is_fallback else ''
        for g in gd:
            sticker_b64 = g.get('sticker_b64', '')
            emoji = g.get('emoji', '🎁')
            icon = f'<img class="gift-sticker" src="{sticker_b64}" alt="">' if sticker_b64 else f'<div class="gift-emoji">{emoji}</div>'
            nm = esc(str(g.get('name') or g.get('id') or '?'))
            is_nft = g.get('gift_num') is not None
            if is_nft:
                bg_center = g.get('bg_center')
                bg_edge = g.get('bg_edge')
                bg_style = ''
                if bg_center or bg_edge:
                    c = bg_center or '#888'
                    e = bg_edge or '#444'
                    bg_style = f' style="background:linear-gradient(135deg,{e},{c})"'
                num_html = f'<div class="gift-num">#{g["gift_num"]}</div>'
                extra_info = ''
                if g.get('model_name'):
                    r = str(g.get('model_rarity', ''))
                    r_cls = ''
                    if r.isdigit(): r_cls = f' <span class="gift-rare r{r}">{r}</span>'
                    extra_info += f'<div class="gift-extra">Model: {esc(g["model_name"])}{r_cls}</div>'
                if g.get('pattern_name'):
                    r = str(g.get('pattern_rarity', ''))
                    r_cls = ''
                    if r.isdigit(): r_cls = f' <span class="gift-rare r{r}">{r}</span>'
                    extra_info += f'<div class="gift-extra">Pattern: {esc(g["pattern_name"])}{r_cls}</div>'
                gb = '<span class="gift-badge nft">NFT</span>'
                if g.get('limited'): gb += '<span class="gift-badge limited">LIMITED</span>'
                if g.get('birthday'): gb += '<span class="gift-badge birthday">BIRTHDAY</span>'
                if g.get('name_hidden'): gb += '<span class="gift-badge hidden">HIDDEN</span>'
            else:
                bg_style = ''
                num_html = ''
                extra_info = ''
                gb = ''
                if g.get('limited'): gb += '<span class="gift-badge limited">LIMITED</span>'
                if g.get('birthday'): gb += '<span class="gift-badge birthday">BIRTHDAY</span>'
                if g.get('name_hidden'): gb += '<span class="gift-badge hidden">HIDDEN</span>'
            msg = esc(str(g.get('message') or ''))
            snd = ''
            if g.get('sender_name'):
                snd = f'<div class="gift-from">from <b>{esc(g["sender_name"])}</b>'
                if g.get('sender_username'): snd += f' {esc(g["sender_username"])}'
                snd += '</div>'
            gd_str = ''
            if g.get('date'): gd_str = f'<div class="gift-date">{esc(g["date"])}</div>'
            msg_html = f'<div class="gift-msg">{msg}</div>' if msg else ''
            gifts += f'<div class="gift-card"{bg_style}>{icon}<div class="gift-name-row">{nm}{gb}</div>{num_html}{extra_info}{snd}{gd_str}{msg_html}</div>'
    else:
        sg_cnt = data.get('stargifts_count', 0)
        if sg_cnt:
            gifts = f'<p style="color:var(--t2)">{sg_cnt} gifts (hidden)</p>'
        else:
            gifts = '<p style="color:var(--t2)">no gifts</p>'
    bio_links = data.get('links_in_bio') or []
    bio_links_html = ''
    if bio_links:
        for l in bio_links[:10]:
            bio_links_html += f'<span class="uname-pill">{esc(l)}</span>'
    reg = data.get('registration_date') or ''
    reg_html = ''
    if reg:
        reg_html = f'<div class="info-row"><span class="info-lbl">Registered</span><span class="info-val hi">{esc(reg)}</span></div>'
    age = data.get('account_age') or ''
    if age:
        reg_html += f'<div class="info-row"><span class="info-lbl">Account Age</span><span class="info-val">{esc(age)}</span></div>'
    extra = ''
    if data.get('stories_count'): extra += f'<div class="info-row"><span class="info-lbl">Stories</span><span class="info-val hi">{data["stories_count"]}</span></div>'
    if data.get('followers_count'): extra += f'<div class="info-row"><span class="info-lbl">Followers</span><span class="info-val hi">{data["followers_count"]}</span></div>'
    if data.get('contacts_count'): extra += f'<div class="info-row"><span class="info-lbl">Contacts</span><span class="info-val hi">{data["contacts_count"]}</span></div>'
    if data.get('lang_code'): extra += f'<div class="info-row"><span class="info-lbl">Language</span><span class="info-val">{esc(data["lang_code"])}</span></div>'
    if data.get('emoji_status'): extra += f'<div class="info-row"><span class="info-lbl">Emoji Status</span><span class="info-val">{esc(data["emoji_status"])}</span></div>'
    if data.get('photos_count') is not None: extra += f'<div class="info-row"><span class="info-lbl">Profile Photos</span><span class="info-val hi">{data["photos_count"]}</span></div>'
    if data.get('stargifts_count') is not None: extra += f'<div class="info-row"><span class="info-lbl">Star Gifts</span><span class="info-val hi">{data["stargifts_count"]}</span></div>'
    if data.get('wallpaper'): extra += '<div class="info-row"><span class="info-lbl">Wallpaper</span><span class="info-val hi">yes</span></div>'
    if data.get('phone_calls') is not None: extra += f'<div class="info-row"><span class="info-lbl">Phone Calls</span><span class="info-val">{esc(data["phone_calls"])}</span></div>'
    if data.get('voice_messages') is not None: extra += f'<div class="info-row"><span class="info-lbl">Voice Messages</span><span class="info-val">{esc(data["voice_messages"])}</span></div>'
    if data.get('auto_delete'): extra += f'<div class="info-row"><span class="info-lbl">Auto-Delete</span><span class="info-val">{esc(data["auto_delete"])}</span></div>'
    if data.get('forward_name'): extra += f'<div class="info-row"><span class="info-lbl">Forward Name</span><span class="info-val">{esc(data["forward_name"])}</span></div>'
    photo_b64 = data.get('photo_b64') or ''
    if photo_b64:
        photo_html = f'<div class="pp-wrap"><img class="pp-img" src="{photo_b64}" alt="photo"><div><div class="page-title" style="margin:0;font-size:24px">{full_name}</div><div class="page-sub" style="margin-top:4px">ID {uid} &middot; {gen}</div></div></div>'
    else:
        photo_html = f'<div class="pp-wrap"><div class="pp-placeholder">?</div><div><div class="page-title" style="margin:0;font-size:24px">{full_name}</div><div class="page-sub" style="margin-top:4px">ID {uid} &middot; {gen}</div></div></div>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dossier - {full_name}</title><style>{GLASS_CSS}</style></head><body>
<div class="wrap">
{photo_html}
<div class="card"><div class="slabel">Status</div><div>{badges}</div></div>
<div class="card"><div class="slabel">Info</div><div class="info-grid">
<div class="info-row"><span class="info-lbl">ID</span><span class="info-val hi">{uid}</span></div>
<div class="info-row"><span class="info-lbl">Name</span><span class="info-val">{first or "-"}</span></div>
<div class="info-row"><span class="info-lbl">Last</span><span class="info-val">{last or "-"}</span></div>
<div class="info-row"><span class="info-lbl">Phone</span><span class="info-val">{phone}</span></div>
<div class="info-row"><span class="info-lbl">Online</span><span class="info-val">{online}</span></div>
<div class="info-row"><span class="info-lbl">Common Chats</span><span class="info-val hi">{data.get("common_chats_count",0)}</span></div>{reg_html}{extra}</div></div>
<div class="card"><div class="slabel">Usernames</div><div>{unames}</div></div>
<div class="card"><div class="slabel">Bio</div><p style="white-space:pre-wrap">{bio or "(empty)"}</p>{'<div style="margin-top:10px">' + bio_links_html + '</div>' if bio_links_html else ""}</div>
<div class="card"><div class="slabel">Common Chats ({data.get("common_chats_count",0)})</div>{chats}</div>
<div class="card"><div class="slabel">Gifts{label} ({gc})</div>{gifts}</div>
<div class="page-footer">made by @s1lentpacket &middot; {gen}</div>
</div></body></html>"""

def build_logs_html(dname, uid, chat_id, entries, stats):
    gen = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    total = stats['total']
    sboxes = ''
    for lbl,val in [('Total',total),('Text',stats['text']),('Photo',stats['photo']),('Video',stats['video']),('Audio',stats['audio']),('Stickers',stats['sticker']),('Files',stats['document']),('Links',stats['links']),('Replies',stats['replied']),('Fwd',stats['forwarded']),('Edited',stats['edited'])]:
        sboxes += f'<div class="stat-box"><div class="stat-num">{val}</div><div class="stat-lbl">{lbl}</div></div>'
    hours = stats.get('hours',Counter()); maxh = max(hours.values()) or 1; hmap = ''
    for h in range(24):
        cnt = hours.get(h,0); px = max(4,int((cnt/maxh)*70)); op = 0.12+(cnt/maxh)*0.88
        hmap += f'<div class="hcol"><div class="hbar" style="height:{px}px;background:rgba(91,164,255,{op:.2f})" title="{h:02d}:00 - {cnt} msgs"></div><div class="hhour">{h:02d}</div></div>'
    rows = ''
    for e in entries:
        flags = ''
        if e['replied']: flags += '<span class="flag">REPLY</span>'
        if e['forwarded']: flags += '<span class="flag">FWD</span>'
        if e['edited']: flags += '<span class="flag">EDITED</span>'
        if e['has_link']: flags += '<span class="flag">LINK</span>'
        ph = ''
        if e.get('photo_b64'): ph = f'<img src="{e["photo_b64"]}" style="max-width:200px;border-radius:8px">'
        txt = f'<div>{esc(e["text"])}</div>' if e['text'] else ''
        lk = ''
        if e.get('link'): lk += f'<a href="{esc(e["link"])}" target="_blank">Open in TG</a>'
        rows += f'<div class="log-entry"><div class="log-time">{esc(e["time"])}</div><div class="log-type">{e["type"]}</div><div class="log-body">{ph}{txt}{lk}</div><div>{flags}</div></div>'
    if not rows: rows = '<p>No messages found.</p>'
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Logs - {esc(dname)}</title><style>{GLASS_CSS}</style></head><body>
<div class="wrap">
<div class="page-header"><div class="page-title">{esc(dname)}</div><div class="page-sub">ID {uid} &middot; chat {chat_id} &middot; {gen}</div></div>
<div class="card"><div class="slabel">Stats</div><div class="stats-grid">{sboxes}</div></div>
<div class="card"><div class="slabel">Hourly Activity</div><div class="heatmap">{hmap}</div></div>
<div class="card"><div class="slabel">Messages ({total})</div>{rows}</div>
<div class="page-footer">made by @s1lentpacket &middot; {gen}</div>
</div></body></html>"""

async def stop_listener():
    global running
    loop = asyncio.get_running_loop()
    while running:
        line = await loop.run_in_executor(None, sys.stdin.readline)
        if line.strip().lower() == 'stop':
            print("\n  Stopping...")
            running = False
            break

async def main():
    global running, afk_data, notes_data, start_time
    config = load_config()
    if config and config.get("api_id"):
        sn = f"{SESSION_NAME}_{config['api_id']}"
        client = TelegramClient(sn, config["api_id"], config["api_hash"])
        await client.connect()
        if await client.is_user_authorized():
            me = await client.get_me()
            print(GL.task("Session", "ok", f"resumed as {me.first_name or me.id}"))
        else:
            await client.disconnect()
            client = await do_login()
    else:
        client = await do_login()

    cfg = load_config()
    if cfg and cfg.get("notes"):
        notes_data = cfg["notes"]
    me = await client.get_me()
    my_id = me.id

    @client.on(events.NewMessage(pattern=r'\.help$'))
    async def help_handler(event):
        if (await event.get_sender()).id != my_id: return
        HELP = """<b>USERBOT COMMANDS</b>

<b>INFORMATION</b>
  <code>.help</code>         - This help
  <code>.id</code>           - Chat/user IDs
  <code>.whois &lt;u&gt;</code>    - Quick user lookup
  <code>.info &lt;u&gt; &lt;f&gt;</code> - Full dossier HTML (-s for JSON)
  <code>.system</code>       - Bot runtime info
  <code>.chats [N]</code>    - List dialogs
  <code>.commonchats &lt;u&gt;</code> - Common chats with user
  <code>.ping</code>         - Latency check

<b>ANALYSIS</b>
  <code>.logs &lt;u&gt; &lt;f&gt;</code>  - Message history HTML
  <code>.stats</code>        - Your account stats
  <code>.top [N]</code>      - Top users in chat
  <code>.activity</code>     - Hourly activity
  <code>.search &lt;q&gt;</code>   - Search messages

<b>TOOLS</b>
  <code>.echo &lt;t&gt;</code>     - Repeat text
  <code>.type &lt;t&gt;</code>     - Typewriter effect
  <code>.purge [N]</code>    - Delete last N messages
  <code>.save &lt;t&gt;</code>     - Save a note
  <code>.notes</code>        - Show notes
  <code>.delnote &lt;N&gt;</code>  - Delete note

<b>UTILITIES</b>
  <code>.neuro &lt;t&gt;</code>    - AI via @TypespaceBot
  <code>.afk [r]</code>      - AFK mode (auto-reply)

<i>Type 'stop' to quit</i>"""
        await client.edit_message(event.chat_id, event.message.id, HELP, parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.id$'))
    async def id_handler(event):
        if (await event.get_sender()).id != my_id: return
        msg = event.message; chat = await event.get_chat()
        cid = getattr(chat,'id','?')
        ctitle = getattr(chat,'title',getattr(chat,'username','Chat'))
        text = f"Chat ID: {cid}\nChat: {ctitle}\n"
        if msg.is_reply:
            replied = await msg.get_reply_message()
            if replied:
                sender = await replied.get_sender()
                text += f"User ID: {sender.id}\nUser: {getattr(sender,'first_name','') or sender.id}"
        else:
            text += f"Your ID: {my_id}"
        await client.edit_message(event.chat_id, event.message.id, f"<pre>{text}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.whois\s+(\S+)'))
    async def whois_handler(event):
        if (await event.get_sender()).id != my_id: return
        inp = event.pattern_match.group(1).strip(); mid = event.message.id
        await client.edit_message(event.chat_id, mid, "Resolving...")
        try:
            user = await client.get_entity(resolve_target(inp))
        except Exception as e:
            await client.edit_message(event.chat_id, mid, f"Error: {e}"); return
        info = [f"ID: {user.id}", f"Name: {getattr(user,'first_name','')} {getattr(user,'last_name','') or ''}",
                f"Username: @{getattr(user,'username','N/A')}", f"Phone: {getattr(user,'phone','hidden')}",
                f"Bot: {getattr(user,'bot',False)}", f"Premium: {getattr(user,'premium',False)}",
                f"Verified: {getattr(user,'verified',False)}", f"Status: {format_status(getattr(user,'status',None))}"]
        txt = "\n".join(info)
        await client.edit_message(event.chat_id, mid, f"<pre>{txt}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.chats\s*(\d*)'))
    async def chats_handler(event):
        if (await event.get_sender()).id != my_id: return
        n = min(max(1,int(event.pattern_match.group(1) or '10')),50)
        mid = event.message.id
        await client.edit_message(event.chat_id, mid, f"Fetching {n} chats...")
        dialogs = await client.get_dialogs(limit=n)
        lines = [f"Last {len(dialogs)} chats:"]
        for d in dialogs:
            lines.append(f"[{d.id}] {d.name or '???'} ({d.unread_count} unread)")
        txt = "\n".join(lines)
        await client.edit_message(event.chat_id, mid, f"<pre>{txt}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.commonchats\s+(\S+)'))
    async def commonchats_handler(event):
        if (await event.get_sender()).id != my_id: return
        target = event.pattern_match.group(1).strip(); mid = event.message.id
        await client.edit_message(event.chat_id, mid, "Resolving...")
        try:
            user = await client.get_entity(resolve_target(target))
        except Exception as e:
            await client.edit_message(event.chat_id, mid, f"Error: {e}"); return
        await client.edit_message(event.chat_id, mid, f"Fetching chats for {user.id}...")
        try:
            ch_list = await get_user_chats(client, user, limit=100)
            lines = [f"Chats for {getattr(user,'first_name','') or user.id}: {len(ch_list)}"]
            for ch in ch_list[:50]:
                lock = '🔒' if ch.get('private') else '🌐'
                lines.append(f"{lock}[{ch['id']}] {ch.get('title','?')} ({ch.get('type','?')})")
            if not ch_list: lines = [f"No chats found for {user.id}"]
            txt = "\n".join(lines)
            await client.edit_message(event.chat_id, mid, f"<pre>{txt}</pre>", parse_mode='html')
        except Exception as e:
            await client.edit_message(event.chat_id, mid, f"Error: {e}")

    @client.on(events.NewMessage(pattern=r'\.stats$'))
    async def stats_handler(event):
        if (await event.get_sender()).id != my_id: return
        mid = event.message.id
        await client.edit_message(event.chat_id, mid, "Collecting stats...")
        me_full = await client.get_me()
        dialogs = await client.get_dialogs(limit=200)
        total_chats = len(dialogs)
        total_unread = sum(d.unread_count for d in dialogs)
        created = getattr(me_full,'date',None)
        age = "unknown"
        if created: age = f"{(datetime.now()-created).days} days"
        info = [f"User: {me_full.first_name or ''} (@{me_full.username or 'N/A'})", f"ID: {me_full.id}",
                f"Phone: {getattr(me_full,'phone','hidden')}", f"Age: {age}",
                f"Premium: {getattr(me_full,'premium',False)}", f"Dialogs: {total_chats}",
                f"Unread: {total_unread}", f"Uptime: {str(datetime.now()-start_time).split('.')[0]}"]
        txt = "\n".join(info)
        await client.edit_message(event.chat_id, mid, f"<pre>{txt}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.system$'))
    async def system_handler(event):
        if (await event.get_sender()).id != my_id: return
        uptime = str(datetime.now()-start_time).split('.')[0]
        import platform
        cfg = load_config()
        aid = (cfg or {}).get("api_id", "?")
        info = [f"UserBot v{VERSION}", f"Python: {sys.version.split()[0]}",
                f"OS: {platform.system()} {platform.release()}", f"Uptime: {uptime}",
                f"Session: {SESSION_NAME}", f"API ID: {aid}"]
        txt = "\n".join(info)
        await client.edit_message(event.chat_id, event.message.id, f"<pre>{txt}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.top\s*(\d*)'))
    async def top_handler(event):
        if (await event.get_sender()).id != my_id: return
        n = min(max(1,int(event.pattern_match.group(1) or '10')),30)
        mid = event.message.id
        await client.edit_message(event.chat_id, mid, "Analyzing...")
        counter = Counter()
        async for msg in client.iter_messages(event.chat_id, limit=500):
            if msg.sender_id: counter[msg.sender_id] += 1
        if not counter:
            await client.edit_message(event.chat_id, mid, "No data"); return
        lines = [f"Top {min(n,len(counter))} users (last 500):"]
        for uid,cnt in counter.most_common(n):
            try:
                u = await client.get_entity(uid)
                name = getattr(u,'first_name','') or str(uid)
            except: name = str(uid)
            lines.append(f"{name}: {cnt}")
        txt = "\n".join(lines)
        await client.edit_message(event.chat_id, mid, f"<pre>{txt}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.activity$'))
    async def activity_handler(event):
        if (await event.get_sender()).id != my_id: return
        mid = event.message.id
        await client.edit_message(event.chat_id, mid, "Analyzing...")
        hours = Counter()
        async for msg in client.iter_messages(event.chat_id, limit=500):
            if msg.date: hours[msg.date.hour] += 1
        if not hours: await client.edit_message(event.chat_id,mid,"No data"); return
        mx = max(hours.values()) or 1
        lines = ["Activity (UTC):"]
        for h in range(24):
            cnt = hours.get(h,0); bar = "#" * int((cnt/mx)*20)
            lines.append(f"{h:02d}:00 {bar} {cnt}")
        txt = "\n".join(lines)
        await client.edit_message(event.chat_id, mid, f"<pre>{txt}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.search\s+(.+)'))
    async def search_handler(event):
        if (await event.get_sender()).id != my_id: return
        q = event.pattern_match.group(1).strip(); mid = event.message.id
        await client.edit_message(event.chat_id, mid, f"Searching: {q[:50]}...")
        results = []
        async for msg in client.iter_messages(event.chat_id, limit=200, search=q):
            if msg.text: results.append(msg)
        if not results:
            await client.edit_message(event.chat_id, mid, f"No results for: {q}"); return
        txt = f"Found {len(results)} for '{q}':\n"
        for i,msg in enumerate(results[:10]):
            sender = await msg.get_sender()
            sname = getattr(sender,'first_name','') or str(msg.sender_id)
            txt += f"{i+1}. {sname}: {(msg.text or '')[:80].replace(chr(10),' ')}\n"
        if len(results) > 10: txt += f"... +{len(results)-10} more"
        await client.edit_message(event.chat_id, mid, f"<pre>{txt}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.ping$'))
    async def ping_handler(event):
        if (await event.get_sender()).id != my_id: return
        t1 = time.time()
        msg = await client.edit_message(event.chat_id, event.message.id, "Pong...")
        t2 = time.time()
        ms = round((t2 - t1) * 1000)
        await client.edit_message(event.chat_id, event.message.id, f"Pong! {ms}ms")

    @client.on(events.NewMessage(pattern=r'\.echo\s+(.+)'))
    async def echo_handler(event):
        if (await event.get_sender()).id != my_id: return
        txt = event.pattern_match.group(1).strip()
        await client.edit_message(event.chat_id, event.message.id, txt)

    @client.on(events.NewMessage(pattern=r'\.purge\s*(\d*)'))
    async def purge_handler(event):
        if (await event.get_sender()).id != my_id: return
        n = min(max(1, int(event.pattern_match.group(1) or '10')), 100)
        mid = event.message.id
        await client.edit_message(event.chat_id, mid, f"Deleting {n} messages...")
        deleted = 0
        async for msg in client.iter_messages(event.chat_id, from_user=my_id, limit=n):
            await msg.delete()
            deleted += 1
        await client.send_message(event.chat_id, f"Deleted {deleted} messages")

    @client.on(events.NewMessage(pattern=r'\.type\s+(.+)'))
    async def type_handler(event):
        if (await event.get_sender()).id != my_id: return
        txt = event.pattern_match.group(1).strip()
        out = ""
        for ch in txt:
            out += ch
            try:
                await client.edit_message(event.chat_id, event.message.id, out)
            except tlerrors.MessageNotModifiedError:
                pass
            await asyncio.sleep(0.1)

    @client.on(events.NewMessage(pattern=r'\.save\s+(.+)'))
    async def save_handler(event):
        if (await event.get_sender()).id != my_id: return
        txt = event.pattern_match.group(1).strip()
        notes_data.append(txt)
        save_config({"notes": notes_data})
        await client.edit_message(event.chat_id, event.message.id, f"Saved note #{len(notes_data)}")

    @client.on(events.NewMessage(pattern=r'\.notes$'))
    async def notes_handler(event):
        if (await event.get_sender()).id != my_id: return
        if not notes_data:
            await client.edit_message(event.chat_id, event.message.id, "No notes")
            return
        lines = [f"{i+1}. {n}" for i, n in enumerate(notes_data)]
        txt = "\n".join(lines)
        await client.edit_message(event.chat_id, event.message.id, f"<pre>{txt}</pre>", parse_mode='html')

    @client.on(events.NewMessage(pattern=r'\.delnote\s*(\d*)'))
    async def delnote_handler(event):
        if (await event.get_sender()).id != my_id: return
        n = int(event.pattern_match.group(1) or '0')
        if not n or n < 1 or n > len(notes_data):
            await client.edit_message(event.chat_id, event.message.id, "Invalid note number")
            return
        removed = notes_data.pop(n - 1)
        save_config({"notes": notes_data})
        await client.edit_message(event.chat_id, event.message.id, f"Deleted note #{n}: {removed[:50]}")

    @client.on(events.NewMessage(pattern=r'\.afk\s*(.*)'))
    async def afk_toggle(event):
        if (await event.get_sender()).id != my_id: return
        reason = event.pattern_match.group(1).strip() or "AFK"
        if afk_data['enabled']:
            afk_data['enabled'] = False
            await client.edit_message(event.chat_id, event.message.id, "AFK off")
        else:
            afk_data['enabled'] = True; afk_data['reason'] = reason; afk_data['since'] = datetime.now()
            await client.edit_message(event.chat_id, event.message.id, f"AFK on: {reason}")

    @client.on(events.NewMessage(incoming=True))
    async def afk_reply(event):
        if not afk_data['enabled'] or not event.is_private: return
        sender = await event.get_sender()
        if sender.id == my_id: return
        mins = int((datetime.now()-afk_data['since']).total_seconds()/60)
        await event.reply(f"AFK ({afk_data['reason']}) - {mins}min away")

    @client.on(events.NewMessage(pattern=r'\.info\s+(\S+)\s+(\S+)(?:\s+(-s))?'))
    async def info_handler(event):
        if (await event.get_sender()).id != my_id: return
        target = event.pattern_match.group(1).strip()
        fname = event.pattern_match.group(2).strip()
        flag_s = event.pattern_match.group(3) == '-s' if event.pattern_match.group(3) else False
        cid, mid = event.chat_id, event.message.id
        for ext in ('.json','.txt','.html'):
            if fname.endswith(ext): fname = fname[:-len(ext)]
        fname += '.html'
        await client.edit_message(cid, mid, "Collecting dossier...")
        try:
            user = await client.get_entity(resolve_target(target))
        except Exception as e:
            await client.edit_message(cid, mid, f"Error: {e}"); return
        try:
            raw = await client(GetFullUserRequest(user.id))
            uf = getattr(raw,'full_user',raw)
            common_chats = []
            try:
                common_chats = await get_user_chats(client, user, limit=100)
            except: pass
            ccnt = len(common_chats)
            gifts = await get_gifts(client,user.id)
            bio_text = (getattr(uf,'about','') or '') if uf else ''
            bio_links = re.findall(r'https?://[^\s]+|@[a-zA-Z0-9_]+',bio_text)
            unames = []
            if getattr(user,'username',None):
                unames.append({'username':user.username,'active':True,'nft':False})
            if hasattr(user,'usernames') and user.usernames:
                for u in user.usernames:
                    e = {'username':getattr(u,'username',str(u)),'active':getattr(u,'active',False),'nft':getattr(u,'editable',None) is False}
                    if not any(x['username']==e['username'] for x in unames): unames.append(e)
            ccnt = (getattr(uf,'common_chats_count',0) or len(common_chats)) if uf else len(common_chats)
            reg_date = getattr(user, 'date', None)
            registration_date_str = ''; account_age_str = ''
            if reg_date:
                if isinstance(reg_date, datetime): dt = reg_date
                elif isinstance(reg_date, (int, float)): dt = datetime.fromtimestamp(reg_date)
                else: dt = None
                if dt:
                    registration_date_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                    age_days = (datetime.now() - dt).days
                    account_age_str = f"{age_days} days ({age_days // 365}y {age_days % 365 // 30}m)"
            data = {'id':user.id,'first_name':getattr(user,'first_name',None),'last_name':getattr(user,'last_name',None),
                    'usernames':unames,'phone':getattr(user,'phone',None),'bio':bio_text,
                    'verified':getattr(user,'verified',False),'premium':getattr(user,'premium',False),
                    'bot':getattr(user,'bot',False),'scam':getattr(user,'scam',False),'fake':getattr(user,'fake',False),
                    'restricted':getattr(user,'restricted',False),'common_chats_count':ccnt,'common_chats':common_chats,
                    'gifts':gifts,'links_in_bio':bio_links,'last_online':format_status(getattr(user,'status',None)),
                    'registration_date': registration_date_str, 'account_age': account_age_str}
            if getattr(user, 'lang_code', None): data['lang_code'] = user.lang_code
            if uf:
                if getattr(uf,'wallpaper',None): data['wallpaper']=True
                if hasattr(uf,'stories_count'): data['stories_count']=uf.stories_count
                if hasattr(uf,'followers_count'): data['followers_count']=uf.followers_count
                if getattr(uf,'contacts_count',None): data['contacts_count']=uf.contacts_count
                es = getattr(uf,'emoji_status',None)
                if es and type(es).__name__ != 'EmojiStatusEmpty':
                    data['emoji_status'] = str(es)
                pa = getattr(uf,'phone_calls_available',None)
                if pa is not None: data['phone_calls'] = 'available' if pa else 'private'
                vm = getattr(uf,'voice_messages_forbidden',None)
                if vm is not None: data['voice_messages'] = 'disabled' if vm else 'enabled'
                ttl = getattr(uf,'ttl_period',None)
                if ttl: data['auto_delete'] = f'{ttl // 86400} days' if ttl >= 86400 else f'{ttl}s'
                fwd = getattr(uf,'private_forward_name',None)
                if fwd: data['forward_name'] = fwd
                sg_cnt = getattr(uf, 'stargifts_count', None)
                if sg_cnt is not None: data['stargifts_count'] = sg_cnt
            try:
                photos = await client.get_profile_photos(user.id, limit=10)
                data['photos_count'] = len(photos)
            except: pass
            try:
                photo_b64 = await get_profile_photo_b64(client, user)
                if photo_b64: data['photo_b64'] = photo_b64
            except: pass
            path = os.path.join(os.getcwd(),fname)
            with open(path,'w',encoding='utf-8') as f: f.write(build_info_html(data))
            dname = data.get('first_name') or str(user.id)
            await client.send_file(cid, path, caption=f"Dossier: {dname}")
            if flag_s:
                pretty = json.dumps(data,ensure_ascii=False,indent=2)
                for chunk in [pretty[i:i+3900] for i in range(0,len(pretty),3900)]:
                    await client.send_message(cid, f"<pre>{chunk}</pre>", parse_mode='html')
            await client.edit_message(cid, mid, f"Done: {fname}")
        except Exception as e:
            await client.edit_message(cid, mid, f"Error: {e}")


    @client.on(events.NewMessage(pattern=r'\.info\s+(\S+)\s*(-s)?$'))
    async def info_fast_handler(event):
        if (await event.get_sender()).id != my_id: return
        target = event.pattern_match.group(1).strip()
        flag_s = event.pattern_match.group(2) == '-s' if event.pattern_match.group(2) else False
        cid, mid = event.chat_id, event.message.id
        fname = f"dossier_{target.replace('@','')}.html"
        await client.edit_message(cid, mid, "Collecting dossier...")
        try:
            user = await client.get_entity(resolve_target(target))
        except Exception as e:
            await client.edit_message(cid, mid, f"Error: {e}"); return
        try:
            raw = await client(GetFullUserRequest(user.id))
            uf = getattr(raw,'full_user',raw)
            common_chats = []
            try:
                common_chats = await get_user_chats(client, user, limit=100)
            except: pass
            ccnt = len(common_chats)
            gifts = await get_gifts(client,user.id)
            bio_text = (getattr(uf,'about','') or '') if uf else ''
            bio_links = re.findall(r'https?://[^\s]+|@[a-zA-Z0-9_]+',bio_text)
            unames = []
            if getattr(user,'username',None):
                unames.append({'username':user.username,'active':True,'nft':False})
            if hasattr(user,'usernames') and user.usernames:
                for u in user.usernames:
                    e = {'username':getattr(u,'username',str(u)),'active':getattr(u,'active',False),'nft':getattr(u,'editable',None) is False}
                    if not any(x['username']==e['username'] for x in unames): unames.append(e)
            ccnt = (getattr(uf,'common_chats_count',0) or len(common_chats)) if uf else len(common_chats)
            reg_date = getattr(user, 'date', None)
            registration_date_str = ''; account_age_str = ''
            if reg_date:
                if isinstance(reg_date, datetime): dt = reg_date
                elif isinstance(reg_date, (int, float)): dt = datetime.fromtimestamp(reg_date)
                else: dt = None
                if dt:
                    registration_date_str = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                    age_days = (datetime.now() - dt).days
                    account_age_str = f"{age_days} days ({age_days // 365}y {age_days % 365 // 30}m)"
            data = {'id':user.id,'first_name':getattr(user,'first_name',None),'last_name':getattr(user,'last_name',None),
                    'usernames':unames,'phone':getattr(user,'phone',None),'bio':bio_text,
                    'verified':getattr(user,'verified',False),'premium':getattr(user,'premium',False),
                    'bot':getattr(user,'bot',False),'scam':getattr(user,'scam',False),'fake':getattr(user,'fake',False),
                    'restricted':getattr(user,'restricted',False),'common_chats_count':ccnt,'common_chats':common_chats,
                    'gifts':gifts,'links_in_bio':bio_links,'last_online':format_status(getattr(user,'status',None)),
                    'registration_date': registration_date_str, 'account_age': account_age_str}
            if getattr(user, 'lang_code', None): data['lang_code'] = user.lang_code
            if uf:
                if getattr(uf,'wallpaper',None): data['wallpaper']=True
                if hasattr(uf,'stories_count'): data['stories_count']=uf.stories_count
                if hasattr(uf,'followers_count'): data['followers_count']=uf.followers_count
                if getattr(uf,'contacts_count',None): data['contacts_count']=uf.contacts_count
                es = getattr(uf,'emoji_status',None)
                if es and type(es).__name__ != 'EmojiStatusEmpty':
                    data['emoji_status'] = str(es)
                pa = getattr(uf,'phone_calls_available',None)
                if pa is not None: data['phone_calls'] = 'available' if pa else 'private'
                vm = getattr(uf,'voice_messages_forbidden',None)
                if vm is not None: data['voice_messages'] = 'disabled' if vm else 'enabled'
                ttl = getattr(uf,'ttl_period',None)
                if ttl: data['auto_delete'] = f'{ttl // 86400} days' if ttl >= 86400 else f'{ttl}s'
                fwd = getattr(uf,'private_forward_name',None)
                if fwd: data['forward_name'] = fwd
                sg_cnt = getattr(uf, 'stargifts_count', None)
                if sg_cnt is not None: data['stargifts_count'] = sg_cnt
            try:
                photos = await client.get_profile_photos(user.id, limit=10)
                data['photos_count'] = len(photos)
            except: pass
            try:
                photo_b64 = await get_profile_photo_b64(client, user)
                if photo_b64: data['photo_b64'] = photo_b64
            except: pass
            path = os.path.join(os.getcwd(),fname)
            with open(path,'w',encoding='utf-8') as f: f.write(build_info_html(data))
            dname = data.get('first_name') or str(user.id)
            await client.send_file(cid, path, caption=f"Dossier: {dname}")
            if flag_s:
                pretty = json.dumps(data,ensure_ascii=False,indent=2)
                for chunk in [pretty[i:i+3900] for i in range(0,len(pretty),3900)]:
                    await client.send_message(cid, f"<pre>{chunk}</pre>", parse_mode='html')
            await client.edit_message(cid, mid, f"Done: {fname}")
        except Exception as e:
            await client.edit_message(cid, mid, f"Error: {e}")
    @client.on(events.NewMessage(pattern=r'\.logs\s+(\S+)(?:\s+(\S+))?'))
    async def logs_fast_handler(event):
        if (await event.get_sender()).id != my_id: return
        target = event.pattern_match.group(1).strip()
        fname = (event.pattern_match.group(2) or target.replace('@','')).strip()
        cid, mid = event.chat_id, event.message.id
        for ext in ('.json','.txt','.html'):
            if fname.endswith(ext): fname = fname[:-len(ext)]
        fname += '.html'
        await client.edit_message(cid, mid, "Resolving...")
        try:
            user = await client.get_entity(resolve_target(target))
        except Exception as e:
            await client.edit_message(cid, mid, f"Error: {e}"); return
        await client.edit_message(cid, mid, f"ID: {user.id}. Collecting messages...")
        try:
            entries, stats = await collect_messages(client, cid, user.id)
            if not entries:
                await client.edit_message(cid, mid, f"No messages from {user.id}"); return
            dname = getattr(user,'first_name',None) or str(user.id)
            html = build_logs_html(dname, user.id, cid, entries, stats)
            path = os.path.join(os.getcwd(),fname)
            with open(path,'w',encoding='utf-8') as f: f.write(html)
            await client.send_file(cid, path, caption=f"Logs {dname} ({len(entries)} msgs)")
            await client.edit_message(cid, mid, f"Done: {fname}")
        except Exception as e:
            await client.edit_message(cid, mid, f"Error: {e}")

    @client.on(events.NewMessage(pattern=r'\.neuro\s+(.+)'))
    async def neuro_handler(event):
        if (await event.get_sender()).id != my_id: return
        q = event.pattern_match.group(1).strip(); cid,mid = event.chat_id,event.message.id
        await client.edit_message(cid,mid, f"AI: {q[:50]}...")
        await client.send_message('@TypespaceBot',q)
        await asyncio.sleep(10)
        answer = None
        async for msg in client.iter_messages('@TypespaceBot',limit=10):
            if msg.out: continue
            t = msg.raw_text or ''
            if not t.strip() or 'Processing' in t: continue
            answer = t; break
        if not answer:
            await client.edit_message(cid,mid, "AI no response"); return
        if len(answer) > 3900: answer = answer[:3900]+"..."
        await client.edit_message(cid,mid, f"**AI:**\n{answer}", parse_mode='markdown')

    asyncio.create_task(stop_listener())
    print()
    print(GL.box(" COMMANDS ", [
        ".help  .id  .whois  .info  .logs  .neuro",
        ".stats  .chats  .commonchats  .top  .activity  .search  .afk",
        ".ping  .echo  .type  .purge  .save  .notes  .system",
    ], 56))
    print()
    print(f"  {GL.BOLD}{GL.GREEN}[+] UserBot v{VERSION} ready{GL.RESET}")
    print(f"  {GL.DIM}Type .help for commands  |  'stop' to exit{GL.RESET}")
    print(f"  {GL.grad('made by @s1lentpacket', '#8b5cf6', '#5ba4ff')}")
    print()
    while running:
        await asyncio.sleep(1)
    await client.disconnect()
    print(f"\n  {GL.task('Bye','ok','disconnected')}")

if __name__ == "__main__":
    print(GL.logo())
    print(f"  {GL.grad('made by @s1lentpacket')}")
    print(f"  {GL.DIM}UserBot v{VERSION}  |  {len(API_CREDENTIALS)} built-in API keys{GL.RESET}")
    print(f"  {GL.DIM}Just enter your phone number to login{GL.RESET}")
    print()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n  {GL.RED}[!] Interrupted{GL.RESET}")
    except Exception as e:
        print(f"\n  {GL.RED}[x] Fatal error: {e}{GL.RESET}")
        import traceback
        traceback.print_exc()
        print(f"\n  {GL.DIM}Press Enter to exit...{GL.RESET}")
        input()
