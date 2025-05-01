import psycopg2
import io
from typing import List, Dict, Any, Tuple
import polars as pl
import pandas as pd

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

    def _get_range(self, dataset: str, schema: str, symbol: str):
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

    def _insert_db(self, dataset: str, schema: str, data: pl.DataFrame) -> None:

        cols = data.columns
        io_buffer = io.StringIO()
        data.write_csv(io_buffer)
        io_buffer.seek(0)

        dataset = self._convert_for_SQL(dataset)
        schema = self._convert_for_SQL(schema)

        copy_query = f' COPY "{dataset}"."{schema}" FROM STDIN WITH CSV HEADER'

        self._cursor.copy_expert(copy_query, io_buffer)
        self._cursor.connection.commit()
        print(f"Data inserted into {dataset}.{schema}.")

    def _check_dataset_exists(self, dataset: str) -> bool:
        """
        Check if the dataset is in the database
        Databento Dataset is one Schema in DB
        """
        dataset = self._convert_for_SQL(dataset)
        ds_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s) AS dataset_exists"
        self._cursor.execute(ds_check_query, (dataset,))
        exists = self._cursor.fetchone()

        return bool(exists[0])

    def _check_schema_exists(self, dataset: str, schema: str) -> bool:
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

    @staticmethod
    def _convert_for_SQL(terms: List[str] | str) -> List[str]:
        """
        Convert the terms to a string
        """
        if isinstance(terms, str):
            return terms.replace(".", "_").replace("-", "_")
        else:
            return [term.replace(".", "_").replace("-", "_") for term in terms]
