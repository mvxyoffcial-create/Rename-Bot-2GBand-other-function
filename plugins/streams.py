from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.ffmpeg import fix_thumb, take_screen_shot
from helper.database import jishubotz
from helper.utils import progress_for_pyrogram, humanbytes, convert
import os, time, json, asyncio


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   FFPROBE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def get_streams(file_path):
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams", "-show_format",
        file_path
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    try:
        data = json.loads(stdout.decode())
        return data.get("streams", []), data.get("format", {})
    except Exception:
        return [], {}


def stream_label(stream):
    idx        = stream.get("index", "?")
    codec_type = stream.get("codec_type", "unknown").upper()
    codec_name = stream.get("codec_name", "?")
    tags       = stream.get("tags", {})
    lang       = tags.get("language", "")
    title      = tags.get("title", "")

    icons = {"VIDEO": "🎞", "AUDIO": "🔊", "SUBTITLE": "💬", "ATTACHMENT": "📎"}
    icon  = icons.get(codec_type, "📄")
    label = f"{icon} [{idx}] {codec_type} • {codec_name}"
    if lang:
        label += f" • {lang}"
    if title:
        label += f" • {title[:20]}{'...' if len(title) > 20 else ''}"
    if codec_type == "VIDEO":
        w, h = stream.get("width", ""), stream.get("height", "")
        if w and h:
            label += f" • {w}x{h}"
    elif codec_type == "AUDIO":
        ch = stream.get("channels", "")
        if ch:
            label += f" • {ch}ch"
    return label


def format_stream_info(streams, fmt):
    duration = fmt.get("duration", "?")
    size     = fmt.get("size", "0")
    try:
        secs = int(float(duration))
        h, rem = divmod(secs, 3600)
        m, s   = divmod(rem, 60)
        dur_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    except Exception:
        dur_str = "Unknown"

    text = (
        f"📊 **File Streams Info**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ **Duration:** `{dur_str}`\n"
        f"📦 **Size:** `{humanbytes(int(size))}`\n"
        f"🔢 **Total Streams:** `{len(streams)}`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
    )
    for s in streams:
        idx        = s.get("index", "?")
        codec_type = s.get("codec_type", "unknown").upper()
        codec_name = s.get("codec_name", "?")
        tags       = s.get("tags", {})
        lang       = tags.get("language", "und")
        title      = tags.get("title", "-")
        icons = {"VIDEO": "🎞", "AUDIO": "🔊", "SUBTITLE": "💬", "ATTACHMENT": "📎"}
        icon  = icons.get(codec_type, "📄")
        text += f"{icon} **Stream #{idx}** — `{codec_type}`\n"
        text += f"  ├ Codec: `{codec_name}`\n"
        text += f"  ├ Language: `{lang}`\n"
        text += f"  └ Title: `{title}`\n"
        if codec_type == "VIDEO":
            w, h = s.get("width","?"), s.get("height","?")
            fps  = s.get("r_frame_rate","?")
            text += f"  ├ Resolution: `{w}x{h}`\n"
            text += f"  └ FPS: `{fps}`\n"
        elif codec_type == "AUDIO":
            ch, sr = s.get("channels","?"), s.get("sample_rate","?")
            text += f"  ├ Channels: `{ch}`\n"
            text += f"  └ Sample Rate: `{sr}Hz`\n"
        text += "\n"
    return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   STEP 1 — rmstream_go / exstream_go
#   callback_data = "rmstream_go_{file_msg_id}"
#                   "exstream_go_{file_msg_id}"
#
#   FIX: file message ID is embedded in callback_data
#        so we fetch it directly — no reply chain issues
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex(r"^rmstream_go_(\d+)$"))
async def rmstream_go(bot, query: CallbackQuery):
    await query.answer()
    file_msg_id = int(query.data.split("_")[-1])
    await handle_stream_action(bot, query, "remove", file_msg_id)


@Client.on_callback_query(filters.regex(r"^exstream_go_(\d+)$"))
async def exstream_go(bot, query: CallbackQuery):
    await query.answer()
    file_msg_id = int(query.data.split("_")[-1])
    await handle_stream_action(bot, query, "extract", file_msg_id)


