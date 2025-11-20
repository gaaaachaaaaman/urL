# -*- coding: utf-8 -*-
"""
Google広告検出モジュール（改善版）
WebサイトでGoogle広告が使用されているかを正確に検出します

重要: Google Tag Manager（GTM）やGoogle Analyticsの存在だけでは
「Google広告使用」とは判定しません。実際の広告配信を示すパターンのみを検出します。
"""

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import re
from typing import Dict, List


class GoogleAdsDetector:
    """Google広告を検出するクラス（改善版）"""

    def __init__(self, use_selenium: bool = True):
        """
        Args:
            use_selenium: JavaScriptを実行してより詳細に検出する場合True
        """
        self.use_selenium = use_selenium
        self.driver = None

        # 実際のGoogle広告配信を示すパターン
        self.google_ads_patterns = [
            r'googlesyndication\.com',  # AdSense
            r'pagead2\.googlesyndication\.com',  # AdSense配信
            r'googleads\.g\.doubleclick\.net',  # DoubleClick広告
            r'adservice\.google\.com',  # 広告サービス
            r'google\.com/adsense',  # AdSense
            r'adsbygoogle',  # 広告ユニット（最も確実）
            r'google\.com/pagead/show',  # 広告表示
        ]

        # コンバージョントラッキング（広告使用の補助的証拠）
        self.conversion_patterns = [
            r'googleadservices\.com/pagead/conversion',
            r'google\.com/pagead/conversion',
        ]

        # リマーケティング（広告使用の補助的証拠）
        self.remarketing_patterns = [
            r'googleadservices\.com/pagead/viewthroughconversion',
        ]

        # 参考情報（これらだけでは広告使用とは判定しない）
        self.reference_patterns = {
            'google_tag_manager': [
                r'googletagmanager\.com/gtag',
                r'googletagmanager\.com/gtm\.js',
            ],
            'google_analytics': [
                r'google-analytics\.com',
                r'googletagmanager\.com/gtag.*analytics',
            ],
        }

    def setup_driver(self):
        """Seleniumドライバーをセットアップ"""
        if self.driver is None:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except Exception as e:
                print("Seleniumドライバーのセットアップエラー: {}".format(str(e)))
                self.use_selenium = False

    def close_driver(self):
        """Seleniumドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            self.driver = None

    def detect_with_requests(self, url: str) -> Dict:
        """
        requestsとBeautifulSoupを使用して広告を検出

        Args:
            url: チェックするURL

        Returns:
            検出結果の辞書
        """
        result = {
            'url': url,
            'has_google_ads': False,
            'ad_types': [],
            'reference_info': [],
            'detected_scripts': [],
            'error': None
        }

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')

            # HTMLソース全体を文字列として取得
            html_content = str(soup)

            # スクリプトタグをチェック
            scripts = soup.find_all('script', src=True)
            for script in scripts:
                src = script.get('src', '')
                result['detected_scripts'].append(src)

            # インラインスクリプトもチェック
            inline_scripts = soup.find_all('script')
            for script in inline_scripts:
                if script.string:
                    html_content += script.string

            # 1. 実際のGoogle広告を検出
            for pattern in self.google_ads_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    result['has_google_ads'] = True
                    if 'google_ads' not in result['ad_types']:
                        result['ad_types'].append('google_ads')
                    break

            # 2. コンバージョントラッキングを検出
            for pattern in self.conversion_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    if 'conversion_tracking' not in result['ad_types']:
                        result['ad_types'].append('conversion_tracking')

            # 3. リマーケティングを検出
            for pattern in self.remarketing_patterns:
                if re.search(pattern, html_content, re.IGNORECASE):
                    if 'remarketing' not in result['ad_types']:
                        result['ad_types'].append('remarketing')

            # 4. 参考情報を記録（これらは広告使用の判定には使わない）
            for ref_type, patterns in self.reference_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, html_content, re.IGNORECASE):
                        if ref_type not in result['reference_info']:
                            result['reference_info'].append(ref_type)

            # 5. Google Adsの広告要素を検出（最も確実な証拠）
            ad_elements = [
                soup.find_all('ins', class_=re.compile('adsbygoogle')),
                soup.find_all('div', attrs={'data-ad-client': True}),
                soup.find_all('script', string=re.compile('adsbygoogle')),
            ]

            for elements in ad_elements:
                if elements:
                    result['has_google_ads'] = True
                    if 'google_ads' not in result['ad_types']:
                        result['ad_types'].append('google_ads')
                    break

        except requests.RequestException as e:
            result['error'] = "リクエストエラー: {}".format(str(e))
        except Exception as e:
            result['error'] = "エラー: {}".format(str(e))

        return result

    def detect_with_selenium(self, url: str) -> Dict:
        """
        Seleniumを使用してJavaScriptを実行し、より詳細に広告を検出

        Args:
            url: チェックするURL

        Returns:
            検出結果の辞書
        """
        result = {
            'url': url,
            'has_google_ads': False,
            'ad_types': [],
            'reference_info': [],
            'detected_scripts': [],
            'network_requests': [],
            'error': None
        }

        try:
            if self.driver is None:
                self.setup_driver()

            if not self.use_selenium:
                return self.detect_with_requests(url)

            self.driver.get(url)
            time.sleep(3)  # ページ読み込み待機

            # ページソースを取得
            page_source = self.driver.page_source

            # 1. 実際のGoogle広告を検出
            for pattern in self.google_ads_patterns:
                if re.search(pattern, page_source, re.IGNORECASE):
                    result['has_google_ads'] = True
                    if 'google_ads' not in result['ad_types']:
                        result['ad_types'].append('google_ads')
                    break

            # 2. コンバージョントラッキングを検出
            for pattern in self.conversion_patterns:
                if re.search(pattern, page_source, re.IGNORECASE):
                    if 'conversion_tracking' not in result['ad_types']:
                        result['ad_types'].append('conversion_tracking')

            # 3. リマーケティングを検出
            for pattern in self.remarketing_patterns:
                if re.search(pattern, page_source, re.IGNORECASE):
                    if 'remarketing' not in result['ad_types']:
                        result['ad_types'].append('remarketing')

            # 4. 参考情報を記録
            for ref_type, patterns in self.reference_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, page_source, re.IGNORECASE):
                        if ref_type not in result['reference_info']:
                            result['reference_info'].append(ref_type)

            # JavaScriptでネットワークリクエストをチェック
            try:
                performance_entries = self.driver.execute_script(
                    "return performance.getEntriesByType('resource').map(e => e.name);"
                )

                for entry in performance_entries:
                    result['network_requests'].append(entry)

                    # 実際のGoogle広告を検出
                    for pattern in self.google_ads_patterns:
                        if re.search(pattern, entry, re.IGNORECASE):
                            result['has_google_ads'] = True
                            if 'google_ads' not in result['ad_types']:
                                result['ad_types'].append('google_ads')
                            break

                    # コンバージョントラッキング
                    for pattern in self.conversion_patterns:
                        if re.search(pattern, entry, re.IGNORECASE):
                            if 'conversion_tracking' not in result['ad_types']:
                                result['ad_types'].append('conversion_tracking')

                    # リマーケティング
                    for pattern in self.remarketing_patterns:
                        if re.search(pattern, entry, re.IGNORECASE):
                            if 'remarketing' not in result['ad_types']:
                                result['ad_types'].append('remarketing')

                    # 参考情報
                    for ref_type, patterns in self.reference_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, entry, re.IGNORECASE):
                                if ref_type not in result['reference_info']:
                                    result['reference_info'].append(ref_type)

            except Exception as e:
                print("Performance API エラー: {}".format(str(e)))

            # Google Ads広告要素をチェック（最も確実）
            ad_elements = self.driver.find_elements('css selector', 'ins.adsbygoogle')
            if ad_elements:
                result['has_google_ads'] = True
                if 'google_ads' not in result['ad_types']:
                    result['ad_types'].append('google_ads')

        except Exception as e:
            result['error'] = "Seleniumエラー: {}".format(str(e))

        return result

    def detect(self, url: str) -> Dict:
        """
        URLでGoogle広告を検出

        Args:
            url: チェックするURL

        Returns:
            検出結果の辞書
        """
        if not url or not url.startswith('http'):
            return {
                'url': url,
                'has_google_ads': False,
                'ad_types': [],
                'reference_info': [],
                'detected_scripts': [],
                'error': '無効なURL'
            }

        if self.use_selenium:
            return self.detect_with_selenium(url)
        else:
            return self.detect_with_requests(url)

    def batch_detect(self, urls: List[str]) -> List[Dict]:
        """
        複数のURLを一括でチェック

        Args:
            urls: チェックするURLのリスト

        Returns:
            検出結果のリスト
        """
        results = []

        try:
            if self.use_selenium:
                self.setup_driver()

            for i, url in enumerate(urls):
                print("[{}/{}] チェック中: {}".format(i+1, len(urls), url))
                result = self.detect(url)
                results.append(result)
                time.sleep(1)  # レート制限対策

        finally:
            if self.use_selenium:
                self.close_driver()

        return results
