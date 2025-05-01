import psycopg2
import io
from typing import List, Dict, Any, Tuple
import polars as pl
import pandas as pd
from datetime import datetime, timedelta, timezone


TYPE_MAP = {
    "int": "NUMERIC",
    "float": "NUMERIC",
    "string": "VARCHAR(255)",
}


class PostgreDBClient:

    def __init__(self, host, port, db_name, username, password):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=db_name,
                user=username,
                password=password,
                connect_timeout=5,
            )
            self._cursor = conn.cursor()

        except:
            print("Error connecting to the database. Please check your configuration.")
            raise

        print("Database connection established.")

    def _insert_database(self, dataset: str, schema: str, data: pd.DataFrame) -> None:

        cols = data.columns
        io_buffer = io.StringIO()
        data.to_csv(io_buffer)
        io_buffer.seek(0)

        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)

        copy_query = f' COPY "{dataset}"."{schema}" FROM STDIN WITH CSV HEADER'

        self._cursor.copy_expert(copy_query, io_buffer)
        self._cursor.connection.commit()
        print(f"Data inserted into {dataset}.{schema}.")

    def _ensure_database_schema(
        self, dataset: str, schemas: List[str], col_dict: Dict[str, List[str]]
    ) -> None:
        if not self._check_dataset_in_database(dataset):
            self._create_dataset(dataset)

        for schema in schemas:
            cols = col_dict.get(schema)
            if not self._check_schema_in_database(dataset, schema):
                self._create_schema(dataset, schema, cols)

    def _get_local_range(
        self, dataset: str, schema: str, symbol: str
    ) -> tuple[datetime, datetime]:

        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)
        symbol = self._convert_for_SQL(symbol)

        start_end_query = f'SELECT MIN(ts_event), MAX(ts_event) FROM "{dataset}"."{schema}" WHERE symbol = %s'
        self._cursor.execute(start_end_query, (symbol,))
        start, end = self._cursor.fetchone()

        return start, end

    def _retrieve_data(self, dataset: str, schema: str, symbol: str):
        """
        Get the start and end dates of the schema
        """
        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)
        symbol = self._convert_for_SQL(symbol)

        start_end_query = f'SELECT * FROM "{dataset}"."{schema}" WHERE symbol = %s'
        self._cursor.execute(start_end_query, (symbol,))
        rows = self._cursor.fetchall()
        columns = [col[0] for col in self._cursor.description]
        all_data = pl.DataFrame(rows, schema=columns, orient="row").to_pandas()
        return all_data

    def _find_missing_range(
        self,
        dataset_range: tuple[datetime, datetime],
        database_range: tuple[datetime | None, datetime | None],
        query_range: tuple[datetime | None, datetime | None],
    ) -> list[tuple[datetime, datetime]]:

        ds_start, ds_end = dataset_range
        db_start, db_end = database_range
        q_start, q_end = query_range

        if q_start is None or q_end is None:
            q_start = ds_start
            q_end = ds_end

        if db_start is not None:
            db_start, db_end = self.drop_tz(db_start), self.drop_tz(db_end)
        q_start, q_end = self.drop_tz(q_start), self.drop_tz(q_end)

        # If nothing in DB, download full query interval
        if db_start is None or db_end is None:
            return [(q_start, q_end)]

        missing = []
        if q_start < db_start:
            missing.append((q_start, min(db_start, q_end)))
        if q_end > db_end:
            missing.append((max(db_end, q_start), q_end))

        return missing

    def _check_dataset_in_database(self, dataset: str) -> bool:
        """
        Check if the dataset is in the database
        Databento Dataset is one Schema in DB
        """
        dataset = self._convert_for_SQL(dataset)
        ds_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s) AS dataset_exists"
        self._cursor.execute(ds_check_query, (dataset,))
        exists = self._cursor.fetchone()

        return bool(exists[0])

    def _check_schema_in_database(self, dataset: str, schema: str) -> bool:
        """
        Check if the schema is in the database
        """
        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)

        schma_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND  table_name = %s ) AS schema_exists"
        self._cursor.execute(schma_check_query, (dataset, schema))
        exists = self._cursor.fetchone()

        return bool(exists[0])

    def _create_dataset(self, dataset: str):
        """
        Create a new dataset in the database
        """
        dataset = self._convert_for_SQL(dataset)

        create_dataset_query = f"CREATE SCHEMA {dataset}"
        self._cursor.execute(create_dataset_query)
        print(f"Dataset {dataset} created.")

    def _create_schema(self, dataset: str, schema: str, cols: List[str]):
        """
        Create a new schema in the database
        """
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

    def _get_datasets(
        self,
    ):

        query = (
            " SELECT schema_name FROM information_schema.schemata ORDER BY schema_name"
        )
        self._cursor.execute(query)
        rows = self._cursor.fetchall()
        datasets = [row[0] for row in rows]
        return datasets

    def _get_schemas(self, dataset: str) -> List[str]:
        """
        Get the schemas in the database
        """
        dataset = self._convert_for_SQL(dataset)
        query = f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{dataset}'"
        self._cursor.execute(query)
        rows = self._cursor.fetchall()
        schemas = [row[0] for row in rows]
        return schemas

    def _get_symbols(self, dataset: str, schema: str) -> List[str]:
        """
        Get the symbols in the database
        """
        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)
        query = f'SELECT DISTINCT symbol FROM "{dataset}"."{schema}"'
        self._cursor.execute(query)
        rows = self._cursor.fetchall()
        symbols = [row[0] for row in rows]
        return symbols

    def _disconnect(self):
        """
        Disconnect from the database
        """
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
    def drop_tz(d: datetime) -> datetime:
        return d.replace(tzinfo=None) if d.tzinfo is not None else d
