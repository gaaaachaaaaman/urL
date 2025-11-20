# -*- coding: utf-8 -*-
"""
統合Google広告検証ツール
1. Webサイトスクレイピングによる検出
2. Google広告透明性センターによる検証
の両方を実施し、結果を比較します
"""

import pandas as pd
from datetime import datetime
import os

from ads_detector import GoogleAdsDetector
from transparency_checker import GoogleAdsTransparencyChecker
from hospital_fetcher import HospitalFetcher


class IntegratedAdsChecker:
    """統合Google広告検証ツール"""

    def __init__(self, use_selenium=False):
        self.ads_detector = GoogleAdsDetector(use_selenium=use_selenium)
        self.transparency_checker = GoogleAdsTransparencyChecker()

    def check_hospitals_comprehensive(self, hospitals, use_transparency=True):
        """
        病院リストを包括的に検証

        Args:
            hospitals: 病院データのリスト
            use_transparency: 透明性センターも使うかどうか

        Returns:
            検証結果のリスト
        """
        print("=" * 60)
        print("統合Google広告検証ツール")
        print("=" * 60)
        print()

        results = []

        # ステップ1: Webサイトスクレイピングによる検出
        print("[1/2] Webサイトから広告を検出中...")
        print()

        for idx, hospital in enumerate(hospitals):
            hospital_name = hospital.get('name', '')
            website = hospital.get('website', '')

            print("[{}/{}] {}".format(idx + 1, len(hospitals), hospital_name))

            result = {
                'name': hospital_name,
                'address': hospital.get('address', ''),
                'phone': hospital.get('phone', ''),
                'website': website,
                'scraping_detected': False,
                'scraping_ad_types': '',
                'scraping_reference_info': '',
                'scraping_error': ''
            }

            if website:
                detection = self.ads_detector.detect(website)
                result['scraping_detected'] = detection['has_google_ads']
                result['scraping_ad_types'] = ', '.join(detection.get('ad_types', []))
                result['scraping_reference_info'] = ', '.join(detection.get('reference_info', []))
                result['scraping_error'] = detection.get('error', '')

            results.append(result)

        self.ads_detector.close_driver()

        print()
        print("✓ Webサイト検出完了")
        print()

        # ステップ2: Google広告透明性センターで検証
        if use_transparency:
            print("[2/2] Google広告透明性センターで検証中...")
            print()

            self.transparency_checker.setup_driver()

            try:
                for idx, result in enumerate(results):
                    hospital_name = result['name']

                    print("[{}/{}] {}".format(idx + 1, len(results), hospital_name))

                    transparency_result = self.transparency_checker.check_advertiser(hospital_name)

                    result['transparency_found'] = transparency_result['found']
                    result['transparency_search_query'] = transparency_result['search_query']
                    result['transparency_ads_count'] = transparency_result['ads_count']
                    result['transparency_error'] = transparency_result.get('error', '')

            finally:
                self.transparency_checker.close_driver()

            print()
            print("✓ 透明性センター検証完了")
            print()

        return results

    def save_results(self, results, output_dir='output'):
        """
        検証結果を保存

        Args:
            results: 検証結果のリスト
            output_dir: 出力ディレクトリ
        """
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = os.path.join(output_dir, 'integrated_ads_report_{}.csv'.format(timestamp))

        # データフレーム作成
        df_data = []
        for r in results:
            # 統合判定：どちらかで検出されたら「あり」
            has_transparency = r.get('transparency_found', False)
            has_scraping = r.get('scraping_detected', False)

            integrated_result = 'あり' if (has_transparency or has_scraping) else 'なし'

            # 一致状況
            if 'transparency_found' in r:
                if has_transparency and has_scraping:
                    match_status = '両方で検出'
                elif has_transparency and not has_scraping:
                    match_status = '透明性センターのみ'
                elif not has_transparency and has_scraping:
                    match_status = 'Webサイトのみ'
                else:
                    match_status = '両方で未検出'
            else:
                match_status = 'Webサイトのみ検証'

            row = {
                '病院名': r['name'],
                '住所': r['address'],
                '電話番号': r['phone'],
                'WebサイトURL': r['website'],
                '総合判定（Google広告使用）': integrated_result,
                '検出状況': match_status,
                'Webサイト検出': 'あり' if has_scraping else 'なし',
                '広告タイプ': r.get('scraping_ad_types', ''),
                '参考情報（GTM/GA）': r.get('scraping_reference_info', ''),
                '透明性センター': 'あり' if has_transparency else 'なし' if 'transparency_found' in r else '未検証',
                '広告数（透明性）': r.get('transparency_ads_count', ''),
                'エラー': r.get('scraping_error', '') or r.get('transparency_error', '')
            }

            df_data.append(row)

        df = pd.DataFrame(df_data)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')

        print("=" * 60)
        print("検証完了！")
        print("=" * 60)
        print()

        # 統計情報
        total = len(results)
        scraping_detected = sum(1 for r in results if r.get('scraping_detected', False))
        transparency_found = sum(1 for r in results if r.get('transparency_found', False))
        both_detected = sum(1 for r in results if r.get('scraping_detected', False) and r.get('transparency_found', False))
        either_detected = sum(1 for r in results if r.get('scraping_detected', False) or r.get('transparency_found', False))

        print("統計情報:")
        print("  総病院数: {}".format(total))
        print()
        print("  Webサイト検出: {} ({:.1f}%)".format(scraping_detected, scraping_detected/total*100 if total > 0 else 0))

        if any('transparency_found' in r for r in results):
            print("  透明性センター検出: {} ({:.1f}%)".format(transparency_found, transparency_found/total*100 if total > 0 else 0))
            print()
            print("  両方で検出: {} ({:.1f}%)".format(both_detected, both_detected/total*100 if total > 0 else 0))
            print("  いずれかで検出: {} ({:.1f}%)".format(either_detected, either_detected/total*100 if total > 0 else 0))

        print()
        print("結果を保存: {}".format(csv_path))
        print()

        return csv_path


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='統合Google広告検証ツール（Webスクレイピング + 透明性センター）'
    )

    parser.add_argument(
        '--source',
        choices=['sample', 'csv'],
        default='csv',
        help='病院データのソース'
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='CSVファイルのパス'
    )

    parser.add_argument(
        '--no-selenium',
        action='store_true',
        help='Seleniumを使用しない（高速モード）'
    )

    parser.add_argument(
        '--no-transparency',
        action='store_true',
        help='透明性センターでの検証をスキップ'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='出力ディレクトリ'
    )

    args = parser.parse_args()

    # 病院データを取得
    fetcher = HospitalFetcher()

    if args.source == 'csv':
        if not args.csv:
            print("エラー: --csv オプションでCSVファイルを指定してください")
            return
        hospitals = fetcher.fetch_from_csv(args.csv)
    else:
        hospitals = fetcher.create_sample_data()

    if not hospitals:
        print("エラー: 病院データを取得できませんでした")
        return

    print("✓ {}件の病院データを読み込みました".format(len(hospitals)))
    print()

    # 統合検証を実行
    checker = IntegratedAdsChecker(use_selenium=not args.no_selenium)
    results = checker.check_hospitals_comprehensive(
        hospitals,
        use_transparency=not args.no_transparency
    )

    # 結果を保存
    checker.save_results(results, output_dir=args.output)


if __name__ == '__main__':
    main()
