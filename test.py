import requests
from bs4 import BeautifulSoup

URL = "https://suumo.jp"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

res = requests.get(URL, headers=HEADERS)
print(f"ステータスコード: {res.status_code}") # 200なら通信成功

soup = BeautifulSoup(res.text, "html.parser")

# 物件数が画面上に何件と表示されているか、テキストを引っ張ってみる
total_count = soup.select_one(".definition_list-item") or soup.find("div", class_="pagination_total")
if total_count:
    print(f"画面上のヒット件数表示: {total_count.text.strip()}")
else:
    print("件数表示が見つかりません（アクセスブロックの可能性あり）")

# カセットが何件あるか
cassettes = soup.select(".cassetteitem")
print(f"検知した物件数（.cassetteitem）: {len(cassettes)} 件")
