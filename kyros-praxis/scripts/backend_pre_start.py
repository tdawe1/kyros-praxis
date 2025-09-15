#!/usr/bin/env python3
"""
Wait for the database to be ready before starting services.
"""
import logging
import os
import sys
import time
from typing import Any

import psycopg2
from psycopg2 import OperationalError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment
max_tries = 60 * 5  # 5 minutes
wait_seconds = 1

def get_db_config() -> dict[str, Any]:
    """Get database configuration from environment variables."""
    return {
        "host": os.getenv("POSTGRES_SERVER", os.getenv("DB_HOST", "localhost")),
        "port": int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", 5432))),
        "database": os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "kyros")),
        "user": os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres")),
        "password": os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "password")),
    }

def wait_for_db() -> None:
    """Wait for the database to be ready."""
    config = get_db_config()
    logger.info(f"Waiting for database at {config['host']}:{config['port']}")
    
    for attempt in range(max_tries):
        try:
            conn = psycopg2.connect(**config)
            conn.close()
            logger.info("Database is ready!")
            return
        except OperationalError as e:
            if attempt % 10 == 0:  # Log every 10 attempts
                logger.info(f"Database not ready yet (attempt {attempt}/{max_tries}): {e}")
            time.sleep(wait_seconds)
    
    logger.error(f"Database not ready after {max_tries} attempts")
    sys.exit(1)

def main() -> None:
    """Main function."""
    logger.info("Initializing service - waiting for database")
    wait_for_db()
    logger.info("Service finished initializing")

if __name__ == "__main__":
    main()