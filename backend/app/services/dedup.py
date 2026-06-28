"""相似项/防重复服务。

在用户"新建字典项"前，对已有字典做模糊匹配并提示，从源头抑制
"轴瓦螺丝掉落 / 轴瓦损坏"这类近义重复。使用 rapidfuzz 综合多种相似度。
"""
from rapidfuzz import fuzz

ItemRef = tuple[int, str]  # (id, name)


def _score(query: str, candidate: str) -> int:
    q = (query or "").strip().lower()
    c = (candidate or "").strip().lower()
    if not q or not c:
        return 0
    return int(round(max(
        fuzz.ratio(q, c),            # 整体相似度
        fuzz.partial_ratio(q, c),    # 子串匹配（命中"轴瓦"片段）
        fuzz.token_set_ratio(q, c),  # 词序/包含
    )))


def find_similar(query: str, items: list[ItemRef], threshold: int = 60, limit: int = 5):
    """返回 [((id, name), score), ...] 按相似度降序。"""
    scored: list[tuple[ItemRef, int]] = []
    for ref in items:
        s = _score(query, ref[1])
        if s >= threshold:
            scored.append((ref, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


def best_match(query: str, items: list[ItemRef], threshold: int = 85):
    res = find_similar(query, items, threshold=threshold, limit=1)
    return res[0] if res else None
