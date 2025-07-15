import feedparser
import requests
import datetime

# ✅ 指定されたWebhook URL
TEAMS_WEBHOOK_URL = "https://prod-63.japaneast.logic.azure.com:443/workflows/bfdd5d1685c74b049bf9aa93d6999fcc/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=IQ-72ieqeQZSLi3yvnfx3ukfmZqrg2K4jIhX0Kd4_zM"

RSS_FEEDS = {
    "PR TIMES 印刷": "https://prtimes.jp/topics/rss/keywords/印刷",
    "Konica Minolta": "https://www.konicaminolta.com/jp-ja/news/rss/news_release.rss"
}

INNOVATION_KEYWORDS = ["革新", "新技術", "AI", "自動化", "スマート", "DX", "デジタル", "IoT", "クラウド"]
PROMOTION_KEYWORDS = ["販促", "チラシ", "紙媒体", "印刷物", "POP", "DM", "パーソナライズ", "プロモーション"]
ACCURIO_KEYWORDS = ["Accurio", "Konica Minolta", "デジタル印刷", "プロダクションプリント", "印刷機", "印刷ソリューション"]

def evaluate_score(text, keywords):
    return min(5, sum(text.count(k) for k in keywords))

def format_stars(score):
    return "★" * score + "☆" * (5 - score)

def generate_summary(title, summary):
    content = title + " " + summary
    sentences = content.replace("。", ".").split(".")
    filtered = [s for s in sentences if any(k in s for k in INNOVATION_KEYWORDS + PROMOTION_KEYWORDS)]
    result = "。".join(filtered) + "。" if filtered else summary
    return result[:300]

def send_to_teams(message):
    headers = {"Content-Type": "application/json"}
    payload = {"text": message}
    response = requests.post(TEAMS_WEBHOOK_URL, json=payload, headers=headers)
    return response.status_code == 200

today = datetime.datetime.now().date()
entries = []
failed_feeds = []

for source_name, feed_url in RSS_FEEDS.items():
    feed = feedparser.parse(feed_url)

    # ✅ RSS取得エラーの検知
    if feed.bozo:
        failed_feeds.append(f"{source_name}（解析エラー）")
        continue

    if hasattr(feed, 'status') and feed.status != 200:
        failed_feeds.append(f"{source_name}（HTTP {feed.status}）")
        continue

    for entry in feed.entries:
        if hasattr(entry, 'published_parsed'):
            published_date = datetime.date(*entry.published_parsed[:3])
        elif hasattr(entry, 'updated_parsed'):
            published_date = datetime.date(*entry.updated_parsed[:3])
        else:
            continue
        if published_date == today:
            title = entry.title
            link = entry.link
            summary = entry.get("summary", "")
            content = title + " " + summary
            innovation_score = evaluate_score(content, INNOVATION_KEYWORDS)
            promotion_score = evaluate_score(content, PROMOTION_KEYWORDS)
            accurio_score = evaluate_score(content, ACCURIO_KEYWORDS)
            total_score = innovation_score + promotion_score + accurio_score
            copilot_summary = generate_summary(title, summary)
            message = (
                f"📰 **{title}**\n"
                f"🔗 {link}\n"
                f"🧠 革新性: {format_stars(innovation_score)}\n"
                f"📢 販促関連度: {format_stars(promotion_score)}\n"
                f"⭐ AccurioDX関連度: {format_stars(accurio_score)}\n"
                f"🚀 情報源: {source_name}\n"
                f"📝 要約: {copilot_summary}\n"
                f"\n---\n"
            )
            entries.append((total_score, message))

# ✅ スコア順に並べて上位10件のみ通知
entries.sort(reverse=True)
top_messages = [m for _, m in entries[:10]]

# ✅ 通知処理
if top_messages:
    full_message = f"🗞️ 本日の印刷業界ニュース（{today.strftime('%Y-%m-%d')}）\n\n" + "\n".join(top_messages)
    send_to_teams(full_message)
else:
    send_to_teams("本日公開された印刷関連の新着ニュースはありません。")

# ✅ RSS取得失敗の通知
if failed_feeds:
    error_message = "⚠️ 以下のRSSフィードの取得に失敗しました：\n" + "\n".join(f"- {f}" for f in failed_feeds)
    send_to_teams(error_message)

print("通知処理が完了しました。")
