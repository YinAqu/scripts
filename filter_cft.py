# -*- coding: utf-8 -*-
import ipaddress
import requests
import json
from netaddr import IPSet
import time

"""
从亚马逊CloudFront IP段中筛选出特定国家(节点服务器所在国家)的IP段，配合cloudflarespeedtest用于优选
注：https://lite.ip2location.com按指定国家查询到的IP段存在一些错误，故筛选结果不能保证完全准确
"""

countries = {
    "1": ["HK","香港"],
    "2": ["TW","台湾"],
    "3": ["SG","新加坡"], 
    "4": ["KR","韩国"],
    "5": ["JP","日本"],
    "6": ["US","美国"],
    "7": ["GB","英国"],
    "8": ["FR","法国"],
    "9": ["DE","德国"],
}
def chooseCountry(first):
    tips = "请选择您要筛选的目标地点的序号：\n" if first else ""
    for key in countries:
        tips += key + "." + countries[key][1] + " "
    tips += "\n"
    target = input(tips)
    try:
        return countries[target]
    except:
        print("您输入的序号不在选项内，请重新选择：")
        return chooseCountry(False)


"""
构建目标国家的IP段
来源：https://lite.ip2location.com
"""
[code, country] = chooseCountry(True)
timestamp = str(round(time.time() * 1000))
response = requests.get(
    f"https://cdn-lite.ip2location.com/datasets/{code}.json?_={timestamp}"
)
ip_ranges = json.loads(response.text)["data"]
target_networks = []
for ip_range in ip_ranges:
    begin = ipaddress.IPv4Address(ip_range[0])
    end = ipaddress.IPv4Address(ip_range[1])
    for jp_network in ipaddress.summarize_address_range(begin, end):
        target_networks.append(str(jp_network))
target_set = IPSet(target_networks)

# 获取CFT的IP段
response = requests.get(
    "https://d7uri8nf7uskq.cloudfront.net/tools/list-cloudfront-ips"
)
aws_networks = json.loads(response.text)["CLOUDFRONT_GLOBAL_IP_LIST"]
aws_set = IPSet(aws_networks)

# 取交集
intersection = target_set & aws_set

ip_count = 0
network_count = 0
f = open(f"CFT_{country}.txt", "w")
for cidr in intersection.iter_cidrs():
    ip_count += cidr.size
    network_count += 1
    f.write(str(cidr) + "\n")
f.close()

print(f"{country}IP段总数：{network_count}，IP总数：{ip_count}")
