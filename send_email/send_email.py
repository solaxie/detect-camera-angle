import smtplib
import os
import logging
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import date

def send_email(sender=None, receivers=None, subject=None, body=None, attachment=None):
    # 設置默認值
    sender = sender or "omo@eslite.com"
    receivers = receivers or ["solaxie@eslite.com", "hectormao@eslite.com"]
    subject = subject or ""
    body = body or ""
    attachment = attachment or ""

    # 設置日誌
    log_dir = '/log'
    os.makedirs(log_dir, exist_ok=True)  # 創建目錄，如果目錄已存在則不進行任何操作
    log_file = os.path.join(log_dir, f'email-log-{date.today().strftime("%Y%m%d")}.txt')  # 設置日誌檔名
    logging.basicConfig(filename=log_file, level=logging.ERROR,
                        format='%(asctime)s - %(levelname)s - %(message)s')  # 設置日誌格式

    # 建立郵件
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # 檢查attachment路徑內的全部.jpg並加到附件
    if attachment and os.path.exists(attachment):  # 檢查attachment路徑是否存在
        jpg_files = [f for f in os.listdir(attachment) if f.endswith('.jpg')]  # 獲取.jpg檔名
        if not jpg_files:  # 檢查是否有.jpg檔
            logging.warning(f"附件目錄 {attachment} 中沒有找到 .jpg 文件")  # 輸出警告訊息
        
        for filename in jpg_files:  # 逐一加到附件
            with open(os.path.join(attachment, filename), 'rb') as f:  # 開啟檔案
                part = MIMEApplication(f.read(), Name=filename)  # 創建MIMEApplication
            part['Content-Disposition'] = f'attachment; filename="{filename}"'  # 設置附件名稱
            msg.attach(part)  # 將附件加到郵件
    elif attachment:  # 檢查attachment路徑是否存在
        logging.warning(f"指定的附件目錄 {attachment} 不存在")  # 輸出警告訊息

    # 發送郵件
    try:
        context = ssl.create_default_context()  # 使用默認的SSL套件
        with smtplib.SMTP('smtp-relay.gmail.com', 587) as server:  # 使用Gmail SMTP伺服器
            server.ehlo()  # 驗證伺服器回應
            server.starttls(context=context)
            response = server.sendmail(sender, receivers, msg.as_string())  # 發送郵件
            
            if not response:
                return True
            else:
                logging.error(f"郵件發送可能有問題: {response}")
                return False
    except Exception as e:  # 處理異常
        logging.error(f"郵件發送失敗：{str(e)}")
        return False

"""
Function:
發送電子郵件，可選擇性地附加 .jpg 文件。

Parameters:
sender (str, optional): 郵件寄件人的電子郵件地址。預設值為 "omo@eslite.com"。
receivers (list of str, optional): 郵件收件人的電子郵件地址列表。預設值為 ["solaxie@eslite.com", "hectormao@eslite.com"]。
subject (str, optional): 郵件主旨。預設為空字符串。
body (str, optional): 郵件內文。預設為空字符串。
attachment (str, optional): 附件的目錄路徑。如果提供，函數將附加該目錄中的所有 .jpg 文件。預設為空字符串。

Returns:
bool: 如果郵件成功發送返回 True，否則返回 False。

Note:
- 如果 attachment 目錄不存在或不包含 .jpg 文件，將記錄警告但仍繼續發送郵件。
- 所有錯誤和警告都會記錄到日誌文件中。

Sample:
camera_number = "105"
success = send_email(
    sender = "omo@eslite.com",                                 # 郵件寄件人，此為預設值，若不傳入參數則使用預設值
    receivers = ["solaxie@eslite.com", "hectormao@eslite.com"],   # 郵件收件人，此為預設值，若不傳入參數則使用預設值。可以添加多個收件人
    subject = f"告警：發現監視器{camera_number}畫面於今日有變化。",  # 郵件主旨，若不傳入參數，則留空白不使用任何值
    body = f"請調查監視器{camera_number}的畫面。",                 # 郵件內文，若不傳入參數，則留空白不使用任何值
    attachment = "/compare-result"                             # 附件的目錄路徑，若不傳入參數，則留空白不使用任何值
    )
if success:
    print("郵件發送成功")
else:
    print("郵件發送失敗")
"""