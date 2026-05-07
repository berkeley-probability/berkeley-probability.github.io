"""
fetch_arxiv.py

Fetches recent arXiv papers for people listed in people.yml and writes:
  - contents/recent-papers.qmd  : papers from the last 6 months (homepage)
  - contents/all-papers.qmd     : papers from the last 12 months (research page)

Run from the project root:
    python3 scripts/fetch_arxiv.py

Requirements:
    python3 -m pip install requests pyyaml
"""

import requests
import yaml
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path
from time import sleep
from urllib.parse import urlparse


# ── Settings ───────────────────────────────────────────────────────────────────
PEOPLE_FILE = "people.yml"
SHORT_FILE  = "contents/recent-papers.qmd"   # homepage
LONG_FILE   = "contents/all-papers.qmd"      # research page
ARXIV_API_URL = "https://export.arxiv.org/api/query"
REQUEST_TIMEOUT = 60
REQUEST_RETRIES = 3
# ───────────────────────────────────────────────────────────────────────────────


def clean_text(value):
    """Normalize whitespace from arXiv's Atom fields."""
    return " ".join(value.split())


def arxiv_id_from_url(url):
    """Return the arXiv identifier from an abs URL."""
    path = urlparse(url).path
    return path.removeprefix("/abs/").strip("/")


def arxiv_pdf_url(arxiv_id):
    """Return the matching arXiv PDF URL."""
    return f"https://arxiv.org/pdf/{arxiv_id}"


def format_authors(authors, limit=8):
    """Format an author list, truncating very long collaborations."""
    shown = authors[:limit]
    authors_str = ", ".join(shown)
    if len(authors) > limit:
        authors_str += " et al."
    return authors_str


def html_text(value):
    """Escape text that is inserted into generated HTML."""
    return escape(value, quote=False)


def paper_list_styles():
    """Return styles for the generated Quarto publication cards."""
    return """```{=html}
<style>
.paper-list-updated {
  color: #555;
  margin-bottom: 1rem;
}

.paper-card {
  border-top: 1px solid #d8dee6;
  padding: 1rem 0 1.1rem 0;
  margin: 0;
}

.paper-card:last-child {
  border-bottom: 1px solid #d8dee6;
}

.paper-date {
  color: #666;
  font-size: 0.9em;
  margin-bottom: 0.15rem;
}

.paper-title {
  font-size: 1.05em;
  font-weight: 700;
  line-height: 1.35;
}

.paper-authors {
  color: #333;
  margin-top: 0.2rem;
}

.paper-links {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem;
  margin-top: 0.45rem;
}

.paper-badge,
.paper-category {
  border: 1px solid #d4dce5;
  border-radius: 4px;
  color: #1a6aab;
  display: inline-block;
  font-size: 0.82em;
  line-height: 1;
  padding: 0.28rem 0.42rem;
}

.paper-category {
  color: #555;
}
</style>
```"""


