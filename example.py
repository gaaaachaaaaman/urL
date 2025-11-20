#!/usr/bin/env python3
"""
使用例スクリプト

このスクリプトは、ツールの基本的な使い方を示します。
"""

from hospital_fetcher import HospitalFetcher
from ads_detector import GoogleAdsDetector
import json


def example_basic():
    """基本的な使い方の例"""
    print("=" * 60)
    print("例1: 基本的な使い方")
    print("=" * 60)
    print()

    # 病院データを取得
    fetcher = HospitalFetcher()
    hospitals = fetcher.create_sample_data()

    print(f"取得した病院数: {len(hospitals)}")
    print()

    # Google広告検出器を初期化
    detector = GoogleAdsDetector(use_selenium=False)  # 高速モード

    # 最初の病院のみテスト
    hospital = hospitals[0]
    print(f"検査対象: {hospital['name']}")
    print(f"URL: {hospital['website']}")
    print()

    # Google広告を検出
    result = detector.detect(hospital['website'])

    print("検出結果:")
    print(f"  Google広告使用: {'あり' if result['has_google_ads'] else 'なし'}")
    print(f"  広告タイプ: {', '.join(result['ad_types']) if result['ad_types'] else 'なし'}")
    print()


def example_batch():
    """一括処理の例"""
    print("=" * 60)
    print("例2: 複数のURLを一括チェック")
    print("=" * 60)
    print()

    # テスト用URL
    urls = [
        "https://www.h.u-tokyo.ac.jp/",
        "https://www.ncc.go.jp/jp/ncch/",
        "https://hospital.luke.ac.jp/"
    ]

    # 検出器を初期化
    detector = GoogleAdsDetector(use_selenium=False)

    # 一括検出
    results = detector.batch_detect(urls)

    # 結果を表示
    for result in results:
        print(f"URL: {result['url']}")
        print(f"  Google広告: {'あり' if result['has_google_ads'] else 'なし'}")
        if result['ad_types']:
            print(f"  タイプ: {', '.join(result['ad_types'])}")
        if result['error']:
            print(f"  エラー: {result['error']}")
        print()


def example_custom():
    """カスタマイズの例"""
    print("=" * 60)
    print("例3: カスタムパターンでの検出")
    print("=" * 60)
    print()

    # 検出器を初期化
    detector = GoogleAdsDetector(use_selenium=False)

    # カスタムパターンを追加
    detector.ad_patterns['custom_tracking'] = [
        r'facebook\.com/tr',
        r'twitter\.com/i/adsct',
    ]

    url = "https://www.h.u-tokyo.ac.jp/"

    result = detector.detect(url)

    print(f"URL: {url}")
    print(f"検出された広告タイプ: {', '.join(result['ad_types']) if result['ad_types'] else 'なし'}")
    print()


def example_csv():
    """CSVからの読み込み例"""
    print("=" * 60)
    print("例4: CSVファイルから病院データを読み込み")
    print("=" * 60)
    print()

    fetcher = HospitalFetcher()

    # CSVファイルから読み込み
    hospitals = fetcher.fetch_from_csv('sample_hospitals.csv')

    if hospitals:
        print(f"読み込んだ病院数: {len(hospitals)}")
        print()
        print("最初の3件:")
        for i, hospital in enumerate(hospitals[:3], 1):
            print(f"{i}. {hospital['name']}")
            print(f"   URL: {hospital['website']}")
        print()
    else:
        print("CSVファイルが見つかりません")
        print()


def main():
    """メイン関数"""
    print()
    print("病院サイトURL取得 & Google広告検出ツール - 使用例")
    print()

    # 各例を実行
    example_basic()
    print()

    example_batch()
    print()

    example_custom()
    print()

    example_csv()
    print()

    print("=" * 60)
    print("すべての例が完了しました")
    print("=" * 60)


if __name__ == '__main__':
    main()
