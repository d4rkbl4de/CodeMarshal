from pathlib import Path

from patterns.marketplace import PatternMarketplace


def test_marketplace_search_returns_results(tmp_path: Path) -> None:
    marketplace = PatternMarketplace(storage_root=tmp_path / "storage")

    result = marketplace.search(query="password", tags=["security"], limit=10)

    assert result.success is True
    assert result.total_count >= 1
    assert any(item.pattern_id == "hardcoded_password" for item in result.results)


def test_marketplace_share_writes_bundle(tmp_path: Path) -> None:
    marketplace = PatternMarketplace(storage_root=tmp_path / "storage")
    bundle_path = tmp_path / "bundle.cmpattern.yaml"

    package = marketplace.share("hardcoded_password", bundle_out=bundle_path)

    assert package.pattern_id == "hardcoded_password"
    assert bundle_path.exists()


def test_marketplace_rate_affects_search_summary(tmp_path: Path) -> None:
    marketplace = PatternMarketplace(storage_root=tmp_path / "storage")
    marketplace.rate("hardcoded_password", rating=4, reviewer="unit_test")

    result = marketplace.search(query="hardcoded_password", limit=5)
    target = next(
        item for item in result.results if item.pattern_id == "hardcoded_password"
    )

    assert target.rating.total_reviews >= 1
    assert target.rating.average_rating >= 4.0
