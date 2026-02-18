import json
import subprocess
import os
from datetime import datetime, timezone, timedelta
from email.utils import formatdate
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# ====== 网站配置（请修改为您的实际信息）======
SITE_TITLE = "游戏合集"
SITE_URL = "https://jzygame.dpdns.org"  # GitHub Pages 地址
SITE_DESCRIPTION = "独立游戏集合"
RSS_FILE = "rss.xml"
DATA_FILE = "games.json"  # 位于根目录
# =========================================

# 东八区时区
tz = timezone(timedelta(hours=8), "CST")

def get_file_last_commit_time(file_path):
    """通过 git 获取文件的最后提交时间戳（UTC），返回 datetime 对象"""
    try:
        # 获取 Unix 时间戳（UTC）
        timestamp = subprocess.check_output(
            ["git", "log", "-1", "--format=%ct", "--", file_path],
            universal_newlines=True,
            stderr=subprocess.DEVNULL
        ).strip()
        if not timestamp:
            # 如果文件从未提交（理论上不会发生），返回当前时间
            return datetime.now(tz)
        # 转换为 datetime（UTC）
        dt_utc = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
        # 转换为东八区
        return dt_utc.astimezone(tz)
    except subprocess.CalledProcessError:
        # 如果 git 命令失败（例如文件不存在），返回当前时间
        return datetime.now(tz)

def format_rfc822(dt):
    """将 datetime 转换为 RSS 所需的 RFC 822 格式，并包含时区"""
    # formatdate 默认生成 UTC 时间，需要先转换为 UTC 再调用
    dt_utc = dt.astimezone(timezone.utc)
    return formatdate(dt_utc.timestamp(), usegmt=True)

def generate_rss(games_with_time):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = SITE_TITLE
    SubElement(channel, "link").text = SITE_URL
    SubElement(channel, "description").text = SITE_DESCRIPTION
    SubElement(channel, "language").text = "zh-cn"
    SubElement(channel, "lastBuildDate").text = format_rfc822(datetime.now(tz))

    # 按时间倒序排列（最新的在前）
    for game in sorted(games_with_time, key=lambda x: x["time"], reverse=True):
        item = SubElement(channel, "item")
        SubElement(item, "title").text = game["title"]
        # 构建游戏完整 URL
        game_url = SITE_URL.rstrip("/") + "/" + game["file"].lstrip("/")
        SubElement(item, "link").text = game_url
        SubElement(item, "description").text = game.get("description", "")
        SubElement(item, "pubDate").text = format_rfc822(game["time"])
        # GUID 与链接相同
        SubElement(item, "guid", isPermaLink="true").text = game_url

    rough_string = tostring(rss, encoding="utf-8")
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding="utf-8")

def main():
    # 读取 games.json
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    games = data["games"]

    # 为每个游戏获取最后提交时间
    games_with_time = []
    for game in games:
        file_path = game["file"]
        commit_time = get_file_last_commit_time(file_path)
        games_with_time.append({
            "title": game["title"],
            "file": game["file"],
            "description": game.get("description", ""),
            "time": commit_time
        })

    rss_content = generate_rss(games_with_time)
    with open(RSS_FILE, "wb") as f:
        f.write(rss_content)

    print(f"✅ RSS 已生成，包含 {len(games_with_time)} 个游戏")
    print("最新游戏：", games_with_time[0]["title"] if games_with_time else "无")

if __name__ == "__main__":
    main()