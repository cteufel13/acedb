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
        click.echo("Connection successful!")
    except Exception as e:
        click.echo(f"Connection failed: {e}")
        return

    # Ensure the config directory exists
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Save the configuration to a file
    with open(CONFIG_PATH, "w") as config_file:
        json.dump(config, config_file)


@cli.command()
def logout():
    """Logout from the database."""
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
        click.echo("Logged out successfully.")
    else:
        click.echo("No active session found.")


@cli.command()
def check_connection():
    """Check the database connection"""
    if not CONFIG_PATH.exists():
        click.echo("No configuration found. Please login first.")
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
        click.echo("Connection successful!")
    except Exception as e:
        click.echo(f"Connection failed: {e}")


@cli.command()
def login_status():
    """Check if the user is logged in."""
    if CONFIG_PATH.exists():
        click.echo("You are logged in.")
    else:
        click.echo("You are not logged in.")


@cli.command()
def list_config():
    """List the current configuration."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as config_file:
            config = json.load(config_file)
        click.echo(json.dumps(config, indent=4))
    else:
        click.echo("No configuration found.")


@cli.command()
def db_login():
    """Adds the Databento API key to env variables file"""

    db_token = click.prompt("Enter your Databento API key")
    db_token = db_token.strip()

    if not db_token:
        click.echo("Databento API key cannot be empty.")
        return

    os.environ["DATABENTO_API_KEY"] = db_token
    click.echo("Databento API key added to environment variables.")


@cli.command()
def db_logout():
    """Removes the Databento API key from env variables file"""

    if "DATABENTO_API_KEY" in os.environ:
        del os.environ["DATABENTO_API_KEY"]
        click.echo("Databento API key removed from environment variables.")
    else:
        click.echo("No Databento API key found in environment variables.")


if __name__ == "__main__":
    cli()
