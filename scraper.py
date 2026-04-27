import requests
from bs4 import BeautifulSoup
import smtplib
from email.message import EmailMessage
import os

# ================= 你的监控网站列表 =================
# 格式：["公司名", "网址", "地区关键词", "岗位关键词"]
# 请按照这个例子修改，注意保留引号和逗号
SITES = [
    ["腾讯", "https://careers.tencent.com/search.html", "深圳", "后台开发"],
    ["字节跳动", "https://jobs.bytedance.com/experienced", "上海", "产品经理"]
]
# =================================================

def send_email(content):
    """发送邮件到你的邮箱"""
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")

    if not sender or not password:
        print("邮箱配置未设置，无法发送邮件")
        return

    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "招聘监控日报 - 发现新岗位"
    msg["From"] = sender
    msg["To"] = receiver

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def check_jobs():
    results = []
    for company, url, location, keyword in SITES:
        print(f"正在检查: {company} - {keyword} in {location}")
        headers = {"User-Agent": "Mozilla/5.0"}
        try:
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            # 这里假设招聘列表在 class="job-item" 的元素里
            # 不同网站结构不同，你可以把实际网址发给我，我帮你改
            for item in soup.select(".job-item"):
                text = item.get_text()
                if location in text and keyword in text:
                    results.append(f"{company}: {text[:100]}\n{url}\n")
        except Exception as e:
            print(f"访问 {company} 出错: {e}")
    return results

def main():
    new_jobs = check_jobs()
    if new_jobs:
        body = "\n".join(new_jobs)
        send_email(body)
        print("发现新岗位，已发送邮件")
    else:
        print("未发现符合条件的新岗位，不发送邮件")

if __name__ == "__main__":
    main()
