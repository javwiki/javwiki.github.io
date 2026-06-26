import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

url = "https://api.video.dmm.co.jp/graphql"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Content-Type": "application/json",
    "Origin": "https://video.dmm.co.jp",
    "Referer": "https://video.dmm.co.jp/av/ranking/?term=monthly",
}

# Try introspection to find available queries
introspection_query = {
    "query": """
    {
        __schema {
            queryType {
                fields {
                    name
                    description
                }
            }
        }
    }
    """
}

print("=== Introspection ===")
resp = requests.post(url, json=introspection_query, headers=headers, timeout=15)
print(f"Status: {resp.status_code}")
if resp.ok:
    data = resp.json()
    if 'data' in data and data['data']:
        fields = data['data']['__schema']['queryType']['fields']
        print(f"\nAvailable queries ({len(fields)}):")
        for field in fields:
            print(f"  - {field['name']}: {field.get('description', 'No description')}")
