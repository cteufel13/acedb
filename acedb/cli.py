import click
from pathlib import Path
from getpass import getpass
import json
import psycopg2
import os

CONFIG_PATH = Path.home() / ".acedb" / "config.json"


@click.group()
def cli():
    """CLI entry point for the acedb package."""
    pass


@cli.command()
def login():
    """Login to the database and save configuration."""
    host = click.prompt("Enter the host")
    port = click.prompt("Enter the port", type=int)
    db_name = click.prompt("Enter the database name")
    username = click.prompt("Enter the username")
    password = getpass("Enter the password")

    config = {
        "host": host,
        "port": port,
        "db_name": db_name,
        "username": username,
        "password": password,
    }

    try:
        # Test the connection
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=db_name,
            user=username,
            password=password,
            connect_timeout=5,
        )
        conn.close()
        click.echo("Success: Database connection established.")
    except Exception as e:
        click.echo(f"Error: Database connection failed - {e}. You may need VPN.")
        return

    # Ensure the config directory exists
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save the configuration to a file
    with open(CONFIG_PATH, "w") as config_file:
        json.dump(config, config_file)
    click.echo("Success: Login credentials saved.")


@cli.command()
def logout():
    """Logout from the database."""

    # Check if the config file exists
    if CONFIG_PATH.exists():

        # Load the config file
        with open(CONFIG_PATH, "r+") as config_file:
            config = json.load(config_file)

        # Set the config values to None
        config["password"] = None
        config["username"] = None
        config["db_name"] = None
        config["host"] = None
        config["port"] = None

        # Save the updated config file
        with open(CONFIG_PATH, "w") as config_file:
            json.dump(config, config_file)

        click.echo("Success: Logged out from database.")
    else:
        click.echo("Error: No active session found.")


@cli.command()
def check_connection():
    """Check the database connection"""
    if not CONFIG_PATH.exists():
        click.echo("Error: No configuration found. Please login first.")
        return

    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)

    try:
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            dbname=config["db_name"],
            user=config["username"],
            password=config["password"],
        )
        conn.close()
        click.echo("Success: Database connection established.")
    except Exception as e:
        click.echo(f"Error: Database connection failed - {e}")
        click.echo(
            "Info: You may need to connect to VPN. Make sure you are logged in to the database."
        )


@cli.command()
def login_status():
    """Check if the user is logged in."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as config_file:
            config = json.load(config_file)
        if config["username"] is not None:
            click.echo(f"Info: Logged in as {config['username']}.")
        else:
            click.echo("Info: Not logged in to database.")

        if config.get("dbn_token", None) is not None:
            click.echo("Info: Databento API key found.")
        else:
            click.echo("Info: Not logged in to Databento.")

        if config.get("fred_token", None) is not None:
            click.echo("Info: FRED API key found.")
        else:
            click.echo("Info: Not logged in to FRED.")

    else:
        click.echo("Error: No configuration found.")


@cli.command()
def list_config():
    """List the current configuration."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as config_file:
            config = json.load(config_file)
        click.echo("Info: Current configuration:")
        click.echo(json.dumps(config, indent=4))
    else:
        click.echo("Error: No configuration found.")


@cli.command()
def dbn_login():
    """Adds the Databento API key to env variables file"""

    db_token = click.prompt("Enter your Databento API key")
    db_token = db_token.strip()

    # Since Login is called from the CLI, we need to ensure the config directory exists
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Assue that API key is not empty
    if not db_token:
        click.echo("Error: Databento API key cannot be empty.")
        return

    # Adds API key to the config file
    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)

    config["dbn_token"] = db_token

    with open(CONFIG_PATH, "w") as config_file:
        json.dump(config, config_file)

    # Adds API key to the environment variables
    os.environ["DATABENTO_API_KEY"] = db_token

    click.echo("Success: Databento API key configured.")


@cli.command()
def fred_login():
    """Adds the FRED API key to env variables file"""

    fred_token = click.prompt("Enter your FRED API key")
    fred_token = fred_token.strip()

    # Since Login is called from the CLI, we need to ensure the config directory exists
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Assure that API key is not empty
    if not fred_token:
        click.echo("Error: FRED API key cannot be empty.")
        return

    with open(CONFIG_PATH, "r") as config_file:
        config = json.load(config_file)

    config["fred_token"] = fred_token

    with open(CONFIG_PATH, "w") as config_file:
        json.dump(config, config_file)

    os.environ["FRED_API_KEY"] = fred_token

    click.echo("Success: FRED API key configured.")


@cli.command()
def dbn_logout():
    """Removes the Databento API key from env variables file"""

    # Check if the config file exists
    if CONFIG_PATH.exists():

        # Load the config file
        with open(CONFIG_PATH, "r+") as config_file:
            config = json.load(config_file)

        # Check if the API key exists in the config file
        if "dbn_token" in config:
            config["dbn_token"] = None

            with open(CONFIG_PATH, "w") as config_file:
                json.dump(config, config_file)

            click.echo("Success: Databento API key removed.")
        else:
            click.echo("Info: No Databento API key found.")

    else:
        click.echo("Error: No configuration found.")


@cli.command()
def fred_logout():
    """Removes the FRED API key from env variables file"""

    # Check if the config file exists
    if CONFIG_PATH.exists():

        # Load the config file
        with open(CONFIG_PATH, "r+") as config_file:
            config = json.load(config_file)

        # Check if the API key exists in the config file
        if "fred_token" in config:
            config["fred_token"] = None

            with open(CONFIG_PATH, "w") as config_file:
                json.dump(config, config_file)

            click.echo("Success: FRED API key removed.")
        else:
            click.echo("Info: No FRED API key found.")

    else:
        click.echo("Error: No configuration found.")


if __name__ == "__main__":
    cli()
