# -*- coding: utf-8 -*-
"""
スクショ用レポート生成ツール
視覚的に魅力的な結果を表示します
"""

import pandas as pd
import glob
import sys


def generate_screenshot_report():
    """スクショ用の見栄えの良いレポートを生成"""

    # 最新のCSVを取得
    csv_files = glob.glob('output/integrated_ads_report_*.csv')

    if not csv_files:
        print("エラー: 結果ファイルが見つかりません")
        return

    latest = max(csv_files)
    df = pd.read_csv(latest)

    # ヘッダー
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "🏥 全国病院Google広告使用状況調査" + " " * 10 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    # 基本統計
    total = len(df)
    ads_yes = len(df[df['総合判定（Google広告使用）'] == 'あり'])
    ads_no = total - ads_yes

    print("📊 調査概要")
    print("─" * 60)
    print("  調査病院数: {}件".format(total))
    print("  調査方法: Webサイト検出 + Google広告透明性センター検証".format())
    print()

    # メイン結果
    print("🎯 調査結果")
    print("─" * 60)
    print()
    print("  ✅ Google広告使用:  {}件  ({:.1f}%)".format(ads_yes, ads_yes/total*100))
    print("  ❌ Google広告未使用: {}件  ({:.1f}%)".format(ads_no, ads_no/total*100))
    print()

    # 検出状況の内訳
    print("🔍 検出方法別の内訳")
    print("─" * 60)

    status_counts = df['検出状況'].value_counts()
    status_map = {
        '両方で検出': '📱 Webサイト + 透明性センター',
        '透明性センターのみ': '🏢 透明性センターのみ',
        'Webサイトのみ': '🌐 Webサイトのみ',
        '両方で未検出': '⭕ 未検出'
    }

    for status in ['両方で検出', '透明性センターのみ', 'Webサイトのみ', '両方で未検出']:
        if status in status_counts.index:
            count = status_counts[status]
            display = status_map.get(status, status)
            print("  {}: {}件".format(display, count))
    print()

    # 広告使用病院のトップ10
    if ads_yes > 0:
        print("📋 Google広告使用病院（一部抜粋）")
        print("─" * 60)

        ads_hospitals = df[df['総合判定（Google広告使用）'] == 'あり'].head(10)

        for idx, (_, row) in enumerate(ads_hospitals.iterrows(), 1):
            name = row['病院名']
            status = row['検出状況']

            # 病院名を短縮（30文字まで）
            if len(name) > 30:
                name = name[:27] + "..."

            print("  {}. {}".format(idx, name))
            print("     └─ {}".format(status))

        print()

    # フッター
    print("─" * 60)
    print("詳細結果: {}".format(latest))
    print()
    print("✨ 統合検証により高精度な結果を実現")
    print()


if __name__ == '__main__':
    generate_screenshot_report()
