# coding=utf-8
from trade.models import *
trades = Trade.objects.all()
for trade in trades:
    if trade.status == 0 and trade.stockid:
        newTrade = Trade_memory.objects.create(trade=trade,stockid=trade.stockid)