import hashlib
import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import List, Set, Optional
from app.services.news.models import RawNewsArticle
from app.core.logging import logger

# Source Reliability Score Mapping
SOURCE_RELIABILITY_MAP = {
    "reuters": 95,
    "bloomberg": 95,
    "livemint": 90,
    "mint": 90,
    "economic times": 90,
    "economictimes": 90,
    "moneycontrol": 90,
    "business standard": 90,
    "business-standard": 90,
    "financial express": 85,
    "cnbc-tv18": 88,
    "cnbctv18": 88,
    "ndtv profit": 85,
    "ndtv": 80,
    "the hindu business line": 88,
    "businessline": 88,
    "zee business": 80,
    "newsapi": 75,
    "finnhub": 80,
    "yahoo finance": 82,
}

# Tracking query parameters to strip during URL normalization
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "fbclid", "gclid", "ref", "ref_src", "source", "_hsenc",
    "_hsmi", "mc_cid", "mc_eid", "soc_src", "soc_trk"
}


def normalize_url(raw_url: str) -> str:
    """
    Strips tracking queries, session identifiers, hash anchors, and normalizes URL.
    Example:
    https://www.moneycontrol.com/news/business/rbi-123.html?utm_source=twitter&ref=abc
    -> https://www.moneycontrol.com/news/business/rbi-123.html
    """
    if not raw_url:
        return ""
    try:
        parsed = urllib.parse.urlparse(raw_url.strip())
        # Clean query parameters
        queries = urllib.parse.parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_queries = [
            (k, v) for k, v in queries if k.lower() not in TRACKING_PARAMS
        ]
        new_query = urllib.parse.urlencode(sorted(cleaned_queries))

        # Normalize path: remove trailing slash unless it's just root '/'
        path = parsed.path
        if len(path) > 1 and path.endswith("/"):
            path = path[:-1]

        cleaned = urllib.parse.urlunparse((
            parsed.scheme.lower(),
            parsed.netloc.lower().replace(":80", "").replace(":443", ""),
            path,
            "",
            new_query,
            ""  # Strip fragment
        ))
        return cleaned
    except Exception:
        return raw_url.strip()


def clean_text_for_hash(text: str) -> str:
    """Normalizes text by removing punctuation, extra whitespaces, and lowercasing."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(cleaned.split())


def compute_article_fingerprint(title: str, content_or_desc: Optional[str] = None) -> str:
    """
    Computes deterministic SHA-256 fingerprint for deduplication.
    Uses normalized title and first 150 chars of description.
    """
    cleaned_title = clean_text_for_hash(title)
    cleaned_body = clean_text_for_hash((content_or_desc or "")[:150])
    payload = f"{cleaned_title}|{cleaned_body}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def tokenize_title(title: str) -> Set[str]:
    """Extracts informative alphanumeric token set from title, filtering stop words."""
    stop_words = {
        "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with",
        "by", "from", "is", "are", "was", "were", "be", "this", "that", "it", "as",
        "has", "have", "had", "will", "would", "its", "says", "market", "stocks", "india"
    }
    words = clean_text_for_hash(title).split()
    return {w for w in words if len(w) > 2 and w not in stop_words}


def calculate_title_similarity(title1: str, title2: str) -> float:
    """
    Calculates Jaccard token set similarity between two article titles.
    Range: 0.0 (completely distinct) to 1.0 (identical keywords).
    """
    tokens1 = tokenize_title(title1)
    tokens2 = tokenize_title(title2)
    if not tokens1 or not tokens2:
        return 0.0
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    return len(intersection) / len(union)


def get_source_reliability(source_name: str) -> int:
    """Returns reliability score (0-100) based on verified financial news publishers."""
    if not source_name:
        return 60
    norm_source = source_name.lower().strip()
    for key, score in SOURCE_RELIABILITY_MAP.items():
        if key in norm_source:
            return score
    return 70  # Standard fallback reliability


def validate_publication_timestamp(pub_time: datetime, max_age_hours: int = 48) -> bool:
    """
    Validates publication timestamp:
    - Rejects timestamps in the future by more than 15 minutes.
    - Rejects stale news older than configured maximum age (default 48 hours).
    """
    now = datetime.now(timezone.utc)
    # Ensure timezone aware
    if pub_time.tzinfo is None:
        pub_time = pub_time.replace(tzinfo=timezone.utc)

    # Future check (15m tolerance for server clock drift)
    if pub_time > now + timedelta(minutes=15):
        logger.warning(f"Rejected news with future timestamp: {pub_time} > {now}")
        return False

    # Stale check
    if pub_time < now - timedelta(hours=max_age_hours):
        return False

    return True


class DeduplicationPipeline:
    """
    In-memory and stateful deduplication filter.
    Handles exact URL duplicates, SHA-256 fingerprint matches, and high title similarity.
    """

    def __init__(self, title_similarity_threshold: float = 0.72):
        self.similarity_threshold = title_similarity_threshold
        self.seen_urls: Set[str] = set()
        self.seen_fingerprints: Set[str] = set()
        self.seen_titles: List[str] = []

    def load_existing_state(self, urls: Set[str], fingerprints: Set[str], titles: List[str]):
        """Initializes deduplicator with historical DB records."""
        self.seen_urls.update(urls)
        self.seen_fingerprints.update(fingerprints)
        self.seen_titles.extend(titles)

    def is_duplicate(self, article: RawNewsArticle) -> bool:
        """
        Determines whether an article is a duplicate:
        1. Exact normalized URL match
        2. Exact fingerprint (SHA-256) match
        3. Semantic title similarity >= threshold
        """
        # 1. URL check
        if article.normalized_url in self.seen_urls:
            return True

        # 2. Fingerprint check
        if article.fingerprint in self.seen_fingerprints:
            return True

        # 3. Title similarity check against recent articles
        for existing_title in self.seen_titles[-100:]:
            sim = calculate_title_similarity(article.title, existing_title)
            if sim >= self.similarity_threshold:
                return True

        return False

    def register(self, article: RawNewsArticle):
        """Marks article as seen."""
        self.seen_urls.add(article.normalized_url)
        self.seen_fingerprints.add(article.fingerprint)
        self.seen_titles.append(article.title)
