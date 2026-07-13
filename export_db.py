"""
Phase 12.2 — Database export script

Exports your local MySQL database to a SQL dump file
that can be imported into Railway MySQL cloud database.

Usage:
  cd cricketiq-ai
  python export_db.py

Output: cricketiq_export.sql (in project root)
"""

import subprocess
import sys
import os
from datetime import datetime


def export_database():

    # Read from .env
    from dotenv import dotenv_values
    env = dotenv_values("backend/.env")

    user     = env.get("MYSQL_USER", "root")
    password = env.get("MYSQL_PASSWORD", "")
    host     = env.get("MYSQL_HOST", "localhost")
    port     = env.get("MYSQL_PORT", "3306")
    database = env.get("MYSQL_DATABASE", "cricketiq")

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"cricketiq_export_{timestamp}.sql"

    print(f"Exporting database '{database}' to {output_file}...")

    cmd = [
        "mysqldump",
        f"--user={user}",
        f"--password={password}",
        f"--host={host}",
        f"--port={port}",
        "--single-transaction",
        "--routines",
        "--triggers",
        "--no-tablespaces",
        database
    ]

    try:
        with open(output_file, "w") as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False

        size_mb = os.path.getsize(output_file) / (1024 * 1024)
        print(f"Export complete: {output_file} ({size_mb:.1f} MB)")
        print(f"\nNext step: Import this file into Railway MySQL")
        return True

    except FileNotFoundError:
        print("mysqldump not found. Make sure MySQL client tools are installed.")
        print("Download: https://dev.mysql.com/downloads/mysql/")
        return False


if __name__ == "__main__":
    success = export_database()
    sys.exit(0 if success else 1)