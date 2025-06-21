import inspect
import sqlite3
import aiosqlite
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

def ensure_schema(database_path):
    with sqlite3.connect(database_path) as conn:
        cursor = conn.cursor()
        for statement in get_create_statements():
            cursor.execute(statement)
        conn.commit()

async def async_ensure_schema(database_path):
    async with aiosqlite.connect(database_path) as db:
        for statement in get_create_statements():
            await db.execute(statement)
        await db.commit()