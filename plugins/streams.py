from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.ffmpeg import fix_thumb, take_screen_shot
from helper.database import jishubotz
from helper.utils import progress_for_pyrogram, humanbytes, convert
import os, time, json, asyncio, random


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   FFPROBE — Get all streams from downloaded file
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def get_streams(file_path):
    """Returns list of stream dicts from ffprobe."""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        file_path
    ]
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()
    try:
        data = json.loads(stdout.decode())
        return data.get("streams", []), data.get("format", {})
    except:
        return [], {}


def stream_label(stream):
    """Build a human-readable label for each stream."""
    idx = stream.get("index", "?")
    codec_type = stream.get("codec_type", "unknown").upper()
    codec_name = stream.get("codec_name", "?")
    tags = stream.get("tags", {})
    lang = tags.get("language", "")
    title = tags.get("title", "")

    icons = {"VIDEO": "🎞", "AUDIO": "🔊", "SUBTITLE": "💬", "ATTACHMENT": "📎"}
    icon = icons.get(codec_type, "📄")

    label = f"{icon} [{idx}] {codec_type} • {codec_name}"
    if lang:
        label += f" • {lang}"
    if title:
        short_title = title[:20] + "..." if len(title) > 20 else title
        label += f" • {short_title}"

    # Extra info
    if codec_type == "VIDEO":
        w = stream.get("width", "")
        h = stream.get("height", "")
        if w and h:
            label += f" • {w}x{h}"
    elif codec_type == "AUDIO":
        ch = stream.get("channels", "")
        sr = stream.get("sample_rate", "")
        if ch:
            label += f" • {ch}ch"

    return label


