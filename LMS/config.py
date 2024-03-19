from dataclasses import dataclass
from typing import Optional
from pathlib import Path

from yaml import safe_load

from .errors import ConfigFileLoaderError
from . import __version__ as LMS_VERSION

@dataclass
class CONFIG:
    @dataclass
    class LMS:
        CONFIG_FILE: Optional[Path] = None
        DESIGNER_FILES: Path = Path(__file__).resolve().parents[0].joinpath("ui", "designer-files")
        VERSION: str = LMS_VERSION

    @dataclass
    class REMOTE:
        HOST: str
        PORT: int
        DATABASE: str

    @dataclass
    class USER:
        USERNAME: str = ""
        PASSWORD: str = ""

def config_load(file: str):
    try:
        data = safe_load(open(file, "r", encoding="utf-8"))

        CONFIG.LMS.CONFIG_FILE = Path(file)

        CONFIG.REMOTE.HOST = data["REMOTE"]["HOST"]
        CONFIG.REMOTE.PORT = int(data["REMOTE"]["PORT"])
        CONFIG.REMOTE.DATABASE = data["REMOTE"]["DATABASE"]

        if "USER" in data:
            if "USERNAME" in data["USER"]:
                CONFIG.USER.USERNAME = data["USER"]["USERNAME"]
            if "PASSWORD" in data["USER"]:
                CONFIG.USER.PASSWORD = data["USER"]["PASSWORD"]
    except Exception as err:
        raise ConfigFileLoaderError(err)
