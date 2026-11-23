from __future__ import annotations

import hashlib
import math
import re
import threading
import unicodedata
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

COLLECTION_NAME = "diabetes_kb_mvp_v1"
LIGHTWEIGHT_DIM = 384
HASH_SLICE_DIM = 320

_EMBEDDER_CACHE: dict[str, Any] = {}
_EMBEDDER_LOCK = threading.Lock()

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_STOPWORDS: frozenset[str] = frozenset(
    {
        # Vietnamese function words & question phrases
        "la",
        "va",
        "cua",
        "cho",
        "nay",
        "kia",
        "do",
        "day",
        "trong",
        "ngoai",
        "tren",
        "duoi",
        "voi",
        "tu",
        "den",
        "ve",
        "mot",
        "hai",
        "ba",
        "nhung",
        "cac",
        "de",
        "khong",
        "co",
        "duoc",
        "bi",
        "se",
        "da",
        "dang",
        "rat",
        "qua",
        "lam",
        "thi",
        "ma",
        "nhu",
        "the",
        "nao",
        "sao",
        "gi",
        "ai",
        "dau",
        "bao",
        "nhieu",
        "hom",
        "ngay",
        "mai",
        "can",
        "nen",
        "phai",
        "hay",
        "hoac",
        "tuy",
        "neu",
        "vi",
        "boi",
        "khi",
        "luc",
        "sau",
        "truoc",
        "giua",
        "cung",
        "deu",
        "chi",
        "moi",
        "tung",
        "lai",
        "ra",
        "vao",
        "len",
        "xuong",
        "di",
        "o",
        "tai",
        "bang",
        "theo",
        "nham",
        "giup",
        "tao",
        "gay",
        "su",
        "viec",
        "cach",
        "loai",
        "muc",
        "so",
        "ban",
        "toi",
        "minh",
        "chung",
        "ho",
        "nguoi",
        "ay",
        "vua",
        "roi",
        "nua",
        "hon",
        "nhat",
        "kha",
        "nha",
        # English function words
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "of",
        "in",
        "to",
        "for",
        "with",
        "on",
        "at",
        "from",
        "by",
        "about",
        "as",
        "into",
        "like",
        "through",
        "after",
        "over",
        "between",
        "out",
        "against",
        "during",
        "without",
        "before",
        "under",
        "around",
        "among",
        "and",
        "or",
        "but",
        "if",
        "because",
        "while",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "these",
        "those",
        "am",
        "it",
        "its",
        "they",
        "them",
        "their",
        "you",
        "your",
        "we",
        "our",
        "he",
        "she",
        "his",
        "her",
        "how",
        "when",
        "where",
        "why",
        "much",
        "many",
        "today",
        "there",
        "here",
        "all",
        "some",
        "any",
        "more",
        "most",
        "other",
        "such",
        "than",
        "then",
        "also",
        "just",
        "only",
        "very",
        "not",
        "no",
    }
)

_CONCEPT_PHRASES: tuple[tuple[int, tuple[str, ...]], ...] = (
    (0, ("hba1c", "a1c", "hemoglobin a1c", "glycated hemoglobin")),
    (1, ("prediabetes", "tien tieu duong", "tien dai thao duong")),
    (2, ("type 2 diabetes", "tieu duong type 2", "tieu duong tuyp 2", "dai thao duong tip 2", "dai thao duong type 2")),
    (3, ("type 1 diabetes", "tieu duong type 1", "dai thao duong type 1")),
    (4, ("gestational diabetes", "tieu duong thai ky")),
    (5, ("diabetes", "tieu duong", "dai thao duong")),
    (6, ("bmi", "overweight", "obesity", "thua can", "beo phi")),
    (7, ("waist", "vong eo", "beo bung")),
    (8, ("risk factor", "risk factors", "yeu to nguy co", "nguy co")),
    (9, ("fasting plasma glucose", "fpg", "blood glucose", "blood sugar", "duong huyet")),
    (10, ("ogtt", "oral glucose tolerance", "nghiem phap dung nap")),
    (11, ("insulin resistance", "khang insulin", "de khang insulin", "insulin")),
    (12, ("symptom", "symptoms", "trieu chung", "khat nuoc", "khat nhieu", "di tieu", "met moi", "nhin mo", "sut can")),
    (13, ("complication", "complications", "bien chung", "heart disease", "tim mach", "kidney", "benh than", "vong mac", "than kinh", "loet ban chan")),
    (14, ("healthy diet", "healthy eating", "che do an", "dinh duong", "chat xo", "tinh bot phuc")),
    (15, ("physical activity", "exercise", "van dong", "tap luyen", "150 phut")),
    (16, ("family history", "tien su gia dinh")),
    (17, ("age 45", "45 or older", "tuoi 45", "35 or older")),
    (18, ("nafld", "fatty liver", "gan nhiem mo", "pcos", "buong trung da nang")),
    (19, ("screening", "blood test", "xet nghiem", "chan doan", "tam soat", "5 7", "6 4", "6 5")),
)


