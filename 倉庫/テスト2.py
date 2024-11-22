import os
from dotenv import load_dotenv

# .envファイルを明示的に指定して読み込む
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# 環境変数を取得
email_user = os.getenv('EMAIL_ADDRESS')
email_password = os.getenv('EMAIL_PASSWORD')

print(f"EMAIL_ADDRESS: {email_user}")
print(f"EMAIL_PASSWORD: {email_password}")
