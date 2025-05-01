from .config import Config
from typing import List, Dict, Any, Tuple
from collections import defaultdict

import pandas as pd

from .postgreclient import PostgreDBClient
from .dbnclient import DBNClient


class AceDB:

    def __init__(self):
        self._config = Config()
        self.database_client = PostgreDBClient(
            host=self._config.host,
            port=self._config.port,
            db_name=self._config.db_name,
            username=self._config.username,
            password=self._config.password,
        )
        self.databento_client = DBNClient()

    def get_data(
        self,
        dataset: str,
        schemas: List[str] | str,
        symbols: List[str] | str,
        start: str = None,
        end: str = None,
        use_databento: bool = True,
        **kwargs,
    ):
        """
        Retrieves data from Database and Databento to find minimum Cost.

        It will check if the data is already in the database. If not, it will
        download the data from Databento and insert it into the database.
        If the data is already in the database, it will retrieve it from there.


        Parameters
        ----------
        dataset : str
            This is the name of the dataset as found on databento.
        schemas : List[str] | str
            This is a schema as a string or multiple schemas as a list of strings, as found on databento.
        symbols : List[str] | str
            This is a symbol as a string or multiple symbols as a list of strings. These are Stock Tickers.
        start : str, optional
            This is the start date of the data to be retrieved. The default is None.
        end : str, optional
            This is the end date of the data to be retrieved. The default is None.

        Returns
        -------
        dict[str, pd.DataFrame]
            A dictionary of DataFrames, where the keys are the schema names and the values are the DataFrames.
            Each DataFrame contains the data for the corresponding schema and symbol.


        Examples
        --------
        >>> acedbget_data(dataset='XNAS.ITCH',schemas='ohlcv-1h',symbols='NVDA',start='2023-01-01',end='2023-01-02')
        """
        # Makes sure schemas and symbols are lists
        schemas = [schemas] if isinstance(schemas, str) else schemas
        symbols = [symbols] if isinstance(symbols, str) else symbols

        if not isinstance(schemas, list) or not isinstance(symbols, list):
            raise ValueError("Schemas and symbols must be lists or strings.")

        # Check if the dataset is valid and exist on databento
        self.databento_client._validate_schema_and_dataset(
            schema=schemas, dataset=dataset
        )

        # Returns the columns of the schema from databento
        col_dict = self.databento_client._get_columns(
            dataset=dataset,
            schema=schemas,
        )

        # Check if the dataset is valid and exist on database and create the database if not
        self.database_client._ensure_database_schema(
            dataset=dataset, schemas=schemas, col_dict=col_dict
        )

        result: dict[str, pd.DataFrame] = {}

        if not use_databento:
            for schema in schemas:
                for symbol in symbols:
                    result.setdefault(schema, pd.DataFrame()).update(
                        self.database_client._retrieve_data(
                            dataset=dataset,
                            schema=schema,
                            symbol=symbol,
                        )
                    )
            return result

        # Get the start and end date of the dataset
        min_start, max_end = self.databento_client._get_dataset_range(dataset=dataset)

        for schema in schemas:
            for symbol in symbols:
                # Find the start and end date of the schema/symbol in the database
                db_start, db_end = self.database_client._get_local_range(
                    dataset=dataset,
                    schema=schema,
                    symbol=symbol,
                )

                # Finds ranges it needs to download from databento
                download_ranges = self.database_client._find_missing_range(
                    dataset_range=(min_start, max_end),
                    database_range=(db_start, db_end),
                    query_range=(start, end),
                )

                # If there are no ranges to download, return the data from the database
                for range_start, range_end in download_ranges:
                    cost = self.databento_client._calculate_cost(
                        dataset=dataset,
                        schema=schema,
                        symbol=symbol,
                        start=range_start,
                        end=range_end,
                    )

                    # Checks if the cost is above a threshold so it doesn't download single data points
                    if cost > 1e-5:
                        if not self._ask_yn(
                            f"Download {schema}/{symbol} from {range_start} to {range_end}? Cost: {cost} [Y/n]"
                        ):
                            continue

                        print("Downloading data...")
                        data = self.databento_client._download_data(
                            dataset=dataset,
                            schema=schema,
                            symbol=symbol,
                            start=range_start,
                            end=range_end,
                        )

                        print("Inserting data into database...")
                        self.database_client._insert_database(
                            dataset=dataset,
                            schema=schema,
                            data=data,
                        )

                        print("Data downloaded and inserted into database.")

                result[schema] = self.database_client._retrieve_data(
                    dataset=dataset,
                    schema=schema,
                    symbol=symbol,
                )
        return result

    def insert(self, dataset: str, schema: str, data: pd.DataFrame) -> None:
        """
        Insert data into the database.

        Parameters
        ----------
        dataset : str
            The name of the dataset.
        schema : str
            The name of the schema.
        data : pd.DataFrame
            The data to be inserted.

        Returns
        -------
        None
        """
        if not isinstance(data, pd.DataFrame):
            raise ValueError("Data must be a pandas DataFrame.")

        self.databento_client._validate_schema_and_dataset(
            schema=schema, dataset=dataset
        )
        col_dict = self.databento_client._get_columns(
            dataset=dataset,
            schema=schema,
        )

        assert (
            data.reset_index() == col_dict[schema]
        ), "DataFrame columns do not match schema columns."

        self.database_client._ensure_database_schema(
            dataset=dataset,
            schemas=[schema],
            col_dict={schema: col_dict},
        )

        self.database_client._insert_database(
            dataset=dataset,
            schema=schema,
            data=data,
        )
        print("Data inserted into database.")

    def get_ranges(
        self,
    ):
        result = {}

        datasets = self.database_client._get_datasets()

        datasets = [
            dataset
            for dataset in datasets
            if dataset
            not in ["public", "qrg_database_s1", "information_schema", "pg_catalog"]
        ]

        for dataset in datasets:

            schemas = self.database_client._get_schemas(dataset=dataset)
            result[dataset] = {}

            for schema in schemas:
                symbols = self.database_client._get_symbols(
                    dataset=dataset,
                    schema=schema,
                )

                result[dataset][schema] = {}
                for symbol in symbols:
                    start, end = self.database_client._get_local_range(
                        dataset=dataset,
                        schema=schema,
                        symbol=symbol,
                    )
                    result[dataset][schema][symbol] = (start, end)
        return result

    @staticmethod
    def _ask_yn(question: str) -> bool:
        """
        Ask a yes or no question and waits for an answer.
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
