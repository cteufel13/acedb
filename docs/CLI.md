# CLI

The `acedb` package provides a command-line interface (CLI) for interacting with various database and API services.

## Installation

If you've installed the package, the CLI should be available in your environment. You can run commands using:

```bash
acedb [COMMAND]
```

## Available Commands

### Database Connection Commands

- **login**: Configure and test database connection
  ```bash
  acedb login
  ```
  You will be prompted to enter:
  - Host
  - Port
  - Database name
  - Username
  - Password

- **logout**: Clear saved database credentials
  ```bash
  acedb logout
  ```

- **check_connection**: Test if the database connection is working
  ```bash
  acedb check_connection
  ```

- **login_status**: Check if you're currently logged in
  ```bash
  acedb login_status
  ```

- **list_config**: Display the current configuration
  ```bash
  acedb list_config
  ```

### Databento API Commands

- **dbn_login**: Configure Databento API access
  ```bash
  acedb dbn_login
  ```
  You will be prompted to enter your Databento API key.

- **dbn_logout**: Remove Databento API credentials
  ```bash
  acedb dbn_logout
  ```

### FRED API Commands

- **fred_login**: Configure FRED API access
  ```bash
  acedb fred_login
  ```
  You will be prompted to enter your FRED API key.

- **fred_logout**: Remove FRED API credentials
  ```bash
  acedb fred_logout
  ```

## Configuration

The CLI stores configuration in `~/.acedb/config.json`. This file contains:
- Database connection details
- API keys for external services

For security reasons, it's recommended not to edit this file directly. Use the CLI commands instead.

