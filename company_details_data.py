import random
import pandas as pd
import time
import signal
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 读取上一步爬好的csv
file_path = 'job_list - 邵阳.csv'
data = pd.read_csv(file_path)

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")


# 路径修改为chromedriver.exe所在路径
service = Service(r"D:\chromedriver\chromedriver.exe")
driver = webdriver.Chrome(options=chrome_options)


# 用于存储当前批次未保存的记录
batch_details = []


def save_progress(details):
    if not details:
        return
    df = pd.DataFrame(details)
    output_path = 'company_details_邵阳.xlsx'
    try:
        existing_df = pd.read_excel(output_path)
        # 将新数据追加到现有数据后面
        df = pd.concat([existing_df, df], ignore_index=True)
    except FileNotFoundError:
        pass
    df.to_excel(output_path, index=False)
    print(f"\nProgress saved to {output_path}")


def signal_handler(sig, frame):
    print('\nInterrupt received, saving progress...')
    save_progress(batch_details)
    driver.quit()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

try:
    for index, row in data.iterrows():
        company_url = row['公司详情链接'] + '?ka=job-cominfo'
        try:
            driver.get(company_url)

            more_info_button = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable((By.XPATH, "//label[@ka='company_full_info']"))
            )
            more_info_button.click()

            business_detail_div = WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'business-detail.show-business-all'))
            )

            li_elements = business_detail_div.find_elements(By.TAG_NAME, 'li')

            company_info = row.to_dict()
            for li in li_elements:
                key = li.find_element(By.CLASS_NAME, 't').text.strip().replace("：", "").replace("\n", "")
                value = li.text.replace(key, '').strip().replace("：", "").replace("\n", "")
                company_info[key] = value

            address_div = driver.find_element(By.CLASS_NAME, 'location-address')
            address = address_div.text.strip()
            company_info['地址'] = address

            # 将当前记录添加到批次列表
            batch_details.append(company_info)
            print(company_info)
            print(f"Current batch count: {len(batch_details)}")

            # 每爬取100条数据保存一次
            if len(batch_details) == 100:
                save_progress(batch_details)
                batch_details = []  # 清空已保存的批次数据

        except Exception as e:
            print(f"Error processing {company_url}: {e}")
            # 出现错误时保存当前已爬取的批次数据，并清空列表（防止重复保存）
            save_progress(batch_details)
            batch_details = []
            continue

        time.sleep(random.uniform(4, 8))

except Exception as e:
    print("Unexpected error during scraping:", e)
    save_progress(batch_details)

finally:
    # 如果循环结束后还有未保存的数据，进行最后保存
    if batch_details:
        save_progress(batch_details)
    driver.quit()