def fetch_arxiv_response(query):
    """Fetch arXiv results with a few retries for slow API responses."""
    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": 100,
    }
    last_error = None

    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            response = requests.get(
                ARXIV_API_URL,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt == REQUEST_RETRIES:
                break
            wait_seconds = 5 * attempt
            print(
                f"arXiv request timed out or failed "
                f"(attempt {attempt}/{REQUEST_RETRIES}); retrying in {wait_seconds}s..."
            )
            sleep(wait_seconds)

    raise RuntimeError(
        "Could not fetch papers from arXiv after "
        f"{REQUEST_RETRIES} attempts. Last error: {last_error}"
    ) from last_error


def get_papers():
    """Fetch all papers from arXiv for all people in one request."""

    # Load names from people.yml.
    with open(PEOPLE_FILE) as f:
        people = yaml.safe_load(f)
    roster = people.get("people", [])

    # Build a single search query: au:"Name1" OR au:"Name2" OR ...
    names = [p["name"] for p in roster if p.get("name")]
    query = " OR ".join(f'au:"{name}"' for name in names)

    # Call the arXiv API
    response = fetch_arxiv_response(query)

    # Parse the XML response
    NS = "http://www.w3.org/2005/Atom"
    root = ET.fromstring(response.text)
    entries = root.findall(f"{{{NS}}}entry")

    papers = []
    for entry in entries:
        published_str = entry.findtext(f"{{{NS}}}published", "")
        published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        updated_str = entry.findtext(f"{{{NS}}}updated", "")
        updated = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
        authors = [
            clean_text(a.findtext(f"{{{NS}}}name", ""))
            for a in entry.findall(f"{{{NS}}}author")
        ]
        url = entry.findtext(f"{{{NS}}}id", "").strip()
        arxiv_id = arxiv_id_from_url(url)
        categories = [
            c.attrib.get("term", "")
            for c in entry.findall(f"{{{NS}}}category")
            if c.attrib.get("term")
        ]
        papers.append({
            "title":       clean_text(entry.findtext(f"{{{NS}}}title", "")),
            "url":         url.replace("http://", "https://"),
            "pdf_url":     arxiv_pdf_url(arxiv_id),
            "arxiv_id":    arxiv_id,
            "authors":     authors,
            "date":        published,
            "updated":     updated,
            "categories":  categories,
        })

    return papers


def write_output(papers, filepath):
    """Write a list of papers to a .qmd file."""
    today = datetime.now().strftime("%B %d, %Y")
    is_short = filepath == SHORT_FILE
    if is_short:
        blurb = f'<p class="paper-list-updated"><em>Last updated {today}. Papers from the last 6 months. See more <a href="contents/all-papers.qmd">here</a>.</em></p>'
    else:
        blurb = f'### Papers\n\n<p class="paper-list-updated"><em>Last updated {today}. Papers going back ~1 year.</em></p>'
    lines = [paper_list_styles(), "", blurb, ""]
    for p in papers:
        date_str = p["date"].strftime("%b %d, %Y")
        authors_str = html_text(format_authors(p["authors"]))
        title = html_text(p["title"])
        category_str = html_text(", ".join(p["categories"][:3]))
        lines.extend([
            '::: {.paper-card}',
            f'<div class="paper-date">{date_str}</div>',
            f'<div class="paper-title"><a href="{p["url"]}">{title}</a></div>',
            f'<div class="paper-authors">{authors_str}</div>',
            '<div class="paper-links">',
            f'<a class="paper-badge" href="{p["url"]}">arXiv:{p["arxiv_id"]}</a>',
            f'<a class="paper-badge" href="{p["pdf_url"]}">PDF</a>',
        ])
        if category_str:
            lines.append(f'<span class="paper-category">{category_str}</span>')
        lines.extend([
            '</div>',
            ':::',
        ])
        lines.append("")
    Path(filepath).write_text("\n".join(lines))
    print(f"Written {len(papers)} papers to {filepath}")


def main():
    # Step 1: Fetch all papers in one request
    print("Step 1: Loading names from people.yml...")
    print("Step 2: Sending request to arXiv API (this may take a few seconds)...")
    all_papers = get_papers()
    print(f"Step 3: Done! Retrieved {len(all_papers)} papers from arXiv.\n")

    now = datetime.now(timezone.utc)

    # Step 4: Filter and write the short list (homepage)
    cutoff_short = now - timedelta(days=180)
    short_papers = [p for p in all_papers if p["date"] >= cutoff_short]
    print(f"Step 4: Filtered to {len(short_papers)} papers from the last 6 months (homepage).")
    write_output(short_papers, SHORT_FILE)

    # Step 5: Filter and write the long list (research page)
    cutoff_long = now - timedelta(days=365)
    long_papers = [p for p in all_papers if p["date"] >= cutoff_long]
    print(f"Step 5: Filtered to {len(long_papers)} papers from the last 12 months (research page).")
    write_output(long_papers, LONG_FILE)

    print("\nAll done!")


if __name__ == "__main__":
    main()
