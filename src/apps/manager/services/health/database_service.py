import time

from django.db import connections
from django.db.utils import OperationalError


class DatabaseService:

    @staticmethod
    def _get_connection():
        return connections["default"]

    @staticmethod
    def _get_latency():
        conn = DatabaseService._get_connection()
        start = time.perf_counter()

        with conn.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        end = time.perf_counter()
        latency = round((end - start) * 1000, 2)
        return latency

    @staticmethod
    def _get_connections_count():
        conn = DatabaseService._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_stat_activity;")
            total = cursor.fetchone()[0]
        return total

    @staticmethod
    def _get_db_size():
        conn = DatabaseService._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT pg_database_size(current_database());")
            size_bytes = cursor.fetchone()[0]

        size_mb = round(size_bytes / 1024 / 1024, 2)
        return size_mb

    @staticmethod
    def _get_active_transactions():
        conn = DatabaseService._get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT count(*) 
                FROM pg_stat_activity
                WHERE state = 'active';
            """)
            active = cursor.fetchone()[0]
        return active

    @staticmethod
    def get_status() -> dict:
        data = {
            "online": False,
            "latency_ms": None,
            "connections": None,
            "db_size_mb": None,
            "active_transactions": None,
        }

        try:
            data["latency_ms"] = DatabaseService._get_latency()
            data["connections"] = DatabaseService._get_connections_count()
            data["db_size_mb"] = DatabaseService._get_db_size()
            data["active_transactions"] = DatabaseService._get_active_transactions()

            data["online"] = True

        except OperationalError as e:
            return e

        return data
