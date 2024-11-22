import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import logging
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from dotenv import load_dotenv
load_dotenv()
import os



from dotenv import load_dotenv
import os

# .env ファイルの読み込み
load_dotenv()

# 環境変数を表示して確認
print(f"EMAIL_ADDRESS: {os.getenv('EMAIL_ADDRESS')}")
print(f"EMAIL_PASSWORD: {os.getenv('EMAIL_PASSWORD')}")



# ログ設定
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# Flaskアプリケーションの作成
app = Flask(__name__)

# エラーハンドラーの定義
@app.errorhandler(Exception)
def handle_exception(e):
    error_details = traceback.format_exc()  # エラー詳細を取得
    app.logger.error(f"An error occurred: {error_details}")  # ログに出力
    return "Internal Server Error occurred. Please contact support.", 500

# Vercel環境用の一時保存ディレクトリ（/tmp）
UPLOAD_FOLDER = "/tmp/uploads"
OUTPUT_FOLDER = "/tmp/outputs"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["OUTPUT_FOLDER"] = OUTPUT_FOLDER

# 必要なフォルダを作成
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# メール送信機能
def send_email_with_file(file_path):
    try:
        # メール情報を環境変数から取得
        sender_email = os.getenv("EMAIL_ADDRESS")
        sender_password = os.getenv("EMAIL_PASSWORD")

        # 環境変数が取得できていない場合のエラー処理
        if not sender_email or not sender_password:
            raise ValueError("環境変数 'EMAIL_ADDRESS' または 'EMAIL_PASSWORD' が設定されていません。")

        recipient_email = "otasuke0297@gmail.com"

        # メールの設定
        subject = "出力ファイルの送信"
        body = "アップロードされたファイルの処理が完了しました。添付ファイルをご確認ください。"

        # メールの内容を作成
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # ファイルを添付
        with open(file_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename={os.path.basename(file_path)}",
        )
        message.attach(part)

        # GmailのSMTPサーバーに接続してメールを送信
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)

        logging.info(f"メールが正常に送信されました: {recipient_email}")

    except Exception as e:
        logging.error(f"メールの送信に失敗しました: {e}")


# URLから価格と在庫を取得する関数
def fetch_price_and_stock(url, column):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        price, stock = None, None

        if column == "ハレルヤ":
            price_element = soup.select_one("span.figure")
            stock_element = soup.select_one("p.product__inventory")
            price = float(price_element.text.replace("¥", "").replace(",", "").strip()) if price_element else None
            stock = "".join(filter(str.isdigit, stock_element.text)) if stock_element else None

        elif column == "CR":
            price_element = soup.select_one("span#pricech")
            stock_element = soup.select_one("div.detail_section.stock")
            price = float(price_element.text.replace("円", "").replace(",", "").strip()) if price_element else None
            stock_text = stock_element.text.strip() if stock_element else ""
            stock = int("".join(filter(str.isdigit, stock_text))) if "在庫数" in stock_text else 0 if "×" in stock_text else None

        return price, stock
    except Exception as e:
        logging.error(f"Error fetching data from URL {url} (Column: {column}): {e}")
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

        # ファイル形式のチェック
        if not (file.filename.endswith(".xlsx") or file.filename.endswith(".xls")):
            return "サポートされていないファイル形式です。Excelファイルをアップロードしてください。", 400

        if file:
            # ファイルを保存
            filename = secure_filename(file.filename)
            input_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(input_path)

            # 処理を実行
            output_path = process_excel(input_path)

            # ファイルをメールで送信
            send_email_with_file(output_path)

            # ダウンロードリンクを返す
            return redirect(url_for("download", filename=os.path.basename(output_path)))

    return render_template("index.html")

# Excelファイルを処理する関数
def process_excel(input_path):
    df = pd.read_excel(input_path, engine="openpyxl")

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
    output_path = os.path.join(app.config["OUTPUT_FOLDER"], f"output_{os.path.basename(input_path)}.xlsx")
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
