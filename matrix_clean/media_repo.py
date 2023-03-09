"""
matrix-media-repo API
"""
from dataclasses import dataclass
from enum import Enum
from types import TracebackType
from typing import Type
from . import config
from datetime import datetime
import aiohttp


class Purpose(Enum):
    """
    Media purpose
    """
    NONE = "none"
    PINNED = "pinned"


@dataclass
class MediaAttrs:
    """
    Media attributes
    """
    purpose: Purpose

@dataclass
class PurgeResult:
    """
    Purge result
    """
    affected: list[str]
    purged: bool

class MatrixMediaRepoClient(object):
    def __init__(self, client: aiohttp.ClientSession):
        self.client = client

    def _parse_mxc_uri(self, mxc_uri: str) -> str:
        if mxc_uri.startswith("mxc://"):
            mxc_uri = mxc_uri[5:]
        return mxc_uri

    async def get_media_attributes(self, mxc_uri: str) -> MediaAttrs:
        mxc_uri = self._parse_mxc_uri(mxc_uri)
        async with self.client.get(config.HOMESERVER_URL + "_matrix/media/unstable/admin/media/" + mxc_uri + "/attributes") as resp:
            if resp.status == 200:
                data = await resp.json()
                return MediaAttrs(Purpose(data["purpose"]))
            else:
                raise Exception(f"Failed to get media from mxc://{mxc_uri}: {await resp.json()}")

    async def media_exists(self, mxc_uri: str) -> bool:
        try:
            await self.get_media_attributes(mxc_uri)
            return True
        except:
            return False

    async def purge_old_media(self, before: datetime) -> PurgeResult:
        before_ms = int(before.timestamp() * 1000)
        async with self.client.post(f"{config.HOMESERVER_URL}_matrix/media/unstable/admin/purge/old",
                                    params = {
                                        "before_ts": before_ms,
                                        "include_local": "true"
                                    }) as resp:
            if resp.status == 200:
                data = await resp.json()
                return PurgeResult(data["affected"], data["purged"])
            else:
                raise Exception(f"Failed to purge old media: {await resp.json()}")


class MatrixMediaRepoAdmin(object):
    def __init__(self, key: str):
        self.session = aiohttp.ClientSession(
            headers = {
                "Authorization": "Bearer " + key
            }
        )

    async def __aenter__(self) -> MatrixMediaRepoClient:
        res = await self.session.__aenter__()
        return MatrixMediaRepoClient(res)

    async def __aexit__(self, exc_type: Type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        await self.session.__aexit__(exc_type, exc_val, exc_tb)
