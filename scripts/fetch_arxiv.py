"""
fetch_arxiv.py

Fetches recent arXiv papers for faculty listed in people.yml and writes:
  - contents/recent-papers.qmd  : last 3 months, up to 10 papers (homepage)
  - contents/all-papers.qmd     : last 12 months, up to 50 papers (research page)

Run from the project root:
    python scripts/fetch_arxiv.py

Requirements:
    pip install requests pyyaml
"""

import requests
import yaml
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path


# ── Settings ───────────────────────────────────────────────────────────────────
PEOPLE_FILE = "people.yml"
SHORT_FILE  = "contents/recent-papers.qmd"   # homepage
LONG_FILE   = "contents/all-papers.qmd"      # research page
# ───────────────────────────────────────────────────────────────────────────────


def get_papers():
    """Fetch all papers from arXiv for all faculty in one request."""

    # Load faculty names from people.yml
    with open(PEOPLE_FILE) as f:
        people = yaml.safe_load(f)
    faculty = people.get("people", [])

    # Build a single search query: au:"Name1" OR au:"Name2" OR ...
    names = [p["name"] for p in faculty if p.get("name")]
    query = " OR ".join(f'au:"{name}"' for name in names)

    # Call the arXiv API
    response = requests.get(
        "http://export.arxiv.org/api/query",
        params={
            "search_query": query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": 100,
        },
        timeout=30,
    )
    response.raise_for_status()

    # Parse the XML response
    NS = "http://www.w3.org/2005/Atom"
    root = ET.fromstring(response.text)
    entries = root.findall(f"{{{NS}}}entry")

    papers = []
    for entry in entries:
        published_str = entry.findtext(f"{{{NS}}}published", "")
        published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
        authors = [a.findtext(f"{{{NS}}}name", "") for a in entry.findall(f"{{{NS}}}author")]
        papers.append({
            "title":   entry.findtext(f"{{{NS}}}title", "").strip().replace("\n", " "),
            "url":     entry.findtext(f"{{{NS}}}id", "").strip(),
            "authors": authors,
            "date":    published,
        })

    return papers


def write_output(papers, filepath):
    """Write a list of papers to a .qmd file."""
    today = datetime.now().strftime("%B %d, %Y")
    is_short = filepath == SHORT_FILE
    if is_short:
        blurb = f"*Last updated {today}. See more [here](contents/all-papers.qmd).*"
    else:
        blurb = f"*Last updated {today}.*"
    lines = [blurb, ""]
    for p in papers:
        date_str    = p["date"].strftime("%b %d, %Y")
        authors_str = ", ".join(p["authors"][:5])
        if len(p["authors"]) > 5:
            authors_str += " et al."
        lines.append(f"- **[{p['title']}]({p['url']})** ({date_str})")
        lines.append(f"  {authors_str}")
        lines.append("")
    Path(filepath).write_text("\n".join(lines))
    print(f"Written {len(papers)} papers to {filepath}")


def main():
    # Step 1: Fetch all papers in one request
    print("Step 1: Loading faculty names from people.yml...")
    print("Step 2: Sending request to arXiv API (this may take a few seconds)...")
    all_papers = get_papers()
    print(f"Step 3: Done! Retrieved {len(all_papers)} papers from arXiv.\n")

    now = datetime.now(timezone.utc)

    # Step 4: Filter and write the short list (homepage)
    cutoff_short = now - timedelta(days=180)
    short_papers = [p for p in all_papers if p["date"] >= cutoff_short][:10]
    print(f"Step 4: Filtered to {len(short_papers)} papers from the last 6 months (homepage).")
    write_output(short_papers, SHORT_FILE)

    # Step 5: Filter and write the long list (research page)
    cutoff_long = now - timedelta(days=365)
    long_papers = [p for p in all_papers if p["date"] >= cutoff_long][:50]
    print(f"Step 5: Filtered to {len(long_papers)} papers from the last 12 months (research page).")
    write_output(long_papers, LONG_FILE)

    print("\nAll done!")


if __name__ == "__main__":
    main()
