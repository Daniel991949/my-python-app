import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, redirect, url_for, send_file
from werkzeug.utils import secure_filename

# Flaskアプリケーションの作成
app = Flask(__name__)

# Vercel環境用の一時保存ディレクトリ（/tmp）
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# 必要なフォルダを作成（Vercelでは必須ではないが、エラー防止のため）
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# URLから価格と在庫を取得する関数
def fetch_price_and_stock(url, column):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        price, stock = None, None

        if column == "ハレルヤ":
            price_element = soup.select_one("span.figure")
            stock_element = soup.select_one("p.product__inventory")
            price = (
                float(price_element.text.replace("¥", "").replace(",", "").strip())
                if price_element
                else None
            )
            stock = (
                "".join(filter(str.isdigit, stock_element.text))
                if stock_element
                else None
            )

        elif column == "CR":
            price_element = soup.select_one("span#pricech")
            stock_element = soup.select_one("div.detail_section.stock")
            price = (
                float(price_element.text.replace("円", "").replace(",", "").strip())
                if price_element
                else None
            )
            if stock_element:
                stock_text = stock_element.text.strip()
                if "在庫数" in stock_text:
                    stock = int("".join(filter(str.isdigit, stock_text)))
                elif "×" in stock_text:
                    stock = 0
                else:
                    stock = None

        return price, stock

    except Exception as e:
        print(f"Error fetching data from URL {url}: {e}")
        return None, None


# メインページ
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # ファイルがアップロードされた場合
        if "file" not in request.files:
            return "ファイルが選択されていません。", 400

        file = request.files["file"]

        if file.filename == "":
            return "ファイルが選択されていません。", 400

        if file:
            # ファイルを保存
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(input_path)

            # 処理を実行
            output_path = process_excel(input_path)
            return redirect(url_for("download", filename=os.path.basename(output_path)))

    return render_template("index.html")


# Excelファイルを処理する関数
def process_excel(input_path):
    df = pd.read_excel(input_path)

    url_columns = ["ハレルヤ", "CR", "C", "D"]
    price_columns = ["価格_ハレルヤ", "価格_CR", "価格_C", "価格_D"]
    stock_columns = ["在庫_ハレルヤ", "在庫_CR", "在庫_C", "在庫_D"]

    for url_col, price_col, stock_col in zip(url_columns, price_columns, stock_columns):
        if url_col in df.columns:
            df[price_col] = None
            df[stock_col] = None
            for index, row in df.iterrows():
                url = row[url_col]
                if pd.notna(url):
                    price, stock = fetch_price_and_stock(url, url_col)
                    df.at[index, price_col] = price
                    df.at[index, stock_col] = stock

    df["最安値"] = None

    for index, row in df.iterrows():
        min_price = float("inf")
        min_url = None

        for url_col, price_col in zip(url_columns, price_columns):
            if url_col in df.columns and price_col in df.columns:
                price = row[price_col]
                url = row[url_col]

                if pd.notna(price) and pd.notna(url):
                    if price < min_price:
                        min_price = price
                        min_url = url

        if min_url:
            df.at[index, "最安値"] = f'=HYPERLINK("{min_url}", "{min_price}円")'

    # 出力ファイルを保存
    output_path = os.path.join(
        app.config["OUTPUT_FOLDER"], f"output_{os.path.basename(input_path)}.xlsx"
    )
    df.to_excel(output_path, index=False, engine="openpyxl")
    return output_path


# ダウンロードページ
@app.route("/download/<filename>")
def download(filename):
    file_path = os.path.join(app.config["OUTPUT_FOLDER"], filename)
    return send_file(file_path, as_attachment=True)


# アプリケーションの起動
if __name__ == "__main__":
    app.run(debug=True)
