#!/usr/bin/python3
import requests
import datetime
import re
import execjs
import sys
import json


def login(sess, uname, pwd):
    salt_url = 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/index.do'
    salt_response = sess.get(salt_url)
    salt_response.encoding = 'utf-8'
    lt = re.search('name="lt" value="(.*?)"', salt_response.text).group(1)
    salt = re.search('id="pwdDefaultEncryptSalt" value="(.*?)"', salt_response.text).group(1)
    execution = re.search('name="execution" value="(.*?)"', salt_response.text).group(1)
    f = open("encrypt.js", 'r', encoding='UTF-8')
    line = f.readline()
    js = ''
    while line:
        js = js + line
        line = f.readline()
    ctx = execjs.compile(js)
    password = ctx.call('_ep', pwd, salt)

    login_url = 'https://newids.seu.edu.cn/authserver/login?service=http%3A%2F%2Fehall.seu.edu.cn%2Fqljfwapp2%2Fsys%2FlwReportEpidemicSeu%2Findex.do'
    personal_info = {'username': uname,
                     'password': password,
                     'lt': lt,
                     'dllt': 'userNamePasswordLogin',
                     'execution': execution,
                     '_eventId': 'submit',
                     'rmShown': '1'}
    login_response = sess.post(login_url, personal_info)
    login_response.encoding = 'utf-8'

    if re.search("学院", login_response.text):
        print("登陆成功!")
    else:
        print("登陆失败!请检查一卡通号和密码。")
        raise


def get_header(sess, cookie_url):
    cookie_response = sess.get(cookie_url)
    weu = requests.utils.dict_from_cookiejar(cookie_response.cookies)['_WEU']
    cookie = requests.utils.dict_from_cookiejar(sess.cookies)

    header = {'Referer': 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/index.do',
              'Cookie': '_WEU=' + weu + '; MOD_AUTH_CAS=' + cookie['MOD_AUTH_CAS'] + ';'}
    return header


def get_info(sess, header, username):
    info_url = 'http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/wdqj/wdqjbg.do'
    info_response = sess.post(info_url, data={"XSBH":username}, headers=header)
    return info_response


def back(sess, username):
    cookie_url = 'http://ehall.seu.edu.cn/ygfw/sys/swpubapp/indexmenu/getAppConfig.do?appId=5869188708264821&appName=xsqjappseuyangong'
    header = get_header(sess, cookie_url)
    info = get_info(sess, header, username)
    
    info.encoding = 'utf-8'
    raw_info = re.search('"rows":\[(.*?)\]', info.text).group(1)
    raw_info = raw_info.split("},")

    leave_list = []
    for item in raw_info:
        if item[-1] != '}':
            item += '}'
        leave_list.append(json.loads(item))

    post_key = ['SQBH', 'XSBH', 'SHZT', 'XJFS', 'XJSJ', 'XJRQ', 'SQR', 'SQRXM', 'THZT', 'XJZT']

    for leave in leave_list:
        if leave["XJZT"] == '0' and leave["SHZT"] == '99':
            post_info = {}
            
            for key in post_key:
                if key in leave.keys():
                    if leave[key] == 'null':
                        post_info[key] = ''
                    else:
                        post_info[key] = leave[key]
            
            post_info["XJFS"] = "2"
            post_info["XJSJ"] = (datetime.datetime.now() + datetime.timedelta()).strftime("%Y-%m-%d %H:%M:%S")
            post_info["XJRQ"] = (datetime.datetime.now() + datetime.timedelta()).strftime("%Y-%m-%d")
            post_info['SQR'] = username
            post_info['SQRXM'] = leave["XM"]
            
            post_info["XJZT"] = '2'
            if post_info["XJZT"] == '1':
                return -1
            else:
                post_info.pop('XJZT')

            post_info = {'data':str(post_info)}
            
            print(post_info)
            back_url = "http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/leaveApply/addXjApply.do"
            back = sess.post(back_url, data=post_info, headers=header)
            back.encoding = 'utf-8'
            if back.status_code == 200:
                print('销假成功！')
            else:
                print("销假失败！")


def main():
    sess = requests.session()
    try:
        username = sys.argv[1]
        password = sys.argv[2]
    except:
        username = input("一卡通号：")
        password = input("密码：")
    login(sess, username, password)
    back(sess, username)
    sess.close()


if __name__ == '__main__':
    main()

