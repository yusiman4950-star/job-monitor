# scraper3.py
import re
import os
import smtplib
from email.message import EmailMessage
from requests_html import HTMLSession

# ================= 只需修改这里 =================
TARGET_URL = "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job-search?keywords=&location=Hong%20Kong&locationId=&locationLevel=&nearByRadius="
LOCATION_KEYWORD = "Hong Kong"
# ===============================================

def extract_jobs_automatically(html):
    """
    完全自动化提取：不依赖任何CSS类名，只依靠正文中的关键词和位置
    """
    # 首先获取页面的纯文本
    text = html.text
    
    # 常见职位标题关键词（摩根大通常用）
    job_title_keywords = [
        "Analyst", "Associate", "Vice President", "Executive Director",
        "Intern", "Summer", "Full-time", "Part-time", "Manager", "Director",
        "Specialist", "Coordinator", "Consultant", "Developer", "Engineer"
    ]
    
    # 方法1：寻找所有包含职位关键词且附近有"Hong Kong"的段落块
    # 将文本按换行分割
    lines = text.split('\n')
    job_blocks = []
    current_block = []
    for line in lines:
        current_block.append(line)
        if line.strip() == "" and len(current_block) > 3:
            # 一个段落结束
            block_text = "\n".join(current_block)
            # 检查是否包含职位关键词且包含香港位置
            if any(kw.lower() in block_text.lower() for kw in job_title_keywords) and LOCATION_KEYWORD.lower() in block_text.lower():
                job_blocks.append(block_text)
            current_block = []
    
    # 去重
    seen = set()
    unique_blocks = []
    for block in job_blocks:
        # 提取职位标题行（通常是第一行或包含关键词的行）
        lines_in_block = block.split('\n')
        first_line = lines_in_block[0].strip()
        if first_line and first_line not in seen:
            seen.add(first_line)
            unique_blocks.append(block)
    
    # 方法2：如果方法1没找到，尝试从HTML元素中提取所有a标签的文本（因为职位通常有链接）
    if not unique_blocks:
        # 获取所有a标签文本
        for link in html.find('a'):
            link_text = link.text.strip()
            if any(kw.lower() in link_text.lower() for kw in job_title_keywords) and LOCATION_KEYWORD.lower() in link_text.lower():
                # 获取父级或附近文本
                parent = link.element.getparent()
                if parent is not None:
                    parent_text = parent.text_content()
                    if LOCATION_KEYWORD.lower() in parent_text.lower():
                        unique_blocks.append(parent_text)
                else:
                    unique_blocks.append(link_text)
    
    # 整理成统一格式
    jobs = []
    for block in unique_blocks:
        # 提取第一行作为标题
        lines = block.split('\n')
        title = lines[0].strip() if lines else "未知职位"
        # 查找链接：尝试从文本中提取url
        url_match = re.search(r'https?://[^\s\)]+', block)
        url = url_match.group(0) if url_match else TARGET_URL
        jobs.append(f"职位: {title}\n链接: {url}\n")
    
    # 如果两种方法都没找到，返回空列表
    return jobs

def fetch_jobs():
    session = HTMLSession()
    print(f"正在加载页面: {TARGET_URL}")
    try:
        response = session.get(TARGET_URL)
        response.html.render(timeout=30, sleep=2)  # 等待JS渲染
        jobs = extract_jobs_automatically(response.html)
        session.close()
        return jobs
    except Exception as e:
        print(f"加载失败: {e}")
        session.close()
        return None

def send_email(jobs, sender, pwd, receiver):
    if not jobs:
        print("未发现符合条件的岗位，不发送邮件。")
        return
    content = f"发现 {len(jobs)} 个在{LOCATION_KEYWORD}的摩根大通职位：\n\n" + "\n".join(jobs)
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = f"摩根大通 {LOCATION_KEYWORD} 职位监控日报"
    msg["From"] = sender
    msg["To"] = receiver
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.starttls()
            smtp.login(sender, pwd)
            smtp.send_message(msg)
        print("邮件发送成功。")
    except Exception as e:
        print(f"邮件发送失败: {e}")

def main():
    sender = os.environ.get("EMAIL_SENDER")
    pwd = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")
    if not all([sender, pwd, receiver]):
        print("请配置邮箱相关的密钥 (EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER)。")
        return
    jobs = fetch_jobs()
    if jobs is not None:
        send_email(jobs, sender, pwd, receiver)

if __name__ == "__main__":
    main()
