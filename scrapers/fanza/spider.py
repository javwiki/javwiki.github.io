"""
FANZA Actress Monthly Ranking Spider
通过 Playwright 抓取 FANZA 女优月度销量排名
"""

from playwright.sync_api import sync_playwright
import yaml
import json
from datetime import datetime
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding='utf-8')


class FanzaActressRankingSpider:
    """FANZA 女优月度排名爬虫"""

    URL = "https://video.dmm.co.jp/av/ranking/?term=monthly&type=actress"

    def __init__(self, output_dir: str = "../../src/_meta/rankings", proxy: str = "socks5://127.0.0.1:7890"):
        self.output_dir = Path(__file__).parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.proxy = proxy

    def fetch_ranking(self, limit: int = 100) -> list[dict]:
        """
        爬取女优月度排名

        Args:
            limit: 获取数量

        Returns:
            排名数据列表
        """
        print(f"Loading: {self.URL}")

        ranking_data = []

        def handle_response(response):
            nonlocal ranking_data
            if 'graphql' in response.url:
                try:
                    body = response.json()
                    data = body.get('data', {})
                    items = data.get('ppvActressRanking', {}).get('items', [])
                    if items:
                        ranking_data = items
                        print(f"Captured {len(items)} items from GraphQL API")
                except:
                    pass

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                proxy={"server": self.proxy} if self.proxy else None,
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

            try:
                page.goto(self.URL, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(10000)

                # Scroll to trigger more data loading
                for _ in range(5):
                    page.evaluate("window.scrollBy(0, 1000)")
                    page.wait_for_timeout(2000)

                page.wait_for_timeout(5000)

            except Exception as e:
                print(f"Error: {e}")
            finally:
                browser.close()

        return self.parse_items(ranking_data, limit)

    def parse_items(self, items: list[dict], limit: int) -> list[dict]:
        """
        解析排名数据

        Args:
            items: API 返回的条目列表
            limit: 最大条目数

        Returns:
            解析后的排名数据
        """
        rankings = []

        for item in items[:limit]:
            actress = item.get('actress', {})
            latest = actress.get('latestContent', {})

            rankings.append({
                "rank": item.get("rank"),
                "actress_id": actress.get("id"),
                "name": actress.get("name"),
                "image": actress.get("imageUrl"),
                "contents_count": actress.get("contentsCountOnSale"),
                "latest_content_id": latest.get("id"),
                "latest_title": latest.get("title"),
            })

        return rankings

    def save_yaml(self, data: list[dict], filename: str = None) -> Path:
        """
        保存为 YAML 文件

        Args:
            data: 排名数据
            filename: 文件名

        Returns:
            保存路径
        """
        if not filename:
            now = datetime.now()
            filename = f"actress-ranking-{now.strftime('%Y%m')}.yaml"

        filepath = self.output_dir / filename

        output = {
            "source": "FANZA",
            "type": "actress_monthly_ranking",
            "url": self.URL,
            "fetched_at": datetime.now().isoformat(),
            "count": len(data),
            "rankings": data,
        }

        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(output, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

        print(f"Saved {len(data)} entries to {filepath}")
        return filepath

    def run(self, limit: int = 100) -> Path:
        """
        执行爬取任务

        Args:
            limit: 获取数量

        Returns:
            保存路径
        """
        print(f"Fetching FANZA actress ranking (top {limit})...")

        data = self.fetch_ranking(limit)

        if not data:
            print("No data fetched")
            return None

        # Print top 10
        print("\nTop 10:")
        for item in data[:10]:
            print(f"  {item['rank']:3d}. {item['name']} ({item['contents_count']} contents)")

        return self.save_yaml(data)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="FANZA Actress Ranking Spider")
    parser.add_argument("--limit", type=int, default=100, help="Number of results (default: 100)")
    parser.add_argument("--output", type=str, default="../../src/_meta/rankings", help="Output directory")
    parser.add_argument("--proxy", type=str, default="socks5://127.0.0.1:7890", help="Proxy server")

    args = parser.parse_args()

    spider = FanzaActressRankingSpider(output_dir=args.output, proxy=args.proxy)
    result = spider.run(args.limit)

    if result:
        print(f"\nDone! Saved to {result}")
    else:
        print("\nFailed to fetch ranking")
        exit(1)


if __name__ == "__main__":
    main()
