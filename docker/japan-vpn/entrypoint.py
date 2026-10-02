"""Build a Japan-only configuration without importing subscription routing rules."""

import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml


def build_config(subscription, secret, pattern):
    if not isinstance(subscription, dict):
        raise ValueError("订阅必须是 Clash / Mihomo YAML 配置")
    matcher = re.compile(pattern)
    nodes = subscription.get("proxies")
    if not isinstance(nodes, list):
        raise ValueError("订阅必须包含 proxies 节点列表；不支持 Base64 或仅 proxy-providers 的订阅")
    selected = [
        node for node in nodes
        if isinstance(node, dict)
        and isinstance(node.get("name"), str)
        and matcher.search(node["name"])
        and node.get("type") not in ("direct", "reject", "compatible", "pass")
    ]
    if not selected:
        raise ValueError("没有匹配的日本节点，请检查订阅与 JAPAN_FILTER")
    names = [node["name"] for node in selected]
    if len(names) != len(set(names)) or set(names) & {"JAPAN", "JAPAN-AUTO", "DIRECT", "REJECT", "GLOBAL"}:
        raise ValueError("日本节点名称重复或与内置策略组重名")
    # Dependencies outside the selected nodes cannot be resolved safely here.
    if any(node.get("dialer-proxy") or node.get("type") in ("relay", "url-test", "select") for node in selected):
        raise ValueError("不支持依赖其他策略组的日本节点，请使用独立节点订阅")
    return {
        "mixed-port": 7890,
        "allow-lan": True,
        "bind-address": "0.0.0.0",
        "mode": "rule",
        "log-level": "warning",
        "ipv6": False,
        "external-controller": "0.0.0.0:9090",
        "external-ui": "/opt/dashboard",
        "secret": secret,
        "profile": {"store-selected": False},
        "proxies": selected,
        "proxy-groups": [
            {"name": "JAPAN", "type": "select", "proxies": ["JAPAN-AUTO", *names]},
            {"name": "JAPAN-AUTO", "type": "url-test", "proxies": names,
             "url": "https://www.gstatic.com/generate_204", "interval": 300, "tolerance": 50},
        ],
        "rules": ["MATCH,JAPAN"],
    }


def main():
    secret = os.environ.get("CLASH_CONTROLLER_SECRET", "")
    if len(secret) < 24 or secret == "replace-with-a-random-secret":
        raise ValueError("请设置至少 24 字符的随机 CLASH_CONTROLLER_SECRET")
    url = os.environ.get("CLASH_SUBSCRIPTION_URL", "")
    if not url.startswith("https://") or "your-provider.example" in url:
        raise ValueError("请设置真实的 HTTPS Clash / Mihomo 订阅地址")
    request = urllib.request.Request(url, headers={"User-Agent": "mihomo/1.19.23"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(10 * 1024 * 1024 + 1)
    if len(data) > 10 * 1024 * 1024:
        raise ValueError("订阅超过 10 MiB 限制")
    config = build_config(yaml.safe_load(data), secret, os.environ.get(
        "JAPAN_FILTER", r"(?i)(日本|Japan|Tokyo|Osaka|东京|東京|大阪|🇯🇵|\bJP\b)"
    ))
    os.umask(0o077)
    config_path = Path("/data/config.yaml")
    config_path.write_text(yaml.safe_dump(config, allow_unicode=True), encoding="utf-8")
    args = ["mihomo", "-d", "/data", "-f", str(config_path)]
    subprocess.run([*args, "-t"], check=True)
    print(f"已载入 {len(config['proxies'])} 个日本节点", flush=True)
    os.execvp(args[0], args)


if __name__ == "__main__":
    try:
        main()
    except ValueError as error:
        # Parser errors can contain subscription fragments: never print them.
        print(f"配置错误：{error}", file=sys.stderr)
        sys.exit(1)
    except Exception as error:
        # Network errors may contain the private subscription URL.
        print(f"启动失败（{type(error).__name__}）；请检查订阅、网络和配置", file=sys.stderr)
        sys.exit(1)
