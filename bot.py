from datetime import datetime
from pytz import timezone
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from config import Config
from aiohttp import web
from route import web_server
import pyromod
import pyrogram.utils

pyrogram.utils.MIN_CHANNEL_ID = -100999999999999


class Bot(Client):

    def __init__(self):
        super().__init__(
            name="renamer",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username  
        self.uptime = Config.BOT_UPTIME

        # Always start web server (required for Render to detect open port)
        try:
            app = web.AppRunner(await web_server())
            await app.setup()       
            await web.TCPSite(app, "0.0.0.0", 10000).start()
            print("Web server started on port 10000")
        except Exception as e:
            print(f"Web server failed to start: {e}")

        print(f"{me.first_name} Is Started.....✨️")

        for id in Config.ADMIN:
            try:
                await self.send_message(id, f"**{me.first_name}  Is Started...**")
            except:
                pass
        
        if Config.LOG_CHANNEL:
            try:
                curr = datetime.now(timezone("Asia/Kolkata"))
                date = curr.strftime('%d %B, %Y')
                time = curr.strftime('%I:%M:%S %p')
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"**{me.mention} Is Restarted !!**\n\n"
                    f"📅 Date : `{date}`\n"
                    f"⏰ Time : `{time}`\n"
                    f"🌐 Timezone : `Asia/Kolkata`\n\n"
                    f"🉐 Version : `v{__version__} (Layer {layer})`"
                )
            except:
                print("Please Make This Is Admin In Your Log Channel")


Bot().run()


# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @MadflixBotz
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
# Contact @MadflixSupport
