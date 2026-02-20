"""
SQLite 存储引擎

提供 chunk 存储、FTS5 全文搜索、向量搜索和混合搜索功能。
使用 struct 模块将浮点向量序列化为二进制 BLOB 存储。
"""
import sqlite3
import struct
import os


SCHEMA_VERSION = "1"

# 数据库初始化 SQL：创建核心表、FTS 虚拟表和同步触发器
_INIT_SQL = """
-- chunks: 存储文本块及其元数据和嵌入向量
CREATE TABLE IF NOT EXISTS chunks (
    id TEXT PRIMARY KEY,          -- 唯一标识，如 log-143005 或 core-0
    content TEXT NOT NULL,        -- 文本内容
    type TEXT,                    -- 类型：fact / core / summary
    memory_type TEXT,             -- 记忆分类：W=客观事实 / B=经历 / O=偏好
    entities TEXT,                -- 关联实体，JSON 数组字符串
    confidence REAL DEFAULT 0.8,  -- 置信度 0.0~1.0
    source_file TEXT,             -- 来源文件路径
    source_id TEXT,               -- 来源条目 ID
    timestamp TEXT,               -- 原始时间戳
    embedding BLOB                -- 嵌入向量（float32 数组的二进制表示）
);

-- chunks_fts: FTS5 全文搜索虚拟表，自动同步 chunks 表内容
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    content,
    entities,
    type,
    content='chunks',
    content_rowid='rowid'
);

-- 触发器：chunks 表增删改时自动同步 FTS 索引
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, content, entities, type)
    VALUES (new.rowid, new.content, new.entities, new.type);
END;

CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, entities, type)
    VALUES ('delete', old.rowid, old.content, old.entities, old.type);
END;

CREATE TRIGGER IF NOT EXISTS chunks_au AFTER UPDATE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, content, entities, type)
    VALUES ('delete', old.rowid, old.content, old.entities, old.type);
    INSERT INTO chunks_fts(rowid, content, entities, type)
    VALUES (new.rowid, new.content, new.entities, new.type);
END;

-- meta: 存储元数据键值对（schema 版本、上次同步时间等）
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- sync_state: 记录每个文件的同步进度，支持增量同步
CREATE TABLE IF NOT EXISTS sync_state (
    file_path TEXT PRIMARY KEY,   -- 被同步的文件相对路径
    last_line INTEGER DEFAULT 0,  -- 上次同步到第几行
    last_id TEXT,                 -- 上次同步的最后一条 ID
    mtime INTEGER,                -- 文件修改时间戳（秒）
    synced_at INTEGER             -- 同步执行时间戳（秒）
);
"""


def serialize_embedding(vec):
    """将浮点向量序列化为二进制 BLOB（每个 float32 占 4 字节）"""
    return struct.pack(f"{len(vec)}f", *vec)


class SQLiteStore:
    """SQLite 存储操作封装"""

    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 查询结果以字典形式返回
        self._init_schema()

    def _init_schema(self):
        """执行建表 SQL，并记录 schema 版本"""
        self.conn.executescript(_INIT_SQL)
        cur = self.conn.execute("SELECT value FROM meta WHERE key='schema_version'")
        row = cur.fetchone()
        if not row:
            self.conn.execute(
                "INSERT INTO meta(key,value) VALUES('schema_version',?)",
                (SCHEMA_VERSION,),
            )
            self.conn.commit()

    def upsert_chunk(self, chunk_id, content, chunk_type=None,
                     memory_type=None, entities=None, confidence=0.8,
                     source_file=None, source_id=None, timestamp=None,
                     embedding=None):
        """插入或更新一个文本块（INSERT OR REPLACE）"""
        emb_blob = serialize_embedding(embedding) if embedding else None
        self.conn.execute("""
            INSERT OR REPLACE INTO chunks
            (id, content, type, memory_type, entities, confidence,
             source_file, source_id, timestamp, embedding)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (chunk_id, content, chunk_type, memory_type, entities,
              confidence, source_file, source_id, timestamp, emb_blob))
        self.conn.commit()

    def search_fts(self, query, limit=10, **kwargs):
        from storage.sqlite_search import search_fts as _search_fts
        return _search_fts(self, query, limit, **kwargs)

    def search_vector(self, query_embedding, limit=10, **kwargs):
        from storage.sqlite_search import search_vector as _search_vector
        return _search_vector(self, query_embedding, limit, **kwargs)

    def hybrid_search(self, query, query_embedding=None, limit=10, **kwargs):
        from storage.sqlite_search import hybrid_search as _hybrid_search
        return _hybrid_search(self, query, query_embedding, limit, **kwargs)

    def get_sync_state(self, file_path):
        """获取某文件的同步状态"""
        cur = self.conn.execute(
            "SELECT * FROM sync_state WHERE file_path=?", (file_path,)
        )
        row = cur.fetchone()
        return dict(row) if row else None

    def update_sync_state(self, file_path, last_line, last_id, mtime):
        """更新某文件的同步状态"""
        import time
        self.conn.execute("""
            INSERT OR REPLACE INTO sync_state(file_path, last_line, last_id, mtime, synced_at)
            VALUES (?, ?, ?, ?, ?)
        """, (file_path, last_line, last_id, mtime, int(time.time())))
        self.conn.commit()

    def set_meta(self, key, value):
        """设置元数据键值对"""
        self.conn.execute(
            "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)", (key, str(value))
        )
        self.conn.commit()

    def get_meta(self, key):
        """获取元数据值"""
        cur = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,))
        row = cur.fetchone()
        return row["value"] if row else None

    def count_chunks(self):
        """统计 chunk 总数"""
        cur = self.conn.execute("SELECT COUNT(*) as cnt FROM chunks")
        return cur.fetchone()["cnt"]

    def close(self):
        """关闭数据库连接"""
        self.conn.close()
