import getpass
import json
import sys
import psycopg


def db_connect(conn_params: dict):
    return psycopg.connect(
        host=conn_params.get("host", "127.0.0.1"),
        port=int(conn_params.get("port", 5432)),
        dbname=conn_params.get("dbname", "postgres"),
        user=conn_params.get("user"),
        password=conn_params.get("password"),
    )


def version(conn_params: dict):
    with db_connect(conn_params).cursor() as cursor:
        cursor.execute("SELECT VERSION();")
        print(cursor.fetchone()[0])


if __name__ == "__main__":
    try:
        with open('../config.json') as file:
            config = json.load(file)
        config["user"] = input("Username: ")
        config["password"] = getpass.getpass("Password: ")
        version(config)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
