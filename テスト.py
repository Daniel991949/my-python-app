import smtplib
from email.mime.text import MIMEText
import os  # osモジュールをインポート

smtp_server = "smtp.gmail.com"
smtp_port = 587
email_user = "otasuke0297@gmail.com"
email_password = "uerj fjrq krex fhuw"

try:
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()  # 暗号化開始
        server.login(email_user, email_password)  # ログイン
        msg = MIMEText("テストメールです")
        msg["Subject"] = "テスト"
        msg["From"] = email_user
        msg["To"] = "otasuke0297@gmail.com"
        server.sendmail(email_user, "otasuke0297@gmail.com", msg.as_string())
        print("メールが送信されました！")
except Exception as e:
    print(f"メールの送信に失敗しました: {e}")
