# -*- coding: utf-8 -*-
# @Time : 2025/5/13 13:48
# @Author : QPK
# @File : drission_boss.py
# @Project : 调试.py
# @Software : PyCharm

import random
import time
import csv
import urllib.parse

from DrissionPage import ChromiumPage
from selenium.common.exceptions import TimeoutException
from tqdm import tqdm

# 要爬取的关键词列表
KEYWORDS = [
    '直播', '电商', '主播', '助播',
    '带货', '卖货', '选品', '互联网营销'
]

# 要爬取的城市及其对应编码
CITIES = {
    '常德': '101250600',
    '邵阳': '101250900'
}

for city_name, city_code in CITIES.items():
    # 根据城市名称动态生成文件名
    csv_path = f"../job_list - {city_name}.csv"
    with open(csv_path, mode='w', encoding='utf-8', newline='') as f:
        fieldnames = [
            '关键词', '职位名称', '薪资', '学历', '经验',
            '联系人', '公司名称', '公司领域', '公司规模',
            '职位城市', '职位区域', '职位商圈',
            '岗位标签', '福利标签','公司详情链接'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        dp = ChromiumPage()
        dp.listen.start('search/joblist.json')

        # 外层进度：关键词列表
        for kw in tqdm(KEYWORDS, desc=f"{city_name} 关键词进度", unit="kw"):
            # 根据当前城市编码动态请求 URL
            url = (
                'https://www.zhipin.com/web/geek/jobs'
                f'?query={urllib.parse.quote(kw)}&city={city_code}'
            )
            dp.get(url)

            # 页面请求循环
            page_bar = tqdm(desc=f"{kw} 页数", unit="页", leave=False)
            while True:
                try:
                    got = dp.listen.wait(timeout=5)
                except TimeoutException:
                    page_bar.write(f"[{kw}] 等待超时，切换下一个关键词")
                    break

                if got is False or got is True:
                    page_bar.write(f"[{kw}] 未获取到新记录，停止本关键词")
                    break

                rec = got
                data = rec.response.body
                jobList = data.get('zpData', {}).get('jobList', [])
                if not jobList:
                    page_bar.write(f"[{kw}] 无更多数据，停止本关键词")
                    break

                for job in jobList:
                    try:
                        writer.writerow({
                            '关键词':   kw,
                            '职位名称': job['jobName'],
                            '薪资':     job['salaryDesc'],
                            '学历':     job['jobDegree'],
                            '经验':     job['jobExperience'],
                            '联系人':   job['bossName'],
                            '公司名称': job['brandName'],
                            '公司领域': job['brandIndustry'],
                            '公司规模': job['brandScaleName'],
                            '职位城市': job['cityName'],
                            '职位区域': job['areaDistrict'],
                            '职位商圈': job['businessDistrict'],
                            '岗位标签': ','.join(job.get('skills', [])),
                            '福利标签': ','.join(job.get('welfareList', [])),
                            '公司详情链接':'https://www.zhipin.com/job_detail/' + str(job['encryptJobId']) + '.html'
                        })
                        # https://www.zhipin.com/job_detail/615d5cfa6a0f820903V_0tW9EVdR.html
                    except Exception:
                        continue

                page_bar.update(1)

                # 滚动触发下一批加载
                dp.scroll.to_bottom()
                time.sleep(random.uniform(1, 2))

            page_bar.close()

    print(f"{city_name} 爬取完成，结果已写入 {csv_path}")

print("所有城市、关键词爬取完毕。")