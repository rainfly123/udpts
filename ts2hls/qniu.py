#!/usr/bin/env python
#coding:utf-8
import os
from hashlib import md5
import urllib
import sys
import time
from urlparse import urlparse, parse_qs
import traceback
import uuid
import base64

# 要求正确的 url_encode 编码，斜线 / 不编码；
# 井号 # 等在浏览器会直接识别为其它含义，若在 path 中必须编码；
# 问号 ? 等在 url 中有特殊含义，若在 path 中必须编码；
# 部分字符 "~!$&'()*+,:;=@[]" 不含双引号 "，虽有特殊含义，但在 path 部分，编码与否，都可以正常访问；
# 另一些，如 双引号 ", 空格 " ", 汉字等必须编码；
#
# 建议 url 的 path 中尽量不含上述部分，建议 url 中尽量不含上述部分。
#
# 参考
# https://www.wikiwand.com/zh-cn/%E7%99%BE%E5%88%86%E5%8F%B7%E7%BC%96%E7%A0%81
# https://www.wikiwand.com/en/Percent-encoding
# https://www.wikiwand.com/de/URL-Encoding
def url_encode(s):
    return urllib.quote(s.decode(sys.stdin.encoding).encode("utf8"), safe="/")

def to_deadline(url, rang):
    up = urlparse(url)
    name = os.path.basename(up.path)
    return int(time.mktime(time.strptime(name,'live-%Y-%m-%d_%H-%M-%S.ts'))) + rang

def t16(t):
    return hex(t)[2:].lower()   # 16 进制小写形式

def summd5(str):
    m = md5()
    m.update(str)
    return m.hexdigest()

def sign(key, t, path):
    a = key + url_encode(path) + t
    sign_s = summd5(a).lower()
    sign_part = "sign=" + sign_s + "&t=" + t
    return sign_part

def sign_url(key, t, p_url):
    url = urllib.unquote(p_url)
    up = urlparse(url)
    path = up.path
    sign_part = sign(key, t, path)
    p_query = up.query
    if p_query:
        query_part = "?" + p_query + "&"+ sign_part
    else:
        query_part = "?" + sign_part

    return up.scheme + "://" + up.netloc + url_encode(path) + query_part

def printurl_encode_help():
    print '''
# 要求正确的 url_encode 编码，斜线 / 不编码；
# 井号 # 等在浏览器会直接识别为其它含义，若在 path 中必须编码；
# 问号 ? 等在 url 中有特殊含义，若在 path 中必须编码；
# 部分字符 "~!$&'()*+,:;=@[]" 不含双引号 "，虽有特殊含义，但在 path 部分，编码与否，都可以正常访问；
# 另一些，如 双引号 ", 空格 " ", 汉字等必须编码；
#
# 建议 url 的 path 中尽量不含上述部分，建议 url 中尽量不含上述部分。
#
# 参考
# https://www.wikiwand.com/zh-cn/%E7%99%BE%E5%88%86%E5%8F%B7%E7%BC%96%E7%A0%81
# https://www.wikiwand.com/en/Percent-encoding
# https://www.wikiwand.com/de/URL-Encoding
    '''

def signt_help():
    print
    print "./signt.py time <key> <url> <t,eg: 3600>"
    print "./signt.py deadline <key> <url> <deadline>"
    print "./signt.py check <key> <signed_url>"
    print "./signt.py show <t, eg: 55bb9b80>"
    print "./signt.py genkey"
    print "\n"
    print '''
# example:

# url = "http://xxx.yyy.com/DIR1/中文/vodfile.mp4?sfdf=dfe"
# key = 12345678
# 过期时间点: Sat Aug  1 00:00:00 2015  ==> 1438358400

# 执行: signt.py deadline 12345678  http://xxx.yyy.com/DIR1/中文/vodfile.mp4?sfdf=dfe 1438358400
# 签名 url 为: http://xxx.yyy.com/DIR1/%E4%B8%AD%E6%96%87/vodfile.mp4?sfdf=dfe&sign=6356bca0d2aecf7211003e468861f5ea&t=55bb9b80

# 执行: signt.py check 12345678 "http://xxx.yyy.com/DIR1/%E4%B8%AD%E6%96%87/vodfile.mp4?sfdf=dfe&sign=6356bca0d2aecf7211003e468861f5ea&t=55bb9b80"
# 显示: True
    '''
    print "\n"
    printurl_encode_help()

def sign_time(key, url, rang):
    deadline = to_deadline(url, rang)
    return sign_deadline(key, url, deadline)

def sign_deadline(key, url, deadline):
    t = t16(deadline)
    signed_url = sign_url(key, t, url)
    return signed_url

# signed_url 是正确 url_encode 编码后签出的 url
# 见 url_encode 方法注释
def sign_check(key, signed_url):
    print "\n 要求: 待检测的 url 是正确 url_encode 编码后签出的 url"
    printurl_encode_help()
    u = urlparse(signed_url)
    t = parse_qs(u.query)["t"][0]
    sign_s = summd5(key + u.path + t).lower()
    print
    print("deadline: " + str(int(t, 16)) + " , " + time.ctime(int(t, 16)))
    print(sign_s)
    print(parse_qs(u.query)["sign"][0] == sign_s)

def show_t(t):
    i_t = int(t, 16)
    s_t = time.ctime(i_t)
    print(t + " : " + str(i_t) + " : " + s_t)

# 仅用于测试
def gen_key():
    print base64.urlsafe_b64encode(str(uuid.uuid4()))[:40].lower()

#300 seconds
TIME = 240
KEY = "c8aa26993ba850ba5da86eab41a84aab1babfcba"

def Sign_URL(url):
    return sign_time(KEY, url, TIME)

if __name__ == "__main__":
    print Sign_URL("http://videoa.southtv.cn/zjws/live.m3u8")
