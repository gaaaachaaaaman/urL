#!/bin/bash
# セットアップスクリプト

echo "================================================"
echo "病院サイトURL取得 & Google広告検出ツール"
echo "セットアップを開始します"
echo "================================================"
echo ""

# Python バージョンチェック
echo "[1/3] Python バージョンを確認中..."
python3 --version
if [ $? -ne 0 ]; then
    echo "エラー: Python 3 がインストールされていません"
    exit 1
fi
echo "✓ Python 3 が見つかりました"
echo ""

# 仮想環境の作成（オプション）
echo "[2/3] 仮想環境を作成しますか? (y/n)"
read -p "選択: " create_venv

if [ "$create_venv" = "y" ] || [ "$create_venv" = "Y" ]; then
    echo "仮想環境を作成中..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✓ 仮想環境を作成しました"
    echo "  有効化: source venv/bin/activate"
    echo "  無効化: deactivate"
fi
echo ""

# 依存パッケージのインストール
echo "[3/3] 依存パッケージをインストール中..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "エラー: 依存パッケージのインストールに失敗しました"
    exit 1
fi
echo "✓ 依存パッケージをインストールしました"
echo ""

# 出力ディレクトリの作成
mkdir -p output

echo "================================================"
echo "セットアップ完了!"
echo "================================================"
echo ""
echo "使い方:"
echo "  サンプルデータで実行:"
echo "    python main.py"
echo ""
echo "  CSVファイルを使用:"
echo "    python main.py --source csv --csv sample_hospitals.csv"
echo ""
echo "  詳細なヘルプ:"
echo "    python main.py --help"
echo ""
