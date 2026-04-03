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
        if not input_path or not os.path.exists(input_path):
            await ms.edit("❌ <i>Input file not found. Cannot add metadata.</i>")
            return None

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        await ms.edit("📝 <i>Adding Metadata To Your File ⚡</i>")

        safe_metadata = str(metadata).replace("'", "").replace('"', "").replace("\\", "").strip()

        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", "0",
            "-c:v", "copy",
            "-c:a", "copy",
            "-c:s", "copy",
            "-map_metadata", "-1",
            "-metadata", f"title={safe_metadata}",
            "-metadata", f"author={safe_metadata}",
            "-metadata", f"artist={safe_metadata}",
            "-metadata", f"comment={safe_metadata}",
            "-metadata", f"encoder={safe_metadata}",
            "-metadata:s:0", "title=",
            "-metadata:s:0", f"title={safe_metadata}",
            "-metadata:s:0", "language=eng",
            "-metadata:s:1", "title=",
            "-metadata:s:1", f"title={safe_metadata}",
            "-metadata:s:1", "language=eng",
            "-metadata:s:2", "title=",
            "-metadata:s:2", f"title={safe_metadata}",
            "-metadata:s:2", "language=eng",
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
#                    ENCODE VIDEO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def encode_video(input_path, output_path, codec, crf, preset, ms):
    try:
        if not input_path or not os.path.exists(input_path):
            await ms.edit("❌ <i>Input file not found. Cannot encode.</i>")
            return None

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        await ms.edit(f"🎬 <i>Encoding video with {codec} CRF:{crf} Preset:{preset}...</i>")

        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", "0",
            "-c:v", codec,
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "copy",
            "-c:s", "copy",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Live progress tracking via ffmpeg stderr
        duration_total = 0
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            line = line.decode("utf-8", errors="ignore").strip()

            if "Duration:" in line and duration_total == 0:
                try:
                    dur_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = dur_str.split(":")
                    duration_total = int(h) * 3600 + int(m) * 60 + float(s)
                except:
                    pass

            if "time=" in line and duration_total > 0:
                try:
                    time_str = line.split("time=")[1].split(" ")[0].strip()
                    h, m, s = time_str.split(":")
                    elapsed = int(h) * 3600 + int(m) * 60 + float(s)
                    percent = min(elapsed / duration_total * 100, 100)
                    done = int(percent / 5)
                    bar = "█" * done + "░" * (20 - done)
                    await ms.edit(
                        f"🎬 **Encoding...**\n"
                        f"`{bar}` **{percent:.1f}%**\n\n"
                        f"🎞 **Codec:** `{codec}`  |  **CRF:** `{crf}`  |  **Preset:** `{preset}`"
                    )
                except:
                    pass

        await process.wait()

        if process.returncode != 0:
            await ms.edit("❌ <i>Encoding failed. Check logs.</i>")
            return None

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            await ms.edit("✅ <i>Encoding Completed Successfully!</i>")
            return output_path
        else:
            await ms.edit("❌ <i>Encoded file missing or empty.</i>")
            return None

    except Exception as e:
        print(f"[encode_video Exception] {e}")
        await ms.edit(f"❌ <i>Encode Error: {e}</i>")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                  REMOVE STREAM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def remove_stream(input_path, output_path, stream_type, ms):
    """
    stream_type: 'video', 'audio', 'subtitle'
    Removes all streams of that type from the file.
    """
    try:
        if not input_path or not os.path.exists(input_path):
            await ms.edit("❌ <i>Input file not found.</i>")
            return None

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        await ms.edit(f"✂️ <i>Removing {stream_type} stream...</i>")

        type_map = {
            "video": "v",
            "audio": "a",
            "subtitle": "s"
        }
        flag = type_map.get(stream_type, "s")

        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", "0",
            f"-map", f"-0:{flag}",
            "-c", "copy",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()

        if process.returncode != 0:
            await ms.edit(f"❌ <i>Failed to remove {stream_type} stream.</i>")
            return None

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            await ms.edit(f"✅ <i>{stream_type.capitalize()} stream removed!</i>")
            return output_path
        else:
            await ms.edit("❌ <i>Output file missing or empty.</i>")
            return None

    except Exception as e:
        print(f"[remove_stream Exception] {e}")
        await ms.edit(f"❌ <i>Error: {e}</i>")
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#                 EXTRACT STREAM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def extract_stream(input_path, output_path, stream_type, ms):
    """
    stream_type: 'video', 'audio', 'subtitle'
    Extracts only that stream type to output_path.
    """
    try:
        if not input_path or not os.path.exists(input_path):
            await ms.edit("❌ <i>Input file not found.</i>")
            return None

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        await ms.edit(f"📤 <i>Extracting {stream_type} stream...</i>")

        type_map = {
            "video": "v",
            "audio": "a",
            "subtitle": "s"
        }
        flag = type_map.get(stream_type, "a")

        command = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-map", f"0:{flag}",
            "-c", "copy",
            output_path
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()

        if process.returncode != 0:
            await ms.edit(f"❌ <i>Failed to extract {stream_type} stream.</i>")
            return None

        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            await ms.edit(f"✅ <i>{stream_type.capitalize()} stream extracted!</i>")
            return output_path
        else:
            await ms.edit("❌ <i>Extracted file missing or empty.</i>")
            return None

    except Exception as e:
        print(f"[extract_stream Exception] {e}")
        await ms.edit(f"❌ <i>Error: {e}</i>")
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
