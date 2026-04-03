from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from helper.database import jishubotz
from helper.ffmpeg import encode_video, fix_thumb, take_screen_shot
from helper.utils import progress_for_pyrogram, humanbytes, convert
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import os, time, random


CODECS = ["libx264", "libx265", "libvpx-vp9"]
PRESETS = ["ultrafast", "superfast", "fast", "medium", "slow", "slower"]
CRF_VALUES = ["18", "20", "23", "26", "28", "30"]


def encode_menu_buttons(codec, crf, preset):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🎞 Codec: {codec}", callback_data="enc_codec_menu")],
        [
            InlineKeyboardButton(f"🎚 CRF: {crf}", callback_data="enc_crf_menu"),
            InlineKeyboardButton(f"⚙️ Preset: {preset}", callback_data="enc_preset_menu"),
        ],
        [InlineKeyboardButton("▶️ Start Encode", callback_data="enc_start")],
        [InlineKeyboardButton("❌ Cancel", callback_data="enc_cancel")],
    ])


@Client.on_callback_query(filters.regex("^enc_"))
async def encode_callback(bot, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    file_message = query.message.reply_to_message

    if data == "enc_cancel" or data == "enc_back":
        await query.message.delete()
        return

    elif data == "enc_codec_menu":
        codec = await jishubotz.get_encode_codec(user_id)
        buttons = []
        for c in CODECS:
            tick = "✅ " if c == codec else ""
            buttons.append([InlineKeyboardButton(f"{tick}{c}", callback_data=f"enc_setcodec_{c}")])
        buttons.append([InlineKeyboardButton("◀️ Back", callback_data="enc_back_settings")])
        await query.message.edit(
            "**🎞 Select Codec:**",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("enc_setcodec_"):
        codec = data.replace("enc_setcodec_", "")
        await jishubotz.set_encode_codec(user_id, codec)
        crf = await jishubotz.get_encode_crf(user_id)
        preset = await jishubotz.get_encode_preset(user_id)
        file = getattr(file_message, file_message.media.value)
        await query.message.edit(
            f"**🎬 Encode Settings**\n\n"
            f"**File:** `{file.file_name}`\n\n"
            f"🎞 **Codec:** `{codec}`\n"
            f"🎚 **CRF:** `{crf}`\n"
            f"⚙️ **Preset:** `{preset}`",
            reply_markup=encode_menu_buttons(codec, crf, preset)
        )

    elif data == "enc_crf_menu":
        crf = await jishubotz.get_encode_crf(user_id)
        buttons = []
        row = []
        for i, c in enumerate(CRF_VALUES):
            tick = "✅" if c == crf else ""
            row.append(InlineKeyboardButton(f"{tick}{c}", callback_data=f"enc_setcrf_{c}"))
            if len(row) == 3:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton("◀️ Back", callback_data="enc_back_settings")])
        await query.message.edit(
            "**🎚 Select CRF Value:**\n_(Lower = Better Quality + Bigger File)_",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("enc_setcrf_"):
        crf = data.replace("enc_setcrf_", "")
        await jishubotz.set_encode_crf(user_id, crf)
        codec = await jishubotz.get_encode_codec(user_id)
        preset = await jishubotz.get_encode_preset(user_id)
        file = getattr(file_message, file_message.media.value)
        await query.message.edit(
            f"**🎬 Encode Settings**\n\n"
            f"**File:** `{file.file_name}`\n\n"
            f"🎞 **Codec:** `{codec}`\n"
            f"🎚 **CRF:** `{crf}`\n"
            f"⚙️ **Preset:** `{preset}`",
            reply_markup=encode_menu_buttons(codec, crf, preset)
        )

    elif data == "enc_preset_menu":
        preset = await jishubotz.get_encode_preset(user_id)
        buttons = []
        for p in PRESETS:
            tick = "✅ " if p == preset else ""
            buttons.append([InlineKeyboardButton(f"{tick}{p}", callback_data=f"enc_setpreset_{p}")])
        buttons.append([InlineKeyboardButton("◀️ Back", callback_data="enc_back_settings")])
        await query.message.edit(
            "**⚙️ Select Preset:**\n_(Slower = Smaller File)_",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data.startswith("enc_setpreset_"):
        preset = data.replace("enc_setpreset_", "")
        await jishubotz.set_encode_preset(user_id, preset)
        codec = await jishubotz.get_encode_codec(user_id)
        crf = await jishubotz.get_encode_crf(user_id)
        file = getattr(file_message, file_message.media.value)
        await query.message.edit(
            f"**🎬 Encode Settings**\n\n"
            f"**File:** `{file.file_name}`\n\n"
            f"🎞 **Codec:** `{codec}`\n"
            f"🎚 **CRF:** `{crf}`\n"
            f"⚙️ **Preset:** `{preset}`",
            reply_markup=encode_menu_buttons(codec, crf, preset)
        )

    elif data == "enc_back_settings":
        codec = await jishubotz.get_encode_codec(user_id)
        crf = await jishubotz.get_encode_crf(user_id)
        preset = await jishubotz.get_encode_preset(user_id)
        file = getattr(file_message, file_message.media.value)
        await query.message.edit(
            f"**🎬 Encode Settings**\n\n"
            f"**File:** `{file.file_name}`\n\n"
            f"🎞 **Codec:** `{codec}`\n"
            f"🎚 **CRF:** `{crf}`\n"
            f"⚙️ **Preset:** `{preset}`",
            reply_markup=encode_menu_buttons(codec, crf, preset)
        )

    elif data == "enc_start":
        codec = await jishubotz.get_encode_codec(user_id)
        crf = await jishubotz.get_encode_crf(user_id)
        preset = await jishubotz.get_encode_preset(user_id)

        file = getattr(file_message, file_message.media.value)
        filename = file.file_name or "output.mkv"
        name, ext = os.path.splitext(filename)
        output_filename = f"{name}_encoded{ext}"

        os.makedirs(f"downloads/{user_id}", exist_ok=True)
        os.makedirs("Encoded", exist_ok=True)

        input_path = f"downloads/{user_id}/{filename}"
        output_path = f"Encoded/{output_filename}"

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

        # Encode
        result = await encode_video(input_path, output_path, codec, crf, preset, ms)
        if not result:
            for f in [input_path]:
                if f and os.path.exists(f):
                    os.remove(f)
            return

        # Get duration for thumb
        duration = 0
        try:
            parser = createParser(input_path)
            meta = extractMetadata(parser)
            if meta and meta.has("duration"):
                duration = meta.get("duration").seconds
            parser.close()
        except:
            pass

        # Thumbnail
        ph_path = None
        c_thumb = await jishubotz.get_thumbnail(user_id)
        if c_thumb:
            ph_path = await bot.download_media(c_thumb)
            _, _, ph_path = await fix_thumb(ph_path)
        elif file.thumbs:
            try:
                ph_path_ = await take_screen_shot(
                    input_path,
                    os.path.dirname(os.path.abspath(input_path)),
                    random.randint(0, max(duration - 1, 0))
                )
                _, _, ph_path = await fix_thumb(ph_path_)
            except:
                ph_path = None

        # Caption
        c_caption = await jishubotz.get_caption(user_id)
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
            caption = f"**{output_filename}**\n🎞 `{codec}` | CRF `{crf}` | `{preset}`"

        await ms.edit("💠 **Uploading encoded file...**")

        try:
            await bot.send_video(
                query.message.chat.id,
                video=output_path,
                caption=caption,
                thumb=ph_path,
                duration=duration,
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
