import os
import time
import smtplib
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ---------- 目标配置 ----------
TARGET_URL = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001"
LOCATION_KEYWORD = "Hong Kong"
# ----------------------------

def setup_driver():
    """配置无头Chrome浏览器"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")                 # 无界面运行
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    return driver

def select_hong_kong(driver):
    """
    模拟点击位置筛选：亚太地区 → 中国香港
    """
    try:
        # 1. 等待页面主要元素加载完成
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)  # 留出额外时间让页面JS充分执行

        # 2. 尝试多种常见选择器定位“地点”相关控件
        location_selectors = [
            "button[aria-label*='location']",
            "button[aria-label*='Location']",
            "div[class*='location'] button",
            "div[class*='Location'] button",
            "//button[contains(., 'Location')]",
            "//span[text()='Location']/parent::button"
        ]
        location_button = None
        for selector in location_selectors:
            try:
                if selector.startswith("//"):
                    location_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    location_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                if location_button:
                    break
            except:
                continue

        if not location_button:
            print("未找到地点筛选按钮，尝试直接搜索香港职位...")
            return False

        # 点击打开地点下拉面板
        driver.execute_script("arguments[0].click();", location_button)
        time.sleep(2)  # 等待下拉内容展开

        # 3. 选择“亚太地区” → “中国香港特别行政区”
        region_selectors = [
            "//span[text()='Asia Pacific']",
            "//span[contains(text(), 'Asia')]",
            "//div[contains(text(), 'Asia Pacific')]"
        ]
        region_selected = False
        for selector in region_selectors:
            try:
                region = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                driver.execute_script("arguments[0].click();", region)
                region_selected = True
                print("已选择：亚太地区")
                break
            except:
                continue

        if not region_selected:
            print("未找到亚太地区选项，尝试直接搜索香港职位...")
            return False

        time.sleep(2)  # 等待子地区加载

        # 4. 勾选“Hong Kong SAR, China”
        hk_selectors = [
            "//span[text()='Hong Kong SAR, China']",
            "//span[contains(text(), 'Hong Kong')]",
            "//label[contains(., 'Hong Kong')]"
        ]
        hk_selected = False
        for selector in hk_selectors:
            try:
                hk = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                driver.execute_script("arguments[0].click();", hk)
                hk_selected = True
                print("已勾选：Hong Kong SAR, China")
                break
            except:
                continue

        if not hk_selected:
            print("未找到香港选项，尝试直接搜索香港职位...")
            return False

        # 5. 点击“确认/应用”按钮（如存在）
        apply_selectors = [
            "button[aria-label*='Apply']",
            "button[aria-label*='apply']",
            "button:contains('Apply')",
            "//button[contains(., 'Apply')]"
        ]
        for selector in apply_selectors:
            try:
                if selector.startswith("//"):
                    apply_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    apply_btn = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                driver.execute_script("arguments[0].click();", apply_btn)
                print("已应用地点筛选")
                break
            except:
                continue

        # 等待页面刷新，加载香港职位
        time.sleep(5)
        return True

    except Exception as e:
        print(f"地点选择过程中出错: {e}")
        return False

def extract_jobs(driver):
    """提取职位列表"""
    jobs = []
    try:
        # 尝试多种常见职位卡片选择器
        job_selectors = [
            "div[class*='job-card']",
            "li[class*='job']",
            "div[class*='JobCard']",
            "article[class*='job']",
            "div[data-automation*='job']"
        ]
        job_cards = []
        for selector in job_selectors:
            job_cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if job_cards:
                print(f"使用选择器 {selector} 找到 {len(job_cards)} 个职位")
                break

        if not job_cards:
            # 如果CSS选择器都没找到，尝试通过文本关键词定位
            page_text = driver.find_element(By.TAG_NAME, "body").text
            lines = page_text.split("\n")
            for i, line in enumerate(lines):
                if ("Analyst" in line or "Associate" in line or "Vice President" in line) and LOCATION_KEYWORD in line:
                    # 提取附近的详细信息
                    job_info = f"{line}\n"
                    if i+1 < len(lines) and ("Hong Kong" in lines[i+1] or "Kong" in lines[i+1]):
                        job_info += f"  位置: {lines[i+1]}\n"
                    else:
                        job_info += f"  位置: 香港\n"
                    jobs.append(job_info)
            return jobs

        for card in job_cards[:50]:  # 最多取50个
            try:
                # 提取标题
                title_elem = card.find_element(By.CSS_SELECTOR, "h3, h2, [class*='title'], [class*='Title']")
                title = title_elem.text.strip()
                # 提取链接
                link_elem = card.find_element(By.TAG_NAME, "a")
                link = link_elem.get_attribute("href")
                if not link.startswith("http"):
                    link = "https://jpmc.fa.oraclecloud.com" + link if link.startswith("/") else TARGET_URL
                # 只保留包含“Hong Kong”的职位（双重保险）
                if LOCATION_KEYWORD in card.text or LOCATION_KEYWORD in title:
                    jobs.append(f"职位: {title}\n链接: {link}\n")
            except:
                continue
    except Exception as e:
        print(f"提取职位时出错: {e}")

    return jobs

def send_email(jobs, sender, password, receiver):
    """发送邮件"""
    if not jobs:
        print("未发现符合条件的岗位，不发送邮件")
        return
    content = f"发现 {len(jobs)} 个摩根大通香港地区职位：\n\n" + "\n\n".join(jobs)
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "摩根大通香港职位监控日报"
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
        print("请配置邮箱密钥：EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER")
        return

    driver = None
    try:
        driver = setup_driver()
        print(f"正在访问: {TARGET_URL}")
        driver.get(TARGET_URL)
        time.sleep(3)  # 等待初始加载

        # 模拟点击选择香港地区
        if select_hong_kong(driver):
            jobs = extract_jobs(driver)
            send_email(jobs, sender, password, receiver)
        else:
            print("无法完成地点筛选，尝试直接提取香港职位...")
            # 退回方案：直接在页面文本中搜索"Hong Kong"
            jobs = extract_jobs(driver)
            send_email(jobs, sender, password, receiver)
    except Exception as e:
        print(f"程序运行出错: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