def format_stream_info(streams, fmt):
    """Build the text showing all stream metadata."""
    duration = fmt.get("duration", "?")
    size = fmt.get("size", "0")
    try:
        secs = int(float(duration))
        h, rem = divmod(secs, 3600)
        m, s = divmod(rem, 60)
        dur_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    except:
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
        idx = s.get("index", "?")
        codec_type = s.get("codec_type", "unknown").upper()
        codec_name = s.get("codec_name", "?")
        tags = s.get("tags", {})
        lang = tags.get("language", "und")
        title = tags.get("title", "-")
        icons = {"VIDEO": "🎞", "AUDIO": "🔊", "SUBTITLE": "💬", "ATTACHMENT": "📎"}
        icon = icons.get(codec_type, "📄")

        text += f"{icon} **Stream #{idx}** — `{codec_type}`\n"
        text += f"  ├ Codec: `{codec_name}`\n"
        text += f"  ├ Language: `{lang}`\n"
        text += f"  └ Title: `{title}`\n"

        if codec_type == "VIDEO":
            w = s.get("width", "?")
            h = s.get("height", "?")
            fps = s.get("r_frame_rate", "?")
            text += f"  ├ Resolution: `{w}x{h}`\n"
            text += f"  └ FPS: `{fps}`\n"
        elif codec_type == "AUDIO":
            ch = s.get("channels", "?")
            sr = s.get("sample_rate", "?")
            text += f"  ├ Channels: `{ch}`\n"
            text += f"  └ Sample Rate: `{sr}Hz`\n"

        text += "\n"

    return text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   STEP 1 — Download file and show stream buttons
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def handle_stream_action(bot, query, action):
    """
    action: 'extract' or 'remove'
    Downloads the file, runs ffprobe, shows per-stream buttons.
    """
    user_id = query.from_user.id
    file_message = query.message.reply_to_message
    file = getattr(file_message, file_message.media.value)
    filename = file.file_name or "input.mkv"

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
        os.remove(input_path)
        return await ms.edit("❌ Could not read streams from this file.")

    # Build one button per stream
    buttons = []
    for s in streams:
        label = stream_label(s)
        idx = s.get("index", 0)
        cb = f"do_{action}_{user_id}_{idx}_{filename[:30]}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"do_{action}_{user_id}_{idx}")])

    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data=f"stream_cancel_{user_id}")])

    stream_text = format_stream_info(streams, fmt)
    action_label = "📤 tap a stream to **extract** it:" if action == "extract" else "✂️ tap a stream to **remove** it:"

    await ms.edit(
        f"{stream_text}\n{action_label}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   Tool menu triggers (called from file_rename.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex("^rmstream_go$"))
async def rmstream_go(bot, query: CallbackQuery):
    await handle_stream_action(bot, query, "remove")


@Client.on_callback_query(filters.regex("^exstream_go$"))
async def exstream_go(bot, query: CallbackQuery):
    await handle_stream_action(bot, query, "extract")


@Client.on_callback_query(filters.regex("^stream_cancel_"))
async def stream_cancel(bot, query: CallbackQuery):
    await query.message.delete()
    # Clean up any downloaded file
    user_id = query.from_user.id
    dl_dir = f"downloads/{user_id}"
    if os.path.isdir(dl_dir):
        for f in os.listdir(dl_dir):
            try:
                os.remove(os.path.join(dl_dir, f))
            except:
                pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#   STEP 2 — User tapped a stream → process it
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex("^do_(extract|remove)_"))
async def do_stream_action(bot, query: CallbackQuery):
    data = query.data  # do_extract_userid_streamidx  or  do_remove_userid_streamidx
    parts = data.split("_")
    # parts: ['do', 'extract'/'remove', user_id, stream_idx]
    action = parts[1]
    user_id = int(parts[2])
    stream_idx = int(parts[3])

    # Find the already-downloaded file
    dl_dir = f"downloads/{user_id}"
    files = [f for f in os.listdir(dl_dir)] if os.path.isdir(dl_dir) else []
    if not files:
        return await query.message.edit("❌ Downloaded file not found. Please try again.")

    input_path = os.path.join(dl_dir, files[0])
    filename = files[0]
    name, ext = os.path.splitext(filename)

    os.makedirs("Streams", exist_ok=True)

    ms = await query.message.edit(f"⚙️ **Processing stream #{stream_idx}...**")

    if action == "extract":
        # Get stream info to determine output extension
        streams, _ = await get_streams(input_path)
        stream = next((s for s in streams if s.get("index") == stream_idx), None)
        codec_type = stream.get("codec_type", "unknown") if stream else "unknown"
        codec_name = stream.get("codec_name", "copy") if stream else "copy"

        ext_map = {
            "video": ".mp4",
            "audio": ".aac",
            "subtitle": ".srt",
            "attachment": ".bin"
        }
        # Use codec-specific extension for audio
        audio_ext_map = {
            "aac": ".aac", "mp3": ".mp3", "ac3": ".ac3",
            "eac3": ".eac3", "flac": ".flac", "opus": ".opus",
            "vorbis": ".ogg", "dts": ".dts"
        }
        if codec_type == "audio" and codec_name in audio_ext_map:
            out_ext = audio_ext_map[codec_name]
        else:
            out_ext = ext_map.get(codec_type, ".mkv")

        output_filename = f"{name}_stream{stream_idx}{out_ext}"
        output_path = f"Streams/{output_filename}"

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", f"0:{stream_idx}",
            "-c", "copy",
            output_path
        ]

    else:  # remove
        output_filename = f"{name}_removed{stream_idx}{ext}"
        output_path = f"Streams/{output_filename}"

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", "0",
            f"-map", f"-0:{stream_idx}",
            "-c", "copy",
            output_path
        ]

    # Run ffmpeg
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        err = stderr.decode().strip()[-300:]
        print(f"[stream ffmpeg error] {err}")
        await ms.edit(f"❌ FFmpeg failed:\n`{err}`")
        return

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        await ms.edit("❌ Output file missing or empty.")
        return

    # Caption
    c_caption = await jishubotz.get_caption(user_id)
    if c_caption:
        try:
            caption = c_caption.format(
                filename=output_filename,
                filesize=humanbytes(os.path.getsize(output_path)),
                duration=""
            )
        except:
            caption = f"**{output_filename}**"
    else:
        action_emoji = "📤" if action == "extract" else "✂️"
        action_text = "Extracted" if action == "extract" else "Removed"
        caption = f"**{output_filename}**\n{action_emoji} Stream `#{stream_idx}` {action_text}"

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
                except:
                    pass


# Jishu Developer
# Don't Remove Credit 🥺
# Telegram Channel @MadflixBotz
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
# Contact @MadflixSupport
