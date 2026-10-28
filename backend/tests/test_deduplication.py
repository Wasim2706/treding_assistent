from datetime import datetime, timezone, timedelta
from app.services.news.deduplication import (
    normalize_url,
    compute_article_fingerprint,
    calculate_title_similarity,
    get_source_reliability,
    validate_publication_timestamp,
    DeduplicationPipeline
)
from app.services.news.models import RawNewsArticle


def test_url_normalization():
    # URL with tracking parameters should be cleaned
    raw = "https://www.moneycontrol.com/news/markets/nifty-record-high-12345.html?utm_source=twitter&utm_medium=social&ref=feed#anchor"
    expected = "https://www.moneycontrol.com/news/markets/nifty-record-high-12345.html"
    assert normalize_url(raw) == expected

    # Trailing slash should be stripped
    assert normalize_url("https://livemint.com/markets/") == "https://livemint.com/markets"


def test_article_fingerprinting():
    title1 = "Nifty hits record high of 25,000 led by Banking stocks"
    desc1 = "The Indian benchmark Nifty 50 surged past 25,000 on Thursday."
    fp1 = compute_article_fingerprint(title1, desc1)

    # Same title with minor spacing and capitalization difference should produce identical fingerprint
    title2 = "Nifty Hits Record High Of 25,000 Led By Banking Stocks   "
    desc2 = "The Indian benchmark Nifty 50 surged past 25,000 on Thursday."
    fp2 = compute_article_fingerprint(title2, desc2)

    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256


def test_title_similarity():
    t1 = "RBI keeps repo rate unchanged at 6.5 percent"
    t2 = "RBI MPC holds repo rate steady at 6.5 percent"
    sim = calculate_title_similarity(t1, t2)
    assert sim >= 0.4  # Substantial token overlap

    t3 = "Tata Motors reports 15 percent jump in passenger vehicle sales"
    sim_unrelated = calculate_title_similarity(t1, t3)
    assert sim_unrelated < 0.15


def test_source_reliability_scoring():
    assert get_source_reliability("Reuters") == 95
    assert get_source_reliability("Livemint Markets") == 90
    assert get_source_reliability("Economic Times") == 90
    assert get_source_reliability("Moneycontrol Top News") == 90
    assert get_source_reliability("Random Blog") == 70


def test_publication_timestamp_validation():
    now = datetime.now(timezone.utc)
    # Valid recent timestamp
    assert validate_publication_timestamp(now - timedelta(hours=2)) is True

    # Stale timestamp (>48h)
    assert validate_publication_timestamp(now - timedelta(hours=50)) is False

    # Timestamp too far in future (>15m)
    assert validate_publication_timestamp(now + timedelta(hours=2)) is False


def test_deduplication_pipeline():
    pipeline = DeduplicationPipeline(title_similarity_threshold=0.7)

    art1 = RawNewsArticle(
        article_id="art1",
        title="Brent crude surges 4% amid Middle East tensions",
        description="Crude prices rallied sharply.",
        url="https://economictimes.com/crude-surges",
        normalized_url="https://economictimes.com/crude-surges",
        source="Economic Times",
        published_at=datetime.now(timezone.utc),
        fingerprint=compute_article_fingerprint("Brent crude surges 4% amid Middle East tensions", "Crude prices rallied sharply.")
    )

    # First time should not be duplicate
    assert pipeline.is_duplicate(art1) is False
    pipeline.register(art1)

    # Second time with identical URL and fingerprint should be duplicate
    assert pipeline.is_duplicate(art1) is True

    # Rewritten title from different publisher should also be flagged as duplicate
    art2 = RawNewsArticle(
        article_id="art2",
        title="Brent crude surges 4% amid Middle East tensions",
        description="Different description from another wire.",
        url="https://reuters.com/crude-prices",
        normalized_url="https://reuters.com/crude-prices",
        source="Reuters",
        published_at=datetime.now(timezone.utc),
        fingerprint=compute_article_fingerprint("Brent crude surges 4% amid Middle East tensions", "Different description")
    )
    assert pipeline.is_duplicate(art2) is True