async def handle_stream_action(bot, query: CallbackQuery, action: str, file_msg_id: int):
    user_id = query.from_user.id
    chat_id = query.message.chat.id

    # ✅ FIX: fetch file message directly by ID — no reply chain needed
    try:
        file_message = await bot.get_messages(chat_id, file_msg_id)
    except Exception as e:
        return await query.message.edit(f"❌ Could not fetch original file: `{e}`")

    if not file_message or not file_message.media:
        return await query.message.edit("❌ Original file not found. Please re-send the file.")

    file     = getattr(file_message, file_message.media.value)
    filename = getattr(file, "file_name", None) or "input.mkv"

    os.makedirs(f"downloads/{user_id}", exist_ok=True)
    input_path = f"downloads/{user_id}/{filename}"

    ms = await query.message.edit("🚀 **Downloading file to analyse streams...**")

    try:
        await bot.download_media(
            message=file_message,
            file_name=input_path,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Downloading...", ms, time.time())
        )
    except Exception as e:
        return await ms.edit(f"❌ Download failed: `{e}`")

    await ms.edit("🔍 **Analysing streams...**")
    streams, fmt = await get_streams(input_path)

    if not streams:
        try:
            os.remove(input_path)
        except Exception:
            pass
        return await ms.edit("❌ Could not read streams from this file.")

    # One button per stream — embed user_id + stream_idx + file_msg_id
    buttons = []
    for s in streams:
        idx = s.get("index", 0)
        buttons.append([InlineKeyboardButton(
            stream_label(s),
            callback_data=f"do_{action}_{user_id}_{idx}_{file_msg_id}"
        )])
    buttons.append([InlineKeyboardButton(
        "❌ Cancel",
        callback_data=f"stream_cancel_{user_id}"
    )])

    action_label = (
        "📤 Tap a stream to **extract** it:"
        if action == "extract"
        else "✂️ Tap a stream to **remove** it:"
    )
    await ms.edit(
        f"{format_stream_info(streams, fmt)}\n{action_label}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   CANCEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex(r"^stream_cancel_"))
async def stream_cancel(bot, query: CallbackQuery):
    await query.answer()
    await query.message.delete()
    dl_dir = f"downloads/{query.from_user.id}"
    if os.path.isdir(dl_dir):
        for f in os.listdir(dl_dir):
            try:
                os.remove(os.path.join(dl_dir, f))
            except Exception:
                pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   STEP 2 — Process chosen stream
#   callback_data = "do_{action}_{user_id}_{idx}_{file_msg_id}"
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex(r"^do_(extract|remove)_"))
async def do_stream_action(bot, query: CallbackQuery):
    await query.answer()

    # do_extract_userid_streamidx_filemsgid
    parts      = query.data.split("_")
    action     = parts[1]
    user_id    = int(parts[2])
    stream_idx = int(parts[3])
    # parts[4] is file_msg_id (carried for reference, not needed here since file is already downloaded)

    dl_dir = f"downloads/{user_id}"
    files  = os.listdir(dl_dir) if os.path.isdir(dl_dir) else []
    if not files:
        return await query.message.edit("❌ Downloaded file not found. Please try again.")

    input_path = os.path.join(dl_dir, files[0])
    filename   = files[0]
    name, ext  = os.path.splitext(filename)

    os.makedirs("Streams", exist_ok=True)
    ms = await query.message.edit(f"⚙️ **Processing stream #{stream_idx}...**")

    if action == "extract":
        streams, _ = await get_streams(input_path)
        stream     = next((s for s in streams if s.get("index") == stream_idx), None)
        codec_type = stream.get("codec_type", "unknown") if stream else "unknown"
        codec_name = stream.get("codec_name", "copy")   if stream else "copy"

        audio_ext_map = {
            "aac": ".aac", "mp3": ".mp3", "ac3": ".ac3",
            "eac3": ".eac3", "flac": ".flac", "opus": ".opus",
            "vorbis": ".ogg", "dts": ".dts"
        }
        ext_map = {"video": ".mp4", "audio": ".aac", "subtitle": ".srt", "attachment": ".bin"}
        out_ext = (
            audio_ext_map[codec_name]
            if codec_type == "audio" and codec_name in audio_ext_map
            else ext_map.get(codec_type, ".mkv")
        )
        output_filename = f"{name}_stream{stream_idx}{out_ext}"
        output_path     = f"Streams/{output_filename}"
        cmd = [
            "ffmpeg", "-y", "-threads", "0",
            "-i", input_path,
            "-map", f"0:{stream_idx}",
            "-c", "copy",
            output_path
        ]
    else:  # remove
        output_filename = f"{name}_removed{stream_idx}{ext}"
        output_path     = f"Streams/{output_filename}"
        cmd = [
            "ffmpeg", "-y", "-threads", "0",
            "-i", input_path,
            "-map", "0",
            "-map", f"-0:{stream_idx}",
            "-c", "copy",
            output_path
        ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode().strip()[-300:]
        print(f"[stream ffmpeg error] {err}")
        return await ms.edit(f"❌ FFmpeg failed:\n`{err}`")

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        return await ms.edit("❌ Output file missing or empty.")

    # Caption
    c_caption = await jishubotz.get_caption(user_id)
    if c_caption:
        try:
            caption = c_caption.format(
                filename=output_filename,
                filesize=humanbytes(os.path.getsize(output_path)),
                duration=""
            )
        except Exception:
            caption = f"**{output_filename}**"
    else:
        emoji  = "📤" if action == "extract" else "✂️"
        verb   = "Extracted" if action == "extract" else "Removed"
        caption = f"**{output_filename}**\n{emoji} Stream `#{stream_idx}` {verb}"

    # Thumbnail
    ph_path = None
    c_thumb = await jishubotz.get_thumbnail(user_id)
    if c_thumb:
        ph_path = await bot.download_media(c_thumb)
        _, _, ph_path = await fix_thumb(ph_path)

    await ms.edit("💠 **Uploading...**")
    try:
        await bot.send_document(
            query.message.chat.id,
            document=output_path,
            thumb=ph_path,
            caption=caption,
            progress=progress_for_pyrogram,
            progress_args=("💠 Uploading...", ms, time.time())
        )
    except Exception as e:
        await ms.edit(f"❌ Upload failed: `{e}`")
    finally:
        await ms.delete()
        for f in [input_path, output_path, ph_path]:
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass


# Jishu Developer
# Don't Remove Credit 🥺
# Telegram Channel @MadflixBotz
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
# Contact @MadflixSupport
