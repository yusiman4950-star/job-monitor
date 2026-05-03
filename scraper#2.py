# scraper_all_banks.py
import os
import time
import re
import smtplib
import requests
import json
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# ================= 1= 邮件配置 ==================
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

# ================= 2= 银行配置 ==================

# 摩根大通 (API 方式)
JPMORGAN_API_URL = "https://jpmc.fa.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
JPMORGAN_PARAMS = {
    "onlyData": "true",
    "expand": "requisitionList,requisitionList.workLocation,requisitionList.otherWorkLocations,requisitionList.secondaryLocations",
    "finder": "findReqs;siteNumber=CX_1001,limit=100,locationId=300000000289330,sortBy=RELEVANCY"
}
JPMORGAN_COOKIE_STRING = 'ORA_FUSION_PREFS=v1.0~bG9jYWxlPWVufmRlZmF1bHRMYW5ndWFnZU1hcmtlcj10cnVl; ORA_FND_SESSION_US2GL1EC_F=DEFAULT_PILLAR:STRetx6XYG7bdT+uoRRgC9hg3VmFALowrIUDuliPCoJF6WYlROZJJMNE9zudUsf+:1777309525721; CX_1001_cookieConsentEnabled=true; ORA_CX_SITE_NUMBER=CX_1001; CX_1001_cookieAccept_functional=true; ORA_CX_USERID_FUNCTIONAL=0c20ffd5-845f-4e22-8e8e-166b0f32cfaa; CX_1001_cookieAccept_analytical=true; ORA_CX_USERID=0c20ffd5-845f-4e22-8e8e-166b0f32cfaa; ORA_FPC=id=b0e3653d-d448-48c8-9e43-fc85caca6447'

# ================= 3= 工具函数 ==================
def clean_string(s):
    """清理字符串中的不可见字符"""
    if not s:
        return s
    s = s.replace('\xa0', ' ').strip()
    s = ''.join(ch for ch in s if ch.isprintable() or ch in '\n\t\r')
    return s

