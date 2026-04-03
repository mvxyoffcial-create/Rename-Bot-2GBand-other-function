import motor.motor_asyncio
from config import Config
from .utils import send_log

class Database:

    def __init__(self, uri, database_name):
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.jishubotz = self._client[database_name]
        self.col = self.jishubotz.user

    def new_user(self, id):
        return dict(
            _id=int(id),
            file_id=None,
            caption=None,
            prefix=None,
            suffix=None,
            metadata=False,
            metadata_code="By :- @MadflixBotz",
            encode=False,
            encode_preset="medium",
            encode_codec="libx264",
            encode_crf="23",
        )

    async def add_user(self, b, m):
        u = m.from_user
        if not await self.is_user_exist(u.id):
            user = self.new_user(u.id)
            await self.col.insert_one(user)
            await send_log(b, u)

    async def is_user_exist(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return bool(user)

    async def total_users_count(self):
        count = await self.col.count_documents({})
        return count

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        await self.col.delete_many({'_id': int(user_id)})


    #======================= Thumbnail ========================#

    async def set_thumbnail(self, id, file_id):
        await self.col.update_one({'_id': int(id)}, {'$set': {'file_id': file_id}})

    async def get_thumbnail(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('file_id', None)


    #======================= Caption ========================#

    async def set_caption(self, id, caption):
        await self.col.update_one({'_id': int(id)}, {'$set': {'caption': caption}})

    async def get_caption(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('caption', None)


    #======================= Prefix ========================#

    async def set_prefix(self, id, prefix):
        await self.col.update_one({'_id': int(id)}, {'$set': {'prefix': prefix}})

    async def get_prefix(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('prefix', None)


    #======================= Suffix ========================#

    async def set_suffix(self, id, suffix):
        await self.col.update_one({'_id': int(id)}, {'$set': {'suffix': suffix}})

    async def get_suffix(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('suffix', None)


    #======================= Metadata ========================#

    async def set_metadata(self, id, bool_meta):
        await self.col.update_one({'_id': int(id)}, {'$set': {'metadata': bool_meta}})

    async def get_metadata(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('metadata', False)


    #======================= Metadata Code ========================#

    async def set_metadata_code(self, id, metadata_code):
        await self.col.update_one({'_id': int(id)}, {'$set': {'metadata_code': metadata_code}})

    async def get_metadata_code(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('metadata_code', "By :- @MadflixBotz")


    #======================= Encode Settings ========================#

    async def set_encode(self, id, bool_encode):
        await self.col.update_one({'_id': int(id)}, {'$set': {'encode': bool_encode}})

    async def get_encode(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('encode', False)

    async def set_encode_preset(self, id, preset):
        await self.col.update_one({'_id': int(id)}, {'$set': {'encode_preset': preset}})

    async def get_encode_preset(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('encode_preset', 'medium')

    async def set_encode_codec(self, id, codec):
        await self.col.update_one({'_id': int(id)}, {'$set': {'encode_codec': codec}})

    async def get_encode_codec(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('encode_codec', 'libx264')

    async def set_encode_crf(self, id, crf):
        await self.col.update_one({'_id': int(id)}, {'$set': {'encode_crf': str(crf)}})

    async def get_encode_crf(self, id):
        user = await self.col.find_one({'_id': int(id)})
        return user.get('encode_crf', '23')


jishubotz = Database(Config.DATABASE_URL, Config.DATABASE_NAME)


# Jishu Developer
# Don't Remove Credit 🥺
# Telegram Channel @MadflixBotz
# Backup Channel @JishuBotz
# Developer @JishuDeveloper
# Contact @MadflixSupport
