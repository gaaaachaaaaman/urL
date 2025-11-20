# -*- coding: utf-8 -*-
"""
病院情報スクレイピングツール
医療機関検索サイトから病院データを取得します
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import re
from urllib.parse import urljoin, quote


class HospitalScraper:
    """病院情報をスクレイピングするクラス"""

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.hospitals = []

    def scrape_from_caloo(self, prefecture='tokyo', limit=100):
        """
        Caloo（カルー）から病院情報を取得
        https://caloo.jp/

        Args:
            prefecture: 都道府県（tokyo, osaka, など）
            limit: 取得する件数
        """
        print("Caloo から病院データを取得中...")

        base_url = "https://caloo.jp"
        prefecture_map = {
            'tokyo': '13',
            'osaka': '27',
            'kanagawa': '14',
            'saitama': '11',
            'chiba': '12',
            'aichi': '23',
            'hokkaido': '01',
            'fukuoka': '40',
        }

        pref_code = prefecture_map.get(prefecture, '13')

        count = 0
        page = 1

        while count < limit:
            try:
                # 病院一覧ページのURL
                url = "{}/hospitals/p{}?pref={}".format(base_url, page, pref_code)

                print("ページ {} を取得中...".format(page))
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'lxml')

                # 病院リストを取得（実際のHTML構造に合わせて調整が必要）
                # これはサンプル構造です
                hospital_items = soup.select('.hospitalItem, .hospital-item, .facility-item')

                if not hospital_items:
                    print("これ以上データが見つかりません")
                    break

                for item in hospital_items:
                    if count >= limit:
                        break

                    try:
                        # 病院名
                        name_elem = item.select_one('.name, .hospital-name, h3, h4')
                        name = name_elem.get_text(strip=True) if name_elem else ''

                        # 住所
                        address_elem = item.select_one('.address, .hospital-address')
                        address = address_elem.get_text(strip=True) if address_elem else ''

                        # 電話番号
                        phone_elem = item.select_one('.tel, .phone, .hospital-tel')
                        phone = phone_elem.get_text(strip=True) if phone_elem else ''
                        phone = re.sub(r'[^\d-]', '', phone)

                        # WebサイトURL
                        website_elem = item.select_one('a[href*="http"]')
                        website = website_elem.get('href', '') if website_elem else ''

                        if name and website:
                            hospital = {
                                'name': name,
                                'address': address,
                                'phone': phone,
                                'website': website
                            }
                            self.hospitals.append(hospital)
                            count += 1
                            print("  [{}/{}] {}".format(count, limit, name))

                    except Exception as e:
                        print("  エラー（スキップ）: {}".format(str(e)))
                        continue

                page += 1
                time.sleep(2)  # サーバー負荷対策

            except Exception as e:
                print("ページ取得エラー: {}".format(str(e)))
                break

        return self.hospitals

    def scrape_from_qlife(self, prefecture='tokyo', limit=100):
        """
        QLife から病院情報を取得
        https://www.qlife.jp/

        Args:
            prefecture: 都道府県
            limit: 取得する件数
        """
        print("QLife から病院データを取得中...")

        # 実装は同様のパターン
        # 実際のサイト構造に合わせて調整が必要

        return self.hospitals

    def create_sample_100_hospitals(self):
        """
        100件のサンプル病院データを作成
        実際のスクレイピングが難しい場合の代替案
        """
        print("サンプル病院データ（100件）を作成中...")

        # 実在する大学病院・大手病院のリスト
        real_hospitals = [
            ("東京大学医学部附属病院", "東京都文京区本郷7-3-1", "03-3815-5411", "https://www.h.u-tokyo.ac.jp/"),
            ("国立がん研究センター中央病院", "東京都中央区築地5-1-1", "03-3542-2511", "https://www.ncc.go.jp/jp/ncch/"),
            ("聖路加国際病院", "東京都中央区明石町9-1", "03-3541-5151", "https://hospital.luke.ac.jp/"),
            ("慶應義塾大学病院", "東京都新宿区信濃町35", "03-3353-1211", "https://www.hosp.keio.ac.jp/"),
            ("虎の門病院", "東京都港区虎ノ門2-2-2", "03-3588-1111", "https://toranomon.kkr.or.jp/"),
            ("順天堂大学医学部附属順天堂医院", "東京都文京区本郷3-1-3", "03-3813-3111", "https://www.juntendo.ac.jp/hospital/"),
            ("日本赤十字社医療センター", "東京都渋谷区広尾4-1-22", "03-3400-1311", "https://www.med.jrc.or.jp/"),
            ("東京医科大学病院", "東京都新宿区西新宿6-7-1", "03-3342-6111", "https://hospinfo.tokyo-med.ac.jp/"),
            ("東京女子医科大学病院", "東京都新宿区河田町8-1", "03-3353-8111", "https://www.twmu.ac.jp/DNH/"),
            ("昭和大学病院", "東京都品川区旗の台1-5-8", "03-3784-8000", "https://www.showa-u.ac.jp/SUH/"),
            ("東邦大学医療センター大森病院", "東京都大田区大森西6-11-1", "03-3762-4151", "https://www.omori.med.toho-u.ac.jp/"),
            ("帝京大学医学部附属病院", "東京都板橋区加賀2-11-1", "03-3964-1211", "https://www.teikyo-hospital.jp/"),
            ("日本大学病院", "東京都千代田区神田駿河台1-6", "03-3293-1711", "https://www.nihon-u.ac.jp/hospital/"),
            ("東京慈恵会医科大学附属病院", "東京都港区西新橋3-19-18", "03-3433-1111", "https://www.hosp.jikei.ac.jp/"),
            ("杏林大学医学部付属病院", "東京都三鷹市新川6-20-2", "0422-47-5511", "https://www.kyorin-u.ac.jp/hospital/"),
            ("東京都立多摩総合医療センター", "東京都府中市武蔵台2-8-29", "042-323-5111", "https://www.fuchu-hp.fuchu.tokyo.jp/"),
            ("東京都立墨東病院", "東京都墨田区江東橋4-23-15", "03-3633-6151", "https://www.byouin.metro.tokyo.lg.jp/sumida/"),
            ("NTT東日本関東病院", "東京都品川区東五反田5-9-22", "03-3448-6111", "https://www.ntt-east.co.jp/kmc/"),
            ("武蔵野赤十字病院", "東京都武蔵野市境南町1-26-1", "0422-32-3111", "https://www.musashino.jrc.or.jp/"),
            ("公立昭和病院", "東京都小平市花小金井8-1-1", "042-461-0052", "https://www.kouritu-showa.jp/"),
            # 大阪
            ("大阪大学医学部附属病院", "大阪府吹田市山田丘2-15", "06-6879-5111", "https://www.hosp.med.osaka-u.ac.jp/"),
            ("大阪市立大学医学部附属病院", "大阪府大阪市阿倍野区旭町1-5-7", "06-6645-2121", "https://www.hosp.med.osaka-cu.ac.jp/"),
            ("関西医科大学附属病院", "大阪府枚方市新町2-5-1", "072-804-0101", "https://www.kmu.ac.jp/hirakata/"),
            ("大阪医科薬科大学病院", "大阪府高槻市大学町2-7", "072-683-1221", "https://hospital.osaka-med.ac.jp/"),
            ("近畿大学病院", "大阪府大阪狭山市大野東377-2", "072-366-0221", "https://www.med.kindai.ac.jp/"),
            # 神奈川
            ("横浜市立大学附属病院", "神奈川県横浜市金沢区福浦3-9", "045-787-2800", "https://www.yokohama-cu.ac.jp/fukuhp/"),
            ("聖マリアンナ医科大学病院", "神奈川県川崎市宮前区菅生2-16-1", "044-977-8111", "https://www.marianna-u.ac.jp/hospital/"),
            ("北里大学病院", "神奈川県相模原市南区北里1-15-1", "042-778-8111", "https://www.khp.kitasato-u.ac.jp/"),
            ("東海大学医学部付属病院", "神奈川県伊勢原市下糟屋143", "0463-93-1121", "https://www.u-tokai.ac.jp/med-hp/"),
            ("昭和大学藤が丘病院", "神奈川県横浜市青葉区藤が丘1-30", "045-971-1151", "https://www.showa-u.ac.jp/SUHF/"),
            # 愛知
            ("名古屋大学医学部附属病院", "愛知県名古屋市昭和区鶴舞町65", "052-741-2111", "https://www.med.nagoya-u.ac.jp/hospital/"),
            ("藤田医科大学病院", "愛知県豊明市沓掛町田楽ヶ窪1-98", "0562-93-2111", "https://www.fujita-hu.ac.jp/hospital/"),
            ("愛知医科大学病院", "愛知県長久手市岩作雁又1-1", "0561-62-3311", "https://www.aichi-med-u.ac.jp/hospital/"),
            ("名古屋市立大学病院", "愛知県名古屋市瑞穂区瑞穂町字川澄1", "052-851-5511", "https://w3hosp.med.nagoya-cu.ac.jp/"),
            # 福岡
            ("九州大学病院", "福岡県福岡市東区馬出3-1-1", "092-641-1151", "https://www.hosp.kyushu-u.ac.jp/"),
            ("福岡大学病院", "福岡県福岡市城南区七隈7-45-1", "092-801-1011", "https://www.hop.fukuoka-u.ac.jp/"),
            ("久留米大学病院", "福岡県久留米市旭町67", "0942-35-3311", "https://www.kurume-u.ac.jp/hospital/"),
            # 北海道
            ("北海道大学病院", "北海道札幌市北区北14条西5丁目", "011-716-1161", "https://www.huhp.hokudai.ac.jp/"),
            ("札幌医科大学附属病院", "北海道札幌市中央区南1条西16丁目", "011-611-2111", "https://web.sapmed.ac.jp/hospital/"),
            # 宮城
            ("東北大学病院", "宮城県仙台市青葉区星陵町1-1", "022-717-7000", "https://www.hosp.tohoku.ac.jp/"),
            # 広島
            ("広島大学病院", "広島県広島市南区霞1-2-3", "082-257-5555", "https://www.hiroshima-u.ac.jp/hosp"),
        ]

        # 40件の実データを追加
        for hospital_data in real_hospitals[:40]:
            self.hospitals.append({
                'name': hospital_data[0],
                'address': hospital_data[1],
                'phone': hospital_data[2],
                'website': hospital_data[3]
            })

        # 残りをダミーデータで補完（実際の使用では削除推奨）
        for i in range(41, 101):
            self.hospitals.append({
                'name': "サンプル病院{}".format(i),
                'address': "東京都〇〇区〇〇{}-{}-{}".format(i, i%10, i%20),
                'phone': "03-{}-{}".format(str(1000 + i), str(1000 + i*2)),
                'website': "https://example-hospital-{}.jp/".format(i)
            })

        return self.hospitals

    def save_to_csv(self, filename='hospitals_100.csv'):
        """
        取得した病院データをCSVファイルに保存

        Args:
            filename: 保存するファイル名
        """
        if not self.hospitals:
            print("保存する病院データがありません")
            return False

        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['name', 'address', 'phone', 'website'])
                writer.writeheader()
                writer.writerows(self.hospitals)

            print("\n✓ {}件の病院データを {} に保存しました".format(len(self.hospitals), filename))
            return True

        except Exception as e:
            print("CSV保存エラー: {}".format(str(e)))
            return False


def main():
    """メイン関数"""
    print("=" * 60)
    print("病院データ取得ツール")
    print("=" * 60)
    print()

    scraper = HospitalScraper()

    print("データ取得方法を選択してください:")
    print("1. サンプルデータ100件を作成（推奨・即座に利用可能）")
    print("2. Webスクレイピング（開発中）")
    print()

    choice = input("選択 (1 or 2): ").strip()

    if choice == '2':
        print("\nWebスクレイピング機能は現在開発中です。")
        print("実際のサイトからデータを取得する場合は、")
        print("各サイトの利用規約とrobots.txtを確認してください。")
        print()
        print("サンプルデータを作成します...")
        scraper.create_sample_100_hospitals()
    else:
        # サンプルデータを作成
        scraper.create_sample_100_hospitals()

    # CSVに保存
    scraper.save_to_csv('hospitals_100.csv')

    print()
    print("=" * 60)
    print("完了！")
    print("=" * 60)
    print()
    print("次のコマンドで広告検出を実行してください:")
    print("  python3 main.py --source csv --csv hospitals_100.csv --no-selenium")
    print()


if __name__ == '__main__':
    main()
