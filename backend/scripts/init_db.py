import os

import pymssql

conn = pymssql.connect(
    server=os.getenv("DB_SERVER"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database="master",
    autocommit=True,
)

db_name = os.getenv("DB_NAME")
cursor = conn.cursor()
cursor.execute(
    f"IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = '{db_name}') "
    f"CREATE DATABASE [{db_name}]"
)
conn.close()
