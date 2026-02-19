"""
时间日期工具函数

所有时间统一使用 UTC，避免时区混乱。
"""
from datetime import datetime, timezone, timedelta
import random
import string


def utcnow() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)


def iso_now() -> str:
    """当前 UTC 时间的 ISO 8601 字符串，格式如 2026-02-18T14:30:00Z"""
    return utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def today_str() -> str:
    """当前 UTC 日期字符串，格式如 2026-02-18"""
    return utcnow().strftime("%Y-%m-%d")


def ts_id() -> str:
    """基于当前时间生成短 ID，格式如 143005123-a7x2（时分秒毫秒+随机后缀），保证高频调用唯一性"""
    now = utcnow()
    ms = now.strftime("%H%M%S") + f"{now.microsecond // 1000:03d}"
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
    return f"{ms}-{suffix}"


def date_range(days: int) -> list:
    """返回从今天往前 N 天的日期字符串列表（含今天），用于衰减加载"""
    now = utcnow()
    return [(now - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]


def parse_iso(ts: str) -> datetime:
    """解析 ISO 时间字符串为 datetime 对象，解析失败返回最小时间"""
    ts = ts.rstrip("Z")
    try:
        return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
