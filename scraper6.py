import requests
import smtplib
import os
from email.message import EmailMessage

# ====== 你只需要修改这一行 ======
API_URL = "https://jpmorganchase.sc.omtrdc.net/b/ss/jpmcglobalnew/1/JS-2.26.0-LGPQ/s57577293672625?AQB=1&ndh=1&pf=1&t=28%2F3%2F2026%201%3A11%3A26%202%20-480&mid=12175353856609444342759862860814361906&aamlh=3&ce=UTF-8&cdp=3&pageName=Programs%20%7C%20JPMorganChase&g=https%3A%2F%2Fwww.jpmorganchase.com%2Fcareers%2Fexplore-opportunities%2Fprograms&cc=USD&server=Launch&events=event6&v7=Asia%20Pacific&c14=D%3Dv7&v22=Checkbox&v23=Hong%20Kong%20SAR%2C%20China&v25=Careers%20Feed%20Component&v28=Hong%20Kong%20SAR%2C%20China%20%7C%20Asia%20Pacific&c33=Global%20%3E%20Programs%20%7C%20JPMorganChase&c44=Global&v44=Global&v51=Global%20%3E%20Programs%20%7C%20JPMorganChase&c58=https%3A%2F%2Fwww.jpmorganchase.com%2Fcareers%2Fexplore-opportunities%2Fprograms&v58=https%3A%2F%2Fwww.jpmorganchase.com%2Fcareers%2Fexplore-opportunities%2Fprograms&v79=Careers&v82=https%3A%2F%2Fwww.jpmorganchase.com%2Fcareers%2Fexplore-opportunities%2Fprograms&v83=https%3A%2F%2Fwww.jpmorganchase.com%2Fcareers%2Fexplore-opportunities%2Fprograms%2Fmarkets-fulltime-analyst&v84=Exploring%20opportunities&pe=lnk_o&pev2=Hong%20Kong%20SAR%2C%20China%20%7C%20Asia%20Pacific&s=2560x1440&c=24&j=1.6&v=N&k=Y&bw=976&bh=1207&mcorgid=BDA71C8B5330AE0C0A490D4D%40AdobeOrg&lrt=155&AQE=1"
# ===============================

def fetch_jobs():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    try:
        resp = requests.get(API_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        jobs = []
        # 根据实际返回的JSON结构提取职位（可能需要微调）
        # 假设返回的列表在 data['jobs'] 或 data['results'] 中
        job_list = data.get('jobs') or data.get('results') or data.get('data', [])
        for item in job_list:
            title = item.get('title') or item.get('jobTitle') or '未知职位'
            location = item.get('location') or item.get('city') or ''
            link = item.get('url') or item.get('applyUrl') or '#'
            if 'hong kong' in location.lower() or 'hong kong' in title.lower():
                jobs.append(f"职位: {title}\n地点: {location}\n链接: {link}\n")
        return jobs
    except Exception as e:
        print(f"抓取失败: {e}")
        return None

def send_email(jobs, sender, pwd, receiver):
    if not jobs:
        print("没有香港岗位，不发送邮件")
        return
    content = f"发现 {len(jobs)} 个摩根大通香港岗位：\n\n" + "\n\n".join(jobs)
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "摩根大通香港岗位日报"
    msg["From"] = sender
    msg["To"] = receiver
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender, pwd)
            smtp.send_message(msg)
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件失败: {e}")

def main():
    sender = os.environ.get("EMAIL_SENDER")
    pwd = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")
    if not all([sender, pwd, receiver]):
        print("请配置邮箱密钥")
        return
    jobs = fetch_jobs()
    if jobs is not None:
        send_email(jobs, sender, pwd, receiver)

if __name__ == "__main__":
    main()
