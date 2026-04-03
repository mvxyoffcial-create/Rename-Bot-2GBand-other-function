from pyrogram import Client, filters
from pyrogram.enums import MessageMediaType
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from hachoir.metadata import extractMetadata
from helper.ffmpeg import fix_thumb, take_screen_shot, add_metadata
from hachoir.parser import createParser
from helper.utils import progress_for_pyrogram, convert, humanbytes, add_prefix_suffix
from helper.database import jishubotz
from asyncio import sleep
from PIL import Image
import os, time, re, random, asyncio


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#         STEP 1 — FILE RECEIVED: Show tool menu
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_message(filters.private & (filters.document | filters.audio | filters.video))
async def rename_start(client, message):
    file = getattr(message, message.media.value)
    filename = file.file_name
    if file.file_size > 2000 * 1024 * 1024:
        return await message.reply_text(
            "Sorry Bro This Bot Doesn't Support Uploading Files Bigger Than 2GB", quote=True
        )

    # Show tools menu first — rename is one of the options
    is_video = message.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]
    is_audio = message.media == MessageMediaType.AUDIO

    buttons = [
        [InlineKeyboardButton("✏️ Rename File", callback_data=f"tool_rename")],
    ]

    if is_video:
        buttons.append([
            InlineKeyboardButton("🎬 Encode Video", callback_data="tool_encode"),
        ])
        buttons.append([
            InlineKeyboardButton("➖ Remove Stream", callback_data=f"rmstream_go_{message.id}"),
            InlineKeyboardButton("📤 Extract Stream", callback_data=f"exstream_go_{message.id}"),
        ])

    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="tool_cancel")])

    try:
        await message.reply_text(
            text=(
                f"**📂 File Received!**\n\n"
                f"**Name:** `{filename}`\n"
                f"**Size:** `{humanbytes(file.file_size)}`\n\n"
                f"**Select What You Want To Do:**"
            ),
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except FloodWait as e:
        await sleep(e.value)
        await message.reply_text(
            text=f"**📂 File Received!**\n\n**Name:** `{filename}`\n\n**Select What You Want To Do:**",
            reply_to_message_id=message.id,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#         TOOL MENU CALLBACK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex("^tool_"))
async def tool_menu_handler(bot, query):
    await query.answer()
    data = query.data
    file_message = query.message.reply_to_message
    file = getattr(file_message, file_message.media.value)
    filename = file.file_name or "file"

    if data == "tool_cancel":
        await query.message.delete()
        return

    elif data == "tool_rename":
        # Trigger rename flow — ask for new filename
        await query.message.delete()
        try:
            await file_message.reply_text(
                text=f"**Please Enter New Filename...**\n\n**Old File Name** :- `{filename}`",
                reply_to_message_id=file_message.id,
                reply_markup=ForceReply(True)
            )
        except FloodWait as e:
            await sleep(e.value)
            await file_message.reply_text(
                text=f"**Please Enter New Filename**\n\n**Old File Name** :- `{filename}`",
                reply_to_message_id=file_message.id,
                reply_markup=ForceReply(True)
            )

    elif data == "tool_encode":
        # Show encode settings menu
        user_id = query.from_user.id
        codec = await jishubotz.get_encode_codec(user_id)
        crf = await jishubotz.get_encode_crf(user_id)
        preset = await jishubotz.get_encode_preset(user_id)

        buttons = [
            [
                InlineKeyboardButton(f"🎞 Codec: {codec}", callback_data="enc_codec_menu"),
            ],
            [
                InlineKeyboardButton(f"🎚 CRF: {crf}", callback_data="enc_crf_menu"),
                InlineKeyboardButton(f"⚙️ Preset: {preset}", callback_data="enc_preset_menu"),
            ],
            [InlineKeyboardButton("▶️ Start Encode", callback_data="enc_start")],
            [InlineKeyboardButton("◀️ Back", callback_data="enc_back")],
        ]
        await query.message.edit(
            f"**🎬 Encode Settings**\n\n"
            f"**File:** `{filename}`\n\n"
            f"🎞 **Codec:** `{codec}`\n"
            f"🎚 **CRF:** `{crf}` _(lower = better quality, larger file)_\n"
            f"⚙️ **Preset:** `{preset}` _(slower = smaller file)_",
            reply_markup=InlineKeyboardMarkup(buttons)
        )




# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#         STEP 2 — RENAME: User types new name
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_message(filters.private & filters.reply)
async def refunc(client, message):
    reply_message = message.reply_to_message
    if (reply_message.reply_markup) and isinstance(reply_message.reply_markup, ForceReply):
        new_name = message.text
        await message.delete()
        msg = await client.get_messages(message.chat.id, reply_message.id)
        file = msg.reply_to_message
        media = getattr(file, file.media.value)
        if "." not in new_name:
            if "." in media.file_name:
                extn = media.file_name.rsplit('.', 1)[-1]
            else:
                extn = "mkv"
            new_name = new_name + "." + extn
        await reply_message.delete()

        button = [[InlineKeyboardButton("📁 Document", callback_data="upload_document")]]
        if file.media in [MessageMediaType.VIDEO, MessageMediaType.DOCUMENT]:
            button.append([InlineKeyboardButton("🎥 Video", callback_data="upload_video")])
        elif file.media == MessageMediaType.AUDIO:
            button.append([InlineKeyboardButton("🎵 Audio", callback_data="upload_audio")])

        await message.reply(
            text=f"**Select The Output File Type**\n\n**File Name :-** `{new_name}`",
            reply_to_message_id=file.id,
            reply_markup=InlineKeyboardMarkup(button)
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#         STEP 3 — UPLOAD (after rename)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@Client.on_callback_query(filters.regex("^upload_"))
async def doc(bot, update):
    await update.answer()
    if not os.path.isdir("Metadata"):
        os.mkdir("Metadata")

    prefix = await jishubotz.get_prefix(update.message.chat.id)
    suffix = await jishubotz.get_suffix(update.message.chat.id)
    new_name = update.message.text
    new_filename_ = new_name.split(":-")[1].strip()

    try:
        new_filename = add_prefix_suffix(new_filename_, prefix, suffix)
    except Exception as e:
        return await update.message.edit(
            f"Something Went Wrong Can't Able To Set Prefix Or Suffix 🥺\n\n"
            f"**Contact My Creator :** @CallAdminRobot\n\n**Error :** `{e}`"
        )

    file_path = f"downloads/{update.from_user.id}/{new_filename}"
    file = update.message.reply_to_message

    ms = await update.message.edit("🚀 Try To Download...  ⚡")
    try:
        path = await bot.download_media(
            message=file,
            file_name=file_path,
            progress=progress_for_pyrogram,
            progress_args=("🚀 Try To Downloading...  ⚡", ms, time.time())
        )
    except Exception as e:
        return await ms.edit(str(e))

    _bool_metadata = await jishubotz.get_metadata(update.message.chat.id)
    metadata_path = f"Metadata/{new_filename}"
    upload_path = file_path

    if _bool_metadata:
        metadata_code = await jishubotz.get_metadata_code(update.message.chat.id)
        await add_metadata(path, metadata_path, metadata_code, ms)
        if os.path.exists(metadata_path):
            upload_path = metadata_path
        else:
            await ms.edit("⚠️ Metadata injection failed, uploading original file...")
            upload_path = file_path
    else:
        await ms.edit("⏳ Mode Changing...  ⚡")

    duration = 0
    try:
        parser = createParser(file_path)
        meta = extractMetadata(parser)
        if meta and meta.has("duration"):
            duration = meta.get('duration').seconds
        parser.close()
    except:
        pass

    ph_path = None
    media = getattr(file, file.media.value)
    c_caption = await jishubotz.get_caption(update.message.chat.id)
    c_thumb = await jishubotz.get_thumbnail(update.message.chat.id)

    if c_caption:
        try:
            caption = c_caption.format(
                filename=new_filename,
                filesize=humanbytes(media.file_size),
                duration=convert(duration)
            )
        except Exception as e:
            return await ms.edit(text=f"Your Caption Error Except Keyword Argument : ({e})")
    else:
        caption = f"**{new_filename}**"

    if media.thumbs or c_thumb:
        if c_thumb:
            ph_path = await bot.download_media(c_thumb)
            width, height, ph_path = await fix_thumb(ph_path)
        else:
            try:
                ph_path_ = await take_screen_shot(
                    file_path,
                    os.path.dirname(os.path.abspath(file_path)),
                    random.randint(0, max(duration - 1, 0))
                )
                width, height, ph_path = await fix_thumb(ph_path_)
            except Exception as e:
                ph_path = None
                print(f"[Thumbnail Error] {e}")

    await ms.edit("💠 Try To Upload...  ⚡")
    upload_type = update.data.split("_")[1]

    try:
        if upload_type == "document":
            await bot.send_document(
                update.message.chat.id,
                document=upload_path,
                thumb=ph_path,
                caption=caption,
                progress=progress_for_pyrogram,
                progress_args=("💠 Try To Uploading...  ⚡", ms, time.time())
            )
        elif upload_type == "video":
            await bot.send_video(
                update.message.chat.id,
                video=upload_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("💠 Try To Uploading...  ⚡", ms, time.time())
            )
        elif upload_type == "audio":
            await bot.send_audio(
                update.message.chat.id,
                audio=upload_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
                progress=progress_for_pyrogram,
                progress_args=("💠 Try To Uploading...  ⚡", ms, time.time())
            )
    except Exception as e:
        return await ms.edit(f"**Error :** `{e}`")
    finally:
        await ms.delete()
        for f in [file_path, metadata_path, ph_path]:
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
