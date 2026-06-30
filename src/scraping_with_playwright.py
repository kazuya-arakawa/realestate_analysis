import time
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# 💡 ミスが起きないよう、ページ番号を単純に末尾にプラスする方式に変更
URL_PREFIX = "https://suumo.jp"
MAX_PAGES = 3

data_list = []

print("Playwrightを起動しています...")
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 800},
        locale="ja-JP"
    )
    page_tab = context.new_page()

    for page_num in range(1, MAX_PAGES + 1):
        # 💡 文字列を直接つなぐことで、絶対に変なURLにならないように担保します
        # 安全にページ番号をクエリに付与する（例: https://suumo.jp/?page=1）
        url = f"{URL_PREFIX}/?page={page_num}"
        print(f"ページ移動中: {page_num} ページ目 (アクセス先: {url})")
        
        page_tab.goto(url)
        page_tab.wait_for_timeout(3000) 

        html_content = page_tab.content()
        soup = BeautifulSoup(html_content, "html.parser")

        cassettes = soup.select(".cassetteitem")
        print(f"-> 物件カセットを {len(cassettes)} 件検知しました。")

        if not cassettes:
            print("物件が取得できませんでした。ブロックされた可能性があります。")
            break

        for cassette in cassettes:
            title = cassette.select_one(".cassetteitem_content-title").text.strip()
            station = cassette.select_one(".cassetteitem_detail-col2").text.strip()
            age = cassette.select_one(".cassetteitem_detail-col3").text.strip()

            rooms = cassette.select(".js-cassette_link")
            for room in rooms:
                try:
                    price_rent = room.select_one(".cassetteitem_price--rent").text.strip()
                    price_admin = room.select_one(".cassetteitem_price--admin").text.strip()
                    deposit = room.select_one(".cassetteitem_price--deposit").text.strip()
                    gratuity = room.select_one(".cassetteitem_price--gratuity").text.strip()
                    madori = room.select_one(".cassetteitem_madori").text.strip()
                    menseki = room.select_one(".cassetteitem_menseki").text.strip()

                    room_html_text = room.text.strip()

                    room_data = {
                        "物件名": title, "立地": station, "築年数": age,
                        "家賃": price_rent, "管理費": price_admin, "敷金": deposit, "礼金": gratuity,
                        "間取り": madori, "専有面積": menseki, 
                        "設備一覧文字列": room_html_text
                    }
                    data_list.append(room_data)
                except Exception:
                    continue

        time.sleep(2.0)

    browser.close()

# CSV出力
if data_list:
    df = pd.DataFrame(data_list)
    df.to_csv("suumo_rent_data_fast.csv", index=False, encoding="utf-8-sig")
    print(f"完了！ {len(df)} 件のデータを 'suumo_rent_data_fast.csv' に保存しました。")
else:
    print("データが1件も取得できませんでした。")
