# Usage Guide

This guide provides instructions on how to use the `acedb` package effectively for accessing and managing financial data.

## Initialization

Before you start using the package, make sure you've completed the setup process described in the [Installation and Setup](installation.md) guide.

### Importing and Creating an Instance

```python
from acedb import AceDB

# Create an instance of AceDB
acedb = AceDB()
```

When you initialize AceDB, it automatically loads your configuration.

## Retrieving Data

### Basic Data Retrieval

The main function for retrieving data is `get_data()`:

```python
data = acedb.get_data(
    dataset="XNAS.ITCH",
    schemas=["ohlcv-1m"],
    symbols=["AAPL", "GOOGL"],
    start="2023-01-01",
    end="2023-01-31"
)
```

### Parameters for `get_data()`

- **dataset** (str): The name of the dataset to retrieve data from (e.g., "XNAS.ITCH", "GLBX.MDP3", or "FRED")
- **schemas** (List[str] | str): Schema names for Databento datasets (e.g., "ohlcv-1m", "ohlcv-1h", "trades")
- **symbols** (List[str] | str): Symbol(s) to retrieve data for
- **start** (str): Start date/time for the data range (format: "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS")
- **end** (str): End date/time for the data range
- **stype_in** (str): Input symbol type. Defaults to "raw_symbol". Use "parent" for futures and options. Use "continuous" for rolling contracts.
- **stype_out** (str): Output symbol type. Defaults to "instrument_id".
- **use_databento** (bool): Whether to source missing data from Databento. Defaults to True.
- **download** (bool): Whether to download the data to a file. Defaults to False.
- **path** (str): Path to save the downloaded data.
- **filetype** (str): File format for downloaded data. Defaults to "csv".

### Working with Databento Data

When retrieving data from Databento, AceDB will:
1. Check if the data is already in the database
2. Download any missing data from Databento (if `use_databento=True`)
3. Store the downloaded data in the database for future use
4. Return the requested data

```python
# Get Databento market data
es_futures_data = acedb.get_data(
    dataset="GLBX.MDP3",
    schemas=["ohlcv-1h"],
    symbols=["ES.c.0"],
    start="2023-01-01",
    end="2023-01-31",
    stype_in="continuous",
    use_databento=True
)
```

### Working with FRED Data

For FRED economic data:
- No need to include a schema since there aren't schemas in the Databento sense.
- The symbols can be both vintages (multiple releases/rereleases) or normal series. Whenever possible this will return vintages.

```python
# Get GDP data from FRED
gdp_data = acedb.get_data(
    dataset="FRED",
    symbols=["GDP"],
    start="2000-01-01",
    end="2023-12-31"
)
```

### Downloading Data to Files

You can download the retrieved data to files:

```python
data = acedb.get_data(
    dataset="XNAS.ITCH",
    schemas=["ohlcv-1m"],
    symbols=["AAPL"],
    start="2023-01-01",
    end="2023-01-31",
    download=True,
    path="data",
    filetype="csv"
)
```

Supported file types include: csv, parquet, json, and excel (xlsx) or anything supported by pandas.

## Inserting Data

You can insert external data into the database:

```python
import polars as pl

# Read data from a file
data = pl.read_csv('market_data.csv')

# Insert into database
acedb.insert(
    dataset="XNAS.ITCH",
    schema="ohlcv-1m",
    symbol="AAPL",
    data=data
)
```

## Exploring Available Data

To get an overview of what data is available in your database:

```python
# Get all available ranges
all_ranges = acedb.get_ranges()

# Get ranges for a specific dataset
xnas_ranges = acedb.get_ranges(dataset="XNAS.ITCH")

# Get ranges for a specific schema in a dataset
ohlcv_ranges = acedb.get_ranges(dataset="XNAS.ITCH", schema="ohlcv-1m")

# Get ranges for a specific symbol
aapl_ranges = acedb.get_ranges(dataset="XNAS.ITCH", schema="ohlcv-1m", symbol="AAPL")
```

The `get_ranges()` function returns a dictionary with information about what data is available in the database, organized by dataset, schema, and symbol.

## Working with Options and Futures

For options and futures data, use the `stype_in="parent"` parameter:

```python
# Get ES futures options data
es_options = acedb.get_data(
    dataset="GLBX.MDP3",
    schemas=["trades"],
    symbols=["ES.OPT"],
    start="2023-01-01",
    end="2023-01-31",
    stype_in="parent"
)
```

For rolling options and futures data, use the `stype_in="continuous"` parameter. You can find an example [here](https://databento.com/docs/examples/symbology/continuous).

For any other combinations take a look at the databento guide [here](https://databento.com/docs/api-reference-historical/basics/symbology).

## Cost Management

When requesting data from Databento that isn't already in your database, AceDB will:

1. Calculate the cost of the request
2. Display the estimated cost
3. Ask for confirmation before proceeding

This helps prevent unexpected charges from the Databento API.

## Best Practices

1. **Start small**: When testing, use small date ranges to minimize costs
2. **Check existing data**: Use `get_ranges()` to see what data is already in your database
3. **Use specific symbols**: Request only the symbols you need
4. **Save downloaded data**: Use the `download=True` parameter to keep a local backup

___

## Additional Resources
- [Home](index.md)
- [Installation and Setup](installation.md)
- [CLI](CLI.md)
