import requests
import smtplib
import os
from email.message import EmailMessage

# 摩根大通香港地区的招聘搜索结果API
# 这个地址来自Oracle招聘系统的API
JPMORGAN_API_URL = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/search"
# 请求API所需的参数，筛选香港地区
SEARCH_PARAMS = {
    "keywords": "",
    "location": "Hong Kong",
    "locationId": "",
    "locationLevel": "",
    "nearByRadius": "",
    "start": 0,
    "rows": 500,  # 一次获取最多500个岗位
}

def fetch_jobs_from_api():
    """调用Oracle API获取摩根大通在香港的岗位列表"""
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        # 添加一个Referer参数，假装是从招聘网站发起的请求，有时可以绕过简单限制
        "Referer": "https://jpmc.fa.oraclecloud.com/",
    }
    try:
        response = requests.post(
            JPMORGAN_API_URL,
            json=SEARCH_PARAMS,  # 发送JSON格式的参数
            headers=headers,
            timeout=30
        )
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()
        # 解析JSON响应，提取岗位信息
        jobs = []
        for job in data.get("data", {}).get("searchResults", {}).get("jobPostings", []):
            job_info = {
                "title": job.get("title", ""),
                "location": job.get("location", ""),
                "url": f"https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{job.get('id','')}/?",
                "posted_date": job.get("postedDate", ""),
            }
            jobs.append(job_info)
        return jobs
    except requests.exceptions.RequestException as e:
        print(f"API请求失败: {e}")
        return None

def send_email_notification(jobs, sender, password, receiver):
    """将岗位列表通过邮件发送出去"""
    if not jobs:
        print("没有新岗位，不发送邮件")
        return
    # 构建邮件正文
    email_content = "摩根大通（JPMorgan）香港地区新职位列表：\n\n"
    for idx, job in enumerate(jobs, 1):
        email_content += f"{idx}. {job['title']}\n"
        email_content += f"   地点：{job['location']}\n"
        email_content += f"   链接：{job['url']}\n\n"
    # 发送邮件（与之前相同逻辑）
    msg = EmailMessage()
    msg.set_content(email_content)
    msg["Subject"] = "摩根大通（JPMorgan）香港岗位监控日报"
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

def main():
    # 从环境变量中读取邮箱配置
    sender_email = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver_email = os.environ.get("EMAIL_RECEIVER")
    if not sender_email or not password or not receiver_email:
        print("请在GitHub Secrets中配置EMAIL_SENDER, EMAIL_PASSWORD和EMAIL_RECEIVER")
        return
    jobs = fetch_jobs_from_api()
    if jobs is not None:
        send_email_notification(jobs, sender_email, password, receiver_email)
    else:
        print("获取岗位失败")

if __name__ == "__main__":
    main()
