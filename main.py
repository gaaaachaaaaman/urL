#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
病院サイトURL取得 & Google広告検出ツール

全国の病院のWebサイトURLを取得し、Google広告の使用状況を判別します。
"""

import argparse
import pandas as pd
import json
from datetime import datetime
import os
from tqdm import tqdm

from hospital_fetcher import HospitalFetcher
from ads_detector import GoogleAdsDetector


def main():
    parser = argparse.ArgumentParser(
        description='全国の病院のサイトURLを取得し、Google広告の使用を検出します'
    )

    parser.add_argument(
        '--source',
        choices=['sample', 'csv', 'mhlw'],
        default='sample',
        help='病院データのソース (デフォルト: sample)'
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='CSVファイルのパス (--source csv の場合に指定)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='出力ディレクトリ (デフォルト: output)'
    )

    parser.add_argument(
        '--use-selenium',
        action='store_true',
        default=True,
        help='Seleniumを使用してより詳細に検出 (デフォルト: True)'
    )

    parser.add_argument(
        '--no-selenium',
        action='store_true',
        help='Seleniumを使用せず、requestsのみで検出 (高速だが精度は低い)'
    )

    parser.add_argument(
        '--format',
        choices=['csv', 'json', 'both'],
        default='both',
        help='出力フォーマット (デフォルト: both)'
    )

    args = parser.parse_args()

    # 出力ディレクトリを作成
    os.makedirs(args.output, exist_ok=True)

    print("=" * 60)
    print("病院サイトURL取得 & Google広告検出ツール")
    print("=" * 60)
    print()

    # ステップ1: 病院データを取得
    print("[1/3] 病院データを取得中...")
    fetcher = HospitalFetcher()

    if args.source == 'csv':
        if not args.csv:
            print("エラー: --csv オプションでCSVファイルを指定してください")
            return
        hospitals = fetcher.get_hospitals(source='csv', csv_path=args.csv)
    else:
        hospitals = fetcher.get_hospitals(source=args.source)

    if not hospitals:
        print("エラー: 病院データを取得できませんでした")
        return

    print("✓ {}件の病院データを取得しました".format(len(hospitals)))
    print()

    # ステップ2: Google広告を検出
    print("[2/3] Google広告の使用状況を検出中...")

    use_selenium = args.use_selenium and not args.no_selenium
    detector = GoogleAdsDetector(use_selenium=use_selenium)

    if use_selenium:
        print("モード: Selenium (詳細検出)")
    else:
        print("モード: Requests (高速)")

    results = []

    try:
        # プログレスバー付きで処理
        for hospital in tqdm(hospitals, desc="検出中"):
            website = hospital.get('website', '')

            if not website:
                result = {
                    'name': hospital.get('name', ''),
                    'address': hospital.get('address', ''),
                    'phone': hospital.get('phone', ''),
                    'website': '',
                    'has_google_ads': False,
                    'ad_types': [],
                    'detected_scripts': [],
                    'error': 'URLが設定されていません'
                }
            else:
                detection_result = detector.detect(website)

                result = {
                    'name': hospital.get('name', ''),
                    'address': hospital.get('address', ''),
                    'phone': hospital.get('phone', ''),
                    'website': detection_result['url'],
                    'has_google_ads': detection_result['has_google_ads'],
                    'ad_types': ', '.join(detection_result['ad_types']),
                    'detected_scripts': detection_result.get('detected_scripts', []),
                    'error': detection_result.get('error', '')
                }

            results.append(result)

    finally:
        detector.close_driver()

    print()
    print("✓ {}件の病院サイトを検出しました".format(len(results)))
    print()

    # ステップ3: 結果を保存
    print("[3/3] 結果を保存中...")

    # 統計情報
    total = len(results)
    with_ads = sum(1 for r in results if r['has_google_ads'])
    without_ads = total - with_ads
    errors = sum(1 for r in results if r['error'])

    print("  総病院数: {}".format(total))
    print("  Google広告使用: {} ({:.1f}%)".format(with_ads, with_ads/total*100))
    print("  Google広告なし: {} ({:.1f}%)".format(without_ads, without_ads/total*100))
    print("  エラー: {}".format(errors))
    print()

    # タイムスタンプ
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # CSV形式で保存
    if args.format in ['csv', 'both']:
        csv_path = os.path.join(args.output, 'hospital_ads_report_{}.csv'.format(timestamp))

        df = pd.DataFrame([{
            '病院名': r['name'],
            '住所': r['address'],
            '電話番号': r['phone'],
            'WebサイトURL': r['website'],
            'Google広告使用': 'あり' if r['has_google_ads'] else 'なし',
            '広告タイプ': r['ad_types'],
            'エラー': r['error']
        } for r in results])

        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print("✓ CSVファイルを保存: {}".format(csv_path))

    # JSON形式で保存
    if args.format in ['json', 'both']:
        json_path = os.path.join(args.output, 'hospital_ads_report_{}.json'.format(timestamp))

        output_data = {
            'timestamp': timestamp,
            'total_hospitals': total,
            'hospitals_with_ads': with_ads,
            'hospitals_without_ads': without_ads,
            'errors': errors,
            'results': results
        }

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print("✓ JSONファイルを保存: {}".format(json_path))

    print()
    print("=" * 60)
    print("完了!")
    print("=" * 60)


if __name__ == '__main__':
    main()
