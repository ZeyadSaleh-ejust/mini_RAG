"""
islamweb.net Fatawa Scraper
============================
Uses requests + BeautifulSoup4 to:
  1. Crawl a fatawa category listing page (with pagination)
  2. Follow each /ar/fatwa/{id}/... link
  3. Extract: title, السؤال (question), الإجابة (answer)
  4. Save all results to a structured .txt file

Target category:
  https://islamweb.net/ar/fatawa/588/السيرة-النبوية
"""

import re
import json
import time
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from typing import Optional

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL = "https://islamweb.net"
CATEGORY_URL = "https://www.islamweb.net/ar/articles/138/%D8%A7%D9%84%D8%B3%D9%8A%D8%B1%D8%A9-%D8%A7%D9%84%D9%86%D8%A8%D9%88%D9%8A%D8%A9"
OUTPUT_FILE = Path(__file__).parent / "islamweb_articles.jsonl"

# Polite delay between requests (seconds)
REQUEST_DELAY = 1.0

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─── HTTP Helper ──────────────────────────────────────────────────────────────

def fetch(url: str) -> Optional[BeautifulSoup]:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        response.encoding = "utf-8"
        return BeautifulSoup(response.text, "lxml")
    except requests.RequestException as e:
        print(f"  ✗ Failed to fetch {url}: {e}")
        return None

# ─── Category Page: Extract Fatwa Links ───────────────────────────────────────

def get_fatwa_links(soup: BeautifulSoup) -> list[str]:
    """
    Extract fatwa URLs only from the main listing section (ul.oneitems).
    This targets the h2 title links inside each list item, which corresponds
    exactly to the count shown in the 'الفتاوى (N)' heading.
    Sidebar links (div.leftblock) and related sections are ignored.
    """
    links = []
    seen = set()

    # The main fatawa list is a <ul class="oneitems"> — each <li> has an <h2><a>
    main_list = soup.find("ul", class_="oneitems")
    if main_list:
        for h2 in main_list.find_all("h2"):
            a_tag = h2.find("a", href=True)
            if not a_tag:
                continue
            href = a_tag["href"]
            full_url = href if href.startswith("http") else BASE_URL + href
            if full_url not in seen:
                seen.add(full_url)
                links.append(full_url)

    return links


def get_next_page_url(soup: BeautifulSoup, current_url: str) -> Optional[str]:
    """
    Find the 'next page' link on a listing page.
    islamweb uses ul.pagination with numbered links (?pageno=N&order=).
    The 'next' button is an <a> containing <i class="fa fa-angle-double-left">.
    """
    # Primary: find the next-page icon link inside ul.pagination
    pagination = soup.find("ul", class_="pagination")
    if pagination:
        for a in pagination.find_all("a", href=True):
            icon = a.find("i", class_=lambda c: c and "fa-angle-double-left" in c)
            if icon:
                href = a["href"]
                if href and href != "#":
                    return urljoin(current_url, href)

    # Fallback: rel="next" <link> in <head>
    next_link = soup.find("link", rel="next")
    if next_link and next_link.get("href"):
        return urljoin(current_url, next_link["href"])

    return None


def crawl_all_fatwa_links(start_url: str) -> list[str]:
    """
    Walk through all pages of a category and collect every fatwa URL.
    """
    all_links: list[str] = []
    page_url: Optional[str] = start_url
    page_num = 1

    while page_url:
        print(f"  📄 Listing page {page_num}: {page_url}")
        soup = fetch(page_url)
        if not soup:
            break

        links = get_fatwa_links(soup)
        print(f"     Found {len(links)} fatwa links")
        all_links.extend(links)

        next_url = get_next_page_url(soup, page_url)
        if next_url and next_url != page_url:
            page_url = next_url
            page_num += 1
            time.sleep(REQUEST_DELAY)
        else:
            break

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for link in all_links:
        if link not in seen:
            seen.add(link)
            unique.append(link)

    return unique

# ─── Individual Fatwa Page: Extract Q&A ───────────────────────────────────────
# Page structure (confirmed via browser inspection):
#   Question: div.mainitem.quest-fatwa (no itemprop) > div[itemprop="text"]
#   Answer:   div.mainitem.quest-fatwa[itemprop="acceptedAnswer"] > div[itemprop="text"]

