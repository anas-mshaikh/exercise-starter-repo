def test_get_db_reads_database_path_env_var_each_call(tmp_path, monkeypatch):
    from app import database

    db1 = tmp_path / "db1.db"
    db2 = tmp_path / "db2.db"

    monkeypatch.setenv("DATABASE_PATH", str(db1))
    conn1 = database.get_db()
    try:
        conn1.execute("CREATE TABLE marker (id INTEGER)")
        conn1.commit()
    finally:
        conn1.close()

    monkeypatch.setenv("DATABASE_PATH", str(db2))
    conn2 = database.get_db()
    try:
        rows = conn2.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='marker'"
        ).fetchall()
        assert rows == []
    finally:
        conn2.close()
