# -*- coding: utf-8 -*-
import ipaddress
import requests
import json
from netaddr import IPSet
import time

"""
从亚马逊CloudFront IP段中筛选出特定地区的IP段，配合cloudflarespeedtest用于优选
注：https://lite.ip2location.com按指定地区查询到的IP段存在一些错误，故筛选结果不能保证完全准确
"""

regions = {
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
def chooseRegion(first):
    tips = "请选择您要筛选的目标地区的序号：\n" if first else ""
    for key in regions:
        tips += key + "." + regions[key][1] + " "
    tips += "\n"
    target = input(tips)
    try:
        return regions[target]
    except:
        print("您输入的序号不在选项内，请重新选择：")
        return chooseRegion(False)


"""
构建目标地区的IP段
来源：https://lite.ip2location.com
"""
[code, region] = chooseRegion(True)
timestamp = str(round(time.time() * 1000))
response = requests.get(
    f"https://cdn-lite.ip2location.com/datasets/{code}.json?_={timestamp}"
)
ip_ranges = json.loads(response.text)["data"]
target_networks = []
for ip_range in ip_ranges:
    begin = ipaddress.IPv4Address(ip_range[0])
    end = ipaddress.IPv4Address(ip_range[1])
    for network in ipaddress.summarize_address_range(begin, end):
        target_networks.append(str(network))
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
output = f"CFT_{region}.txt";
f = open(output, "w")
for cidr in intersection.iter_cidrs():
    ip_count += cidr.size
    network_count += 1
    f.write(str(cidr) + "\n")
f.close()

print(f"{region}的IP段已存入：{output}，IP段总数：{network_count}，IP总数：{ip_count}")
