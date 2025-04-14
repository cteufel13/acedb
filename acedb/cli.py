import click
from pathlib import Path
from getpass import getpass
import json
import psycopg2

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


if __name__ == "__main__":
    cli()
