import databento as dbn
import os
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse
from typing import List
import polars as pl


class DBNClient:
    """
    Databento Client Wrapper"""

    def __init__(self):

        if "DATABENTO_API_KEY" not in os.environ:
            raise ValueError("Missing Databento API key")

        self._client = dbn.Historical()
        print("Databento client initialized.")

    def _download_data(
        self,
        dataset: str,
        schema: str,
        symbol: str,
        start: str,
        end: str,
    ):
        """
        Download data from Databento
        """

        data = self._client.timeseries.get_range(
            dataset=dataset,
            schema=schema,
            symbols=symbol,
            start=start,
            end=end,
        ).to_df()
        return data

    def _get_dataset_range(
        self,
        dataset: str,
    ) -> tuple[datetime, datetime]:
        """
        Get the range of a dataset
        """
        range = self._client.metadata.get_dataset_range(dataset)
        start_str = range["start"]
        end_str = range["end"]
        start = isoparse(start_str)
        end = isoparse(end_str)

        if (
            end.hour == 4
            and end.minute == 0
            and end.second == 0
            and end.microsecond == 0
        ):
            prev = end - timedelta(days=1)
            end = datetime(
                prev.year,
                prev.month,
                prev.day,
                23,
                58,
                tzinfo=None,
            )

        return start, end

    def _get_columns(
        self,
        dataset: str,
        schema: str | List[str],
    ) -> dict[list[str]]:
        """
        Get the columns in the schema from Databento and prepare them for Database
        """
        if isinstance(schema, str):
            schema = [schema]

        col_dict = {}

        # validate dataset and schema
        for s in schema:
            cols = self._client.metadata.list_fields(s, "csv")

            for col in cols:
                if col["name"] in ("ts_event", "ts_recv"):
                    col["type"] = "timestamp"

            # symbol always appears at the end
            cols.append({"name": "symbol", "type": "string"})
            col_dict[s] = cols

        return col_dict

    def _validate_schema_and_dataset(self, dataset: str, schema: list[str]) -> None:
        """
        Validate the dataset and schema in Databento
        """
        if not self._validate_dataset(dataset):
            raise ValueError(f"Dataset {dataset} not found in Databento.")
        for s in schema:
            if not self._validate_schema(dataset, s):
                raise ValueError(f"Schema {s} not found in Databento.")

    def _validate_dataset(self, dataset: str) -> bool:
        if dataset not in self._client.metadata.list_datasets():
            print(f"Dataset {dataset} not found in Databento.")
            return False
        return True

    def _validate_schema(self, dataset: str, schema: str) -> bool:
        if schema not in self._client.metadata.list_schemas(dataset):
            print(f"Schema {schema} not found in Databento.")
            return False
        return True

    def _calculate_cost(
        self,
        dataset: str,
        schema: str,
        symbol: str,
        start: str,
        end: str,
    ) -> float:
        """
        Calculate the cost of downloading data from Databento
        """

        # Get the size of the data
        cost = self._client.metadata.get_cost(
            dataset=dataset,
            schema=schema,
            symbols=symbol,
            start=start,
            end=end,
        )
        return cost
