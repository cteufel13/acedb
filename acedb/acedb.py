from .config import Config
from typing import List, Dict, Any, Tuple

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
        **kwargs,
    ):

        schemas = [schemas] if isinstance(schemas, str) else schemas
        symbols = [symbols] if isinstance(symbols, str) else symbols

        if not isinstance(schemas, list) or not isinstance(symbols, list):
            raise ValueError("Schemas and symbols must be lists or strings.")

        self.databento_client._validate_schema_and_dataset(
            schema=schemas, dataset=dataset
        )

        col_dict = self.databento_client._get_columns(
            dataset=dataset,
            schema=schemas,
        )

        self.database_client._ensure_database_schema(
            dataset=dataset, schemas=schemas, col_dict=col_dict
        )

        result: dict[str, pd.DataFrame] = {}

        min_start, max_end = self.databento_client._get_dataset_range(dataset=dataset)

        query_start = start or min_start
        query_end = end or max_end

        for schema in schemas:
            for symbol in symbols:
                db_start, db_end = self.database_client._get_local_range(
                    dataset=dataset,
                    schema=schema,
                    symbol=symbol,
                )

                download_ranges = self.database_client._find_missing_range(
                    dataset_range=(min_start, max_end),
                    database_range=(db_start, db_end),
                    query_range=(start, end),
                )

                for range_start, range_end in download_ranges:
                    cost = self.databento_client._calculate_cost(
                        dataset=dataset,
                        schema=schema,
                        symbol=symbol,
                        start=range_start,
                        end=range_end,
                    )

                    if cost > 1e-5:
                        if not self._ask_yn(
                            f"Download {schema}/{symbol} from {range_start} to {range_end}? Cost: {cost}"  # noqa: E501
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
