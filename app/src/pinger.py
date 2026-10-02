import logging
import os
import time
import json
import sys
import psycopg

DEFAULT_TIMEOUT = 300


def build_logger(log_file: str | None) -> logging.Logger:
    logger = logging.getLogger("pinger")
    logger.setLevel(logging.DEBUG)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(lambda r: r.levelno <= logging.WARNING)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.addFilter(lambda r: r.levelno > logging.WARNING)
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    if log_file:
        try:
            fmt = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(fmt)
            logger.addHandler(file_handler)
            logger.debug("File logging enabled → %s", log_file)
        except OSError as exc:
            logger.error("Cannot open log file %s: %s", log_file, exc)

    return logger


def db_connect(config: dict):
    return psycopg.connect(
        host=config.get("host", "127.0.0.1"),
        port=int(config.get("port", 5432)),
        dbname=config.get("dbname", "postgres"),
        user=os.environ.get("PG_USER"),
        password=os.environ.get("PG_PASSWORD"),
        connect_timeout=int(config.get("connect_timeout", DEFAULT_TIMEOUT)),
    )


def ping(conn_params: dict, logger: logging.Logger) -> None:
    try:
        with db_connect(conn_params).cursor() as cur:
            cur.execute("SELECT VERSION();")
            row = cur.fetchone()

        if row is None:
            logger.error("Empty response from SELECT VERSION()")
            return

        version_str: str = row[0]

        if version_str.startswith("PostgreSQL"):
            logger.info("OK | %s", version_str)
        else:
            logger.warning("WARNING | UNEXPECTED VERSION STRING | %s", version_str)

    except psycopg.OperationalError as exc:
        logger.error("ERROR | Connection failed: %s", exc)
    except psycopg.Error as exc:
        logger.error("ERROR | Database error: %s", exc)
    except Exception as exc:
        logger.error("ERROR | Unexpected error: %s", exc)


def pinger(conn_params: dict) -> None:
    log_file = os.environ.get("LOG_FILE", "logs/file.txt")

    try:
        interval_seconds = int(os.environ.get("PING_INTERVAL", DEFAULT_TIMEOUT))
    except ValueError:
        interval_seconds = 3

    logger = build_logger(log_file)

    logger.info(
        "Pinger starting | interval=%ds | log_file=%s",
        interval_seconds,
        log_file or "—",
    )

    logger.debug(
        "Connection params (no password): host=%s port=%s dbname=%s user=%s timeout=%s",
        conn_params.get("host"),
        conn_params.get("port"),
        conn_params.get("dbname"),
        conn_params.get("user"),
        conn_params.get("connect_timeout"),
    )

    while True:
        ping(conn_params, logger)
        logger.debug("Sleeping %d seconds until next ping …", interval_seconds)
        time.sleep(interval_seconds)



if __name__ == "__main__":
    try:
        with open('config.json') as file:
            config = json.load(file)
        pinger(config)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
