# 病院サイトURL取得 & Google広告検出ツール

全国の病院のWebサイトURLを取得し、Google広告の使用状況を自動判別するPythonツールです。

## 機能

- 📋 病院データの取得（CSVファイル、サンプルデータ対応）
- 🔍 WebサイトでのGoogle広告使用状況の自動検出
- 🎯 複数の広告タイプを識別（Google Ads、Google Tag Manager、コンバージョントラッキング、リマーケティング）
- 📊 CSV/JSON形式での結果出力
- ⚡ Seleniumによる詳細検出モード / Requestsによる高速モード

## 検出できる広告タイプ

- **Google Ads Script**: 一般的なGoogle広告スクリプト
- **Google Tag Manager**: GTMタグ
- **Conversion Tracking**: コンバージョントラッキング
- **Remarketing**: リマーケティングタグ

## インストール

### 必要要件

- Python 3.8以上
- Chrome または Chromium（Seleniumモード使用時）

### 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

## 使い方

### 基本的な使用方法

サンプルデータで試す：

```bash
python main.py
```

### CSVファイルから病院データを読み込む

```bash
python main.py --source csv --csv hospitals.csv
```

CSVファイルの形式：

```csv
name,address,phone,website
東京大学医学部附属病院,東京都文京区本郷7-3-1,03-3815-5411,https://www.h.u-tokyo.ac.jp/
```

### 高速モード（Seleniumなし）

```bash
python main.py --no-selenium
```

### 出力形式の指定

CSV形式のみ：

```bash
python main.py --format csv
```

JSON形式のみ：

```bash
python main.py --format json
```

両方（デフォルト）：

```bash
python main.py --format both
```

### 出力ディレクトリの指定

```bash
python main.py --output results
```

### 使用例を実行

ツールの基本的な使い方を学ぶには：

```bash
python example.py
```

このスクリプトは以下の例を実行します：
- 基本的な使い方
- 複数のURLを一括チェック
- カスタムパターンでの検出
- CSVからの読み込み

## オプション一覧

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--source` | データソース (sample/csv/mhlw) | sample |
| `--csv` | CSVファイルのパス | - |
| `--output` | 出力ディレクトリ | output |
| `--use-selenium` | Seleniumを使用（詳細検出） | True |
| `--no-selenium` | Seleniumを使用しない（高速） | False |
| `--format` | 出力形式 (csv/json/both) | both |

## 出力例

### CSV出力

```csv
病院名,住所,電話番号,WebサイトURL,Google広告使用,広告タイプ,エラー
東京大学医学部附属病院,東京都文京区本郷7-3-1,03-3815-5411,https://www.h.u-tokyo.ac.jp/,なし,,
聖路加国際病院,東京都中央区明石町9-1,03-3541-5151,https://hospital.luke.ac.jp/,あり,"google_ads_script, google_tag_manager",
```

### JSON出力

```json
{
  "timestamp": "20250120_143022",
  "total_hospitals": 5,
  "hospitals_with_ads": 2,
  "hospitals_without_ads": 3,
  "errors": 0,
  "results": [
    {
      "name": "東京大学医学部附属病院",
      "address": "東京都文京区本郷7-3-1",
      "phone": "03-3815-5411",
      "website": "https://www.h.u-tokyo.ac.jp/",
      "has_google_ads": false,
      "ad_types": "",
      "detected_scripts": [],
      "error": ""
    }
  ]
}
```

## Google広告の検出方法

このツールは以下の方法でGoogle広告の使用を検出します：

1. **スクリプトタグの解析**: Google Adsのドメイン（googleadservices.com、googlesyndication.comなど）を検出
2. **HTMLタグの検出**: `<ins class="adsbygoogle">` などの広告要素を検出
3. **ネットワークリクエストの監視**: Seleniumモードでは、ページ読み込み時のネットワークリクエストを監視
4. **正規表現パターンマッチング**: 広告関連のURLパターンを検出

### 検出されるパターン

- `googleads.g.doubleclick.net`
- `googlesyndication.com`
- `adservice.google.com`
- `google.com/adsense`
- `googleadservices.com`
- `googletagmanager.com/gtag`
- その他多数

## ファイル構成

```
.
├── main.py                  # メインスクリプト
├── hospital_fetcher.py      # 病院データ取得モジュール
├── ads_detector.py          # Google広告検出モジュール
├── example.py               # 使用例スクリプト
├── requirements.txt         # 依存パッケージ一覧
├── sample_hospitals.csv     # サンプル病院データ
├── setup.sh                 # セットアップスクリプト
├── run_sample.sh            # サンプル実行スクリプト
├── README.md                # このファイル
└── output/                  # 出力ディレクトリ（自動生成）
```

## 開発

### 新しい病院データソースの追加

`hospital_fetcher.py` の `HospitalFetcher` クラスに新しいメソッドを追加：

```python
def fetch_from_new_source(self) -> List[Dict]:
    # 実装
    pass
```

### 新しい広告パターンの追加

`ads_detector.py` の `GoogleAdsDetector.__init__` で `ad_patterns` に追加：

```python
self.ad_patterns = {
    'new_ad_type': [
        r'new-pattern-regex',
    ]
}
```

## トラブルシューティング

### Seleniumが動作しない

Chrome/Chromiumがインストールされているか確認してください：

```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# macOS
brew install --cask google-chrome
```

### メモリ不足エラー

大量の病院データを処理する場合は、`--no-selenium` オプションを使用してください。

### タイムアウトエラー

ネットワークが遅い場合は、`ads_detector.py` の `timeout` 値を増やしてください。

## 注意事項

- このツールは教育・研究目的で提供されています
- Webサイトへのアクセス頻度に注意し、適切な間隔を設けてください
- robots.txtを尊重してください
- 大量のリクエストを送る場合は、対象サイトの負荷に配慮してください

## ライセンス

MIT License

## 貢献

プルリクエストやイシューの報告を歓迎します！

---

# Hospital Website URL Fetcher & Google Ads Detector

A Python tool to fetch hospital website URLs across Japan and automatically detect Google Ads usage.

## Features

- 📋 Hospital data fetching (CSV file, sample data support)
- 🔍 Automatic Google Ads detection on websites
- 🎯 Multiple ad type identification (Google Ads, Google Tag Manager, Conversion Tracking, Remarketing)
- 📊 CSV/JSON output formats
- ⚡ Detailed detection mode with Selenium / Fast mode with Requests

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with sample data
python main.py

# Run with your CSV file
python main.py --source csv --csv your_hospitals.csv
```

## Documentation

See the Japanese section above for detailed documentation.
