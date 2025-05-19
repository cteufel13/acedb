from fredapi import Fred
import os


class FredClient:

    def __init__(self):
        self._client = Fred(api_key=os.environ["FRED_API_KEY"])
        print("FRED client initialized.")

    def get_data(self, series_id):
        try:
            data = self.get_vintages(series_id)

        except Exception as e:
            data = self.get_series(series_id)
        finally:
            return data

    def get_series(self, series_id):
        """
        Get a series from FRED.
        """
        series = self._client.get_series(series_id)
        return series

    def get_series_info(self, series_id):
        """
        Get information about a series from FRED.
        """
        series_info = self._client.get_series_info(series_id)
        return series_info

    def get_vintages(self, series_id):
        """
        Get a list of vintages from FRED.
        """
        vintages = self._client.get_series_all_releases(series_id)
        return vintages
