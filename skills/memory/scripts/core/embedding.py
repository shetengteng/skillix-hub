"""
嵌入模型加载与向量生成

使用 sentence-transformers 库加载本地嵌入模型，生成文本的向量表示。
模型采用全局单例模式，首次加载后缓存复用。
依赖为可选：如果 sentence-transformers 未安装，所有函数安全降级。
"""
import os
import time
from service.config import _DEFAULTS
from service.logger import get_logger

log = get_logger("embedding")

_EMB_MODEL = _DEFAULTS["embedding"]["model"]
_MODEL_CACHE = os.path.expanduser(_DEFAULTS["embedding"]["cache_dir"])

_model = None
_model_name = None


def _load_model(model_name=None):
    """
    加载嵌入模型（单例）

    加载优先级：
    1. 如果已加载且模型名一致，直接返回缓存
    2. 检查 ~/.memory-skill/models/ 下是否有本地缓存
    3. 缓存不存在则从 HuggingFace 下载
    """
    global _model, _model_name
    name = model_name or _EMB_MODEL
    if _model is not None and _model_name == name:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        # sentence-transformers 使用 "models--BAAI--bge-small-zh-v1.5" 格式缓存
        cache_dir_name = "models--" + name.replace("/", "--")
        local_path = os.path.join(_MODEL_CACHE, cache_dir_name)
        t0 = time.time()
        os.makedirs(_MODEL_CACHE, exist_ok=True)
        if os.path.isdir(local_path):
            log.info("从本地缓存加载模型 %s", local_path)
        else:
            log.info("本地缓存未命中，首次下载 %s 到 %s", name, _MODEL_CACHE)
        _model = SentenceTransformer(name, cache_folder=_MODEL_CACHE)
        elapsed = time.time() - t0
        dim = _model.get_sentence_embedding_dimension()
        log.info("模型加载完成 dim=%d (耗时 %.1fs)", dim, elapsed)
        _model_name = name
        return _model
    except ImportError:
        log.warning("sentence-transformers 未安装，嵌入功能不可用")
        return None
    except Exception as e:
        log.error("模型加载失败: %s", e)
        return None


def is_available(model_name=None):
    """检查嵌入模型是否可用（会触发加载）"""
    return _load_model(model_name) is not None


def embed_text(text, model_name=None):
    """将单条文本转换为归一化向量，返回 list[float] 或 None"""
    model = _load_model(model_name)
    if model is None:
        return None
    t0 = time.time()
    vec = model.encode(text, normalize_embeddings=True)
    elapsed = time.time() - t0
    log.debug("生成向量 dim=%d, 文本长度=%d (耗时 %.3fs)", len(vec), len(text), elapsed)
    return vec.tolist()


def embed_batch(texts, model_name=None):
    """批量将文本转换为向量，batch_size=32"""
    model = _load_model(model_name)
    if model is None:
        return None
    t0 = time.time()
    vecs = model.encode(texts, normalize_embeddings=True, batch_size=32)
    elapsed = time.time() - t0
    log.info("批量生成向量 %d 条, dim=%d (耗时 %.2fs)", len(texts), len(vecs[0]), elapsed)
    return [v.tolist() for v in vecs]


def get_dimensions(model_name=None):
    """获取模型的向量维度"""
    model = _load_model(model_name)
    if model is None:
        return 0
    return model.get_sentence_embedding_dimension()
