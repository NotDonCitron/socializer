import sqlite3
import sys
from rich.console import Console
from rich.table import Table
import argparse

def inspect_db(db_path, query=None, list_tables=False):
    console = Console()
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        if list_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            console.print(f"[bold green]Tables in {db_path}:[/bold green]")
            for table in tables:
                console.print(f" - {table[0]}")
            return

        if not query:
            console.print("[red]No query provided.[/red]")
            return

        cursor.execute(query)
        rows = cursor.fetchall()
        colnames = [description[0] for description in cursor.description]

        table = Table(title=f"Query Results: {query}")
        for col in colnames:
            table.add_column(col)

        for row in rows:
            table.add_row(*[str(item) for item in row])

        console.print(table)
        conn.close()
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect SQLite databases.")
    parser.add_argument("db_path", help="Path to the SQLite database file")
    parser.add_argument("-q", "--query", help="SQL query to execute")
    parser.add_argument("-l", "--list-tables", action="store_true", help="List all tables in the database")
    
    args = parser.parse_args()
    inspect_db(args.db_path, args.query, args.list_tables)