def extract_section_text(container) -> str:
    """Get clean text from a BeautifulSoup element."""
    if not container:
        return ""
    return container.get_text(separator="\n", strip=True)


def scrape_fatwa_page(url: str) -> Optional[dict]:
    """
    Scrape an individual fatwa page and return a dict with:
      - url, title, question, answer
    Returns None on failure.
    """
    soup = fetch(url)
    if not soup:
        return None

    # Title — prefer h1 inside the fatwa content area
    title_tag = soup.find("h1") or soup.find("h2") or soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "لا يوجد عنوان"

    # ── السؤال ────────────────────────────────────────────────────────────────
    # The question block is: div.mainitem.quest-fatwa (WITHOUT itemprop attribute)
    # Its text content lives inside: div[itemprop="text"]
    question = ""
    for block in soup.find_all("div", class_=lambda c: c and "mainitem" in c and "quest-fatwa" in c):
        if not block.get("itemprop"):          # question block has no itemprop
            text_div = block.find("div", attrs={"itemprop": "text"})
            if text_div:
                question = extract_section_text(text_div)
                break

    # ── الإجابة ────────────────────────────────────────────────────────────────
    # The answer block is: div.mainitem[itemprop="acceptedAnswer"]
    # Its text content lives inside: div[itemprop="text"]
    answer = ""
    accepted = soup.find("div", attrs={"itemprop": "acceptedAnswer"})
    if accepted:
        text_div = accepted.find("div", attrs={"itemprop": "text"})
        if text_div:
            answer = extract_section_text(text_div)

    # Fallback: if both empty, dump whole body
    if not question and not answer:
        body = soup.find("body")
        answer = body.get_text(separator="\n", strip=True) if body else ""

    return {
        "url": url,
        "title": title,
        "question": question,
        "answer": answer,
    }

# ─── Output Writer ────────────────────────────────────────────────────────────

SEP = "=" * 80


def _extract_fatwa_id(url: str) -> str:
    """Pull the numeric fatwa ID from a URL like /ar/fatwa/266092/..."""
    m = re.search(r"/ar/fatwa/(\d+)/", url)
    return m.group(1) if m else url


def write_results(results: list[dict], output_path: Path) -> None:
    """
    Write all scraped fatwas to a JSONL file (one JSON object per line).

    Each record contains:
      - id       : numeric fatwa ID (unique, used as vector DB document ID)
      - text     : question + answer combined — this is the field that gets embedded
      - metadata : title, url, category, plus separate question/answer fields
                   for display/filtering without re-embedding
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as f:
        for fatwa in results:
            question = fatwa["question"] or ""
            answer   = fatwa["answer"]   or ""

            # Combined text for embedding: label each section clearly
            text = f"السؤال: {question}\nالإجابة: {answer}".strip()

            record = {
                "id": _extract_fatwa_id(fatwa["url"]),
                "text": text,
                "metadata": {
                    "title":    fatwa["title"],
                    "url":      fatwa["url"],
                    "category": "السيرة النبوية",
                    "question": question,
                    "answer":   answer,
                    "source":   "islamweb.net",
                },
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\n✓ Saved {len(results)} fatwas → {output_path.resolve()}")

# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print(SEP)
    print("islamweb.net Fatawa Scraper (requests + BeautifulSoup4)")
    print(SEP)

    # Step 1: Collect all fatwa URLs from the category
    print("\n[1/3] Crawling category listing pages …")
    fatwa_urls = crawl_all_fatwa_links(CATEGORY_URL)
    print(f"\n  ✓ Total unique fatwa URLs collected: {len(fatwa_urls)}")

    if not fatwa_urls:
        print("  ✗ No fatwa links found. Exiting.")
        return

    # Step 2: Scrape each fatwa page
    print("\n[2/3] Scraping individual fatwa pages …")
    results = []
    for idx, url in enumerate(fatwa_urls, 1):
        print(f"  [{idx}/{len(fatwa_urls)}] {url}")
        data = scrape_fatwa_page(url)
        if data:
            results.append(data)
        time.sleep(REQUEST_DELAY)

    print(f"\n  ✓ Successfully scraped: {len(results)} fatwas")

    # Step 3: Write output
    print("\n[3/3] Writing output file …")
    write_results(results, OUTPUT_FILE)

    print("\n" + SEP)
    print("Done!")
    print(SEP)


if __name__ == "__main__":
    main()
