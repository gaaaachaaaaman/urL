# -*- coding: utf-8 -*-
"""
Google広告検出モジュール
WebサイトでGoogle広告が使用されているかを検出します
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
    """Google広告を検出するクラス"""

    def __init__(self, use_selenium: bool = True):
        """
        Args:
            use_selenium: JavaScriptを実行してより詳細に検出する場合True
        """
        self.use_selenium = use_selenium
        self.driver = None

        # Google広告関連のパターン
        self.ad_patterns = {
            'google_ads_script': [
                r'googleads\.g\.doubleclick\.net',
                r'googlesyndication\.com',
                r'adservice\.google\.com',
                r'google\.com/adsense',
                r'googleadservices\.com',
                r'google-analytics\.com/.*gtag',
            ],
            'google_tag_manager': [
                r'googletagmanager\.com/gtag',
                r'googletagmanager\.com/gtm\.js',
            ],
            'conversion_tracking': [
                r'google-analytics\.com/collect',
                r'google\.com/pagead/conversion',
                r'googleadservices\.com/pagead/conversion',
            ],
            'remarketing': [
                r'googleadservices\.com/pagead/viewthroughconversion',
            ]
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
                print(f"Seleniumドライバーのセットアップエラー: {str(e)}")
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

            # パターンマッチング
            for ad_type, patterns in self.ad_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, html_content, re.IGNORECASE):
                        result['has_google_ads'] = True
                        if ad_type not in result['ad_types']:
                            result['ad_types'].append(ad_type)

            # Google Adsの一般的な要素をチェック
            ad_elements = [
                soup.find_all('ins', class_=re.compile('adsbygoogle')),
                soup.find_all('div', attrs={'data-ad-client': True}),
                soup.find_all('script', string=re.compile('adsbygoogle')),
            ]

            for elements in ad_elements:
                if elements:
                    result['has_google_ads'] = True
                    if 'google_ads_display' not in result['ad_types']:
                        result['ad_types'].append('google_ads_display')
                    break

        except requests.RequestException as e:
            result['error'] = f"リクエストエラー: {str(e)}"
        except Exception as e:
            result['error'] = f"エラー: {str(e)}"

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

            # パターンマッチング
            for ad_type, patterns in self.ad_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, page_source, re.IGNORECASE):
                        result['has_google_ads'] = True
                        if ad_type not in result['ad_types']:
                            result['ad_types'].append(ad_type)

            # JavaScriptでネットワークリクエストをチェック
            # Performance APIを使用
            try:
                performance_entries = self.driver.execute_script(
                    "return performance.getEntriesByType('resource').map(e => e.name);"
                )

                for entry in performance_entries:
                    result['network_requests'].append(entry)
                    for ad_type, patterns in self.ad_patterns.items():
                        for pattern in patterns:
                            if re.search(pattern, entry, re.IGNORECASE):
                                result['has_google_ads'] = True
                                if ad_type not in result['ad_types']:
                                    result['ad_types'].append(ad_type)

            except Exception as e:
                print(f"Performance API エラー: {str(e)}")

            # Google Ads要素をチェック
            ad_elements = self.driver.find_elements('css selector', 'ins.adsbygoogle')
            if ad_elements:
                result['has_google_ads'] = True
                if 'google_ads_display' not in result['ad_types']:
                    result['ad_types'].append('google_ads_display')

        except Exception as e:
            result['error'] = f"Seleniumエラー: {str(e)}"

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
                print(f"[{i+1}/{len(urls)}] チェック中: {url}")
                result = self.detect(url)
                results.append(result)
                time.sleep(1)  # レート制限対策

        finally:
            if self.use_selenium:
                self.close_driver()

        return results
