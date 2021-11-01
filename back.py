#!/usr/bin/python3
import requests
import datetime
import re
import execjs
import sys


def login(sess, uname, pwd):
    login_url = 'http://ehall.seu.edu.cn/qljfwapp2/sys/lwReportEpidemicSeu/index.do'
    get_login = sess.get(login_url)
    get_login.encoding = 'utf-8'
    lt = re.search('name="lt" value="(.*?)"', get_login.text).group(1)
    salt = re.search('id="pwdDefaultEncryptSalt" value="(.*?)"', get_login.text).group(1)
    execution = re.search('name="execution" value="(.*?)"', get_login.text).group(1)
    f = open("encrypt.js", 'r', encoding='UTF-8')
    line = f.readline()
    js = ''
    while line:
        js = js + line
        line = f.readline()
    ctx = execjs.compile(js)
    password = ctx.call('_ep', pwd, salt)

    login_post_url = 'https://newids.seu.edu.cn/authserver/login?service=http%3A%2F%2Fehall.seu.edu.cn%2Fqljfwapp2%2Fsys%2FlwReportEpidemicSeu%2Findex.do'
    personal_info = {'username': uname,
                     'password': password,
                     'lt': lt,
                     'dllt': 'userNamePasswordLogin',
                     'execution': execution,
                     '_eventId': 'submit',
                     'rmShown': '1'}
    post_login = sess.post(login_post_url, personal_info)
    post_login.encoding = 'utf-8'

    if re.search("学院", post_login.text):
        print("登陆成功!")
    else:
        print("登陆失败！请检查一卡通号和密码。")


def get_header(sess, cookie_url):
    get_cookie = sess.get(cookie_url)
    weu = requests.utils.dict_from_cookiejar(get_cookie.cookies)['_WEU']
    cookie = requests.utils.dict_from_cookiejar(sess.cookies)

    header = {'Referer': 'http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/*default/index.do',
              'Cookie': '_WEU=' + weu + '; MOD_AUTH_CAS=' + cookie['MOD_AUTH_CAS'] + ';'}
    return header


def get_info(sess, header, username):
    personal_info_url = 'http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/wdqj/wdqjbg.do'
    get_personal_info = sess.post(personal_info_url, data={"XSBH":username}, headers=header)
    return get_personal_info


def back(sess, username):
    cookie_url = 'http://ehall.seu.edu.cn/ygfw/sys/swpubapp/indexmenu/getAppConfig.do?appId=5869188708264821&appName=xsqjappseuyangong'
    header = get_header(sess, cookie_url)
    get_personal_info = get_info(sess, header, username)
    
    get_personal_info.encoding = 'utf-8'
    raw_personal_info = re.search('"rows":\[\{(.*?)}', get_personal_info.text).group(1)
    raw_personal_info = raw_personal_info.split(',')

    post_key = ['SQBH', 'XSBH', 'SHZT', 'XJFS', 'XJSJ', 'XJRQ', 'SQR', 'SQRXM', 'THZT']

    temp_dict = {}
    post_info = {}
    for info in raw_personal_info:
        key_value = info.split(':')
        key = key_value[0].strip('"')
        val = key_value[1].strip('"')
        temp_dict[key] = val

    for key in post_key:
        if key in temp_dict.keys():
            if temp_dict[key] == 'null':
                post_info[key] = ''
            else:
                post_info[key] = temp_dict[key]
    
    post_info["XJFS"] = "2"
    post_info["XJSJ"] = (datetime.datetime.now() + datetime.timedelta()).strftime("%Y-%m-%d %H:%M:%S")
    post_info["XJRQ"] = (datetime.datetime.now() + datetime.timedelta()).strftime("%Y-%m-%d")
    post_info['SQR'] = username
    post_info['SQRXM'] = temp_dict["XM"]

    post_info = {'data':str(post_info)}
    
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