def fold_text(text: str) -> str:
    """Normalize text to lowercase ASCII with Vietnamese diacritics folded."""
    decomposed = unicodedata.normalize("NFD", text or "")
    without_marks = "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")
    return without_marks.replace("đ", "d").replace("Đ", "D").lower()


def extract_content_tokens(text: str) -> list[str]:
    """Return stopword-filtered ASCII tokens of length >= 2."""
    folded = fold_text(text)
    raw_tokens = _TOKEN_RE.findall(folded)
    return [tok for tok in raw_tokens if len(tok) >= 2 and tok not in _STOPWORDS]


def _hash_feature(feature: str) -> tuple[int, float]:
    digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=8).digest()
    val = int.from_bytes(digest, "little")
    idx = val % HASH_SLICE_DIM
    sign = 1.0 if ((val >> 8) & 1) == 0 else -1.0
    return idx, sign


def lightweight_embed(text: str) -> list[float]:
    """Deterministically project content tokens and diabetes concepts into a 384-d unit vector."""
    vec = [0.0] * LIGHTWEIGHT_DIM
    folded = fold_text(text)
    tokens = extract_content_tokens(text)

    for tok in tokens:
        idx, sign = _hash_feature(f"u:{tok}")
        weight = 0.7 if len(tok) == 2 else 1.0
        vec[idx] += sign * weight

    for i in range(len(tokens) - 1):
        bigram = f"b:{tokens[i]}_{tokens[i + 1]}"
        idx, sign = _hash_feature(bigram)
        vec[idx] += sign * 1.4

    for slot, phrases in _CONCEPT_PHRASES:
        if any(phrase in folded for phrase in phrases):
            vec[HASH_SLICE_DIM + slot] += 2.2

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        vec[0] = 1.0
        return vec
    return [v / norm for v in vec]


def _get_sentence_transformer(model_name: str) -> Any:
    if model_name not in _EMBEDDER_CACHE:
        with _EMBEDDER_LOCK:
            if model_name not in _EMBEDDER_CACHE:
                from sentence_transformers import SentenceTransformer

                _EMBEDDER_CACHE[model_name] = SentenceTransformer(
                    model_name,
                    local_files_only=True,
                )
    return _EMBEDDER_CACHE[model_name]


