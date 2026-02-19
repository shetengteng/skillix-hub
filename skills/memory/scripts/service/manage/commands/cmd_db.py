"""db 子命令组：查看 SQLite 索引数据库内容"""
import sys
import os
import json
import subprocess
import webbrowser

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../.."))

from service.config import get_config, INDEX_DB
from ._helpers import _json_out


def _get_db_path(project_path):
    cfg = get_config(project_path)
    data_dir = cfg.get("paths.data_dir")
    return os.path.join(project_path, data_dir, INDEX_DB)


def _connect(db_path):
    import sqlite3
    if not os.path.isfile(db_path):
        return None, f"数据库文件不存在: {db_path}"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn, None


def cmd_db_tables(args):
    db_path = _get_db_path(args.project_path)
    conn, err = _connect(db_path)
    if err:
        _json_out("error", "db tables", error={"code": "DB_NOT_FOUND", "message": err})
        sys.exit(2)

    cur = conn.execute("SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name")
    tables = []
    for row in cur.fetchall():
        name = row["name"]
        if name.startswith("sqlite_") or name.endswith("_config") or name.endswith("_docsize") or name.endswith("_data") or name.endswith("_idx") or name.endswith("_content"):
            continue
        count_cur = conn.execute(f"SELECT COUNT(*) as cnt FROM [{name}]")
        tables.append({"name": name, "type": row["type"], "rows": count_cur.fetchone()["cnt"]})

    conn.close()
    _json_out("ok", "db tables", {"db_path": db_path, "tables": tables})


def cmd_db_schema(args):
    db_path = _get_db_path(args.project_path)
    conn, err = _connect(db_path)
    if err:
        _json_out("error", "db schema", error={"code": "DB_NOT_FOUND", "message": err})
        sys.exit(2)

    table = args.table
    cur = conn.execute(f"PRAGMA table_info([{table}])")
    columns = [{"name": r["name"], "type": r["type"], "notnull": bool(r["notnull"]), "pk": bool(r["pk"])} for r in cur.fetchall()]

    if not columns:
        conn.close()
        _json_out("error", "db schema", error={"code": "TABLE_NOT_FOUND", "message": f"表不存在: {table}"})
        sys.exit(2)

    conn.close()
    _json_out("ok", "db schema", {"table": table, "columns": columns})


def cmd_db_show(args):
    db_path = _get_db_path(args.project_path)
    conn, err = _connect(db_path)
    if err:
        _json_out("error", "db show", error={"code": "DB_NOT_FOUND", "message": err})
        sys.exit(2)

    table = args.table
    limit = args.limit or 20
    offset = args.offset or 0

    count_cur = conn.execute(f"SELECT COUNT(*) as cnt FROM [{table}]")
    total = count_cur.fetchone()["cnt"]

    order_clause = ""
    if table == "chunks":
        order_clause = "ORDER BY timestamp DESC"
    elif table == "sync_state":
        order_clause = "ORDER BY synced_at DESC"

    cur = conn.execute(f"SELECT * FROM [{table}] {order_clause} LIMIT ? OFFSET ?", (limit, offset))
    rows = []
    for row in cur.fetchall():
        d = dict(row)
        if "embedding" in d:
            emb = d["embedding"]
            d["embedding"] = f"<blob {len(emb)} bytes>" if emb else None
        rows.append(d)

    conn.close()
    _json_out("ok", "db show", {"table": table, "total": total, "offset": offset, "limit": limit, "rows": rows})


def cmd_db_query(args):
    db_path = _get_db_path(args.project_path)
    conn, err = _connect(db_path)
    if err:
        _json_out("error", "db query", error={"code": "DB_NOT_FOUND", "message": err})
        sys.exit(2)

    sql = args.sql.strip()
    sql_upper = sql.upper()
    if not sql_upper.startswith("SELECT") and not sql_upper.startswith("PRAGMA"):
        conn.close()
        _json_out("error", "db query", error={"code": "READONLY", "message": "仅支持 SELECT 和 PRAGMA 查询"})
        sys.exit(2)

    try:
        cur = conn.execute(sql)
        rows = []
        for row in cur.fetchall():
            d = dict(row)
            for k, v in d.items():
                if isinstance(v, bytes):
                    d[k] = f"<blob {len(v)} bytes>"
            rows.append(d)
        conn.close()
        _json_out("ok", "db query", {"sql": sql, "count": len(rows), "rows": rows})
    except Exception as e:
        conn.close()
        _json_out("error", "db query", error={"code": "SQL_ERROR", "message": str(e)})
        sys.exit(2)


def cmd_db_stats(args):
    db_path = _get_db_path(args.project_path)
    conn, err = _connect(db_path)
    if err:
        _json_out("error", "db stats", error={"code": "DB_NOT_FOUND", "message": err})
        sys.exit(2)

    total = conn.execute("SELECT COUNT(*) as cnt FROM chunks").fetchone()["cnt"]
    with_emb = conn.execute("SELECT COUNT(*) as cnt FROM chunks WHERE embedding IS NOT NULL").fetchone()["cnt"]

    type_cur = conn.execute("SELECT type, COUNT(*) as cnt FROM chunks GROUP BY type")
    by_type = {r["type"]: r["cnt"] for r in type_cur.fetchall()}

    mtype_cur = conn.execute("SELECT memory_type, COUNT(*) as cnt FROM chunks WHERE memory_type IS NOT NULL GROUP BY memory_type")
    by_memory_type = {r["memory_type"]: r["cnt"] for r in mtype_cur.fetchall()}

    sync_count = conn.execute("SELECT COUNT(*) as cnt FROM sync_state").fetchone()["cnt"]

    meta_cur = conn.execute("SELECT key, value FROM meta")
    meta = {r["key"]: r["value"] for r in meta_cur.fetchall()}

    file_size = os.path.getsize(db_path) if os.path.isfile(db_path) else 0

    conn.close()
    _json_out("ok", "db stats", {
        "db_path": db_path,
        "file_size_kb": round(file_size / 1024, 1),
        "total_chunks": total,
        "with_embedding": with_emb,
        "by_type": by_type,
        "by_memory_type": by_memory_type,
        "synced_files": sync_count,
        "meta": meta,
    })


def cmd_db_browse(args):
    """启动 datasette Web 界面浏览 SQLite 数据库"""
    db_path = _get_db_path(args.project_path)
    if not os.path.isfile(db_path):
        _json_out("error", "db browse", error={"code": "DB_NOT_FOUND", "message": f"数据库文件不存在: {db_path}"})
        sys.exit(2)

    port = args.port or 8685

    try:
        subprocess.run([sys.executable, "-m", "datasette", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        _json_out("error", "db browse", error={
            "code": "DATASETTE_NOT_FOUND",
            "message": "datasette 未安装，请先执行: pip install datasette"
        })
        sys.exit(2)

    url = f"http://localhost:{port}"
    _json_out("ok", "db browse", {"db_path": db_path, "url": url, "message": f"正在启动 datasette，浏览器将打开 {url}"})
    sys.stdout.flush()

    webbrowser.open(url)
    try:
        subprocess.run(
            [sys.executable, "-m", "datasette", db_path, "--port", str(port), "--open"],
            check=False,
        )
    except KeyboardInterrupt:
        pass
