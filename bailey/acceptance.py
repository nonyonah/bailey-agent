"""Read-only native SQLite check; never create an empty database by accident."""
import os
from pathlib import Path
import sqlite3


def check_database(path):
    if not path.is_file():
        raise ValueError("Native state.db does not exist; complete a real conversation first")
    with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Native session database integrity failed")
        if db.execute("PRAGMA journal_mode").fetchone()[0].lower() != "wal":
            raise ValueError("Native session database is not using WAL")
    return True


if __name__ == "__main__":
    check_database(Path(os.environ["HERMES_HOME"]) / "state.db")
    print("Native session database integrity and WAL verified")
