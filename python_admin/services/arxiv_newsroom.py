"""
=============================================================================
QuantCAI — Autonomous arXiv Research Newsroom
=============================================================================
Scrapes the arXiv Atom API for the latest papers in quantum physics (quant-ph)
and computer security (cs.CR), deduplicates against a local SQLite registry,
and feeds abstracts into the AI content generation pipeline for autonomous
social media publishing.

arXiv API Terms:
  - Max 30,000 records per query
  - Polite inter-request delay (3 seconds minimum)
  - Rate-limiting aware with exponential backoff

Copyright (c) 2026 QuantCAI — All rights reserved.
=============================================================================
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree

import httpx
from loguru import logger

# =============================================================================
# Constants
# =============================================================================
ARXIV_API_BASE = "http://export.arxiv.org/api/query"
ARXIV_CATEGORIES = ["cat:quant-ph", "cat:cs.CR"]
ARXIV_MAX_RESULTS = 25  # Per category, per fetch cycle
ARXIV_REQUEST_DELAY = 3.0  # Seconds between requests (arXiv policy)
ARXIV_TIMEOUT = httpx.Timeout(30.0, connect=10.0)

# Atom XML namespaces
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

# SQLite database for deduplication (independent of Prisma/PostgreSQL)
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "arxiv_registry.db"


# =============================================================================
# Data Models
# =============================================================================
@dataclass
class ArxivPaper:
    """Parsed arXiv paper metadata."""
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    published: str = ""
    updated: str = ""
    pdf_url: str = ""
    abs_url: str = ""


# =============================================================================
# SQLite Deduplication Registry
# =============================================================================
class ArxivRegistry:
    """
    Lightweight SQLite-backed registry to ensure no arXiv paper is processed
    twice. Operates independently from the main PostgreSQL database to keep
    the automation engine self-contained.
    """

    def __init__(self, db_path: Path = DB_PATH):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Create the papers table if it doesn't exist."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_papers (
                    arxiv_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT,
                    processed_at TEXT NOT NULL,
                    x_posted BOOLEAN DEFAULT 0,
                    linkedin_posted BOOLEAN DEFAULT 0,
                    content_hash TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_at 
                ON processed_papers(processed_at)
            """)
            conn.commit()
        logger.debug(f"arXiv registry initialized at {self.db_path}")

    def is_processed(self, arxiv_id: str) -> bool:
        """Check if a paper has already been processed."""
        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM processed_papers WHERE arxiv_id = ?",
                (arxiv_id,)
            )
            return cursor.fetchone() is not None

    def mark_processed(
        self,
        arxiv_id: str,
        title: str,
        category: str = "",
        x_posted: bool = False,
        linkedin_posted: bool = False,
    ):
        """Mark a paper as processed in the registry."""
        content_hash = hashlib.sha256(f"{arxiv_id}:{title}".encode()).hexdigest()[:16]
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO processed_papers 
                   (arxiv_id, title, category, processed_at, x_posted, linkedin_posted, content_hash)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    arxiv_id,
                    title,
                    category,
                    datetime.now(timezone.utc).isoformat(),
                    x_posted,
                    linkedin_posted,
                    content_hash,
                )
            )
            conn.commit()

    def update_post_status(
        self, arxiv_id: str, x_posted: bool = False, linkedin_posted: bool = False
    ):
        """Update the posting status for a paper."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """UPDATE processed_papers 
                   SET x_posted = ?, linkedin_posted = ?
                   WHERE arxiv_id = ?""",
                (x_posted, linkedin_posted, arxiv_id)
            )
            conn.commit()

    def get_stats(self) -> dict:
        """Get processing statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            total = conn.execute("SELECT COUNT(*) FROM processed_papers").fetchone()[0]
            x_count = conn.execute(
                "SELECT COUNT(*) FROM processed_papers WHERE x_posted = 1"
            ).fetchone()[0]
            li_count = conn.execute(
                "SELECT COUNT(*) FROM processed_papers WHERE linkedin_posted = 1"
            ).fetchone()[0]
            return {
                "total_processed": total,
                "x_posted": x_count,
                "linkedin_posted": li_count,
            }


