from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.ffmpeg import remove_stream, extract_stream, fix_thumb, take_screen_shot
from helper.database import jishubotz
from helper.utils import progress_for_pyrogram, humanbytes, convert
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import os, time, random


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#               REMOVE STREAM CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex("^rmstream_"))
async def remove_stream_callback(bot, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    file_message = query.message.reply_to_message

    if data == "rmstream_back":
        await query.message.delete()
        return

    stream_type = data.replace("rmstream_", "")

    file = getattr(file_message, file_message.media.value)
    filename = file.file_name or "output.mkv"
    name, ext = os.path.splitext(filename)
    output_filename = f"{name}_no{stream_type}{ext}"

    os.makedirs(f"downloads/{user_id}", exist_ok=True)
    os.makedirs("Streams", exist_ok=True)

    input_path = f"downloads/{user_id}/{filename}"
    output_path = f"Streams/{output_filename}"

    ms = await query.message.edit("🚀 **Downloading file...**")

    try:
        await bot.download_media(
            message=file_message,
            file_name=input_path,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Downloading...", ms, time.time())
        )
    except Exception as e:
        return await ms.edit(f"❌ Download failed: `{e}`")

    result = await remove_stream(input_path, output_path, stream_type, ms)
    if not result:
        for f in [input_path]:
            if f and os.path.exists(f):
                os.remove(f)
        return

    # Caption
    c_caption = await jishubotz.get_caption(user_id)
    duration = 0
    try:
        parser = createParser(input_path)
        meta = extractMetadata(parser)
        if meta and meta.has("duration"):
            duration = meta.get("duration").seconds
        parser.close()
    except:
        pass

    if c_caption:
        try:
            caption = c_caption.format(
                filename=output_filename,
                filesize=humanbytes(os.path.getsize(output_path)),
                duration=convert(duration)
            )
        except:
            caption = f"**{output_filename}**"
    else:
        caption = f"**{output_filename}**\n✂️ `{stream_type}` stream removed"

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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#               EXTRACT STREAM CALLBACKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex("^exstream_"))
async def extract_stream_callback(bot, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    file_message = query.message.reply_to_message

    if data == "exstream_back":
        await query.message.delete()
        return

    stream_type = data.replace("exstream_", "")

    file = getattr(file_message, file_message.media.value)
    filename = file.file_name or "output.mkv"
    name, _ = os.path.splitext(filename)

    # Set correct extension per stream type
    ext_map = {
        "video": ".mp4",
        "audio": ".aac",
        "subtitle": ".srt"
    }
    output_ext = ext_map.get(stream_type, ".mkv")
    output_filename = f"{name}_{stream_type}{output_ext}"

    os.makedirs(f"downloads/{user_id}", exist_ok=True)
    os.makedirs("Streams", exist_ok=True)

    input_path = f"downloads/{user_id}/{filename}"
    output_path = f"Streams/{output_filename}"

    ms = await query.message.edit("🚀 **Downloading file...**")

    try:
        await bot.download_media(
            message=file_message,
            file_name=input_path,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Downloading...", ms, time.time())
        )
    except Exception as e:
        return await ms.edit(f"❌ Download failed: `{e}`")

    result = await extract_stream(input_path, output_path, stream_type, ms)
    if not result:
        for f in [input_path]:
            if f and os.path.exists(f):
                os.remove(f)
        return

    # Caption
    c_caption = await jishubotz.get_caption(user_id)
    duration = 0
    try:
        parser = createParser(input_path)
        meta = extractMetadata(parser)
        if meta and meta.has("duration"):
            duration = meta.get("duration").seconds
        parser.close()
    except:
        pass

    if c_caption:
        try:
            caption = c_caption.format(
                filename=output_filename,
                filesize=humanbytes(os.path.getsize(output_path)),
                duration=convert(duration)
            )
        except:
            caption = f"**{output_filename}**"
    else:
        caption = f"**{output_filename}**\n📤 Extracted `{stream_type}` stream"

    await ms.edit("💠 **Uploading...**")

    try:
        await bot.send_document(
            query.message.chat.id,
            document=output_path,
            caption=caption,
            progress=progress_for_pyrogram,
            progress_args=("💠 Uploading...", ms, time.time())
        )
    except Exception as e:
        await ms.edit(f"❌ Upload failed: `{e}`")
    finally:
        await ms.delete()
        for f in [input_path, output_path]:
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
