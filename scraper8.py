import requests
import os
import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================= 配置区域 =========================
COOKIE_STRING = 'ORA_FUSION_PREFS=v1.0~bG9jYWxlPWVufmRlZmF1bHRMYW5ndWFnZU1hcmtlcj10cnVl; ORA_FND_SESSION_US2GL1EC_F=DEFAULT_PILLAR:STRetx6XYG7bdT+uoRRgC9hg3VmFALowrIUDuliPCoJF6WYlROZJJMNE9zudUsf+:1777309525721; CX_1001_cookieConsentEnabled=true; ORA_CX_SITE_NUMBER=CX_1001; CX_1001_cookieAccept_functional=true; ORA_CX_USERID_FUNCTIONAL=0c20ffd5-845f-4e22-8e8e-166b0f32cfaa; CX_1001_cookieAccept_analytical=true; ORA_CX_USERID=0c20ffd5-845f-4e22-8e8e-166b0f32cfaa; ORA_FPC=id=b0e3653d-d448-48c8-9e43-fc85caca6447'

HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'en',
    'Content-Type': 'application/vnd.oracle.adf.resourceitem+json;charset=utf-8',
    'Ora-Irc-Language': 'en',
    'Referer': 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?location=Hong+Kong&locationId=300000000289330&locationLevel=country&mode=location',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
}

API_URL = "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
PARAMS = {
    "onlyData": "true",
    "expand": "requisitionList,requisitionList.workLocation,requisitionList.otherWorkLocations,requisitionList.secondaryLocations",
    "finder": "findReqs;siteNumber=CX_1001,limit=100,locationId=300000000289330,sortBy=RELEVANCY"
}
# ============================================================

def fetch_jobs():
    session = requests.Session()
    session.headers.update(HEADERS)
    for item in COOKIE_STRING.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            session.cookies.set(key, value)
    
    try:
        response = session.get(API_URL, params=PARAMS, timeout=30)
        response.raise_for_status()
        data = response.json()
        print("API 返回的顶层键:", list(data.keys()))
        items = data.get('items', [])
        if not items:
            print("未找到 items 数组")
            return []
        requisition_list = items[0].get('requisitionList', [])
        print(f"找到 {len(requisition_list)} 个原始职位记录")
        jobs = []
        for req in requisition_list:
            title = req.get('Title', '')
            if not title:
                continue
            location = req.get('PrimaryLocation', 'Hong Kong')
            job_id = req.get('Id', '')
            if job_id:
                job_url = f"https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{job_id}"
            else:
                job_url = '#'
            # 清理可能存在的非法字符，替换 \xa0 为普通空格
            title = title.replace('\xa0', ' ')
            location = location.replace('\xa0', ' ')
            jobs.append(f"职位: {title}\n地点: {location}\n链接: {job_url}\n")
        # 打印前两条职位预览（调试用）
        if jobs:
            print("前两个职位示例:")
            for j in jobs[:2]:
                print(j)
        return jobs
    except Exception as e:
        print(f"抓取失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def send_email(jobs, sender, password, receiver):
    if not jobs:
        print("未发现任何岗位，不发送邮件。")
        return
    # 构造邮件内容
    subject = "摩根大通香港岗位日报 (无关键词限制)"
    content = f"发现 {len(jobs)} 个摩根大通香港地区岗位：\n\n" + "\n\n".join(jobs)
    # 使用 MIMEText 明确指定 UTF-8 编码
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = receiver
    
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")
        # 打印详细错误
        import traceback
        traceback.print_exc()

def main():
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")
    if not all([sender, password, receiver]):
        print("请在 GitHub Secrets 中配置 EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER")
        return
    jobs = fetch_jobs()
    if jobs is not None:
        send_email(jobs, sender, password, receiver)
    else:
        print("获取岗位数据失败，未发送邮件。")

if __name__ == "__main__":
    main()
