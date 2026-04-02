import time
import os
import asyncio
from PIL import Image
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                    FIX THUMBNAIL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def fix_thumb(thumb):
    width = 320
    height = 320
    try:
        if thumb is not None and os.path.exists(thumb):
            parser = createParser(thumb)
            if parser:
                metadata = extractMetadata(parser)
                if metadata:
                    if metadata.has("width"):
                        width = metadata.get("width")
                    if metadata.has("height"):
                        height = metadata.get("height")
                parser.close()

            with Image.open(thumb) as img:
                img = img.convert("RGB")
                img = img.resize((width, height))
                img.save(thumb, "JPEG")
    except Exception as e:
        print(f"[fix_thumb Error] {e}")
        thumb = None

    return width, height, thumb


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                   TAKE SCREENSHOT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def take_screen_shot(video_file, output_directory, ttl):
    out_put_file_name = os.path.join(output_directory, f"{time.time()}.jpg")
    command = [
        "ffmpeg", "-y",
        "-ss", str(ttl),
        "-i", video_file,
        "-vframes", "1",
        "-q:v", "2",
        out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await process.communicate()
    if os.path.exists(out_put_file_name):
        return out_put_file_name
    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                    ADD METADATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def add_metadata(input_path, output_path, metadata, ms):
    try:
        # Verify input file actually exists before running ffmpeg
        if not input_path or not os.path.exists(input_path):
            await ms.edit("❌ <i>Input file not found. Cannot add metadata.</i>")
            return None

        # Ensure the Metadata/ output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        await ms.edit("📝 <i>Adding Metadata To Your File ⚡</i>")

        # Sanitize metadata string — remove characters that break ffmpeg args
        safe_metadata = str(metadata).replace("'", "").replace('"', "").replace("\\", "").strip()

        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", "0",
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", "copy",
            "-metadata", f"title={safe_metadata}",
            "-metadata", f"author={safe_metadata}",
            "-metadata", f"artist={safe_metadata}",
            "-metadata:s:v", f"title={safe_metadata}",
            "-metadata:s:a", f"title={safe_metadata}",
            "-metadata:s:s", f"title={safe_metadata}",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error = stderr.decode().strip()
            print(f"[add_metadata FFmpeg Error]\n{error}")
            await ms.edit("❌ <i>FFmpeg Failed To Add Metadata.</i>")
            return None

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            await ms.edit("✅ <i>Metadata Added Successfully!</i>")
            return output_path
        else:
            await ms.edit("❌ <i>Metadata output file is missing or empty.</i>")
            return None

    except Exception as e:
        print(f"[add_metadata Exception] {e}")
        await ms.edit(f"❌ <i>Error While Adding Metadata: {e}</i>")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#               FAST PROGRESS BAR
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def fast_progress(current, total, message, start_time, action="Processing"):
    try:
        now = time.time()
        elapsed = now - start_time
        speed = current / elapsed if elapsed > 0 else 0
        eta = (total - current) / speed if speed > 0 else 0
        percent = current * 100 / total
        done = int(percent / 5)
        bar = "█" * done + "░" * (20 - done)

        speed_str = humanbytes(speed) + "/s"
        current_str = humanbytes(current)
        total_str = humanbytes(total)
        eta_str = time_formatter(eta)

        text = (
            f"**{action}**\n"
            f"`{bar}` **{percent:.1f}%**\n\n"
            f"📦 **Size:** `{current_str}` / `{total_str}`\n"
            f"⚡ **Speed:** `{speed_str}`\n"
            f"⏳ **ETA:** `{eta_str}`"
        )
        await message.edit(text)
    except Exception:
        pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                  HELPER FUNCTIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def humanbytes(size):
    if not size:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def time_formatter(seconds):
    seconds = int(seconds)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Jishu Developer
# Don't Remove Credit 🥺
# Telegram Channel @MadflixBotz
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
# Contact @MadflixSupport
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
