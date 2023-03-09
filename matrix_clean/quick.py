"""
Quick cleanup
"""

import asyncio
import datetime

from matrix_clean.media_repo import MatrixMediaRepoAdmin
from . import config, mautrix_discord, mautrix_signal, mautrix_telegram, mautrix_whatsapp

async def main():
    async with MatrixMediaRepoAdmin(config.SYNAPSE_ADMIN_KEY) as client:
        dt = datetime.datetime.now() - datetime.timedelta(days=90)
        print("Pruning old media")
        result = await client.purge_old_media(dt)
        print("Deleting old media from database")
        mautrix_discord.delete_media(result.affected)
        print("Deleted from discord")
        mautrix_signal.delete_media(result.affected)
        print("Deleted from signal")
        mautrix_telegram.delete_media(result.affected)
        print("Deleted from telegram")
        mautrix_whatsapp.delete_media(result.affected)
        print("Deleted from whatsapp")
        print("Done")


if __name__ == '__main__':
    asyncio.run(main())
