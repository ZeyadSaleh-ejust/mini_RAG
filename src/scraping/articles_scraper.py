import requests
from bs4 import BeautifulSoup
import time
import os
import re

def sanitize_filename(name):
    """Removes characters that aren't allowed in filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def scrape_article_content(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    # Try the request up to 3 times if it times out
    for attempt in range(3):
        try:
            # Increased timeout to 30 seconds
            response = requests.get(url, headers=headers, timeout=30)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')

            article_id = url.split('/')[-2] if '/article/' in url else "000"
            
            title_el = soup.select_one('div.fatwalist h1')
            title = title_el.get_text(strip=True) if title_el else "No Title"

            cat_tag = soup.find('category')
            category = cat_tag.get_text(strip=True) if cat_tag else "General"

            body_el = soup.select_one('div.articletxt')
            content = body_el.get_text(separator="\n", strip=True) if body_el else "No Content Found"

            return {"id": article_id, "title": title, "category": category, "content": content}
            
        except requests.exceptions.Timeout:
            print(f"   Timeout on attempt {attempt + 1} for {url}. Retrying...")
            time.sleep(5)  # Wait 5 seconds before trying again
        except Exception as e:
            print(f"   Error scraping content at {url}: {e}")
            break 

    return None

def main():
    output_dir = "scraped_articles"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_list_url = "https://www.islamweb.net/ar/articles/138/السيرة-النبوية?pageno="
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    article_count = 0

    # CHANGED: range(6, 67) starts at page 6 and ends at page 66
    for page_num in range(13, 14):
        print(f"\n>>> Accessing List Page {page_num} <<<")
        page_url = f"{base_list_url}{page_num}"
        
        try:
            res = requests.get(page_url, headers=headers)
            res.encoding = 'utf-8'
            soup = BeautifulSoup(res.text, 'html.parser')
            
            items_container = soup.select_one('div.itemslist')
            if not items_container:
                print(f"   Warning: Could not find 'div.itemslist' on page {page_num}")
                continue
                
            links = items_container.find_all('a', href=re.compile(r'/ar/article/\d+/'))
            
            unique_links = []
            seen_hrefs = set()
            for l in links:
                h = l.get('href')
                if h not in seen_hrefs:
                    unique_links.append(h)
                    seen_hrefs.add(h)

            print(f"   Found {len(unique_links)} unique articles to scrape.")

            for href in unique_links:
                full_url = f"https://www.islamweb.net{href}"
                data = scrape_article_content(full_url)
                
                if data:
                    safe_category = sanitize_filename(data['category'])
                    filename = f"page{page_num}_{safe_category}_{data['id']}.txt"
                    filepath = os.path.join(output_dir, filename)

                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(f"Title: {data['title']}\n")
                        f.write(f"Category: {data['category']}\n")
                        f.write(f"URL: {full_url}\n")
                        f.write("-" * 50 + "\n")
                        f.write(data['content'])

                    article_count += 1
                    print(f"   [{article_count}] Saved: {filename}")
                
                time.sleep(0.7) 

        except Exception as e:
            print(f"   Failed to process page {page_num}: {e}")

    print(f"\nDone! Successfully saved {article_count} articles.")

if __name__ == "__main__":
    main()