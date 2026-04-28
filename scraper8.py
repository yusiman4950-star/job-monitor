import requests
import os
import smtplib
import json
from email.message import EmailMessage

# ========================= 配置区域 =========================
# 从你的 cURL 命令中提取的 Cookie（原样复制）
COOKIE_STRING = 'ORA_FUSION_PREFS=v1.0~bG9jYWxlPWVufmRlZmF1bHRMYW5ndWFnZU1hcmtlcj10cnVl; ORA_FND_SESSION_US2GL1EC_F=DEFAULT_PILLAR:STRetx6XYG7bdT+uoRRgC9hg3VmFALowrIUDuliPCoJF6WYlROZJJMNE9zudUsf+:1777309525721; CX_1001_cookieConsentEnabled=true; ORA_CX_SITE_NUMBER=CX_1001; CX_1001_cookieAccept_functional=true; ORA_CX_USERID_FUNCTIONAL=0c20ffd5-845f-4e22-8e8e-166b0f32cfaa; CX_1001_cookieAccept_analytical=true; ORA_CX_USERID=0c20ffd5-845f-4e22-8e8e-166b0f32cfaa; ORA_FPC=id=b0e3653d-d448-48c8-9e43-fc85caca6447'

# 请求头
HEADERS = {
    'Accept': '*/*',
    'Accept-Language': 'en',
    'Content-Type': 'application/vnd.oracle.adf.resourceitem+json;charset=utf-8',
    'Ora-Irc-Language': 'en',
    'Referer': 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?location=Hong+Kong&locationId=300000000289330&locationLevel=country&mode=location',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
}

# API 地址和参数（不带 keyword 限制，只按香港地区 + locationId）
API_URL = "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
PARAMS = {
    "onlyData": "true",
    "expand": "requisitionList,requisitionList.workLocation,requisitionList.otherWorkLocations,requisitionList.secondaryLocations",
    "finder": "findReqs;siteNumber=CX_1001,limit=100,locationId=300000000289330,sortBy=RELEVANCY"
}
# ============================================================

def fetch_jobs():
    """直接调用 API 获取香港地区所有岗位"""
    session = requests.Session()
    session.headers.update(HEADERS)
    # 解析 Cookie
    for item in COOKIE_STRING.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            session.cookies.set(key, value)
    
    try:
        response = session.get(API_URL, params=PARAMS, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # 打印返回的顶层结构，方便调试
        print("API 返回的顶层键:", list(data.keys()))
        
        # 职位数据通常在 items[0]['requisitionList'] 中
        items = data.get('items', [])
        if not items:
            print("未找到 items 数组")
            return []
        
        # 取第一个 item 中的 requisitionList
        requisition_list = items[0].get('requisitionList', [])
        print(f"找到 {len(requisition_list)} 个原始职位记录")
        
        jobs = []
        for req in requisition_list:
            title = req.get('Title', '')
            if not title:
                continue
            location = req.get('PrimaryLocation', 'Hong Kong')
            job_id = req.get('Id', '')
            # 构造详情页链接
            if job_id:
                job_url = f"https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{job_id}"
            else:
                job_url = '#'
            jobs.append(f"职位: {title}\n地点: {location}\n链接: {job_url}\n")
        
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
    content = f"发现 {len(jobs)} 个摩根大通香港地区岗位：\n\n" + "\n\n".join(jobs)
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "摩根大通香港岗位日报 (无关键词限制)"
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
