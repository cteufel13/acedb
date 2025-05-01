import databento as dbn
import os
from datetime import datetime, timedelta, timezone
from dateutil.parser import isoparse
import polars as pl


class DBNClient:
    """
    Databento Client Wrapper"""

    def __init__(self, token: str):

        if "DATABENTO_API_KEY" not in os.environ:
            raise ValueError("Missing Databento API key")

        self._client = dbn.Historical()
        print("Databento client initialized.")

    def get_data(
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

        data = (
            self._client.timeseries.get_range(
                dataset=dataset,
                schema=schema,
                symbols=symbol,
                start=start,
                end=end,
            )
            .to_df()
            .reset_index()
        )
        return data

    def get_dataset_range(
        self,
        dataset: str,
        start: str,
        end: str,
        symbology: str = "default",
    ) -> tuple[datetime, datetime]:
        """
        Get the range of a dataset
        """
        rng = self._client.metadata.get_dataset_range(dataset)
        start_str = rng["start"]
        end_str = rng["end"]
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

    def get_columns(
        self,
        dataset: str,
        schema: str,
    ) -> list[str]:
        """
        Get the columns in the schema from Databento and prepare them for Database
        """

        cols = self._client.metadata.list_fields(schema, "csv")

        # convert ts_event and ts_recv to timestamp
        for col in cols:
            if col["name"] in ("ts_event", "ts_recv"):
                col["type"] = "timestamp"

        # symbol always appears at the end
        cols.append({"name": "symbol", "type": "string"})

        return cols

    def check_dataset(self, dataset: str) -> bool:
        if dataset not in self._client.metadata.list_datasets():
            print(f"Dataset {dataset} not found in Databento.")
            return False
        return True

    def check_schema(self, dataset: str, schema: str) -> bool:
        if schema not in self._client.metadata.list_schemas(dataset):
            print(f"Schema {schema} not found in Databento.")
            return False
        return True
