# -*- coding:utf-8 -*-
# bb[0]:股票名  bb[1]:今日开盘价    bb[2]：昨日收盘价    bb[3]:当前价格   bb[4]:今日最高价    bb[5]:今日最低价
# bb[6]:买一报价 bb[7]:卖一报价     bb[8]:成交股票数/100 bb[9]:成交金额/w bb[10]:买一申请股数 bb[11]:买一报价
# bb[12]:买二股数 bb[13]:买二报价   bb[14]:买三股数      bb[15]:买三报价  bb[16]:买四申请股数 bb[17]:买四报价
# bb[18]:买五股数 bb[19]:买五报价   bb[20]:卖一股数      bb[21]:卖一报价  bb[22]:卖二申请股数 bb[23]:卖二报价
# bb[24]:卖三股数 bb[25]:卖三报价   bb[26]:卖四股数      bb[27]:卖四报价  bb[28]:卖五股数     bb[29]:卖五报价
# bb[30]:日期     bb[31]:时间     bb[8]:不知道

import urllib2
import time
from django.core.management.base import BaseCommand
from stock.models import *

# from stockSort import stocksort
stockDict = {}
stockTimeList = []


class updatePrice(object):
    def __init__(self):
        self.url = 'http://hq.sinajs.cn/list='

    def getSellPrice(self, stockID):
        dataList = {}
        try:
            if stockID[0] == '0' or stockID[0] == '3':
                stockID = 'sz' + stockID
            elif stockID[0] == '6':
                stockID = 'sh' + stockID

            request = urllib2.Request(self.url + str(stockID))
            response = urllib2.urlopen(request)
            contents = response.read()

            sellPrice = (contents).split(",")[3]
            # if sellPrice == '0.000':
            #     print(self.url+stockID)

            return sellPrice

        except urllib2.URLError, e:
            print "Connction failed"


# if __name__ == '__main__':

class Command(BaseCommand):
    def handle(self, *args, **options):
        getCurrentPrice = updatePrice()
    # ff = open("/Users/DengJ/PycharmProjects/Test/stockCodeList.txt", "r")
    #
    # stocks = []
    # for stock in ff.readlines():
    #     strTemp = stock.split("\t")[0]
    #     stocks.append(strTemp)
    # ff.close()

    # stockscode = []
        stocks = Stock.objects.all()
    # for stock in stocks:
    #     strTemp = stock.stockid + ','
    #     strTemp = unicode.encode(strTemp, encoding='utf-8')
    #     if strTemp[0] == '0' or strTemp[0] == '3':
    #         strTemp = 'sz' + strTemp
    #     elif strTemp[0] == '6':
    #         strTemp = 'sh' + strTemp
    #     stockscode = stockscode + strTemp
    # # print(stocks.__len__())
        count = 0
        t1 = time.time()
        for stockId in stocks:
            count += 1
            stockcode = unicode.encode(stockId.stockid,encoding='utf-8')
            sellprice = getCurrentPrice.getSellPrice(stockcode)
            print(sellprice)
        # print(count)
        t2 = time.time()
        print(t2 - t1)
        print('finished')