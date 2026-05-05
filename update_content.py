#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
終活ナビ トップページ コンテンツ月次更新スクリプト
民間サービス情報・制度情報など静的コンテンツを見直して差し替える
"""

import os
import re
import json
import sys
from datetime import datetime

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


def read_html():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()


def extract_section(content, section_id):
    pattern = re.compile(
        rf'(<section id="{section_id}">)(.*?)(</section>)',
        re.DOTALL
    )
    m = pattern.search(content)
    return m.group(2) if m else ""


def update_section(content, section_id, new_inner):
    pattern = re.compile(
        rf'(<section id="{section_id}">)(.*?)(</section>)',
        re.DOTALL
    )
    return pattern.sub(rf'\1{new_inner}\3', content, count=1)


def generate_services_html(current_html):
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    today = datetime.now().strftime("%Y年%m月")

    prompt = f"""今は{today}です。
終活ポータルサイトの「民間サービス情報」セクションのHTMLを見直し、古い情報があれば最新の情報に差し替えてください。

現在のHTML：
{current_html}

条件：
- 銀行・信託・葬儀・法律・総合の各カテゴリを維持すること
- サービス名・URL・説明文が実在する最新のものであること
- 廃止・変更されたサービスがあれば別の実在するサービスに差し替えること
- 追加で有用なサービスがあれば1〜2件追加してもよい（最大8件）
- HTMLの構造（service-card・service-tag・service-footer等のclass名）は変えないこと
- マークダウン不要、HTMLのみ出力すること
- <section>タグは含めず、<div class="container">から始めること"""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


def generate_honnin_html(current_html):
    from anthropic import Anthropic
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    today = datetime.now().strftime("%Y年%m月")

    prompt = f"""今は{today}です。
終活ポータルサイトの「本人向け情報」セクションのHTMLを見直してください。

現在のHTML：
{current_html}

確認・更新してほしい点：
- 相続税申告期限・相続放棄期限などの法律上の期限が正確か
- 法務局の遺言書保管制度の手数料（3,900円）が現行のままか
- 公的機関へのリンクURLが有効か（厚労省・法務省・国税庁・裁判所）
- 制度名・条文に古い情報があれば最新に更新する
- 内容が古くなければそのまま返してよい

HTMLのみ出力。<section>タグは含めず<div class="container">から始めること。"""

    message = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=3000,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()


def main():
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"🔄 終活ナビ コンテンツ月次更新開始 [{today}]")

    content = read_html()

    print("🏦 民間サービスセクション更新中...")
    services_inner = extract_section(content, "services")
    new_services = generate_services_html(services_inner)
    content = update_section(content, "services", "\n" + new_services + "\n  ")
    print("  完了")

    print("📋 本人向けセクション確認中...")
    honnin_inner = extract_section(content, "honnin")
    new_honnin = generate_honnin_html(honnin_inner)
    content = update_section(content, "honnin", "\n" + new_honnin + "\n  ")
    print("  完了")

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ 月次コンテンツ更新完了！")


if __name__ == "__main__":
    main()
