"""
patterns/marketplace.py - Local-first pattern marketplace services.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from patterns.loader import PatternDefinition, PatternLoader, PatternManager


@dataclass(frozen=True)
class PatternReview:
    """Single local review event."""

    reviewer: str
    rating: int
    comment: str
    created_at: str


@dataclass(frozen=True)
class PatternRatingSummary:
    """Aggregated rating metrics for one pattern."""

    average_rating: float
    total_reviews: int


@dataclass(frozen=True)
class MarketplacePattern:
    """Pattern listing entry returned by marketplace search APIs."""

    pattern_id: str
    name: str
    description: str
    severity: str
    tags: list[str]
    languages: list[str]
    version: str
    source: str
    installed: bool
    rating: PatternRatingSummary


@dataclass(frozen=True)
class MarketplaceQuery:
    """Search query payload for marketplace operations."""

    query: str = ""
    tags: list[str] = field(default_factory=list)
    severity: str | None = None
    language: str | None = None
    limit: int = 20


@dataclass(frozen=True)
class MarketplaceSearchResult:
    """Search result from local marketplace index."""

    success: bool
    total_count: int
    results: list[MarketplacePattern]
    message: str = ""
    error: str | None = None


@dataclass(frozen=True)
class PatternPackage:
    """Bundle metadata for shared pattern files."""

    package_id: str
    pattern_id: str
    version: str
    path: str
    created_at: str


class PatternMarketplace:
    """Local-only marketplace for discovering and sharing patterns."""

    def __init__(
        self,
        *,
        storage_root: Path | str = Path("storage"),
        patterns_dir: Path | None = None,
    ) -> None:
        self.storage_root = Path(storage_root)
        self.marketplace_dir = self.storage_root / "pattern_marketplace"
        self.packages_dir = self.marketplace_dir / "packages"
        self.catalog_file = self.marketplace_dir / "catalog.json"
        self.reviews_file = self.marketplace_dir / "reviews.json"

        self.loader = PatternLoader(patterns_dir=patterns_dir)
        self.manager = PatternManager()

        self.marketplace_dir.mkdir(parents=True, exist_ok=True)
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        if not self.catalog_file.exists():
            self._write_json(self.catalog_file, [])
        if not self.reviews_file.exists():
            self._write_json(self.reviews_file, {})

    def search(
        self,
        query: MarketplaceQuery | str = "",
        *,
        tags: list[str] | None = None,
        severity: str | None = None,
        language: str | None = None,
        limit: int = 20,
    ) -> MarketplaceSearchResult:
        """Search locally indexed/built-in patterns."""
        request = self._normalize_query(
            query, tags=tags, severity=severity, language=language, limit=limit
        )
        all_patterns = self._index_patterns()

        filtered: list[tuple[MarketplacePattern, int]] = []
        q = request.query.strip().lower()
        tag_set = {item.strip().lower() for item in request.tags if item.strip()}
        normalized_severity = (
            request.severity.strip().lower() if request.severity else None
        )
        normalized_lang = request.language.strip().lower() if request.language else None

        for pattern in all_patterns:
            if normalized_severity and pattern.severity.lower() != normalized_severity:
                continue

            pattern_tags = {item.lower() for item in pattern.tags}
            if tag_set and not tag_set.issubset(pattern_tags):
                continue

            pattern_langs = {item.lower() for item in pattern.languages}
            if normalized_lang and normalized_lang not in pattern_langs:
                continue

            score = self._score_pattern(pattern, q)
            if q and score == 0:
                continue
            filtered.append((pattern, score))

        filtered.sort(key=lambda item: (item[1], item[0].name.lower()), reverse=True)
        trimmed = [item[0] for item in filtered[: max(int(request.limit), 0)]]
        return MarketplaceSearchResult(
            success=True,
            total_count=len(trimmed),
            results=trimmed,
            message=f"Found {len(trimmed)} pattern(s)",
        )

    def install(self, pattern_ref: str, *, force: bool = False) -> dict[str, Any]:
        """Install a pattern by id or bundle path into custom pattern storage."""
        ref = pattern_ref.strip()
        if not ref:
            return {"success": False, "error": "pattern_ref is required"}

        pattern = self._resolve_pattern_reference(ref)
        if pattern is None:
            return {"success": False, "error": f"Pattern not found: {ref}"}

        existing = {
            item.id.strip().lower()
            for item in self.loader.load_custom_patterns()
            if item.id.strip()
        }
        if pattern.id.lower() in existing and not force:
            return {
                "success": True,
                "installed": False,
                "pattern_id": pattern.id,
                "message": "Pattern already installed",
            }

        installed = self.manager.add_custom_pattern(pattern)
        if not installed:
            return {"success": False, "error": f"Failed to install pattern: {pattern.id}"}

        self._upsert_catalog_entry(
            {
                "pattern_id": pattern.id,
                "name": pattern.name,
                "description": pattern.description,
                "severity": pattern.severity,
                "tags": list(pattern.tags),
                "languages": list(pattern.languages),
                "version": "1.0.0",
                "source": "local_install",
                "installed": True,
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )
        return {
            "success": True,
            "installed": True,
            "pattern_id": pattern.id,
            "message": "Pattern installed",
        }

    def share(
        self,
        pattern_id: str,
        *,
        bundle_out: Path | str | None = None,
        include_examples: bool = False,
    ) -> PatternPackage:
        """Create shareable bundle (`.cmpattern.yaml`) for a pattern id."""
        normalized = pattern_id.strip()
        if not normalized:
            raise ValueError("pattern_id is required")

        pattern = self._find_by_id(normalized)
        if pattern is None:
            raise ValueError(f"Pattern not found: {pattern_id}")

        timestamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
        package_id = f"{pattern.id}-{timestamp}"
        if bundle_out is None:
            bundle_path = self.packages_dir / f"{package_id}.cmpattern.yaml"
        else:
            bundle_path = Path(bundle_out).resolve()

        bundle = {
            "schema_version": "1.0",
            "package": {
                "id": package_id,
                "pattern_id": pattern.id,
                "version": "1.0.0",
                "created_at": datetime.now(UTC).isoformat(),
                "source": "local_share",
            },
            "pattern": asdict(pattern),
        }
        if include_examples:
            bundle["examples"] = {
                "positive": [],
                "negative": [],
            }

        bundle_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_path.write_text(
            yaml.safe_dump(bundle, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )

        self._upsert_catalog_entry(
            {
                "pattern_id": pattern.id,
                "name": pattern.name,
                "description": pattern.description,
                "severity": pattern.severity,
                "tags": list(pattern.tags),
                "languages": list(pattern.languages),
                "version": "1.0.0",
                "source": "local_share",
                "installed": True,
                "bundle_path": str(bundle_path),
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )

        return PatternPackage(
            package_id=package_id,
            pattern_id=pattern.id,
            version="1.0.0",
            path=str(bundle_path),
            created_at=datetime.now(UTC).isoformat(),
        )

    def rate(
        self,
        pattern_id: str,
        rating: int,
        *,
        reviewer: str = "local",
        comment: str = "",
    ) -> PatternReview:
        """Record a local review/rating event for a pattern."""
        if rating < 1 or rating > 5:
            raise ValueError("rating must be between 1 and 5")
        review = PatternReview(
            reviewer=reviewer,
            rating=int(rating),
            comment=comment.strip(),
            created_at=datetime.now(UTC).isoformat(),
        )
        reviews = self._read_json_dict(self.reviews_file)
        entries = reviews.get(pattern_id, [])
        if not isinstance(entries, list):
            entries = []
        entries.append(asdict(review))
        reviews[pattern_id] = entries
        self._write_json(self.reviews_file, reviews)
        return review

    def review(
        self,
        pattern_id: str,
        *,
        reviewer: str,
        rating: int,
        comment: str = "",
    ) -> PatternReview:
        """Alias for `rate` with explicit review semantics."""
        return self.rate(
            pattern_id=pattern_id,
            rating=rating,
            reviewer=reviewer,
            comment=comment,
        )

    def list_installed(self) -> list[MarketplacePattern]:
        """List currently installed custom patterns."""
        installed_ids = {
            item.id.strip().lower()
            for item in self.loader.load_custom_patterns()
            if item.id.strip()
        }
        return [item for item in self._index_patterns() if item.pattern_id.lower() in installed_ids]

    def _index_patterns(self) -> list[MarketplacePattern]:
        entries: dict[str, MarketplacePattern] = {}
        installed_ids = {
            item.id.strip().lower()
            for item in self.loader.load_custom_patterns()
            if item.id.strip()
        }

        for pattern in self.loader.load_all_patterns():
            summary = self._rating_summary(pattern.id)
            key = pattern.id.strip().lower()
            entries[key] = MarketplacePattern(
                pattern_id=pattern.id,
                name=pattern.name,
                description=pattern.description,
                severity=pattern.severity,
                tags=list(pattern.tags),
                languages=list(pattern.languages),
                version="1.0.0",
                source="builtin_or_custom",
                installed=key in installed_ids,
                rating=summary,
            )

        for item in self._read_json_list(self.catalog_file):
            pattern_id = str(item.get("pattern_id") or "").strip()
            if not pattern_id:
                continue
            key = pattern_id.lower()
            summary = self._rating_summary(pattern_id)
            entries[key] = MarketplacePattern(
                pattern_id=pattern_id,
                name=str(item.get("name") or pattern_id),
                description=str(item.get("description") or ""),
                severity=str(item.get("severity") or "warning"),
                tags=[str(tag) for tag in item.get("tags", []) if str(tag).strip()],
                languages=[
                    str(lang) for lang in item.get("languages", []) if str(lang).strip()
                ],
                version=str(item.get("version") or "1.0.0"),
                source=str(item.get("source") or "catalog"),
                installed=bool(item.get("installed", False) or key in installed_ids),
                rating=summary,
            )

        return list(entries.values())

    def _resolve_pattern_reference(self, pattern_ref: str) -> PatternDefinition | None:
        candidate_path = Path(pattern_ref)
        if candidate_path.exists() and candidate_path.is_file():
            return self._load_bundle_pattern(candidate_path)
        return self._find_by_id(pattern_ref)

    def _find_by_id(self, pattern_id: str) -> PatternDefinition | None:
        target = pattern_id.strip().lower()
        if not target:
            return None
        for pattern in self.loader.load_all_patterns():
            if pattern.id.strip().lower() == target:
                return pattern
        return None

    def _load_bundle_pattern(self, bundle_path: Path) -> PatternDefinition | None:
        try:
            payload = yaml.safe_load(bundle_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return None

        pattern_payload: dict[str, Any] | None = None
        if isinstance(payload, dict):
            if isinstance(payload.get("pattern"), dict):
                pattern_payload = payload["pattern"]
            elif "id" in payload and "pattern" in payload:
                pattern_payload = payload
        if not isinstance(pattern_payload, dict):
            return None

        try:
            return PatternDefinition(**pattern_payload)
        except Exception:
            return None

    def _rating_summary(self, pattern_id: str) -> PatternRatingSummary:
        reviews = self._read_json_dict(self.reviews_file)
        entries = reviews.get(pattern_id, [])
        if not isinstance(entries, list) or not entries:
            return PatternRatingSummary(average_rating=0.0, total_reviews=0)

        values = [
            int(item.get("rating", 0))
            for item in entries
            if isinstance(item, dict) and re.fullmatch(r"[1-5]", str(item.get("rating")))
        ]
        if not values:
            return PatternRatingSummary(average_rating=0.0, total_reviews=0)
        average = sum(values) / len(values)
        return PatternRatingSummary(average_rating=round(average, 2), total_reviews=len(values))

    def _score_pattern(self, pattern: MarketplacePattern, query: str) -> int:
        if not query:
            return 1
        score = 0
        haystacks = [
            pattern.pattern_id.lower(),
            pattern.name.lower(),
            pattern.description.lower(),
            " ".join(pattern.tags).lower(),
        ]
        for index, haystack in enumerate(haystacks):
            if query in haystack:
                score += 4 - min(index, 3)
        return score

    def _normalize_query(
        self,
        query: MarketplaceQuery | str,
        *,
        tags: list[str] | None,
        severity: str | None,
        language: str | None,
        limit: int,
    ) -> MarketplaceQuery:
        if isinstance(query, MarketplaceQuery):
            return query
        return MarketplaceQuery(
            query=str(query or "").strip(),
            tags=list(tags or []),
            severity=severity,
            language=language,
            limit=max(int(limit), 0),
        )

    def _upsert_catalog_entry(self, entry: dict[str, Any]) -> None:
        pattern_id = str(entry.get("pattern_id") or "").strip()
        if not pattern_id:
            return

        rows = self._read_json_list(self.catalog_file)
        normalized = pattern_id.lower()
        replaced = False
        updated_rows: list[dict[str, Any]] = []
        for row in rows:
            row_id = str(row.get("pattern_id") or "").strip().lower()
            if row_id == normalized:
                updated_rows.append(dict(entry))
                replaced = True
            else:
                updated_rows.append(row)
        if not replaced:
            updated_rows.append(dict(entry))
        self._write_json(self.catalog_file, updated_rows)

    @staticmethod
    def _read_json_list(path: Path) -> list[dict[str, Any]]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    @staticmethod
    def _read_json_dict(path: Path) -> dict[str, Any]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
        if isinstance(payload, dict):
            return payload
        return {}

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

