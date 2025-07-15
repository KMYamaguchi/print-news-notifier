import feedparser
import requests
import datetime
from collections import Counter

TEAMS_WEBHOOK_URL = "https://prod-63.japaneast.logic.azure.com:443/workflows/bfdd5d1685c74b049bf9aa93d6999fcc/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=IQ-72ieqeQZSLi3yvnfx3ukfmZqrg2K4jIhX0Kd4_zM"  # あなたのTeams Webhook URL

RSS_FEEDS = {
    "PR TIMES 印刷": "https://prtimes.jp/topics/rss/keywords/印刷",
    "Konica Minolta": "https://www.konicaminolta.com/jp-ja/news/rss/news_release.rss"
}

INNOVATION_KEYWORDS = ["革新", "新技術", "AI", "自動化", "スマート", "DX", "デジタル", "IoT", "クラウド"]
PROMOTION_KEYWORDS = ["販促", "チラシ", "紙媒体", "印刷物", "POP", "DM", "パーソナライズ", "プロモーション"]
ACCURIO_KEYWORDS = ["Accurio", "Konica Minolta", "デジタル印刷", "プロダクションプリント", "印刷機", "印刷ソリューション"]

def evaluate_score(text, keywords):
    return min(5, sum(text.count(k) for k in keywords))

def send_to_teams(message):
    headers = {"Content-Type": "application/json"}
    payload = {"text": message}
    response = requests.post(TEAMS_WEBHOOK_URL, json=payload, headers=headers)
    return response.status_code == 200
today = datetime.datetime.now().date()
week_ago = today - datetime.timedelta(days=7)

entries = []
keyword_counter = Counter()
source_counter = Counter()

for source_name, feed_url in RSS_FEEDS.items():
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        if hasattr(entry, 'published_parsed'):
            published_date = datetime.date(*entry.published_parsed[:3])
        elif hasattr(entry, 'updated_parsed'):
            published_date = datetime.date(*entry.updated_parsed[:3])
        else:
            continue

        if week_ago <= published_date <= today:
            title = entry.title
            link = entry.link
            summary = entry.get("summary", "")
            content = title + " " + summary

            innovation_score = evaluate_score(content, INNOVATION_KEYWORDS)
            promotion_score = evaluate_score(content, PROMOTION_KEYWORDS)
            accurio_score = evaluate_score(content, ACCURIO_KEYWORDS)

            entries.append((title, link, innovation_score, promotion_score, accurio_score, source_name))
            keyword_counter.update([k for k in INNOVATION_KEYWORDS + PROMOTION_KEYWORDS + ACCURIO_KEYWORDS if k in content])
            source_counter[source_name] += 1

top_entries = sorted(entries, key=lambda x: (x[2] + x[3] + x[4]), reverse=True)[:5]

message = f"🗓️ 週次印刷業界ニュースまとめ（{week_ago}〜{today}）\n\n"
message += "📰 トップニュース:\n" + "\n".join([f"- {e[0]} ({e[1]})" for e in top_entries]) + "\n\n"
message += "📊 キーワード出現ランキング:\n" + "\n".join([f"- {k}: {v}件" for k, v in keyword_counter.most_common(5)]) + "\n\n"
message += "🏢 件数の多かった情報源:\n" + "\n".join([f"- {s}: {c}件" for s, c in source_counter.most_common()])

send_to_teams(message)
print("週次要約通知が完了しました。")
