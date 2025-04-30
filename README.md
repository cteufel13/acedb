# ACEDB - Analytics Club ETH Database

## Overview
ACEDB is a wrapper for a PostgreSQL database that fetches and retrieves financial data from the Databento API. It efficiently stores this data in a structured database format, enabling easy access and analysis of market information. This was originally for the Analytics Club at ETH (ACE)

## Features
- Seamless integration with Databento API
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
acedb dbn_login

# Help
acedb --help
```

## Usage
```python
from acedb import AceDB

dba = AceDB()

# Retrieve Data
data = dba.get(dataset = "XNAS.ITCH",
        schemas=  ["ohlcv-1m","ohlcv-1s"],
        symbols= ['AAPL','GOOGL'] ,
        start="2024-01-02",
        end="2025-01-02",)

# Upload Downloaded Data (pd/pl DataFrame)

dba.insert(dataset = "XNAS.ITCH",schema = "ohlcv-1m", data = your_data)

```

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Contact
Project Link: [https://github.com/yourusername/acedb](https://github.com/cteufel13/acedb)