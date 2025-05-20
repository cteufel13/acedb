import psycopg2
import io
from typing import List, Dict, Any, Tuple
import polars as pl
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta, timezone


TYPE_MAP = {
    "int": "NUMERIC",
    "float": "NUMERIC",
    "string": "VARCHAR(255)",
    "float64": "NUMERIC",
    "datetime64[ns]": "TIMESTAMP",
    "datetime64[ns, UTC]": "TIMESTAMP",
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

    def _insert_data(
        self, sql_schema: str, table_name: str, data: pd.DataFrame
    ) -> None:
        """
        Insert data into the database.
        """
        cols = data.columns
        io_buffer = io.StringIO()
        data.to_csv(io_buffer, index=False)
        io_buffer.seek(0)
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)

        copy_query = f' COPY "{sql_schema}"."{table_name}" FROM STDIN WITH CSV HEADER'

        self._cursor.copy_expert(copy_query, io_buffer)
        self._cursor.connection.commit()
        print(f"Data inserted into {sql_schema}.{table_name}.")

    def _retrieve_data(
        self,
        sql_schema: str,
        table_name: str,
        symbol: str | List[str] = None,
        start: datetime = None,
        end: datetime = None,
    ) -> pd.DataFrame:
        """
        Retrieve data from the database.
        """
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)

        if isinstance(symbol, str):
            symbol = self._convert_for_SQL(symbol)
            symbol_query = f" WHERE symbol = '{symbol}'"
        elif isinstance(symbol, list):
            symbol = [self._convert_for_SQL(s) for s in symbol]
            symbol_query = f" WHERE symbol IN ({', '.join(map(repr, symbol))})"
        else:
            symbol_query = ""

        if start and end:
            date_query = f" AND ts_event BETWEEN '{start}' AND '{end}'"
        elif start:
            date_query = f" AND ts_event >= '{start}'"
        elif end:
            date_query = f" AND ts_event <= '{end}'"
        else:
            date_query = ""

        select_query = (
            f'SELECT * FROM "{sql_schema}"."{table_name}" '
            + f"{symbol_query} {date_query}"
        )
        self._cursor.execute(select_query)
        data = self._cursor.fetchall()
        columns = [col[0] for col in self._cursor.description]
        df = pd.DataFrame(data, columns=columns)
        df["ts_event"] = pd.to_datetime(df["ts_event"], format="%Y-%m-%d %H:%M:%S")
        df = df.sort_values(by=["ts_event"])
        return df

    ###### Checking database objects ######

    def _ensure_schema(self, sql_schema: str) -> None:
        """
        Ensure the SQL schema is in the correct format.
        """
        if not sql_schema:
            raise ValueError("SQL schema cannot be empty.")
        if not isinstance(sql_schema, str):
            raise ValueError("SQL schema must be a string.")

        sql_schema = self._convert_for_SQL(sql_schema)

        if not self._check_schemas_in_database(sql_schema):
            # Create the schema if it doesn't exist
            self._create_schema(sql_schema)

    def _check_schemas_in_database(self, sql_schema: str) -> bool:
        """
        Check if the schemas exist in the database.
        """
        sql_schema = self._convert_for_SQL(sql_schema)

        ds_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = %s) AS dataset_exists"
        self._cursor.execute(ds_check_query, (sql_schema,))
        exists = self._cursor.fetchone()

        return bool(exists[0])

    def _check_table_in_database(self, sql_schema: str, table_name: str) -> bool:
        """
        Check if the table exists in the database.
        """
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)
        table_check_query = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = %s AND table_name = %s) AS table_exists"
        self._cursor.execute(table_check_query, (sql_schema, table_name))
        exists = self._cursor.fetchone()
        return bool(exists[0])

    def _ensure_columns_exist(
        self, sql_schema: str, table_name: str, col_dict: List[Dict[str, str]]
    ) -> None:
        """
        Ensure the columns exist in the table.
        """
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)

        for col in col_dict:
            col_name = self._convert_for_SQL(col["name"])
            col_type = TYPE_MAP.get(col["type"], col["type"])

            column_check_query = (
                "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
                f"WHERE table_schema = %s AND table_name = %s AND column_name = %s) AS column_exists"
            )
            self._cursor.execute(column_check_query, (sql_schema, table_name, col_name))
            exists = self._cursor.fetchone()

            if not exists[0]:
                alter_table_query = f'ALTER TABLE "{sql_schema}"."{table_name}" ADD COLUMN "{col_name}" {col_type}'
                self._cursor.execute(alter_table_query)
                print(f"Column {col_name} added to {sql_schema}.{table_name}.")

        self._cursor.connection.commit()

    ##### Time #####

    def _get_max_time(
        self, sql_schema: str, table_name: str, symbol: str = None
    ) -> datetime | None:
        """
        Get the maximum time from the database.
        """
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)
        if symbol:
            symbol = self._convert_for_SQL(symbol)
            symbol_query = f" WHERE symbol = {symbol}"
        else:
            symbol_query = ""

        max_time_query = (
            f'SELECT MAX(ts_event) FROM "{sql_schema}"."{table_name}" '
            + f"{symbol_query}"
        )
        self._cursor.execute(max_time_query)
        max_time = self._cursor.fetchone()

        return max_time[0] if max_time[0] else None

    def retrieve_ranges(
        self, sql_schema: str, table_name: str, symbol
    ) -> List[Tuple[datetime, datetime]]:
        """
        Retrieve the ranges of data for a given symbol.
        """
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)

        query = f""" SELECT request_start, request_end FROM "time".time_range WHERE "schema" = '{sql_schema}' AND "table" = '{table_name}' AND "symbol" = '{symbol}'"""
        self._cursor.execute(query)
        ranges = self._cursor.fetchall()

        return [(r[0], r[1]) for r in ranges]

    def _append_ranges(
        self,
        sql_schema: str,
        table_name: str,
        symbol: str,
        ranges: List[Tuple[datetime, datetime]],
    ) -> None:
        """
        Append the ranges of data for a given symbol.
        """
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)

        for start, end in ranges:
            query = f""" INSERT INTO "time".time_range ("schema", "table", "symbol", "request_start", "request_end") VALUES ('{sql_schema}', '{table_name}', '{symbol}', '{start}', '{end}')"""
            self._cursor.execute(query)

        self._cursor.connection.commit()

    def _retrieve_existing_ranges(self):

        query = (
            """ SELECT DISTINCT "schema", "table", "symbol" FROM "time".time_range"""
        )
        self._cursor.execute(query)
        data = self._cursor.fetchall()
        df = pd.DataFrame(data, columns=[col[0] for col in self._cursor.description])
        df["schema"] = df["schema"].str.replace("_", ".")
        df["table"] = df["table"].str.replace("_", "-")
        return df

    ##### Create Database Objects #####

    def _create_schema(self, sql_schema: str) -> None:
        """
        Create the schema in the database.
        """
        create_schema_query = f'CREATE SCHEMA IF NOT EXISTS "{sql_schema}"'
        self._cursor.execute(create_schema_query)
        self._cursor.connection.commit()
        print(f"Schema {sql_schema} created.")
        self._add_permissions(sql_schema)

    def _create_table(
        self, sql_schema: str, table_name: str, col_dict: List[Dict[str, str]]
    ) -> None:
        """
        Create a table in the database.
        """
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)

        create_schema_query = (
            f'CREATE TABLE IF NOT EXISTS "{sql_schema}"."{table_name}"  '
        )
        col_defs = ",\n    ".join(
            f'"{col["name"]}" {TYPE_MAP.get(col["type"], col["type"])}'
            for col in col_dict
        )
        create_schema_query += f"({col_defs})"

        self._cursor.execute(create_schema_query)
        self._cursor.connection.commit()

        print(f"Table {table_name} created in Schema {sql_schema}.")

    ##### Temporary Table #####

    def _create_temp_symbols(self, table_name: str, symbols) -> None:
        """
        Create a temporary table in the database.
        """
        create_temp_table_query = f"CREATE TEMP TABLE {table_name} (symbol TEXT)"
        self._cursor.execute(create_temp_table_query)

        buffer = io.StringIO()
        for symbol in symbols:
            buffer.write(f"{symbol}\n")
        buffer.seek(0)
        buffer.seek(0)

        self._cursor.copy_expert("COPY temp_symbols (symbol) FROM STDIN", buffer)
        self._cursor.connection.commit()

        self._cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")

    def _retrieve_temp_symbols(
        self,
        sql_schema: str,
        table_name: str,
        temp_table_name: str,
        start: datetime = None,
        end: datetime = None,
    ) -> pd.DataFrame:
        """
        Retrieve symbols from the temporary table.
        """
        sql_schema = self._convert_for_SQL(sql_schema)
        table_name = self._convert_for_SQL(table_name)
        temp_table_name = self._convert_for_SQL(temp_table_name)

        if start and end:
            date_query = f" WHERE t.ts_event BETWEEN '{start}' AND '{end}'"
        elif start:
            date_query = f" WHERE t.ts_event >= '{start}'"
        elif end:
            date_query = f" WHERE t.ts_event <= '{end}'"
        else:
            date_query = ""

        query = (
            f' SELECT t.* FROM "{sql_schema}"."{table_name}" t JOIN {temp_table_name} s ON t.symbol = s.symbol'
            + date_query
        )
        self._cursor.execute(query)
        data = self._cursor.fetchall()
        df = pd.DataFrame(data, columns=[col[0] for col in self._cursor.description])
        df["ts_event"] = pd.to_datetime(df["ts_event"], format="%Y-%m-%d %H:%M:%S")

        return df

    ##### Permissions #####

    def _add_permissions(self, sql_schema: str) -> None:
        """
        Add permissions to the dataset and schema
        """
        query = f"GRANT USAGE, CREATE ON SCHEMA {sql_schema} TO PUBLIC;"
        query2 = f"""ALTER DEFAULT PRIVILEGES IN SCHEMA {sql_schema}
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO PUBLIC;"""
        query += query2
        self._cursor.execute(query)
        self._cursor.connection.commit()

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
