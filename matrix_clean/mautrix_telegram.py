"""
Cleaning code for mautrix_telegram
"""

from typing import Iterable
from sqlalchemy import create_engine, text

from matrix_clean.util import batch
from . import config
from tqdm import tqdm

engine = create_engine(config.MAUTRIX_TELEGRAM_DB)


def delete_media(mxurls: Iterable[str]):
    """
    Delete media from mautrix_telegram database
    :param mxurls: list of media urls
    :return: None
    """
    with engine.connect() as conn:
        with conn.begin():
            for mxurl in tqdm(mxurls):
                conn.execute(text("UPDATE mx_user_profile SET avatar_url = '' WHERE avatar_url IN (:mxurl)"), {"mxurl": mxurl})
                conn.execute(text("UPDATE portal SET avatar_url = NULL, avatar_set = 'f' WHERE avatar_url IN (:mxurl)"), {"mxurl": mxurl})
                conn.execute(text("UPDATE puppet SET avatar_url = NULL, avatar_set = 'f' WHERE avatar_url IN (:mxurl)"), {"mxurl": mxurl})
                conn.execute(text("DELETE FROM telegram_file WHERE mxc IN (:mxurl)"), {"mxurl": mxurl})


def known_media() -> Iterable[str]:
    """
    Get all known media urls from mautrix_telegram database
    :return: list of media urls
    """
    with engine.connect() as conn:
        with conn.begin():
            yield from map(lambda x: x[0], conn.execute(text("SELECT mxc FROM telegram_file WHERE mxc IS NOT NULL")).fetchall())


def delete_missing_messages(existing_messages: Iterable[str]):
    """
    Delete all messages from mautrix_telegram database that are not in existing_messages
    :param existing_messages: list of existing messages
    :return: None
    """
    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text("DROP TABLE IF EXISTS current_messages"))
            conn.execute(text("CREATE TABLE current_messages (mxid TEXT PRIMARY KEY NOT NULL)"))
            for chunk in batch(tqdm(existing_messages), 10_000):
                conn.execute(text("INSERT INTO current_messages (mxid) VALUES (unnest(:mxid))"), {"mxid": chunk})
            conn.execute(text("DELETE FROM crypto_message_index WHERE NOT EXISTS (SELECT 1 FROM current_messages WHERE event_id = mxid)"))
            conn.execute(text("DELETE FROM disappearing_message WHERE NOT EXISTS (SELECT 1 FROM current_messages WHERE event_id = mxid)"))
            conn.execute(text("DELETE FROM message WHERE NOT EXISTS (SELECT 1 FROM current_messages WHERE message.mxid = current_messages.mxid)"))
            conn.execute(text("UPDATE portal SET first_event_id = '' WHERE NOT EXISTS (SELECT 1 FROM current_messages WHERE mxid = first_event_id)"))
            conn.execute(text("DELETE FROM reaction WHERE NOT EXISTS (SELECT 1 FROM current_messages WHERE reaction.mxid = current_messages.mxid)"))
            conn.execute(text("DELETE FROM reaction WHERE NOT EXISTS (SELECT 1 FROM current_messages WHERE msg_mxid = current_messages.mxid)"))
            conn.execute(text("DROP TABLE IF EXISTS current_messages"))
