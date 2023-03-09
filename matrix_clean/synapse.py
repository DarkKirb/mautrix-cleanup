from typing import Iterable
from sqlalchemy import create_engine, text
from . import config

engine = create_engine(config.SYNAPSE_DB)

def get_event_ids() -> Iterable[str]:
    with engine.connect() as conn:
        with conn.begin():
            yield from map(lambda x: x[0], conn.execute(text("SELECT event_id FROM event_json")).fetchall())
