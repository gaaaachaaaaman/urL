# -*- coding: utf-8 -*-
"""
Google広告透明性センター検証ツール
Google Ads Transparency Centerで実際の広告出稿状況を確認します
"""

import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import csv
import pandas as pd
from datetime import datetime


class GoogleAdsTransparencyChecker:
    """Google広告透明性センターで広告出稿を確認するクラス"""

    def __init__(self):
        self.base_url = "https://adstransparency.google.com/?region=JP"
        self.driver = None

    def setup_driver(self):
        """Seleniumドライバーをセットアップ"""
        print("ブラウザを起動中...")
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            print("✓ ブラウザを起動しました")
        except Exception as e:
            print("エラー: ブラウザの起動に失敗しました - {}".format(str(e)))
            raise

    def close_driver(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def normalize_hospital_name(self, name):
        """
        病院名を検索用に正規化

        例:
        「東京大学医学部附属病院」→「東京大学病院」
        「国立がん研究センター中央病院」→「国立がん研究センター」
        """
        # 一般的なパターンで短縮
        name = re.sub(r'医学部附属', '', name)
        name = re.sub(r'附属', '', name)
        name = re.sub(r'医療センター', '', name)

        # 複数の検索クエリを生成
        queries = [name]

        # 「病院」を除いたバージョンも追加
        if '病院' in name:
            queries.append(name.replace('病院', '').strip())

        # 「大学」で終わる場合は追加
        if '大学' in name and not name.endswith('大学'):
            base = name.split('大学')[0] + '大学'
            queries.append(base)

        return queries

    def check_advertiser(self, hospital_name):
        """
        Google広告透明性センターで広告主を検索

        Args:
            hospital_name: 病院名

        Returns:
            dict: {
                'found': bool,
                'advertiser_name': str,
                'ads_count': int,
                'search_query': str
            }
        """
        result = {
            'found': False,
            'advertiser_name': '',
            'ads_count': 0,
            'search_query': '',
            'error': None
        }

        try:
            # 検索クエリを生成
            search_queries = self.normalize_hospital_name(hospital_name)

            for query in search_queries:
                result['search_query'] = query

                # ページにアクセス
                search_url = "{}".format(self.base_url)
                self.driver.get(search_url)
                time.sleep(3)  # ページ読み込み待機

                try:
                    # 検索ボックスを探す
                    search_box = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="text"], input[placeholder*="検索"], input[placeholder*="Search"]'))
                    )

                    # 検索実行
                    search_box.clear()
                    search_box.send_keys(query)
                    time.sleep(1)
                    search_box.submit()

                    # 結果を待機
                    time.sleep(5)

                    # 結果をチェック
                    # 「結果が見つかりません」や「No results」などのメッセージを探す
                    page_source = self.driver.page_source.lower()

                    # 結果なしパターン
                    no_results_patterns = [
                        '結果が見つかりません',
                        'no results',
                        '該当する広告主が見つかりません',
                        'no advertisers found'
                    ]

                    has_no_results = any(pattern in page_source for pattern in no_results_patterns)

                    if not has_no_results:
                        # 結果がある可能性
                        # 広告主リンクや広告カードを探す
                        try:
                            advertiser_elements = self.driver.find_elements(By.CSS_SELECTOR,
                                'a[href*="advertiser"], .advertiser-card, div[data-advertiser]')

                            if advertiser_elements:
                                result['found'] = True
                                result['advertiser_name'] = query
                                result['ads_count'] = len(advertiser_elements)
                                print("  ✓ 見つかりました: {}（{}件の広告）".format(query, len(advertiser_elements)))
                                return result
                        except NoSuchElementException:
                            pass

                except TimeoutException:
                    print("  タイムアウト: {}".format(query))
                    continue
                except Exception as e:
                    print("  エラー: {} - {}".format(query, str(e)))
                    continue

            # すべてのクエリで見つからなかった
            print("  ✗ 見つかりませんでした: {}".format(hospital_name))

        except Exception as e:
            result['error'] = str(e)
            print("  エラー: {}".format(str(e)))

        return result

    def check_hospitals_from_csv(self, input_csv, output_csv=None):
        """
        CSVファイルから病院リストを読み込んで検証

        Args:
            input_csv: 入力CSVファイルパス
            output_csv: 出力CSVファイルパス（Noneの場合は自動生成）
        """
        print("=" * 60)
        print("Google広告透明性センター検証ツール")
        print("=" * 60)
        print()

        # CSVを読み込み
        try:
            df = pd.read_csv(input_csv)
            print("✓ {}件の病院データを読み込みました".format(len(df)))
        except Exception as e:
            print("エラー: CSVファイルの読み込みに失敗しました - {}".format(str(e)))
            return

        # ドライバーをセットアップ
        self.setup_driver()

        results = []

        try:
            for idx, row in df.iterrows():
                hospital_name = row.get('name', row.get('病院名', ''))

                print("[{}/{}] 検証中: {}".format(idx + 1, len(df), hospital_name))

                # Google広告透明性センターで検索
                transparency_result = self.check_advertiser(hospital_name)

                # 既存のデータに検証結果を追加
                result_row = row.to_dict()
                result_row['広告透明性センター検証'] = 'あり' if transparency_result['found'] else 'なし'
                result_row['検索クエリ'] = transparency_result['search_query']
                result_row['広告数'] = transparency_result['ads_count'] if transparency_result['found'] else 0
                result_row['検証エラー'] = transparency_result['error'] if transparency_result['error'] else ''

                results.append(result_row)

                # サーバー負荷対策
                time.sleep(2)

        finally:
            self.close_driver()

        # 結果を保存
        if output_csv is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_csv = 'hospital_ads_verified_{}.csv'.format(timestamp)

        result_df = pd.DataFrame(results)
        result_df.to_csv(output_csv, index=False, encoding='utf-8-sig')

        print()
        print("=" * 60)
        print("検証完了！")
        print("=" * 60)
        print()

        # 統計
        total = len(results)
        found = sum(1 for r in results if r['広告透明性センター検証'] == 'あり')
        not_found = total - found

        print("統計情報:")
        print("  総病院数: {}".format(total))
        print("  広告出稿確認: {} ({:.1f}%)".format(found, found/total*100 if total > 0 else 0))
        print("  広告出稿なし: {} ({:.1f}%)".format(not_found, not_found/total*100 if total > 0 else 0))
        print()
        print("結果を保存: {}".format(output_csv))


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Google広告透明性センターで病院の広告出稿状況を検証'
    )
    parser.add_argument(
        'input_csv',
        help='入力CSVファイル（病院リスト）'
    )
    parser.add_argument(
        '--output',
        help='出力CSVファイル',
        default=None
    )

    args = parser.parse_args()

    checker = GoogleAdsTransparencyChecker()
    checker.check_hospitals_from_csv(args.input_csv, args.output)


if __name__ == '__main__':
    main()
