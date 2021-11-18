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


def leave(sess, username, reason):
    cookie_url = 'http://ehall.seu.edu.cn/ygfw/sys/swpubapp/indexmenu/getAppConfig.do?appId=5869188708264821&appName=xsqjappseuyangong'
    header = get_header(sess, cookie_url)
    info = get_info(sess, header, username)
    
    info.encoding = 'utf-8'
    raw_info = re.search('"rows":\[(.*?)\]', info.text).group(1)
    raw_info = raw_info.split("},")

    leave_list = []
    for leave in raw_info:
        if leave[-1] != '}':
            leave += '}'
        leave_list.append(json.loads(leave))

    post_key = ['QJLX_DISPLAY', 'QJLX', 'DZQJSY_DISPLAY', 'DZQJSY', 'QJXZ_DISPLAY', 'QJXZ', 'QJFS_DISPLAY', 'QJFS', 'YGLX_DISPLAY', 'YGLX', 'SQSM', 'QJKSRQ', 'QJJSRQ', 'QJTS', 'QJSY', 'ZMCL', 'SJH', 'DZSFLX_DISPLAY', 'DZSFLX', 'HDXQ_DISPLAY', 'HDXQ', 'DZSFLN_DISPLAY', 'DZSFLN', 'DZSFLKJSS_DISPLAY', 'DZSFLKJSS', 'DZ_SFCGJ_DISPLAY', 'DZ_SFCGJ', 'DZ_GJDQ_DISPLAY', 'DZ_GJDQ', 'QXSHEN_DISPLAY', 'QXSHEN', 'QXSHI_DISPLAY', 'QXSHI', 'QXQ_DISPLAY', 'QXQ', 'QXJD', 'XXDZ', 'JTGJ_DISPLAY', 'JTGJ', 'CCHBH', 'SQBH', 'XSBH', 'JJLXR', 'JJLXRDH', 'JZXM', 'JZLXDH', 'DSXM', 'DSDH', 'FDYXM', 'FDYDH', 'SFDSQ']

    last_leave = leave_list[0]
    post_info = {}

    for key in post_key:
        if key in last_leave.keys():
            if last_leave[key] == 'null':
                post_info[key] = ''
            elif last_leave[key] == None:
                post_info[key] = ''
            else:
                post_info[key] = last_leave[key]

    post_info['SQBH'] = ""
    post_info['XSBH'] = ""
    post_info['QJTS'] = "1"
    post_info['QJKSRQ'] = (datetime.datetime.now() + datetime.timedelta(days=+1)).strftime("%Y-%m-%d") + " 07:00"
    post_info['QJJSRQ'] = (datetime.datetime.now() + datetime.timedelta(days=+1)).strftime("%Y-%m-%d") + " 23:00"
    post_info['QJFS_DISPLAY'] = "请假"
    post_info['QJFS'] = "1"
    post_info['QJSY'] = reason
    post_info['ZMCL'] = ""
    post_info['JTGJ_DISPLAY'] = ""
    post_info['JTGJ'] = ""
    post_info['CCHBH'] = ""
    post_info['SFDSQ'] = "0"

    post_info = {'data':str(post_info)}
    print(post_info)

    leave_url = "http://ehall.seu.edu.cn/ygfw/sys/xsqjappseuyangong/modules/leaveApply/addLeaveApply.do"
    leave_response = sess.post(leave_url, data=post_info, headers=header)
    leave_response.encoding = 'utf-8'
    if leave_response.status_code == 200:
        print('请假成功！')
        print(leave_response.text)
    else:
        print("请假失败！")


def main():
    sess = requests.session()
    try:
        username = sys.argv[1]
        password = sys.argv[2]
        reason = sys.argv[3]
    except:
        username = input("一卡通号：")
        password = input("密码：")
        reason = input("请假理由：")
    login(sess, username, password)
    leave(sess, username, reason)
    sess.close()


if __name__ == '__main__':
    main()

