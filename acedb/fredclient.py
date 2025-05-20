from fredapi import Fred
import os
import pandas as pd


class FREDClient:

    def __init__(self):
        self._client = Fred(api_key=os.environ["FRED_API_KEY"])
        print("FRED client initialized.")

    def get_data(self, series_id: str):
        """
        Get data from FRED for a given series ID.
        """
        try:
            series_data = self._get_vintage(series_id)
            series_data = self._process_vintage(series_data)
            series_data = series_data.reset_index()

            return series_data, self._get_column_dict(series_data)
        except:
            series_data = self._get_series(series_id)
            series_data.index = pd.to_datetime(series_data.index, format="%Y-%m-%d")
            series_data.index.name = "ts_event"
            series_data = series_data.reset_index()
            return series_data, self._get_column_dict(series_data)

    def _validate_symbol(self, dataset: str) -> bool:
        """
        Validate if the dataset exists in FRED.
        """
        if self._get_series_info(dataset) is None:
            return False
        return True

    def _get_series_info(self, series_id: str) -> pd.Series:
        """
        Get information about a series from FRED.
        """
        series_info = self._client.get_series_info(series_id)
        return series_info

    def _get_series(self, series_id: str) -> pd.Series:
        """
        Get series data from FRED.
        """
        series_data = self._client.get_series(series_id)
        return series_data

    def _get_vintage(self, series_id: str) -> pd.Series:
        """
        Get vintage data from FRED.
        """
        series_data = self._client.get_series_all_releases(series_id)
        return series_data

    def _process_vintage(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process vintage data from FRED.
        """
        df["value"] = df["value"].astype(float)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
        pivot_df = df.pivot(index="realtime_start", columns="date", values="value")
        pivot_df.columns = pivot_df.columns.strftime("%Y-%m-%d")

        pivot_df = pivot_df.ffill(axis=0)
        pivot_df.index = pd.to_datetime(pivot_df.index, format="%Y-%m-%d")
        pivot_df.index.name = "ts_event"
        return pivot_df

    def _get_column_dict(self, data: pd.DataFrame) -> list:
        col_dict = [
            {"name": str(col), "type": str(dtype.name)}
            for col, dtype in data.dtypes.items()
        ]
        return col_dict
