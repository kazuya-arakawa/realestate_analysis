import os
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 1. 抽出したいエリア・条件のSUUMO検索結果URL（1ページ目）を設定
# ※ここでは例として「東京都世田谷区・賃貸マンション・アパート」の検索結果
BASE_URL = (
    "https://suumo.jp?"
    "ar=030&bs=040&ta=13&sc=13112&page={}"
)

# データを格納するリスト
data_list = []

# 2. 取得するページ数を指定（負荷軽減のため、まずは3ページほどでテストしてください）
MAX_PAGES = 3

# ブラウザを偽装するためのHeaders（スクレイピング時のマナー）
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

print("スクレイピングを開始します...")

for page in range(1, MAX_PAGES + 1):
    url = BASE_URL.format(page)
    print(f"読み込み中: {page} ページ目...")

    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"

        if response.status_code != 200:
            print(f"エラー: ステータスコード {response.status_code}")
            break

        soup = BeautifulSoup(response.text, "html.parser")

        # 物件ブロックの取得（SUUMOの各物件の塊）
        cassettes = soup.select(".cassetteitem")

        if not cassettes:
            print("これ以上の物件が見つかりませんでした。")
            break

        for cassette in cassettes:
            # 物件の基本情報
            title = cassette.select_one(".cassetteitem_content-title").text.strip()
            station = cassette.select_one(".cassetteitem_detail-col2").text.strip()
            age = cassette.select_one(".cassetteitem_detail-col3").text.strip()

            # 部屋ごとの情報を取得（1つの建物に複数の空室があるため）
            rooms = cassette.select(".js-cassette_link")

            for room in rooms:
                try:
                    # 家賃・管理費
                    price_rent = room.select_one(".cassetteitem_price--rent").text.strip()
                    price_admin = room.select_one(".cassetteitem_price--admin").text.strip()

                    # 敷金・礼金
                    deposit = room.select_one(".cassetteitem_price--deposit").text.strip()
                    gratuity = room.select_one(".cassetteitem_price--gratuity").text.strip()

                    # 間取り・面積
                    madori = room.select_one(".cassetteitem_madori").text.strip()
                    menseki = room.select_one(".cassetteitem_menseki").text.strip()

                    # 💡詳細ページ（付帯設備が書かれているページ）のURLを取得
                    detail_btn = room.select_one("a.js-cassette_link_href")
                    if not detail_btn:
                        continue
                    detail_url = "https://suumo.jp" + detail_btn["href"]

                    # --- 詳細ページにアクセスして設備を取得 ---
                    # サーバー負荷軽減のため、アクセスごとに必ず1秒待機
                    time.sleep(1.0)

                    detail_res = requests.get(detail_url, headers=HEADERS, timeout=10)
                    detail_res.encoding = "utf-8"
                    detail_soup = BeautifulSoup(detail_res.text, "html.parser")

                    # 設備の文字列が格納されているエリアを抽出
                    # ※SUUMOの詳細ページにある「部屋の特徴・設備」の部分
                    equipment_element = detail_soup.select_one(
                        "#content > div.clearfix.gap_b10 > div.w748 > table:nth-child(4) > tr:nth-child(3) > td"
                    ) or detail_soup.find("dt", text="部屋の特徴・設備")

                    if equipment_element:
                        # 見つかった場合は、隣のddタグやテキストを取得
                        if hasattr(equipment_element, "next_sibling"):
                            equipment_text = (
                                equipment_element.find_next("dd").text.strip()
                                if equipment_element.name == "dt"
                                else equipment_element.text.strip()
                            )
                        else:
                            equipment_text = equipment_element.text.strip()
                    else:
                        equipment_text = ""

                    # データの辞書化
                    room_data = {
                        "物件名": title,
                        "立地": station,
                        "築年数": age,
                        "家賃": price_rent,
                        "管理費": price_admin,
                        "敷金": deposit,
                        "礼金": gratuity,
                        "間取り": madori,
                        "専有面積": menseki,
                        "設備一覧文字列": equipment_text,
                        "詳細URL": detail_url,
                    }
                    data_list.append(room_data)

                except Exception as e:
                    # 特定の部屋のエラーで全体を止めないためのスキップ
                    continue

    except Exception as e:
        print(f"ページ取得エラー: {e}")
        break

    # ページ間の待機（マナー）
    time.sleep(1.5)

# 3. pandasのDataFrameに変換してCSV出力
df = pd.DataFrame(data_list)
df.to_csv("suumo_rent_data.csv", index=False, encoding="utf-8-sig")
print(f"完了しました！ {len(df)} 件のデータを 'suumo_rent_data.csv' に保存しました。")
