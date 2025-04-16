import psycopg2
from pathlib import Path
import json
import os

CONFIG_PATH = Path.home() / ".acedb" / "config.json"


class AceDB:

    def __init__(self):
        print(Path.home())
        self._config = None
        self.__password = None
        self.cursor = None

        self._load_config()
        self._init_db()

    @property
    def password(self):
        raise AttributeError("Password is not accessible directly.")

    def get(self, dataset, schema, symbols, start=None, end=None, **kwargs):
        """
        First checks the postgre database for data that fullfills the query
        It then downloads rest from databento and appends it to database and returns the data
        """

        # Check if the dataset is in the database
        self._check_in_db(dataset, schema, symbols, start, end)

        self._disc_db()

    def _load_config(self):
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
        with open(CONFIG_PATH, "r") as config_file:
            raw_config = json.load(config_file)

        self.__password = raw_config.get("password")
        self._config = {k: v for k, v in raw_config.items() if k != "password"}

    def _init_db(self):

        try:
            conn = psycopg2.connect(
                host=self._config["host"],
                port=self._config["port"],
                dbname=self._config["db_name"],
                user=self._config["username"],
                password=self.__password,
                connect_timeout=5,
            )
            self.cursor = conn.cursor()

        except:
            print("Error connecting to the database. Please check your configuration.")
            raise

        print("Database connection established.")

    def _check_in_db(self, dataset, schema, symbols, start, end):
        """
        Check if the datas  et is in the database
        """

        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)
        symbols = self._convert_for_SQL(symbols)

        if 

    def _check_ds(self, dataset):
        """
        Check if the dataset is in the database
        Databento Dataset is one Schema in DB
        """
        ds_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s) AS dataset_exists"
        self.cursor.execute(ds_check_query, (dataset,))
        exists = self.cursor.fetchone()

        return exists

    def _check_schma(self, dataset, schema):
        """
        Check if the schema is in the database
        """

        schema_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND  table_name = %s ) AS schema_exists"
        self.cursor.execute(schema_check_query, (dataset, schema))
        exists = self.cursor.fetchone()
        return exists

    def _check_symbols(self, dataset, schema, symbol):
        """
        Check if the symbol is in a specific schema in a dataset
        """
        symbol_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = %s AND table_name = %s AND column_name = symbol) AS symbol_exists"
        self.cursor.execute(symbol_check_query, (dataset, schema))
        exists = self.cursor.fetchone()
        return exists

    def _convert_for_SQL(self, terms):
        """
        Convert the terms to a string
        """
        return [term.replace(".", "_") for term in terms]

    def _disc_db(self):
        """
        Disconnect from the database
        """
        if self.cursor:
            self.cursor.close()
            self.cursor.connection.close()
        print("Database connection closed.")
