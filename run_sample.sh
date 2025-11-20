#!/bin/bash
# サンプル実行スクリプト

echo "================================================"
echo "サンプルCSVで実行します"
echo "================================================"
echo ""

python main.py --source csv --csv sample_hospitals.csv --format both

echo ""
echo "完了! output/ ディレクトリに結果が保存されました"
