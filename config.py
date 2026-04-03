import os, time, re
id_pattern = re.compile(r'^.\d+$')



class Config(object):
    # pyro client config
    API_ID    = "20288994"
    API_HASH  = "d702614912f1ad370a0d18786002adbf"
    BOT_TOKEN = "8659662712:AAFDH1Vr2avs4b4bJ2vUthygv__KrA470RM" 
   
    # database config
    DATABASE_NAME = "Cluster0"
    DATABASE_URL  = "mongodb+srv://vsandeepa183_db_user:venura8907@cluster0.o1c53d4.mongodb.net/?appName=Cluster0"
 
    # other configs
    BOT_UPTIME  = time.time()
    START_PIC   = "https://i.ibb.co/S4Y8w1NT/img-8108646188.jpg"
    ADMIN="8498741978 @venuboyy"

    # channels logs
    FORCE_SUBS   = "Zerodev2"
    LOG_CHANNEL = "-1003712131076"

    # wes response configuration     
    WEBHOOK = True



class Txt(object):
    # part of text configuration
    START_TXT = """<b>ʜᴇʏ, {}!</b>

<b>ɪ'ᴍ ᴀ ᴘᴏᴡᴇʀғᴜʟ ʀᴇɴᴀᴍᴇ ʙᴏᴛ ⚡</b>

<b>ɪ ᴄᴀɴ ʀᴇɴᴀᴍᴇ ʏᴏᴜʀ ғɪʟᴇs, ᴠɪᴅᴇᴏs & ᴅᴏᴄᴜᴍᴇɴᴛs ᴜᴘ ᴛᴏ 𝟺ɢʙ 💾</b>

<b>ᴊᴜsᴛ sᴇɴᴅ ᴍᴇ ᴀɴʏ ғɪʟᴇ — ᴀɴᴅ ɢᴇᴛ ɪᴛ ʀᴇɴᴀᴍᴇᴅ ɪɴ sᴇᴄᴏɴᴅs ⚡</b>"""

    ABOUT_TXT = """
╭───────────────⍟
├<b>🤖 My Name</b> : {}
├<b>🖥️ Developer</b> : <a href=https://t.me/venuboyy>Venuboy</a> 
├<b>👨‍💻 Programer</b> : <a href=https://t.me/zerodev2>Zerodev</a>
├<b>📕 Library</b> : <a href=https://github.com/pyrogram>Pyrogram</a>
├<b>✏️ Language</b> : <a href=https://www.python.org>Python 3</a>
├<b>💾 Database</b> : <a href=https://cloud.mongodb.com>Mongo DB</a>
├<b>📊 Build Version</b> : <a href=https://instagram.com/jishukumarsinha>Rename v4.7.0</a></b>     
╰───────────────⍟
"""

    HELP_TXT = """
🌌 <b><u>How To Set Thumbnail</u></b>
  
➪ /start - Start The Bot And Send Any Photo To Automatically Set Thumbnail.
➪ /del_thumb - Use This Command To Delete Your Old Thumbnail.
➪ /view_thumb - Use This Command To View Your Current Thumbnail.

📑 <b><u>How To Set Custom Caption</u></b>

➪ /set_caption - Use This Command To Set A Custom Caption
➪ /see_caption - Use This Command To View Your Custom Caption
➪ /del_caption - Use This Command To Delete Your Custom Caption
➪ Example - <code>/set_caption 📕 Name ➠ : {filename}

🔗 Size ➠ : {filesize} 

⏰ Duration ➠ : {duration}</code>

✏️ <b><u>How To Rename A File</u></b>

➪ Send Any File And Type New File Name And Select The Format [ Document, Video, Audio ].           

𝗔𝗻𝘆 𝗢𝘁𝗵𝗲𝗿 𝗛𝗲𝗹𝗽 𝗖𝗼𝗻𝘁𝗮𝗰𝘁 :- <a href=https://t.me/venuboyy>venuboy</a>
"""

    PROGRESS_BAR = """\n
 <b>🔗 Size :</b> {1} | {2}
️ <b>⏳️ Done :</b> {0}%
 <b>🚀 Speed :</b> {3}/s
️ <b>⏰️ ETA :</b> {4}
"""

    DONATE_TXT = """
<b>🥲 Thanks For Showing Interest In Donation! ❤️</b>

If You Like My Bots & Projects, You Can 🎁 Donate Me Any Amount From 10 Rs Upto Your Choice.

<b>🛍 UPI ID:</b> `kumarjishusinha@ibl`
"""


    SEND_METADATA = """<b><u>🖼️  HOW TO SET CUSTOM METADATA</u></b>

For Example :-

<code>By :- @Venuboyy</code>

💬 For Any Help Contact @Venuboyy
"""








# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @MadflixBotz
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
# Contact @MadflixSupport
