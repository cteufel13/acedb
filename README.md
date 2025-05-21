# ACEDB - Analytics Club ETH Database

## Overview
ACEDB is a wrapper for a PostgreSQL database that fetches and retrieves financial data from the Databento API. It efficiently stores this data in a structured database format, enabling easy access and analysis of market information. This was originally for the Analytics Club at ETH (ACE)

## Features
- Seamless integration with Databento API
- Integration with FRED API
- Automated data fetching and storage
- PostgreSQL database management
- Historical data storage and retrieval

## Installation
```bash
# Clone the repository
git clone https://github.com/cteufel13/acedb.git

# Use pip
pip install acedb
```

## Configuration

```bash
# Enter Postgre Database Information:
acedb login

# Enter Databento API Token:
acedb dbn-login

#Enter FRED API Token:
acedb fred-login

# Help
acedb --help
```

## Usage
```python
from acedb import AceDB

dba = AceDB()

# Retrieve Data
data = dba.Get(dataset = "XNAS.ITCH",
        schemas=  ["ohlcv-1m","ohlcv-1s"],
        symbols= ['AAPL','GOOGL'] ,
        start="2024-01-02",
        end="2025-01-02",
        download = True
        filetype = "csv")

# Upload Downloaded Data (pd/pl DataFrame)

dba.insert(dataset = "XNAS.ITCH",schema = "ohlcv-1m", data = your_data)

# get current overview of what schemas and the symbols in it exist

dba.get_ranges()
```

## Planned Features:
- Adding unconvential/custom data along the lines of news reports/ non databento data
- Crypto

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
Project Link: [https://github.com/cteufel13/acedb](https://github.com/cteufel13/acedb)

## More Details:

Take a look at the [documentation](docs/index.md)