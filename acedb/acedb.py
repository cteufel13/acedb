import psycopg2
from pathlib import Path
import json
import os
from typing import List, Dict, Any
import databento as dbn

CONFIG_PATH = Path.home() / ".acedb" / "config.json"

TYPE_MAP = {
    "int": "INTEGER",
    "float": "FLOAT",
    "string": "VARCHAR(255)",
}


class AceDB:

    def __init__(self):
        print(Path.home())
        self._config = None
        self.__password = None
        self._cursor = None
        self._client = None

        self._load_config()
        self._init_db()
        self._init_dbn_client()

    @property
    def password(self):
        raise AttributeError("Password is not accessible directly.")

    def get(
        self,
        dataset: str,
        schemas: List[str] | str,
        symbols: List[str] | str,
        start=None,
        end=None,
        **kwargs,
    ):
        """
        First checks the postgre database for data that fullfills the query
        It then downloads rest from databento and appends it to database and returns the data
        """

        if isinstance(schemas, str):
            schemas = [schemas]
        if isinstance(symbols, str):
            symbols = [symbols]

        # Check if the dataset and schema exist in the databento
        if not self._check_ds_in_dbn(dataset):
            raise ValueError("Not a valid dataset!")

        for schema in schemas:
            if not self._check_schma_in_dbn(dataset, schema):
                raise ValueError(f"Not a valid schema for dataset {dataset}: {schema}")

        # Creating all necessary Schemas in the database
        if not self._check_ds_in_dbase(dataset):
            print(f"Dataset {dataset} not found in database. Creating it.")
            self._create_dataset(dataset)

        for schema in schemas:
            if not self._check_schma_in_dbase(dataset, schema):
                print(f"Schema {schema} not found in database. Creating it.")
                self._create_schema(dataset, schema)

        # Check symbol in database

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
            self._cursor = conn.cursor()

        except:
            print("Error connecting to the database. Please check your configuration.")
            raise

        print("Database connection established.")

    def _init_dbn_client(self):

        if "DATABENTO_API_KEY" not in os.environ:
            raise ValueError("Missing Datebento API key")

        self._client = dbn.Historical()
        print("Databento client initialized.")

    def _check_dschma_in_dbase(
        self, dataset: str, schema: str, symbols: List[str] | str, start, end
    ) -> bool:
        """
        Check if the dataset and schema exist in the database
        """

        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)
        return self._check_ds_in_dbase(dataset) and self._check_schma_in_dbase(
            dataset, schema
        )

    def _check_ds_in_dbase(self, dataset: str) -> bool:
        """
        Check if the dataset is in the database
        Databento Dataset is one Schema in DB
        """
        dataset = self._convert_for_SQL(dataset)
        ds_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s) AS dataset_exists"
        self._cursor.execute(ds_check_query, (dataset,))
        exists = self._cursor.fetchone()

        return bool(exists[0])

    def _check_schma_in_dbase(self, dataset: str, schema: str) -> bool:
        """
        Check if the schema is in the database
        """
        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)
        schma_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND  table_name = %s ) AS schema_exists"
        self._cursor.execute(schma_check_query, (dataset, schema))
        exists = self._cursor.fetchone()

        return bool(exists[0])

    def _check_ds_in_dbn(self, dataset: str) -> bool:
        if dataset not in self._client.metadata.list_datasets():
            print(f"Dataset {dataset} not found in Databento.")
            return False
        return True

    def _check_schma_in_dbn(self, dataset: str, schema: str) -> bool:
        if schema not in self._client.metadata.list_schemas(dataset):
            print(f"Schema {schema} not found in Databento.")
            return False
        return True

    def _get_cols_in_dbn(self, dataset: str, schema: str):
        """
        Get the columns in the schema from Databento
        """

        cols = self._client.metadata.list_fields(schema, "csv")

        # symbol always appears at the end
        cols.append({"name": "symbol", "type": "string"})

        return cols

    def _create_dataset(self, dataset: str):
        """
        Create a new dataset in the database
        """
        dataset = self._convert_for_SQL(dataset)

        create_dataset_query = f"CREATE SCHEMA {dataset}"
        self._cursor.execute(create_dataset_query)
        print(f"Dataset {dataset} created.")

    def _create_schema(self, dataset: str, schema: str):
        """
        Create a new schema in the database
        """
        cols = self._get_cols_in_dbn(dataset, schema)
        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)
        create_schema_query = f'CREATE TABLE IF NOT EXISTS "{dataset}"."{schema}"  '
        col_defs = ",\n    ".join(
            f"{col['name']} {TYPE_MAP.get(col['type'], col['type'])}" for col in cols
        )
        create_schema_query += f"({col_defs})"
        self._cursor.execute(create_schema_query)
        self._cursor.connection.commit()

        print(f"Table {schema} created in Schema {dataset}.")

    def _disc_db(self):
        """
        Disconnect from the database
        """
        if self._cursor:
            self._cursor.close()
            self._cursor.connection.close()
        print("Database connection closed.")

    @staticmethod
    def _convert_for_SQL(terms: List[str] | str) -> List[str]:
        """
        Convert the terms to a string
        """
        if isinstance(terms, str):
            return terms.replace(".", "_").replace("-", "_")
        else:
            return [term.replace(".", "_").replace("-", "_") for term in terms]

    @staticmethod
    def _ask_yn(question: str) -> bool:
        """
        Ask a yes or no question
        """
        while True:
            answer = input(question).strip().lower()
            if answer in ("y", "yes"):
                return True
            elif answer in ("n", "no"):
                return False
            else:
                print("Please enter 'y' or 'n'.")
                continue
