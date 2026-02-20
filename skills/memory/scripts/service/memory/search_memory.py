#!/usr/bin/env python3
"""
Agent 搜索工具：在 SQLite 索引中检索历史记忆。

使用场景：由 memory-rules 或 SKILL 引导 Agent 在需要时调用，支持 hybrid/FTS/vector
三种检索方式。依赖 sync_index.py 预先构建的 index.sqlite。
"""
import sys
import os
import json
import time
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))

from service.config import get_memory_dir
from service.config import INDEX_DB
from storage.sqlite_store import SQLiteStore
from service.logger import get_logger

log = get_logger("search")


def main():
    """
    根据 query 在 index.sqlite 中搜索，输出 JSON 格式结果。

    参数：query(必填)、--max-results、--method(hybrid/fts/vector)、--project-path
    退出码：0=有结果，1=无结果，2=索引不存在
    """
    parser = argparse.ArgumentParser(description="Search memory")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--max-results", type=int, default=10)
    parser.add_argument("--method", choices=["hybrid", "fts", "vector"], default="hybrid")
    parser.add_argument("--days", type=int, help="限制搜索最近 N 天的记忆")
    parser.add_argument("--from", dest="from_date", help="起始日期 YYYY-MM-DD")
    parser.add_argument("--to", help="结束日期 YYYY-MM-DD")
    parser.add_argument("--project-path", default=os.getcwd())
    args = parser.parse_args()

    from service.logger import redirect_to_project
    redirect_to_project(args.project_path)

    memory_dir = get_memory_dir(args.project_path)
    db_path = os.path.join(memory_dir, INDEX_DB)

    if not os.path.exists(db_path):
        log.warning("索引文件不存在: %s", db_path)
        print(json.dumps({"results": [], "method": args.method, "total": 0,
                          "error": "Index not found. Run sync_index.py first."}))
        sys.exit(2)

    store = SQLiteStore(db_path)
    t0 = time.time()

    # hybrid/vector 需要嵌入向量，若模型不可用则回退到 FTS
    query_embedding = None
    actual_method = args.method

    if args.method in ("hybrid", "vector"):
        try:
            from core.embedding import embed_text, is_available
            if is_available():
                query_embedding = embed_text(args.query)
                log.info("使用嵌入模型生成查询向量")
            elif args.method == "vector":
                log.warning("嵌入模型不可用，回退到 FTS 搜索")
                actual_method = "fts"
        except Exception as e:
            log.warning("嵌入模型加载异常: %s，回退到 FTS", e)
            if args.method == "vector":
                actual_method = "fts"

    time_kwargs = dict(days=args.days, from_date=args.from_date, to_date=args.to)

    if actual_method == "fts":
        results = store.search_fts(args.query, limit=args.max_results, **time_kwargs)
        for r in results:
            r["score"] = round(abs(r.get("rank", 0)), 4)
            r.pop("rank", None)
    elif actual_method == "vector" and query_embedding:
        results = store.search_vector(query_embedding, limit=args.max_results, **time_kwargs)
    else:
        results = store.hybrid_search(args.query, query_embedding, limit=args.max_results, **time_kwargs)

    store.close()
    elapsed = time.time() - t0

    log.info("搜索完成 method=%s query='%s' results=%d (耗时 %.3fs)",
             actual_method, args.query[:50], len(results), elapsed)

    output = {
        "results": results,
        "method": actual_method,
        "total": len(results),
    }
    print(json.dumps(output, ensure_ascii=False))
    sys.exit(0 if results else 1)


if __name__ == "__main__":
    main()
