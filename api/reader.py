from sqlalchemy.orm import Session
from sqlalchemy import func, create_engine
from sqlalchemy.pool import NullPool

from datetime import datetime, timedelta
from pathlib import Path
from api.models import *
import os
from urllib.parse import quote_plus

CONFIG_DIR = Path(r"C:\Users\OrCon\airlines\secrets")


def read_value(filename, cast=str):
    path = CONFIG_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing secret file: {path}")
    return cast(path.read_text().strip())


pwd = read_value("db_password.txt")
# Central DB config
DB_SET_UP = {
    "dbtype": "postgresql",
    "dbname": read_value("db_name.txt"),
    "user": read_value("db_user.txt"),
    "pwd": quote_plus(pwd),
    "host": read_value("db_host.txt"),
    "port": read_value("db_port.txt", int),
}


def get_db_url():
    return (
        f"{DB_SET_UP['dbtype']}://"
        f"{DB_SET_UP['user']}:{DB_SET_UP['pwd']}@"
        f"{DB_SET_UP['host']}:{DB_SET_UP['port']}/"
        f"{DB_SET_UP['dbname']}"
    )


# Create engine ONCE
engine = create_engine(get_db_url(), poolclass=NullPool, json_deserializer=lambda x: x)


def get_session_and_engine():
    session = Session(engine, autocommit=True)
    return session, engine
