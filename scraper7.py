import os
import re
import smtplib
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ================= 你已经筛选好的香港+Analyst岗位页面 =================
URL = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=Analyst&location=Hong+Kong&locationId=300000000289330&locationLevel=country&mode=location"
# =================================================================

def setup_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    return driver

def extract_jobs_from_page(driver):
    """从页面文本中自动提取职位（不需要任何CSS选择器）"""
    try:
        # 等待页面加载完成
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # 按行拆分
        lines = page_text.split('\n')
        jobs = []
        current_job = {}
        
        # 常见职位关键词
        keywords = ["Analyst", "Associate", "Vice President", "Executive Director", "Intern", "Summer"]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            # 如果某行包含职位关键词，认为是标题
            if any(kw in line for kw in keywords):
                if current_job.get('title'):
                    jobs.append(current_job)
                current_job = {'title': line}
            # 如果包含"Hong Kong"或"Location"，认为是地点
            elif 'Hong Kong' in line or 'Location' in line:
                current_job['location'] = line
            # 如果包含"http"且是jpmc链接，认为是职位详情页
            elif 'https://jpmc.fa.oraclecloud.com' in line and 'job' in line:
                current_job['url'] = line
        
        if current_job.get('title'):
            jobs.append(current_job)
        
        # 去重并格式化
        unique_jobs = []
        seen_titles = set()
        for job in jobs:
            title = job.get('title', '')
            if title and title not in seen_titles:
                seen_titles.add(title)
                loc = job.get('location', 'Hong Kong')
                url = job.get('url', '#')
                unique_jobs.append(f"职位: {title}\n地点: {loc}\n链接: {url}\n")
        return unique_jobs
    except Exception as e:
        print(f"提取职位时出错: {e}")
        return []

def send_email(jobs, sender, password, receiver):
    if not jobs:
        print("未发现新岗位，不发送邮件")
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
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")
    if not all([sender, password, receiver]):
        print("请配置邮箱密钥")
        return
    
    driver = None
    try:
        driver = setup_driver()
        print(f"正在访问: {URL}")
        driver.get(URL)
        jobs = extract_jobs_from_page(driver)
        send_email(jobs, sender, password, receiver)
    except Exception as e:
        print(f"运行出错: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
