from playwright.sync_api import sync_playwright
import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

api_responses = []

def handle_response(response):
    url = response.url
    if 'graphql' in url or 'ranking' in url:
        try:
            body = response.text()
            api_responses.append({'url': url, 'body': body[:5000]})
        except:
            pass

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        proxy={"server": "socks5://127.0.0.1:7890"},
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="ja-JP",
    )
    context.add_cookies([
        {"name": "age_check_done", "value": "1", "domain": ".dmm.co.jp", "path": "/"},
        {"name": "adult_check", "value": "done", "domain": ".dmm.co.jp", "path": "/"},
    ])

    page = context.new_page()
    page.on("response", handle_response)

    url = "https://video.dmm.co.jp/av/ranking/?term=monthly&type=actress"
    print(f"Loading: {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(8000)

    # Scroll to load content
    for _ in range(3):
        page.evaluate("window.scrollBy(0, 800)")
        page.wait_for_timeout(1500)

    # Save screenshot
    page.screenshot(path="actress_ranking.png", full_page=True)
    print("Saved screenshot: actress_ranking.png")

    # Check content
    content = page.content()
    print(f"Page content length: {len(content)}")

    # Save HTML
    with open("actress_ranking.html", "w", encoding="utf-8") as f:
        f.write(content)

    # Check API responses
    print(f"\nCaptured {len(api_responses)} API responses:")
    for r in api_responses:
        if 'graphql' in r['url']:
            print(f"\n--- GraphQL: {r['url'][:80]} ---")
            print(r['body'][:2000])

    browser.close()
