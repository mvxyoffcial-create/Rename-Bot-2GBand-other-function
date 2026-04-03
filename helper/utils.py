import math, time, re, os, shutil
from datetime import datetime
from pytz import timezone
from config import Config, Txt
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ULTRA-FAST PROGRESS BAR
#   • Updates every 2 s instead of 5 s for snappier UI
#   • Skips edit if percentage hasn't meaningfully changed (saves flood-wait)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_last_edit: dict = {}   # message_id → (last_time, last_pct)

async def progress_for_pyrogram(current, total, ud_type, message, start):
    now = time.time()
    diff = now - start
    if diff == 0:
        return

    # Throttle: update every 2 s OR on completion
    mid = message.id
    last_time, last_pct = _last_edit.get(mid, (0, -1))
    percentage = current * 100 / total
    if current != total and (now - last_time) < 2 and abs(percentage - last_pct) < 1:
        return
    _last_edit[mid] = (now, percentage)

    speed = current / diff
    elapsed_ms = round(diff) * 1000
    eta_ms = round((total - current) / speed) * 1000 if speed > 0 else 0
    total_ms = elapsed_ms + eta_ms

    elapsed_str = TimeFormatter(milliseconds=elapsed_ms)
    eta_str     = TimeFormatter(milliseconds=total_ms)

    filled = math.floor(percentage / 5)
    progress = "▣" * filled + "▢" * (20 - filled)

    tmp = progress + Txt.PROGRESS_BAR.format(
        round(percentage, 2),
        humanbytes(current),
        humanbytes(total),
        humanbytes(speed),
        eta_str if eta_str else "0 s"
    )
    try:
        await message.edit(
            text=f"{ud_type}\n\n{tmp}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("✖️ Cancel ✖️", callback_data="close")]]
            )
        )
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   HUMAN-READABLE BYTES  (power-of-1024)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def humanbytes(size):
    if not size:
        return ""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   TIME FORMATTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes   = divmod(minutes, 60)
    days, hours      = divmod(hours, 24)
    parts = (
        (f"{days}d, "         if days         else "") +
        (f"{hours}h, "        if hours        else "") +
        (f"{minutes}m, "      if minutes      else "") +
        (f"{seconds}s, "      if seconds      else "") +
        (f"{milliseconds}ms, " if milliseconds else "")
    )
    return parts[:-2] if parts else "0 s"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   CONVERT  seconds → H:MM:SS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def convert(seconds):
    seconds = int(seconds) % 86400
    h = seconds // 3600
    seconds %= 3600
    m = seconds // 60
    s = seconds % 60
    return "%d:%02d:%02d" % (h, m, s)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   LOG NEW USER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def send_log(b, u):
    if Config.LOG_CHANNEL is not None:
        curr = datetime.now(timezone("Asia/Kolkata"))
        date = curr.strftime('%d %B, %Y')
        t    = curr.strftime('%I:%M:%S %p')
        await b.send_message(
            Config.LOG_CHANNEL,
            f"<b><u>New User Started The Bot :</u></b> \n\n"
            f"<b>User Mention</b> : {u.mention}\n"
            f"<b>User ID</b> : `{u.id}`\n"
            f"<b>First Name</b> : {u.first_name} \n"
            f"<b>Last Name</b> : {u.last_name} \n"
            f"<b>User Name</b> : @{u.username} \n"
            f"<b>User Link</b> : <a href='tg://openmessage?user_id={u.id}'>Click Here</a>\n\n"
            f"<b>Date</b> : {date}\n<b>Time</b> : {t}"
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   PREFIX / SUFFIX HELPER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def add_prefix_suffix(input_string, prefix='', suffix=''):
    pattern = r'(?P<filename>.*?)(\.\w+)?$'
    match = re.search(pattern, input_string)
    if not match:
        return input_string
    filename  = match.group('filename')
    extension = match.group(2) or ''
    p = prefix or ''
    s = suffix or ''
    if p and s:
        return f"{p}{filename} {s}{extension}"
    if p:
        return f"{p}{filename}{extension}"
    if s:
        return f"{filename} {s}{extension}"
    return f"{filename}{extension}"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   MAKE DIRECTORY  (wipe & recreate)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def makedir(name: str):
    """Create a fresh directory, removing any existing one first."""
    if os.path.exists(name):
        shutil.rmtree(name)
    os.mkdir(name)


# Jishu Developer
# Don't Remove Credit 🥺
# Telegram Channel @MadflixBotz
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
# Contact @MadflixSupport
