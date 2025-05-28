# markdown.py

import asyncio
from typing import List, Dict, Any
from api_management import get_supabase_client
from utils import generate_unique_name
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

supabase = get_supabase_client()

async def get_fit_markdown_async(url: str, timeout_settings: Dict[str, Any] = None) -> str:
    """
    Async function using crawl4ai's AsyncWebCrawler to produce the regular raw markdown.
    Now accepts timeout_settings to configure crawling behavior.
    """
    # Use default timeout settings if none provided
    if timeout_settings is None:
        from assets import TIMEOUT_SETTINGS
        timeout_settings = TIMEOUT_SETTINGS

    # Convert page_timeout from minutes to milliseconds for crawl4ai
    page_timeout_ms = int(timeout_settings.get("page_timeout", 2.0) * 60 * 1000)

    # Create crawler run config with timeout settings
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=page_timeout_ms,
        delay_before_return_html=float(timeout_settings.get("delay_before_return_html", 0.1)),
        scroll_delay=float(timeout_settings.get("scroll_delay", 0.2)),
        mean_delay=float(timeout_settings.get("mean_delay", 0.1)),
        max_range=float(timeout_settings.get("max_range", 0.3)),
    )

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if result.success:
            return result.markdown
        else:
            return ""


def fetch_fit_markdown(url: str, timeout_settings: Dict[str, Any] = None) -> str:
    """
    Synchronous wrapper around get_fit_markdown_async().
    Now accepts timeout_settings to pass to the async function.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(get_fit_markdown_async(url, timeout_settings))
    finally:
        loop.close()

def read_raw_data(unique_name: str) -> dict:
    """
    Query the 'scraped_data' table for the row with this unique_name,
    and return a dictionary containing 'raw_data' and 'url' fields.
    """
    response = supabase.table("scraped_data").select("raw_data,url").eq("unique_name", unique_name).execute()
    data = response.data
    if data and len(data) > 0:
        return {
            "content": data[0]["raw_data"],
            "url": data[0].get("url", "")
        }
    return {
        "content": "",
        "url": ""
    }

def save_raw_data(unique_name: str, url: str, raw_data: str) -> None:
    """
    Save or update the row in supabase with unique_name, url, and raw_data.
    If a row with unique_name doesn't exist, it inserts; otherwise it might upsert.
    """
    supabase.table("scraped_data").upsert({
        "unique_name": unique_name,
        "url": url,
        "raw_data": raw_data
    }, on_conflict="id").execute()
    BLUE = "\033[34m"
    RESET = "\033[0m"
    print(f"{BLUE}INFO:Raw data stored for {unique_name}{RESET}")

def fetch_and_store_markdowns(urls: List[str], timeout_settings: Dict[str, Any] = None) -> List[str]:
    """
    For each URL:
      1) Generate unique_name
      2) Check if there's already a row in supabase with that unique_name
      3) If not found or if raw_data is empty, fetch fit_markdown
      4) Save to supabase
    Return a list of unique_names (one per URL).
    Now accepts timeout_settings to configure crawling behavior.
    """
    unique_names = []

    for url in urls:
        unique_name = generate_unique_name(url)
        MAGENTA = "\033[35m"
        RESET = "\033[0m"
        # check if we already have raw_data in supabase
        raw_data = read_raw_data(unique_name)
        if raw_data and raw_data.get("content"):  # Check if there's actual content
            print(f"{MAGENTA}Found existing data in supabase for {url} => {unique_name}{RESET}")
        else:
            # fetch fit markdown with timeout settings
            fit_md = fetch_fit_markdown(url, timeout_settings)
            print(fit_md)
            save_raw_data(unique_name, url, fit_md)
        unique_names.append(unique_name)

    return unique_names
