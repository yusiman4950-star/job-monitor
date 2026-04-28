import requests
import os
import smtplib
from email.message import EmailMessage

# 从你提供的cURL命令中提取的API请求参数
url = "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
params = {
    "onlyData": "true",
    "expand": "requisitionList.workLocation,requisitionList.otherWorkLocations,requisitionList.secondaryLocations,flexFieldsFacet.values,requisitionList.requisitionFlexFields",
    "finder": "findReqs;siteNumber=CX_1001,facetsList=LOCATIONS%3BWORK_LOCATIONS%3BWORKPLACE_TYPES%3BTITLES%3BCATEGORIES%3BORGANIZATIONS%3BPOSTING_DATES%3BFLEX_FIELDS,limit=25,keyword=%22Analyst%22,locationId=300000000289330,sortBy=RELEVANCY"
}
headers = {
    'Accept': '*/*',
    'Accept-Language': 'en',
    'Content-Type': 'application/vnd.oracle.adf.resourceitem+json;charset=utf-8',
    'Ora-Irc-Language': 'en',
    'Referer': 'https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=Analyst&location=Hong+Kong&locationId=300000000289330&locationLevel=country&mode=location',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36',
}
# 这个方法就是让你替换那个关键的Cookie
def get_cookie_string():
    # 复制你cURL命令里 -b 后面的整段内容，替换这里的字符串
    return 'ORA_FUSION_PREFS=v1.0~bG9jYWxlPWVufmRlZmF1bHRMYW5ndWFnZU1hcmtlcj10cnVl; ORA_FND_SESSION_US2GL1EC_F=DEFAULT_PILLAR:STRetx6XYG7bdT+uoRRgC9hg3VmFALowrIUDuliPCoJF6WYlROZJJMNE9zudUsf+:1777309525721; CX_1001_cookieConsentEnabled=true; ORA_CX_SITE_NUMBER=CX_1001'

def fetch_jobs():
    try:
        session = requests.Session()
        session.headers.update(headers)
        # 从 get_cookie_string 解析 Cookie
        for cookie_pair in get_cookie_string().split('; '):
            if '=' in cookie_pair:
                name, value = cookie_pair.split('=', 1)
                session.cookies.set(name, value)
        response = session.get(url, params=params)
        response.raise_for_status()
        json_data = response.json()
        # 解析职位数据
        requisition_list = json_data.get('requisitionList', [])
        jobs = []
        for req in requisition_list:
            title = req.get('Title', 'N/A')
            location = req.get('PrimaryLocation', 'N/A')
            job_id = req.get('Id', 'N/A')
            job_url = f"https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{job_id}"
            jobs.append(f"职位: {title}\n地点: {location}\n链接: {job_url}\n")
        return jobs
    except Exception as e:
        print(f"抓取失败: {e}")
        return None

def send_mail(jobs):
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")
    if not jobs:
        print("未发现新岗位，不发送邮件。")
        return
    content = f"发现 {len(jobs)} 个摩根大通香港Analyst岗位：\n\n" + "\n\n".join(jobs)
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "摩根大通香港Analyst岗位日报"
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
    jobs = fetch_jobs()
    if jobs is not None:
        send_mail(jobs)
    else:
        print("未获取到岗位数据。")

if __name__ == "__main__":
    main()
