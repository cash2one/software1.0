#!/usr/local/python

import requests
from bs4 import BeautifulSoup
import re
from  datetime import datetime


class IDNO(object):

    INFO_RE = re.compile(r'性&nbsp;&nbsp;&nbsp;&nbsp;别：</td><td class="tdc2">(?P<gender>.)</td>.*?出生日期：</td><td class="tdc2">(?P<birthday>.{11})</td>.*?发&nbsp;证&nbsp;地：</td><td class="tdc2">(?P<birthplace>.*?)<br/>')

    def __init__(self, idno):
        self.idno = idno

    def info(self, dic):
        gender = dic['gender'].strip() 
        birthday = dic['birthday'].strip()

        gender = 1 if gender == '男' else 0
        birthday = datetime.strptime(birthday, '%Y年%m月%d日')
        birthplace = dic['birthplace'].strip()
        
        return {'gender': gender, 'birthday': birthday, 'birthplace': birthplace}
    

    def ip138(self):

        flag, msg = self.validno()
        if not flag:
            return flag, msg
        url = 'http://qq.ip138.com/idsearch/index.asp?action=idcard&userid=' + self.idno
        info = requests.get(url).content
        info = info.decode('gbk')
        m = IDNO.INFO_RE.search(info)
        if m:
            info = self.info(m.groupdict())
            return (True, info)
        else:
            return (False, '查无此人')


    def validno(self):

        idno = self.idno

        Errors=[
            '验证通过!',
            '身份证号码位数不对!',
            '身份证号码出生日期超出范围或含有非法字符!',
            '身份证号码校验错误!',
            '身份证地区非法!'
        ]

        area={
            "11":"北京","12":"天津","13":"河北","14":"山西","15":"内蒙古",
            "21":"辽宁","22":"吉林","23":"黑龙江",
            "31":"上海","32":"江苏","33":"浙江","34":"安徽","35":"福建","36":"江西","37":"山东",
            "41":"河南","42":"湖北","43":"湖南","44":"广东","45":"广西","46":"海南",
            "50":"重庆","51":"四川","52":"贵州","53":"云南","54":"西藏",
            "61":"陕西","62":"甘肃","63":"青海","64":"宁夏","65":"新疆",
            "71":"台湾","81":"香港","82":"澳门","91":"国外"
        }

        idno=str(idno).strip()
        idno_list=list(idno)

        
        if(idno[0:2] not in area): # 地区校验
            return (False, Errors[4])

        if(len(idno)==15): # 15位身份号码检测
            if((int(idno[6:8])+1900) % 4 == 0 or((int(idno[6:8])+1900) % 100 == 0 and (int(idno[6:8])+1900) % 4 == 0 )):
                ereg=re.compile('[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}$')#//测试出生日期的合法性
            else:
                ereg=re.compile('[1-9][0-9]{5}[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}$')#//测试出生日期的合法性

            if(re.match(ereg,idno)):
                return (True, Errors[0])
            else:
                return (False, Errors[2])

        elif(len(idno)==18): # 18位身份号码检测
            #出生日期的合法性检查
            #闰年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))
            #平年月日:((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))
            if(int(idno[6:10]) % 4 == 0 or (int(idno[6:10]) % 100 == 0 and int(idno[6:10])%4 == 0 )):
                ereg=re.compile('[1-9][0-9]{5}19[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|[1-2][0-9]))[0-9]{3}[0-9Xx]$')#//闰年出生日期的合法性正则表达式
            else:
                ereg=re.compile('[1-9][0-9]{5}19[0-9]{2}((01|03|05|07|08|10|12)(0[1-9]|[1-2][0-9]|3[0-1])|(04|06|09|11)(0[1-9]|[1-2][0-9]|30)|02(0[1-9]|1[0-9]|2[0-8]))[0-9]{3}[0-9Xx]$')#//平年出生日期的合法性正则表达式

            #//测试出生日期的合法性
            if(re.match(ereg,idno)):
                #//计算校验位
                S = (int(idno_list[0]) + int(idno_list[10])) * 7 + (int(idno_list[1]) + int(idno_list[11])) * 9 + (int(idno_list[2]) + int(idno_list[12])) * 10 + (int(idno_list[3]) + int(idno_list[13])) * 5 + (int(idno_list[4]) + int(idno_list[14])) * 8 + (int(idno_list[5]) + int(idno_list[15])) * 4 + (int(idno_list[6]) + int(idno_list[16])) * 2 + int(idno_list[7]) * 1 + int(idno_list[8]) * 6 + int(idno_list[9]) * 3
                Y = S % 11
                M = "F"
                JYM = "10X98765432"
                M = JYM[Y]#判断校验位
                if(M == idno_list[17]):#检测ID的校验位
                    return (True, Errors[0])
                else:
                    return (False, Errors[3])
            else:
                return (False, Errors[2])
        else:
            return (False, Errors[1])

if __name__ == '__main__':
    info = IDNO('610114198903153555').ip138()
    #info = IDNO('632223199011260314').ip138()
    print(info)