class ChromaRAGStore:
    """ChromaDB persistent vector store for diabetes medical documents."""

    def __init__(
        self,
        chroma_dir: Path,
        *,
        use_lightweight_embedder: bool = False,
        embed_model_name: str = "intfloat/multilingual-e5-small",
    ) -> None:
        self.chroma_dir = Path(chroma_dir)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.use_lightweight_embedder = use_lightweight_embedder
        self.embed_model_name = embed_model_name

        self._client = chromadb.PersistentClient(
            path=str(self.chroma_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _embed_passages(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.use_lightweight_embedder:
            return [lightweight_embed(t) for t in texts]
        model = _get_sentence_transformer(self.embed_model_name)
        prefixed = [f"passage: {t}" for t in texts]
        vectors = model.encode(prefixed, normalize_embeddings=True)
        return [vec.tolist() for vec in vectors]

    def _embed_query(self, query_text: str) -> list[float]:
        if self.use_lightweight_embedder:
            return lightweight_embed(query_text)
        model = _get_sentence_transformer(self.embed_model_name)
        vec = model.encode([f"query: {query_text}"], normalize_embeddings=True)[0]
        return vec.tolist()

    def count_chunks(self, active_only: bool = False) -> int:
        if not active_only:
            return self._collection.count()
        res = self._collection.get(where={"status": "active"}, include=[])
        return len(res.get("ids") or [])

    def upsert_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        ids = [str(c["chunk_id"]) for c in chunks]
        documents = [str(c["text"]) for c in chunks]
        embeddings = self._embed_passages(documents)
        metadatas = [
            {
                "source_id": str(c["source_id"]),
                "title": str(c["title"]),
                "publisher": str(c["publisher"]),
                "source_url": str(c.get("source_url") or ""),
                "language": str(c.get("language") or "en"),
                "status": str(c.get("status") or "active"),
                "chunk_index": int(c.get("chunk_index", 0)),
                "heading": str(c.get("heading") or ""),
            }
            for c in chunks
        ]
        self._collection.upsert(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def set_source_status(self, source_id: str, status: str) -> int:
        existing = self._collection.get(
            where={"source_id": source_id},
            include=["metadatas"],
        )
        ids = existing.get("ids") or []
        if not ids:
            return 0
        metadatas = existing.get("metadatas") or []
        updated = []
        for meta in metadatas:
            copy_meta = dict(meta or {})
            copy_meta["status"] = status
            updated.append(copy_meta)
        self._collection.update(ids=ids, metadatas=updated)
        return len(ids)

    def delete_source(self, source_id: str) -> int:
        existing = self._collection.get(where={"source_id": source_id}, include=[])
        ids = existing.get("ids") or []
        if not ids:
            return 0
        self._collection.delete(ids=ids)
        return len(ids)

    def query(
        self,
        query_text: str,
        *,
        top_k: int = 4,
        active_source_ids: set[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> list[dict]:
        total = self._collection.count()
        if total == 0 or top_k <= 0:
            return []
        if active_source_ids is not None and len(active_source_ids) == 0:
            return []

        effective_where: dict[str, Any]
        if where is not None:
            effective_where = where
        elif active_source_ids is not None:
            effective_where = {
                "$and": [
                    {"status": {"$eq": "active"}},
                    {"source_id": {"$in": sorted(active_source_ids)}},
                ]
            }
        else:
            effective_where = {"status": "active"}

        # Check matching count so Chroma never errors when n_results exceeds filtered pool
        matched = self._collection.get(where=effective_where, include=[])
        matched_count = len(matched.get("ids") or [])
        if matched_count == 0:
            return []

        n_results = min(top_k, matched_count)
        q_vec = self._embed_query(query_text)
        res = self._collection.query(
            query_embeddings=[q_vec],
            n_results=n_results,
            where=effective_where,
            include=["documents", "metadatas", "distances"],
        )

        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]

        results: list[dict] = []
        for cid, doc, meta, dist in zip(ids, docs, metas, dists):
            meta = meta or {}
            source_id = str(meta.get("source_id", ""))
            if meta.get("status") != "active":
                continue
            if active_source_ids is not None and source_id not in active_source_ids:
                continue
            score = max(0.0, min(1.0, 1.0 - float(dist)))
            url_val = str(meta.get("source_url") or "").strip()
            results.append(
                {
                    "chunk_id": str(cid),
                    "source_id": source_id,
                    "title": str(meta.get("title", "")),
                    "publisher": str(meta.get("publisher", "")),
                    "url": url_val if url_val else None,
                    "text": str(doc or ""),
                    "score": round(score, 4),
                    "heading": str(meta.get("heading", "")),
                }
            )
        return results
