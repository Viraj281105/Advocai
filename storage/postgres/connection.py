# storage/postgres/connection.py

import os
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class PostgresConnection:
    """
    Centralized PostgreSQL connection pool for AdvocAI.
    Uses psycopg2 SimpleConnectionPool for safe, reusable DB connections.
    """

    _pool = None

    @staticmethod
    def initialize():
        """Initializes the global DB connection pool."""
        if PostgresConnection._pool is None:
            try:
                PostgresConnection._pool = SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    host=os.getenv("DB_HOST", "localhost"),
                    port=os.getenv("DB_PORT", "5432"),
                    database=os.getenv("DB_NAME"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    connect_timeout=5
                )
                print("✅ PostgreSQL connection pool initialized.")
            except Exception as e:
                raise RuntimeError(f"❌ Failed to initialize PostgreSQL pool: {e}")

    @staticmethod
    def get_connection():
        """Returns a usable DB connection from the pool."""
        if PostgresConnection._pool is None:
            PostgresConnection.initialize()
        try:
            return PostgresConnection._pool.getconn()
        except Exception as e:
            raise RuntimeError(f"❌ Could not get DB connection: {e}")

    @staticmethod
    def return_connection(conn):
        """Returns a used connection back to the pool."""
        try:
            PostgresConnection._pool.putconn(conn)
        except Exception as e:
            print(f"⚠️ Failed to return connection to pool: {e}")

    @staticmethod
    def close_all():
        """Closes all connections in the pool."""
        if PostgresConnection._pool:
            PostgresConnection._pool.closeall()
            print("🔒 All PostgreSQL connections closed.")
