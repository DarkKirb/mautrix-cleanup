"""
full cleanup
"""

import asyncio
import datetime
from typing import Awaitable

from tqdm import tqdm

from matrix_clean.media_repo import MatrixMediaRepoAdmin
from . import config, mautrix_discord, mautrix_signal, mautrix_telegram, mautrix_whatsapp, synapse

async def main():
    # First of all, we need to figure out what media is even referenced
    # in the database
    media : set[str] = set()
    media.update(mautrix_discord.known_media())
    media.update(mautrix_signal.known_media())
    media.update(mautrix_telegram.known_media())
    media.update(mautrix_whatsapp.known_media())
    print(f"Found {len(media)} media")
    async with MatrixMediaRepoAdmin(config.SYNAPSE_ADMIN_KEY) as client:
        dt = datetime.datetime.now() - datetime.timedelta(days=90)
        print("Pruning old media")
        result = await client.purge_old_media(dt)
        print(f"Prune {len(result.affected)} media")
        pbar = tqdm(media)
        media_to_delete : set[str] = set()
        sem = asyncio.Semaphore(16)
        futs: list[Awaitable[None]] = []

        async def fetch_task(media_id: str) -> None:
            async with sem:
                if not await client.media_exists(media_id):
                    media_to_delete.add(media_id)
                pbar.update(1)

        for mxc in media:
            if mxc == "":
                continue
            futs.append(fetch_task(mxc))

        await asyncio.gather(*futs)

        print(f"Deleting {len(media_to_delete)} media from the database")
        print("Deleting media for discord")
        mautrix_discord.delete_media(media_to_delete)
        print("deleting media for signal")
        mautrix_signal.delete_media(media_to_delete)
        print("deleting media for telegram")
        mautrix_telegram.delete_media(media_to_delete)
        print("deleting media for whatsapp")
        mautrix_whatsapp.delete_media(media_to_delete)
        print("finished deleting missing media, checking messages")
        print("fixing messages for discord")
        mautrix_discord.delete_missing_messages(synapse.get_event_ids())
        print("fixing messages for signal")
        mautrix_signal.delete_missing_messages(synapse.get_event_ids())
        print("fixing messages for telegram")
        mautrix_telegram.delete_missing_messages(synapse.get_event_ids())
        print("fixing messages for whatsapp")
        mautrix_whatsapp.delete_missing_messages(synapse.get_event_ids())
        print("done.")



if __name__ == '__main__':
    asyncio.run(main())