# =============================================================================
# arXiv API Client
# =============================================================================
def _parse_arxiv_entry(entry: ElementTree.Element) -> Optional[ArxivPaper]:
    """Parse a single Atom entry element into an ArxivPaper."""
    try:
        # Extract arXiv ID from the <id> element (format: http://arxiv.org/abs/XXXX.XXXXX[vN])
        raw_id = entry.findtext("atom:id", default="", namespaces=ATOM_NS)
        arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id

        title = entry.findtext("atom:title", default="", namespaces=ATOM_NS)
        title = " ".join(title.split())  # Normalize whitespace

        abstract = entry.findtext("atom:summary", default="", namespaces=ATOM_NS)
        abstract = " ".join(abstract.split())

        if not arxiv_id or not title or not abstract:
            return None

        # Authors
        authors = []
        for author_el in entry.findall("atom:author", namespaces=ATOM_NS):
            name = author_el.findtext("atom:name", default="", namespaces=ATOM_NS)
            if name:
                authors.append(name)

        # Categories
        categories = []
        for cat_el in entry.findall("atom:category", namespaces=ATOM_NS):
            term = cat_el.get("term", "")
            if term:
                categories.append(term)

        # Links
        pdf_url = ""
        abs_url = ""
        for link_el in entry.findall("atom:link", namespaces=ATOM_NS):
            href = link_el.get("href", "")
            link_type = link_el.get("type", "")
            if link_type == "application/pdf" or href.endswith(".pdf"):
                pdf_url = href
            elif link_el.get("rel") == "alternate":
                abs_url = href

        published = entry.findtext("atom:published", default="", namespaces=ATOM_NS)
        updated = entry.findtext("atom:updated", default="", namespaces=ATOM_NS)

        return ArxivPaper(
            arxiv_id=arxiv_id,
            title=title,
            abstract=abstract,
            authors=authors,
            categories=categories,
            published=published,
            updated=updated,
            pdf_url=pdf_url,
            abs_url=abs_url or f"https://arxiv.org/abs/{arxiv_id}",
        )
    except Exception as e:
        logger.warning(f"Failed to parse arXiv entry: {e}")
        return None


async def fetch_arxiv_papers(
    categories: list[str] | None = None,
    max_results: int = ARXIV_MAX_RESULTS,
) -> list[ArxivPaper]:
    """
    Fetch the latest papers from arXiv for the specified categories.

    Args:
        categories: arXiv category search terms (e.g., ["cat:quant-ph", "cat:cs.CR"])
        max_results: Maximum number of results per query

    Returns:
        List of parsed ArxivPaper objects
    """
    if categories is None:
        categories = ARXIV_CATEGORIES

    all_papers: list[ArxivPaper] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(timeout=ARXIV_TIMEOUT) as client:
        for category in categories:
            try:
                params = {
                    "search_query": category,
                    "start": 0,
                    "max_results": max_results,
                    "sortBy": "submittedDate",
                    "sortOrder": "descending",
                }

                logger.info(f"[ARXIV] Fetching latest papers for {category}...")
                response = await client.get(ARXIV_API_BASE, params=params)
                response.raise_for_status()

                # Parse Atom XML
                root = ElementTree.fromstring(response.text)
                entries = root.findall("atom:entry", namespaces=ATOM_NS)

                category_count = 0
                for entry in entries:
                    paper = _parse_arxiv_entry(entry)
                    if paper and paper.arxiv_id not in seen_ids:
                        seen_ids.add(paper.arxiv_id)
                        all_papers.append(paper)
                        category_count += 1

                logger.info(f"[ARXIV] Found {category_count} papers for {category}")

                # Respect arXiv rate limiting
                time.sleep(ARXIV_REQUEST_DELAY)

            except httpx.HTTPStatusError as e:
                logger.error(f"[ARXIV] HTTP error fetching {category}: {e.response.status_code}")
            except Exception as e:
                logger.error(f"[ARXIV] Error fetching {category}: {e}")

    logger.info(f"[ARXIV] Total unique papers fetched: {len(all_papers)}")
    return all_papers


async def fetch_and_filter_new_papers(
    registry: ArxivRegistry | None = None,
    categories: list[str] | None = None,
    max_results: int = ARXIV_MAX_RESULTS,
) -> list[ArxivPaper]:
    """
    Fetch papers from arXiv and filter out any that have already been processed.

    Args:
        registry: ArxivRegistry instance for deduplication
        categories: arXiv categories to search
        max_results: Max results per category

    Returns:
        List of NEW (unprocessed) ArxivPaper objects
    """
    if registry is None:
        registry = ArxivRegistry()

    papers = await fetch_arxiv_papers(categories=categories, max_results=max_results)

    new_papers = []
    for paper in papers:
        if not registry.is_processed(paper.arxiv_id):
            new_papers.append(paper)
        else:
            logger.debug(f"[ARXIV] Skipping already-processed paper: {paper.arxiv_id}")

    logger.info(
        f"[ARXIV] {len(new_papers)} new papers out of {len(papers)} total"
    )
    return new_papers
