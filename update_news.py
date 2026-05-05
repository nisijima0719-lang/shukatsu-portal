#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
終活ナビ ニュース自動更新スクリプト
毎週実行し、終活関連の最新ニュースをAIで生成してindex.htmlに反映する
"""

import os
import re
import json
import sys
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "index.html")
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")

FALLBACK_CONFIG = os.path.join(SCRIPT_DIR, "..", "blog_auto", "config.json")
for path in [CONFIG_PATH, FALLBACK_CONFIG]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        ANTHROPIC_API_KEY = config.get("anthropic_api_key", "")
        if ANTHROPIC_API_KEY:
            break
    except FileNotFoundError:
        pass
else:
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

if not ANTHROPIC_API_KEY:
    print("❌ anthropic_api_keyが設定されていません")
    sys.exit(1)


def generate_news_html():
    """Claude APIで今週の終活ニュースHTMLを生成"""
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    today = datetime.now().strftime("%Y年%m月%d日")

    prompt = f"""今日は{today}です。
終活ポータルサイトの「最新ニュース」セクション用に、以下の3つのニュースカードのHTMLを生成してください。

条件：
- 終活・相続・デジタル終活・死後事務・高齢者支援・遺言・介護に関連する最新トピック
- 実在する制度・法律・社会問題に基づいた信頼性の高い内容
- 1件目：制度・法律系（タグ: 🏛️ 新制度 または ⚖️ 法制度）
- 2件目：デジタル・テクノロジー系（タグ: 📱 デジタル）
- 3件目：生活・実用系（タグ: 💡 実用情報 または 🏠 生活）
- 各カードは150字程度で簡潔に

以下のHTML形式で3件分を出力してください（マークダウン不要、HTMLのみ）:

<div class="news-card">
  <div class="news-card-header">
    <div class="news-tag">🏛️ 新制度</div>
    <h3>タイトル</h3>
  </div>
  <div class="news-card-body">
    <p>本文</p>
    <div class="news-date">📅 {today}更新</div>
    <div class="news-source"><a href="出典URL" target="_blank" rel="noopener">📎 出典：出典名 →</a></div>
  </div>
</div>

<div class="news-card">
  ...（2件目）
</div>

<div class="news-card">
  ...（3件目）
</div>

出典URLは厚生労働省・法務省・国税庁・内閣府など実在する日本の公的機関の公式サイトのURLを使用してください。"""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()


def generate_tips_html():
    """Claude APIで今週の豆知識6件HTMLを生成"""
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    today = datetime.now().strftime("%Y年%m月%d日")

    prompt = f"""終活・相続・デジタル終活・死後事務に関する役立つ豆知識を6件、HTMLで生成してください。
今日は{today}です。

以下のHTML形式で6件分出力してください（マークダウン不要、HTMLのみ）：

<div class="knowledge-card">
  <div class="k-icon">🏛️</div>
  <h4>タイトル（15字以内）</h4>
  <p>説明（60字程度）</p>
</div>

絵文字は内容に合ったものを使ってください（🏛️🔑📜💰🏠🩺👥📱💳☁️📮💸など）"""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text.strip()


def update_html(news_html: str, tips_html: str):
    """index.htmlのニュースグリッドと豆知識グリッドを更新"""
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # ニュースグリッド（<div class="news-grid">〜</div>）を置換
    news_pattern = re.compile(
        r'(<div class="news-grid">)\s*(.*?)\s*(</div>)',
        re.DOTALL
    )
    new_news_block = f'<div class="news-grid">\n      {news_html}\n    </div>'
    content, n1 = news_pattern.subn(new_news_block, content, count=1)
    if n1 == 0:
        print("⚠️  news-gridが見つかりませんでした")

    # 豆知識グリッド（<div class="knowledge-grid">〜</div>）を置換
    tips_pattern = re.compile(
        r'(<div class="knowledge-grid">)\s*(.*?)\s*(</div>)',
        re.DOTALL
    )
    new_tips_block = f'<div class="knowledge-grid">\n      {tips_html}\n    </div>'
    content, n2 = tips_pattern.subn(new_tips_block, content, count=1)
    if n2 == 0:
        print("⚠️  knowledge-gridが見つかりませんでした")

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ HTML更新完了（ニュース:{n1}件, 豆知識:{n2}件）")


def main():
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"🔄 終活ナビ ニュース更新開始 [{today}]")

    print("📰 ニュース生成中...")
    news_html = generate_news_html()
    print(f"  生成完了（{len(news_html)}文字）")

    print("💡 豆知識生成中...")
    tips_html = generate_tips_html()
    print(f"  生成完了（{len(tips_html)}文字）")

    print("📝 HTMLファイル更新中...")
    update_html(news_html, tips_html)

    print("✅ 完了！")


if __name__ == "__main__":
    main()
