#!/usr/bin/env python3
"""
桃吉屋 · 每日简报采集脚本
运行: python3 fetch_daily_brief.py
输出: brief.json (页面自动读取)
"""

import json
import time
import urllib.request
import urllib.error
import ssl
from datetime import date
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

OUTPUT = Path(__file__).parent / "brief.json"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


def get(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        return None


def get_json(url, timeout=10):
    raw = get(url, timeout)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def fetch_bilibili():
    """B站热门视频"""
    data = get_json("https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all")
    if not data:
        return []
    items = []
    for v in data.get("data", {}).get("list", [])[:15]:
        items.append({
            "title": v.get("title", ""),
            "url": f"https://www.bilibili.com/video/{v.get('bvid','')}",
            "hot": f"{v.get('stat',{}).get('view',0):,}播放"
        })
    return items


def fetch_zhihu():
    """知乎热榜 — 使用第三方公开接口"""
    # Try tenapi
    raw = get("https://tenapi.cn/v2/zhihuhot", 8)
    if raw:
        try:
            data = json.loads(raw)
            items = []
            for item in data.get("data", [])[:15]:
                items.append({
                    "title": item.get("name", ""),
                    "url": item.get("url", item.get("link", "")),
                })
            if items:
                return items
        except json.JSONDecodeError:
            pass

    # Fallback: use V2EX as alternative
    return []


def fetch_weibo():
    """微博热搜 — 使用第三方公开接口"""
    raw = get("https://tenapi.cn/v2/weibohot", 8)
    if raw:
        try:
            data = json.loads(raw)
            items = []
            for item in data.get("data", [])[:20]:
                items.append({
                    "title": item.get("name", ""),
                    "url": f"https://s.weibo.com/weibo?q={urllib.parse.quote(item.get('name',''))}",
                })
            if items:
                return items
        except json.JSONDecodeError:
            pass

    return []


def fetch_hackernews():
    """HackerNews 热门"""
    ids = get_json("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not ids:
        return []
    items = []
    for nid in ids[:12]:
        item = get_json(f"https://hacker-news.firebaseio.com/v0/item/{nid}.json")
        if item and item.get("title"):
            items.append({
                "title": item["title"],
                "url": item.get("url", f"https://news.ycombinator.com/item?id={nid}"),
            })
    return items


def main():
    today = date.today().isoformat()
    print(f"📰 桃吉屋每日简报 · {today}")
    print("=" * 40)

    bilibili = fetch_bilibili()
    print(f"✅ B站热门: {len(bilibili)} 条")

    zhihu = fetch_zhihu()
    print(f"💡 知乎热榜: {len(zhihu)} 条")

    weibo = fetch_weibo()
    print(f"🔥 微博热搜: {len(weibo)} 条")

    hn = fetch_hackernews()
    print(f"🌍 HackerNews: {len(hn)} 条")

    sources = [
        {"name": "知乎热榜", "icon": "💡", "items": zhihu},
        {"name": "微博热搜", "icon": "🔥", "items": weibo},
        {"name": "B站热门", "icon": "📺", "items": bilibili},
    ]
    if hn:
        sources.append({"name": "HackerNews", "icon": "🌍", "items": hn})

    brief = {
        "date": today,
        "updatedAt": time.strftime("%H:%M"),
        "items": sources,
    }

    OUTPUT.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

    total = len(zhihu) + len(weibo) + len(bilibili) + len(hn)
    print(f"\n📁 已保存: {OUTPUT}")
    print(f"📊 总计: {total} 条热点")

    if total == 0:
        print("\n⚠️ 提示: 部分国内API受限，可安装 OpenCLI 浏览器扩展后通过 AutoCLI 获取完整数据:")
        print("   autocli zhihu hot -f json >> brief.json")


if __name__ == "__main__":
    main()
