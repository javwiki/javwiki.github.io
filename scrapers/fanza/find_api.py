from playwright.sync_api import sync_playwright
import sys

sys.stdout.reconfigure(encoding='utf-8')

api_calls = []

def handle_response(response):
    url = response.url
    if any(kw in url for kw in ['api', 'ranking', 'item', 'product']):
        api_calls.append(url)

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        proxy={"server": "socks5://127.0.0.1:7890"},
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        locale="ja-JP",
    )
    context.add_cookies([
        {"name": "age_check_done", "value": "1", "domain": ".dmm.co.jp", "path": "/"},
        {"name": "adult_check", "value": "done", "domain": ".dmm.co.jp", "path": "/"},
    ])
    
    page = context.new_page()
    page.on("response", handle_response)
    
    url = "https://www.dmm.co.jp/digital/videoa/-/ranking/"
    print(f"Loading: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(10000)
    
    print(f"\nFound {len(api_calls)} API calls:")
    for call in api_calls:
        print(f"  {call[:150]}")
    
    browser.close()
