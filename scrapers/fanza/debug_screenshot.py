from playwright.sync_api import sync_playwright
import sys

# Set stdout encoding to utf-8
sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        proxy={"server": "socks5://127.0.0.1:7890"},
    )
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        locale="ja-JP",
        viewport={"width": 1920, "height": 1080},
    )
    context.add_cookies([
        {"name": "age_check_done", "value": "1", "domain": ".dmm.co.jp", "path": "/"},
        {"name": "adult_check", "value": "done", "domain": ".dmm.co.jp", "path": "/"},
    ])
    
    page = context.new_page()
    
    url = "https://www.dmm.co.jp/digital/videoa/-/ranking/"
    print(f"Loading: {url}")
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(8000)
    
    # Scroll down multiple times to trigger lazy loading
    for _ in range(5):
        page.evaluate("window.scrollBy(0, 500)")
        page.wait_for_timeout(1000)
    
    page.screenshot(path="debug_ranking.png", full_page=True)
    print("Saved screenshot: debug_ranking.png")
    
    # Check for ranking content
    content = page.content()
    if "/cid/" in content:
        print("Found /cid/ links in content!")
        # Count them
        import re
        cids = re.findall(r'/cid/(\w+)', content)
        print(f"Found {len(cids)} CID references")
    else:
        print("No /cid/ links found")
        # Look for any useful content
        print(f"Content length: {len(content)}")
        # Save for inspection
        with open("debug_full.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("Saved full HTML to debug_full.html")
    
    browser.close()
