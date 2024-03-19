from sys import argv
from typing import Optional
from argparse import ArgumentParser, Namespace

from .config import CONFIG, config_load

class TypedArgumentParser(Namespace):
    config: Optional[str] = None
    host: str = ""
    port: int = 3306
    db: str = "LMS_DB"
    user: Optional[str] = None
    passwd: Optional[str] = None

def argument_parser() -> None:
    parser = ArgumentParser()
    parser.add_argument("--config", type=str)
    parser.add_argument("--host", type=str, required=("--config" not in argv))
    parser.add_argument("--port", type=int)
    parser.add_argument("--db", type=str)
    parser.add_argument("--user", type=str)
    parser.add_argument("--passwd", type=str)

    args = parser.parse_args(namespace=TypedArgumentParser())

    if args.config is not None:
        config_load(args.config)
    else:
        CONFIG.REMOTE.HOST = args.host
        CONFIG.REMOTE.PORT = args.port
        CONFIG.REMOTE.DATABASE = args.db

    if args.user is not None:
        CONFIG.USER.USERNAME = args.user
    if args.passwd is not None:
        CONFIG.USER.PASSWORD = args.passwd
