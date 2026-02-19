"""
SQLite 搜索功能：FTS5 全文搜索、向量相似度搜索、混合搜索（RRF 融合）。

接受 SQLiteStore 实例，使用其 conn 执行查询。
"""
import sqlite3
import struct
import math


def deserialize_embedding(blob):
    """将二进制 BLOB 反序列化为浮点元组"""
    n = len(blob) // 4
    return struct.unpack(f"{n}f", blob)


def cosine_similarity(a, b):
    """计算两个向量的余弦相似度，范围 [-1, 1]"""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def search_fts(store, query, limit=10):
    """FTS5 全文搜索，按 BM25 相关性排序"""
    try:
        cur = store.conn.execute("""
            SELECT c.id, c.content, c.type, c.memory_type, c.entities,
                   c.confidence, c.source_file, c.timestamp,
                   bm25(chunks_fts) as rank
            FROM chunks_fts f
            JOIN chunks c ON c.rowid = f.rowid
            WHERE chunks_fts MATCH ?
            ORDER BY rank
            LIMIT ?
        """, (query, limit))
        return [dict(r) for r in cur.fetchall()]
    except sqlite3.OperationalError:
        return []


def search_vector(store, query_embedding, limit=10):
    """向量相似度搜索：遍历所有有嵌入的 chunk，计算余弦相似度"""
    cur = store.conn.execute(
        "SELECT id, content, type, memory_type, entities, confidence, "
        "source_file, timestamp, embedding FROM chunks WHERE embedding IS NOT NULL"
    )
    scored = []
    for row in cur.fetchall():
        row_dict = dict(row)
        emb = deserialize_embedding(row_dict.pop("embedding"))
        score = cosine_similarity(query_embedding, emb)
        row_dict["score"] = score
        scored.append(row_dict)
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


def hybrid_search(store, query, query_embedding=None, limit=10):
    """
    混合搜索：结合 FTS5 和向量搜索，使用 RRF(Reciprocal Rank Fusion) 融合排名

    RRF 公式：score(d) = Σ 1/(k + rank_i(d))，k=60
    """
    fts_results = search_fts(store, query, limit=limit * 2)

    # 收集 FTS 排名
    fts_ranks = {}
    for i, r in enumerate(fts_results):
        fts_ranks[r["id"]] = i + 1

    # 收集向量搜索排名
    vec_ranks = {}
    vec_results = []
    if query_embedding:
        vec_results = search_vector(store, query_embedding, limit=limit * 2)
        for i, r in enumerate(vec_results):
            vec_ranks[r["id"]] = i + 1

    # RRF 融合
    all_ids = set(fts_ranks.keys()) | set(vec_ranks.keys())
    k = 60  # RRF 常数，值越大越平滑
    rrf_scores = {}
    item_map = {}
    for r in fts_results:
        item_map[r["id"]] = r
    if query_embedding:
        for r in vec_results:
            if r["id"] not in item_map:
                item_map[r["id"]] = r

    for doc_id in all_ids:
        score = 0
        if doc_id in fts_ranks:
            score += 1.0 / (k + fts_ranks[doc_id])
        if doc_id in vec_ranks:
            score += 1.0 / (k + vec_ranks[doc_id])
        rrf_scores[doc_id] = score

    sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)
    results = []
    for doc_id in sorted_ids[:limit]:
        item = dict(item_map[doc_id])
        item["score"] = round(rrf_scores[doc_id], 4)
        item.pop("rank", None)
        results.append(item)
    return results
