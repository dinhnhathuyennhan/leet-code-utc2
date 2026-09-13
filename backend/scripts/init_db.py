import os

import psycopg
from psycopg import sql

conn = psycopg.connect(
    host=os.getenv("DB_SERVER"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    dbname="postgres",
    autocommit=True,
)

db_name = os.getenv("DB_NAME")
cursor = conn.cursor()
cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
if cursor.fetchone() is None:
    cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
conn.close()
