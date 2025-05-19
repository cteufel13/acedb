from pathlib import Path
import json
import os

CONFIG_PATH = CONFIG_PATH = Path.home() / ".acedb" / "config.json"


class Config:

    host: str = None
    port: int = None
    db_name: str = None
    username: str = None
    password: str = None

    def __init__(self):
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
        with open(CONFIG_PATH, "r") as config_file:
            raw_config = json.load(config_file)

        self.password = raw_config.get("password")

        if "dbn_token" in raw_config:
            os.environ["DATABENTO_API_KEY"] = raw_config["dbn_token"]

        if "fred_token" in raw_config:
            os.environ["FRED_API_KEY"] = raw_config["fred_token"]

        self.host = raw_config.get("host")
        self.port = raw_config.get("port")
        self.db_name = raw_config.get("db_name")
        self.username = raw_config.get("username")
