from dotenv import load_dotenv
import os

# .env ファイルの読み込み
load_dotenv()

# 環境変数を表示して確認
email_address = os.getenv("EMAIL_ADDRESS")
email_password = os.getenv("EMAIL_PASSWORD")

print("EMAIL_ADDRESS:", email_address)
print("EMAIL_PASSWORD:", email_password)
