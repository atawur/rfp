from playwright.sync_api import sync_playwright
import httpx
import logging

logger = logging.getLogger(__name__)

class PlaywrightCrawler:
    def fetch_page_content(self, url: str) -> str:
        """
        Uses Playwright to fetch a page, executing JS and returning the rendered HTML.
        Falls back to HTTPX if browser execution fails.
        """
        logger.info(f"Fetching page content for: {url}")
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=15000)
                content = page.content()
                browser.close()
                if content and len(content) > 100:
                    return content
        except Exception as e:
            logger.warning(f"Playwright crawling timed out or failed for {url}: {str(e)}. Falling back to HTTPX.")

        # HTTPX Fallback
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
            with httpx.Client(timeout=15.0, follow_redirects=True, verify=False) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.text
                else:
                    logger.warning(f"HTTPX fallback returned status code {resp.status_code} for {url}")
        except Exception as http_err:
            logger.error(f"HTTPX fallback also failed for {url}: {str(http_err)}")

        return ""

playwright_crawler = PlaywrightCrawler()