def setup_driver():
    """配置无头Chrome浏览器"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=options)
    return driver

def send_email(all_jobs):
    """发送汇总邮件"""
    if not all_jobs:
        print("所有银行均未发现新岗位，不发送邮件。")
        return

    # 构建邮件内容
    content_lines = []
    for bank, jobs in all_jobs.items():
        if jobs:
            content_lines.append(f"\n========== {bank} ==========\n")
            content_lines.extend(jobs)

    subject = "多家银行香港岗位日报"
    content = "\n".join(content_lines)

    msg = MIMEText(content, 'plain', 'utf-8')
    msg['Subject'] = subject
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f"邮件发送成功，共发现 {sum(len(jobs) for jobs in all_jobs.values())} 个岗位。")
    except Exception as e:
        print(f"邮件发送失败: {e}")

# ================= 4= 各银行抓取函数 ==================

def fetch_jpmorgan():
    """抓取摩根大通岗位 (API方式)"""
    print("正在抓取摩根大通...")
    session = requests.Session()
    headers = {
        'Accept': '*/*',
        'Content-Type': 'application/vnd.oracle.adf.resourceitem+json;charset=utf-8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    session.headers.update(headers)
    for item in JPMORGAN_COOKIE_STRING.split('; '):
        if '=' in item:
            key, value = item.split('=', 1)
            session.cookies.set(key, value)

    try:
        response = session.get(JPMORGAN_API_URL, params=JPMORGAN_PARAMS, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get('items', [])
        if not items:
            return []
        requisition_list = items[0].get('requisitionList', [])
        analyst_jobs = []
        for req in requisition_list:
            title = req.get('Title', '')
            if not title:
                continue
            if 'analyst' in title.lower():
                location = req.get('PrimaryLocation', 'Hong Kong')
                job_id = req.get('Id', '')
                job_url = f"https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/{job_id}" if job_id else '#'
                title = clean_string(title)
                location = clean_string(location)
                analyst_jobs.append(f"职位: {title}\n地点: {location}\n链接: {job_url}\n")
        print(f"摩根大通: 发现 {len(analyst_jobs)} 个 Analyst 岗位")
        return analyst_jobs
    except Exception as e:
        print(f"摩根大通抓取失败: {e}")
        return []

def fetch_morgan_stanley():
    """抓取摩根士丹利岗位 (Selenium)"""
    print("正在抓取摩根士丹利...")
    driver = None
    try:
        driver = setup_driver()
        url = "https://www.morganstanley.com/careers/career-opportunities-search?opportunity=sg"
        driver.get(url)
        time.sleep(5)

        # 尝试选择地点
        try:
            location_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Location')]"))
            )
            location_btn.click()
            time.sleep(2)
            hk_option = driver.find_element(By.XPATH, "//span[contains(text(), 'Hong Kong')]")
            hk_option.click()
            time.sleep(2)
            apply_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Apply')]")
            apply_btn.click()
            time.sleep(5)
        except Exception as e:
            print(f"摩根士丹利筛选地点时出错: {e}")

        # 提取岗位
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = page_text.split('\n')
        jobs = []
        for i, line in enumerate(lines):
            if 'Hong Kong' in line and ('Analyst' in line or 'Associate' in line):
                job_title = line
                job_link = "#"
                # 尝试获取附近链接
                for j in range(max(0, i-5), min(len(lines), i+5)):
                    if 'http' in lines[j]:
                        job_link = lines[j]
                        break
                jobs.append(f"职位: {job_title}\n链接: {job_link}\n")
        print(f"摩根士丹利: 发现 {len(jobs)} 个岗位")
        return jobs
    except Exception as e:
        print(f"摩根士丹利抓取失败: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def fetch_ubs():
    """抓取瑞银岗位 (Selenium + Cookie预设)"""
    print("正在抓取瑞银...")
    driver = None
    try:
        driver = setup_driver()
        url = "https://jobs.ubs.com/TGnewUI/Search/home/HomeWithPreLoad?partnerid=25008&siteid=5131&PageType=searchResults&SearchType=linkquery&LinkID=15232"
        driver.get(url)
        time.sleep(5)

        # 尝试通过Cookie预设地点
        try:
            driver.add_cookie({'name': 'locationPreference', 'value': 'Hong Kong', 'domain': 'jobs.ubs.com'})
            driver.refresh()
            time.sleep(5)
        except:
            pass

        # 尝试图形化筛选
        try:
            location_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "locationSearch"))
            )
            location_input.clear()
            location_input.send_keys("Hong Kong")
            time.sleep(2)
            search_btn = driver.find_element(By.ID, "searchBtn")
            search_btn.click()
            time.sleep(5)
        except Exception as e:
            print(f"瑞银筛选地点时出错: {e}")

        # 提取岗位
        page_text = driver.find_element(By.TAG_NAME, "body").text
        lines = page_text.split('\n')
        jobs = []
        for i, line in enumerate(lines):
            if 'Hong Kong' in line and ('Analyst' in line or 'Associate' in line):
                job_title = line
                job_link = "#"
                for j in range(max(0, i-5), min(len(lines), i+5)):
                    if 'http' in lines[j]:
                        job_link = lines[j]
                        break
                jobs.append(f"职位: {job_title}\n链接: {job_link}\n")
        print(f"瑞银: 发现 {len(jobs)} 个岗位")
        return jobs
    except Exception as e:
        print(f"瑞银抓取失败: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def fetch_barclays():
    """抓取巴克莱岗位 (requests + API)"""
    print("正在抓取巴克莱...")
    try:
        url = "https://search.jobs.barclays/search-jobs/results"
        params = {
            "keywords": "",
            "location": "hong kong",
            "lat": "1.35208",
            "lon": "103.82",
            "page": 1
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        jobs = []
        for job in data.get('jobs', []):
            title = job.get('title', '')
            if 'analyst' in title.lower():
                job_url = job.get('url', '#')
                location = job.get('location', 'Hong Kong')
                jobs.append(f"职位: {title}\n地点: {location}\n链接: {job_url}\n")
        print(f"巴克莱: 发现 {len(jobs)} 个岗位")
        return jobs
    except Exception as e:
        print(f"巴克莱抓取失败: {e}")
        return []

def fetch_hsbc():
    """抓取汇丰岗位 (requests + BeautifulSoup)"""
    print("正在抓取汇丰...")
    try:
        url = "https://www.hsbc.com/careers/students-and-graduates/find-a-programme?location=hong-kong-sar&page=1"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        lines = page_text.split('\n')
        jobs = []
        for i, line in enumerate(lines):
            if 'Hong Kong' in line and ('Programme' in line or 'Analyst' in line):
                job_title = line.strip()
                # 尝试提取链接
                job_link = "#"
                for link in soup.find_all('a'):
                    if job_title in link.get_text():
                        job_link = link.get('href', '#')
                        if not job_link.startswith('http'):
                            job_link = 'https://www.hsbc.com' + job_link
                        break
                jobs.append(f"职位: {job_title}\n链接: {job_link}\n")
        print(f"汇丰: 发现 {len(jobs)} 个岗位")
        return jobs
    except Exception as e:
        print(f"汇丰抓取失败: {e}")
        return []

# ================= 5= 主程序 ==================
def main():
    print("开始抓取所有银行的香港岗位...")
    all_results = {}

    # 逐个银行抓取
    all_results["摩根大通 (JPMorgan)"] = fetch_jpmorgan()
    all_results["摩根士丹利 (Morgan Stanley)"] = fetch_morgan_stanley()
    all_results["瑞银 (UBS)"] = fetch_ubs()
    all_results["巴克莱 (Barclays)"] = fetch_barclays()
    all_results["汇丰 (HSBC)"] = fetch_hsbc()

    # 发送汇总邮件
    send_email(all_results)

if __name__ == "__main__":
    main()
