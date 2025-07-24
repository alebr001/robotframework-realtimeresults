import inspect
import sqlite3
import aiosqlite
import psycopg2
import asyncpg
from shared.helpers.config_loader import load_config
import shared.helpers.sql_definitions as sql_definitions

def get_create_statements():
    """
    Extracts all SQL CREATE statements from the sql_definitions module.
    This function assumes that all CREATE statements are defined as string constants
    and prefixed with 'CREATE_'.
    """
    return [
        value for name, value in inspect.getmembers(sql_definitions)
        if name.startswith("CREATE_") and isinstance(value, str)
    ]

def ensure_schema(database_url):
    if database_url.startswith("postgresql://"):
        conn = psycopg2.connect(database_url)
        try:
            with conn:
                with conn.cursor() as cursor:
                    for statement in get_create_statements():
                        cursor.execute(statement)
        finally:
            conn.close()
    else:
        with sqlite3.connect(database_url.replace("sqlite:///", "")) as conn:
            cursor = conn.cursor()
            for statement in get_create_statements():
                cursor.execute(statement)
            conn.commit()

async def async_ensure_schema(database_url):
    if database_url.startswith("postgresql://"):
        conn = await asyncpg.connect(database_url)
        try:
            for statement in get_create_statements():
                await conn.execute(statement)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(database_url) as db:
            for statement in get_create_statements():
                await db.execute(statement)
            await db.commit()
