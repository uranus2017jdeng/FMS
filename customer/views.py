# coding=utf-8
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db.models import Q
from django.utils import timezone

import os
import random
import string
import datetime
import traceback
import json
import time
import urllib2

from shande.settings import BASE_DIR
from shande.util import *
from ops.models import *
from super.models import *
from sale.models import *
from customer.models import *
from spot.models import *
from trade.models import *
from stock.models import *
# from spot.models import *
from teacher.models import *

import logging
logger = logging.getLogger("django")

@login_required()
def customerManage(request):
    # t1 = time.clock()
    if (not request.user.userprofile.title.role_name in ['admin', 'ops', 'sale', 'salemanager', 'saleboss']):
        return HttpResponseRedirect("/")
    endDate = request.POST.get('endDate', "")
    if endDate == '':
        endDate = datetime.date.today() + datetime.timedelta(days=1)
    else:
        endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d").date()
    startDate = request.POST.get('startDate', "")
    if startDate == "":
        startDate = datetime.date.today()
    else:
        startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
    wxList = None
    qqList = None
    if request.user.userprofile.title.role_name in ['sale']:
        try:
            sale = Sale.objects.get(binduser=request.user)
            wxList = Wx.objects.filter(bindsale=sale)
            qqList = Qq.objects.filter(bindsale=sale)
        except:
            data = {
                "message": "该用户尚未绑定开发ID，请联系经理绑定ID后重新登陆。"
            }
            return render(request, 'error.html', data)
    data = {
        "wxList": wxList,
        "qqList": qqList,
        "startDate": str(startDate),
        "endDate": str(endDate),
    }
    print(str(startDate))
    # t2 = time.clock()
    # logger.error("customer/customerManage cost time: %f"%(t2-t1))
    return render(request, 'customer/customerManage.html', data)

@login_required()
def queryCustomer(request):
    #查看权限：admin ops saleboss salemanager sale
    # t1 = time.clock()
    customers = Customer.objects.all().order_by('-modify')

    #不同角色看到不同的列表
    if request.user.userprofile.title.role_name in ['salemanager']:
        company = request.user.userprofile.company
        department = request.user.userprofile.department
        customers = customers.filter(sales__company=company, sales__department=department)
    elif request.user.userprofile.title.role_name in ['saleboss']:
        company = request.user.userprofile.company
        customers = customers.filter(sales__company=company)
    elif request.user.userprofile.title.role_name in ['sale']:
        sale = Sale.objects.get(binduser=request.user)
        customers = customers.filter(sales=sale)
    else:
        customers = customers
    # 去掉不诚信和删除状态的客户
    if not request.user.userprofile.title.role_name in ['admin', 'ops', 'saleboss']:
        customers = customers.exclude(status=98)
    customers = customers.exclude(status=99)

    #按条件查询
    # customers = customers.filter(sales__company__icontains=request.GET.get('company', ''))
    # customers = customers.filter(sales__department__icontains=request.GET.get('department', ''))
    if request.GET.get('saleid') :
         customers = customers.filter(sales__saleId__icontains=request.GET.get('saleid'))
    # if request.GET.get('saleswx', '') != '':
    #     customers = customers.filter(saleswx__wxid__icontains=request.GET.get('saleswx', ''))
    # if request.GET.get('salesqq', '') != '':
    #     customers = customers.filter(salesqq__qqid__icontains=request.GET.get('salesqq', ''))
    if request.GET.get('wxqq') :
        customers = customers.filter(Q(wxid="", qqid__icontains=request.GET.get('wxqq'))|Q(qqid="", wxid__icontains=request.GET.get('wxqq')))
    customers = customers.filter(name__icontains=request.GET.get('name', ''))
    customers = customers.filter(phone__icontains=str(request.GET.get('phone', '')).strip())
    # if request.GET.get('wxid', '') != '':
    #     customers = customers.filter(wxid__icontains=request.GET.get('wxid', ''))
    # if request.GET.get('wxname', '') != '':
    #     customers = customers.filter(wxname__icontains=request.GET.get('wxname', ''))
    # if request.GET.get('qqid', '') != '':
    #     customers = customers.filter(qqid__icontains=request.GET.get('qqid', ''))
    # if request.GET.get('qqname', '') != '':
    #     customers = customers.filter(qqname__icontains=request.GET.get('qqname', ''))
    # customers = customers.filter(message__icontains=request.GET.get('message', ''))
    # if request.GET.get('minstartup', '') != '':
    #     customers = customers.filter(startup__gte=request.GET.get('minstartup'))
    # if request.GET.get('maxstartup', '') != '':
    #     customers = customers.filter(startup__lte=request.GET.get('maxstartup'))
    # if request.GET.get('gem', '') != '':
    #     customers = customers.filter(gem=request.GET.get('gem'))
    if request.GET.get('startDate', '') != '':
        customers = customers.filter(create__gte=request.GET.get('startDate'))
    if request.GET.get('endDate', '') != '':
        customers = customers.filter(create__lte=request.GET.get('endDate'))
    if(request.GET.get('status', '') != ''):
        if request.GET.get('status') == '40':
            customers = customers.filter(status=request.GET.get('status'))
        elif request.GET.get('status') == '20':
            customers = customers.filter(status=request.GET.get('status'))
        elif request.GET.get('status') == '0':
            customers = customers.filter(status=request.GET.get('status'))
        else:
            customers = customers.exclude(status=40)

    #分页
    p = Paginator(customers, 20)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        customerPage = p.page(page)
    except (EmptyPage, InvalidPage):
        customerPage = p.page(p.num_pages)
    data = {
        "customerPage": customerPage,
        "requestArgs": getArgsExcludePage(request),
    }
    # t2 = time.clock()
    # logger.error("customer/queryCustomer cost time: %f"%(t2-t1))
    return render(request, 'customer/queryCustomer.html', data)

#编辑和修改客户信息
@login_required()
def addCustomer(request):
    # t1 = time.clock()
    data = {}

    try:
        sale = Sale.objects.get(binduser=request.user)
        # if not sale.bindteacher.binduser:
        #    raise Exception("teacher no bind user")
        # if not sale.bindteacher.bindbursar:
        #     raise Exception("teacher no bind user")
        # if not sale.bindteacher.bindbursar.binduser:
        #    raise Exception("bursar not bind user")

        if request.POST['id'] == "":  #新增客户
            newCustomer = Customer.objects.create(sales=sale, create=timezone.now(), modify=timezone.now())
            newAdd = True
            newCustomer.realuser = sale.binduser
            teachers = Teacher.objects.filter(binduser__isnull=False, company=request.user.userprofile.company).order_by('customercount')
            for teacher in teachers:
                newCustomer.teacher = teacher
                teacher.customercount += 1
                break

            # newCustomer.bursar = sale.bindteacher.bindbursar
            newCustomer.bursar = newCustomer.teacher.bindbursar

            newCustomer.create = timezone.now()
            newCustomer.status = 0
        else:  #修改客户
            newAdd = False
            newCustomer = Customer.objects.get(id=int(request.POST['id']))
            newCustomer.create = timezone.now()
            newCustomer.modify = timezone.now()
            newCustomer.realuser = sale.binduser
            # newCustomer.teacher = sale.bindteacher
            # newCustomer.bursar = sale.bindteacher.bindbursar
            ## 新录入的客户不允许修改，该段代码废弃
            # if request.user.userprofile.title.role_name == 'sale' and newCustomer.status == 0:
            #     sale = Sale.objects.get(binduser=request.user)
            #     saleManagerPwList = SaleManagerPassword.objects.filter(company=sale.company, department=sale.department)
            #     match = False
            #     for pw in saleManagerPwList:
            #         if pw.password == request.POST.get('managerPassword', '错误的密钥'):
            #             match = True
            #             break
            #     if(not match):
            #         raise Exception("manager password incorrect")
            if newCustomer.status == 0:
                newCustomer.status = 0
            elif newCustomer.status == 10:
                newCustomer.status = 0
                newCustomer.message = ""
            elif newCustomer.status == 30:
                newCustomer.status = 20
                newCustomer.message = ""
            else:
                newCustomer.status = newCustomer.status
        newCustomer.name = request.POST.get('name', '')
        newCustomer.phone = request.POST.get('phone', '')
        newCustomer.startup = request.POST.get('startup', 0)
        newCustomer.gem = 'gem' in request.POST
        if request.POST.get('saletool') == 'wx':
            newCustomer.wxid = request.POST.get('wxid', '')
            newCustomer.wxname = request.POST.get('wxname', '')
            if request.POST.get('saleswx'):
                newCustomer.saleswx = Wx.objects.get(id=int(request.POST.get('saleswx')))
        else:
            newCustomer.qqid = request.POST.get('qqid', '')
            newCustomer.qqname = request.POST.get('qqname', '')
            if request.POST.get('salesqq'):
                newCustomer.salesqq = Qq.objects.get(id=int(request.POST.get('salesqq')))
        newCustomer.save()

        # 新增客户，管理处理客户数+1后保存
        if newAdd and teacher:
            teacher.save()

        #开发绩效管理
        # 提交数加1
        request.user.userprofile.commit += 1
        request.user.userprofile.save()
        #提交数历史当天的记录加1
        userCommitHis, created = request.user.usercommithis_set.get_or_create(user=request.user, day=datetime.date.today())
        userCommitHis.delta += 1
        userCommitHis.total = request.user.userprofile.commit
        userCommitHis.save()
        #提交的同时建立有效客户历史
        userGradeHis, created = request.user.usergradehis_set.get_or_create(user=request.user, day=datetime.date.today())
        userGradeHis.total = request.user.userprofile.grade
        userGradeHis.save()

        #提交时刷新对应老师的消息
        # teacherUser = newCustomer.teacher.binduser
        # if teacherUser:
        #     transmission, created = Transmission.objects.get_or_create(user=teacherUser)
        #     transmission.transmission = "客户信息有更新，请刷新页面查看。"
        #     transmission.checked = False
        #     transmission.save()

        #添加成功
        newAdd = False

        data['msg'] = "操作成功"
        data['msgLevel'] = "info"
    except Exception as e:
        if newAdd:
            newCustomer.delete()
        print(e.__str__())
        if str(e.__str__()).__contains__('saleId'):
            data['msg'] = "操作失败,开发ID已存在"
        elif str(e.__str__()).__contains__('teacher no bind user'):
            data['msg'] = "操作失败,对应客户管理专员未绑定用户"
        elif str(e.__str__()).__contains__('teacher no bind bursar'):
            data['msg'] = "操作失败,无绑定财务信息"
        elif str(e.__str__()).__contains__('bursar not bind user'):
            data['msg'] = "操作失败,对应财务专员未绑定用户"
        elif str(e.__str__()).__contains__('manager password'):
            data['msg'] = "部门密钥错误"
        elif str(e.__str__()).__contains__('SaleManagerPassword'):
            data['msg'] = "部门密钥错误"
        else:
            data['msg'] = "操作失败,请联系管理员。错误信息:%s" % e.__str__()
        data['msgLevel'] = "error"

    # t2 = time.clock()
    # logger.error("addCustomer cost time: %f"%(t2-t1))
    return HttpResponse(json.dumps(data))

@login_required()
def delCustomer(request):
    data = {}
    try:
        tmpCustomer = Customer.objects.get(id=request.POST['id'])
        if request.POST.get("real", '') == 'true':
            tmpCustomer.delete()
        else:
            tmpCustomer.status = 99
            tmpCustomer.save()
        data['msg'] = "操作成功"
        data['msgLevel'] = "info"
    except Exception as e:
        print(e.__str__())
        data['msg'] = "操作失败"
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def delCustomerBySale(request):
    data = {}
    try:
        tmpCustomer = Customer.objects.get(id=request.POST['id'])
        sale = Sale.objects.get(binduser=request.user)
        saleManagerPwList = SaleManagerPassword.objects.filter(company=sale.company, department=sale.department)
        match = False
        for pw in saleManagerPwList:
            if pw.password == request.POST.get('emanagerPassword', '错误的密钥'):
                match = True
                break
        if (not match):
            raise Exception("manager password incorrect")
        tmpCustomer.delete()
        data['msg'] = "操作成功"
        data['msgLevel'] = "info"
    except Exception as e:
        traceback.print_exc()
        if str(e.__str__()).__contains__('saleId'):
            data['msg'] = "操作失败,开发ID已存在"
        elif str(e.__str__()).__contains__('binduser'):
            data['msg'] = "操作失败,用户已绑定开发，请刷新页面重试"
        elif str(e.__str__()).__contains__('bursar'):
            data['msg'] = "操作失败,无绑定财务信息"
        elif str(e.__str__()).__contains__('manager password'):
            data['msg'] = "经理授权错误，请核实后再次输入。"
        elif str(e.__str__()).__contains__('SaleManagerPassword'):
            data['msg'] = "经理授权错误，请核实后再次输入。"
        else:
            data['msg'] = "操作失败,请联系管理员。错误信息:%s" % e.__str__()
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def checkCustomerPhone(request):
    # t1 = time.clock()
    customerPhone = request.POST.get('phone')
    valid = True

    try:
        customers = Customer.objects.filter(phone=customerPhone,phone__isnull=False)
        if customers.__len__() != 0:   #手机号码重复
            for customer in customers:
               if customer.status == 98: #不诚信客户
                   valid = False
                   break
               else:                     #诚信客户
                   if customer.status == 40:
                       nowtime = timezone.now()
                       latest = customer.latest
                       if latest:
                           deltaday = (nowtime - latest).days
                           if deltaday < 90.0:
                              valid = False
                              break
    except:
        traceback.print_exc()

    data = {
        'valid': valid,
    }
    # t2 = time.clock()
    # logger.error("customer/checkCustomerPhone cost time: %f"%(t2-t1))
    return HttpResponse(json.dumps(data))

def checkCustomerPhoneForEdit(request):
    customerPhone = request.POST.get('phone')
    valid = False
    try:
        customers = Customer.objects.filter(phone=customerPhone,phone__isnull=False)
        if customers.__len__() <= 1:
            valid = True
    except:
        traceback.print_exc()

    data = {
        'valid': valid,
    }

    return HttpResponse(json.dumps(data))

@login_required()
def customerHandle(request):
    # t1 = time.clock()
    if (not request.user.userprofile.title.role_name in ['admin', 'ops', 'teacher', 'teachermanager', 'teacherboss']):
        return HttpResponseRedirect("/")
    endDate = request.POST.get('endDate', "")
    if endDate == '':
        endDate = datetime.date.today() + datetime.timedelta(days=1)
    else:
        endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d").date()
    startDate = request.POST.get('startDate', "")
    if startDate == "":
        startDate = datetime.date.today()
    else:
        startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
    # spotTeachers = SpotTeacher.objects.filter(binduser__isnull=False)

    if request.user.userprofile.title.role_name == 'teacher':
        teacher = Teacher.objects.get(binduser=request.user)
        teachers = None
    else:
        teacher = None
        teachers = Teacher.objects.all()
        if request.user.userprofile.title.role_name == 'teacherboss':
            teachers = teachers.filter(company=request.user.userprofile.company, binduser__isnull=False)
        elif request.user.userprofile.title.role_name == 'teachermanager':
            teachers = teachers.filter(company= request.user.userprofile.company, department=request.user.userprofile.department,
                                          group= request.user.userprofile.group, binduser__isnull=False)
        elif request.user.userprofile.title.role_name in ['admin', 'ops']:
            teachers = teachers.filter(binduser__isnull=False)

    data = {
        # "spotTeachers": spotTeachers,
        "startDate": str(startDate),
        "endDate": str(endDate),
        "teacher": teacher,
        "teachers": teachers,
    }
    # t2 = time.clock()
    # logger.error("customer/customerHandle cost time: %f"%(t2-t1))
    return render(request, 'customer/customerHandle.html', data)

@login_required()
def queryCustomerHandle(request):
    # t1 = time.clock()
    endDate = request.GET.get('endDate', "")
    if endDate == '':
        endDate = datetime.datetime.today() + datetime.timedelta(days=1)
    else:
        endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d")
    startDate = request.GET.get('startDate', "")
    if startDate == "":
        startDate = datetime.datetime.today()
    else:
        startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d")
    # customers = Customer.objects.all().order_by( 'status', '-create', 'teacher__teacherId')

    customers = Customer.objects.all()
    #客户状态条件筛选
    customer_status = request.GET.get('customerstatus','')
    if customer_status == '10':
        customers = customers.filter(~Q(status=30))
        customers = customers.filter(~Q(status=40))
        customers = customers.filter(~Q(status=98))
        customers = customers.filter(~Q(status=99))
    elif customer_status == '40':
        customers = customers.filter(status=40)
    else:
        customers = customers


    # 不同角色看到不同的列表
    if request.user.userprofile.title.role_name in ['teachermanager']:
        company = request.user.userprofile.company
        department = request.user.userprofile.department
        group = request.user.userprofile.group
        customers = customers.filter(teacher__company=company, teacher__department=department, teacher__group=group)
        customers = customers.filter(~Q(status=99))

    elif request.user.userprofile.title.role_name in ['teacherboss']:
        company = request.user.userprofile.company
        customers = customers.filter(teacher__company=company)
        customers = customers.filter(~Q(status=99))
    elif request.user.userprofile.title.role_name in ['teacher']:
        teacher = Teacher.objects.get(binduser=request.user)
        customers = customers.filter(teacher=teacher)
        customers = customers.filter(~Q(status=99))
    else:
        customers = customers

    # 去掉退回状态的客户
    customers = customers.exclude(status=10)
    customers = customers.exclude(status=30)
    customers = customers.exclude(status=98)
    # 按条件查询
    # customers = customers.filter(sales__company__icontains=request.GET.get('company', ''))
    # customers = customers.filter(sales__department__icontains=request.GET.get('department', ''))
    if request.GET.get('saleid', '') !='':
        customers = customers.filter(sales__saleId__icontains=request.GET.get('saleid', ''))
    if request.GET.get('teacherid', '') != '':
        customers = customers.filter(teacher__teacherId__icontains=request.GET.get('teacherid', ''))
    if request.GET.get('saleswx', '') != '':
        customers = customers.filter(saleswx__wxid__icontains=request.GET.get('saleswx', ''))
    if request.GET.get('salesqq', '') != '':
        customers = customers.filter(salesqq__qqid__icontains=request.GET.get('salesqq', ''))
    if request.GET.get('wxqq', '') != '':
        customers = customers.filter(
            Q(wxid="", qqid__icontains=request.GET.get('wxqq')) | Q(qqid="", wxid__icontains=request.GET.get('wxqq')))
    customers = customers.filter(name__icontains=request.GET.get('name', ''))
    # customers = customers.filter(phone__icontains=request.GET.get('phone', ''))

    #放开权限
    phone = request.GET.get('phone')
    if request.GET.get('phone'):
        customers = Customer.objects.all().order_by('status', '-create', 'teacher__teacherId')
        customers = customers.filter(~Q(status=99))
        # 去掉退回状态的客户
        customers = customers.exclude(status=10)
        customers = customers.exclude(status=30)
        customers = customers.exclude(status=98)
        # 通过电话号码获取客户信息
        customers = customers.filter(phone__icontains=request.GET.get('phone'))

    if request.GET.get('wxid', '') != '':
        customers = customers.filter(wxid__icontains=request.GET.get('wxid', ''))
    if request.GET.get('wxname', '') != '':
        customers = customers.filter(wxname__icontains=request.GET.get('wxname', ''))
    if request.GET.get('qqid', '') != '':
        customers = customers.filter(qqid__icontains=request.GET.get('qqid', ''))
    if request.GET.get('qqname', '') != '':
        customers = customers.filter(qqname__icontains=request.GET.get('qqname', ''))
    customers = customers.filter(message__icontains=request.GET.get('message', ''))
    if request.GET.get('minstartup', '') != '':
        customers = customers.filter(startup__gte=request.GET.get('minstartup'))
    if request.GET.get('maxstartup', '') != '':
        customers = customers.filter(startup__lte=request.GET.get('maxstartup'))
    if request.GET.get('gem', '') != '':
        customers = customers.filter(gem=request.GET.get('gem'))
    if request.GET.get('vip', '') != '':
        customers = customers.filter(vip=request.GET.get('vip'))
    if request.GET.get('spot', '') != '':
        customers = customers.filter(spotStatus=request.GET.get('spot'))

    customers = customers.filter(modify__gte=startDate, modify__lte=endDate)
    # 排除掉交易时间不在所选时间范围内的有修改记录的客户
    customers = customers.filter(~Q(status=40,latest__lte=startDate))
    customers = customers.filter(~Q(status=40, latest__gte=endDate))


    if request.GET.get('status', '') != '':
        customers = customers.filter(status=request.GET.get('status'))
    if (request.GET.get('stockid', '') != ''):
        customers = customers.filter(trade__stock__stockid=request.GET.get('stockid'), trade__status=0)
    if (request.GET.get('stockname', '') != ''):
        customers = customers.filter(Q(trade__stock__stockname__icontains=request.GET.get('stockname'))
                                     |Q(trade__stock__stockid__icontains=request.GET.get('stockname')))
    if request.GET.get('crude', '') == '1':
        customers = customers.filter(trade__buycash__gte=100000)
        tmpCustomers = customers
        if request.GET.get('crude') :
            for customer in customers:
                if customer.getLatestTradeBuycash() == '' or customer.getLatestTradeBuycash() < 100000:
                    tmpCustomers = tmpCustomers.exclude(id=customer.id)
        customers = tmpCustomers
    customers = customers.order_by("-tradecount","teacher__teacherId","-create")

    oldcustomer = customers.filter(tradecount__gte=2).count()
    newcustomer = customers.count() - oldcustomer
    oldcustomer = json.dumps(oldcustomer)
    newcustomer = json.dumps(newcustomer)

    p = Paginator(customers, 20)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        customerPage = p.page(page)
    except (EmptyPage, InvalidPage):
        customerPage = p.page(p.num_pages)
    data = {
        "customerPage": customerPage,
        "oldcustomer": oldcustomer,
        "newcustomer": newcustomer,
        "requestArgs": getArgsExcludePage(request),
    }
    # t2 = time.clock()
    # logger.error("customer/queryCustomerHande cost time: %f" %(t2-t1))

    return render(request, 'customer/queryCustomerHandle.html', data)

@login_required()
def handleCustomer(request):
    # t1 = time.clock()
    data = {}
    try:
        customerId = request.POST.get('id')
        customer = Customer.objects.get(id=customerId)
        status = request.POST.get('status')
        customer.status = status
        customer.bursar = customer.teacher.bindbursar
        customer.modify = timezone.now()
        if status == '10':
            customer.message = request.POST.get('message')
        customer.save()
        data['msg'] = "操作成功"
        data['msgLevel'] = "info"
    except Exception as e:
        print(e.__str__())
        data['msg'] = "操作失败"
        data['msgLevel'] = "error"
    # t2 = time.clock()
    # logger.error("customer/handleCustomer cost time: %f"%(t2-t1))
    return HttpResponse(json.dumps(data))

#已经加微信的客户
@login_required()
def handleValidCustomer(request):
    data = {}
    try:
        customerId = request.POST.get('validCustomerId')
        customer = Customer.objects.get(id=customerId)
        validCustomerChange = int(request.POST.get('validCustomerChange'))
        if validCustomerChange == 100000:
            customer.crude = True
        elif validCustomerChange == 30:
            customer.status = 30
            customer.message = request.POST.get('redoMessage')
        elif validCustomerChange == 98:
            customer.status = 98
            customer.honest = False
            customer.message = request.POST.get('dishonestMessage')
        elif validCustomerChange == 99:
            customer.status = 99
            customer.message = request.POST.get('delMessage')
        else:
            raise Exception("unknown operation")
        customer.modify = timezone.now()
        customer.realteacher = request.user
        customer.save()
        data['msg'] = "操作成功"
        data['msgLevel'] = "info"
    except Exception as e:
        print(e.__str__())
        data['msg'] = "操作失败"
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def getCustomerById(request):
    customer = Customer.objects.get(id=request.GET.get('customerid'))
    data = {
        "customer": customer,
    }
    return render(request, 'customer/getCustomerById.html', data)

@login_required()
def getSpotCustomerById(request):
    customer = Customer.objects.get(id=request.GET.get('customerid'))
    data = {
        "customer": customer,
    }
    return render(request, 'customer/getSpotCustomerById.html', data)

@login_required()
def customerPay(request):
    if (not request.user.userprofile.title.role_name in ['admin', 'ops', 'bursar', 'bursarmanager']):
        return HttpResponseRedirect("/")
    data = {}
    return render(request, 'customer/customerPay.html', data)

@login_required()
def queryCustomerPay(request):
    # t1 = time.clock()
    customers = Customer.objects.all().order_by('-modify')
    # 不同角色看到不同的列表
    if request.user.userprofile.title.role_name in ['bursarmanager']:
        company = request.user.userprofile.company
        department = request.user.userprofile.department
        customers = customers.filter(bursar__company=company, bursar__department=department)
        customers = customers.exclude(status=99)
    elif request.user.userprofile.title.role_name in ['bursar']:
        bursar = Bursar.objects.get(binduser=request.user)
        customers = customers.filter(bursar=bursar)
        customers = customers.exclude(status=99)
    else:
        customers = customers

    # 只看盈利客户
    customers = customers.filter(trade__status__gte=20)

    # 按条件查询
    customers = customers.filter(teacher__teacherId__icontains=request.GET.get('teacherid', ''))
    if request.GET.get('saleswx', '') != '':
        customers = customers.filter(saleswx__wxid__icontains=request.GET.get('saleswx', ''))
    if request.GET.get('salesqq', '') != '':
        customers = customers.filter(salesqq__qqid__icontains=request.GET.get('salesqq', ''))
    customers = customers.filter(name__icontains=request.GET.get('name', ''))
    customers = customers.filter(phone__icontains=request.GET.get('phone', ''))
    if request.GET.get('wxid', '') != '':
        customers = customers.filter(wxid__icontains=request.GET.get('wxid', ''))
    if request.GET.get('wxname', '') != '':
        customers = customers.filter(wxname__icontains=request.GET.get('wxname', ''))
    if request.GET.get('qqid', '') != '':
        customers = customers.filter(qqid__icontains=request.GET.get('qqid', ''))
    if request.GET.get('qqname', '') != '':
        customers = customers.filter(qqname__icontains=request.GET.get('qqname', ''))
    customers = customers.filter(message__icontains=request.GET.get('message', ''))
    if request.GET.get('minstartup', '') != '':
        customers = customers.filter(startup__gte=request.GET.get('minstartup'))
    if request.GET.get('maxstartup', '') != '':
        customers = customers.filter(startup__lte=request.GET.get('maxstartup'))
    if request.GET.get('gem', '') != '':
        customers = customers.filter(gem=request.GET.get('gem'))
    if request.GET.get('startDate', '') != '':
        customers = customers.filter(modify__gte=request.GET.get('startDate'))
    if request.GET.get('endDate', '') != '':
        customers = customers.filter(modify__lte=request.GET.get('endDate'))
    if (request.GET.get('status', '') != ''):
        customers = customers.filter(status=request.GET.get('status'))

    p = Paginator(customers, 20)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        customerPage = p.page(page)
    except (EmptyPage, InvalidPage):
        customerPage = p.page(p.num_pages)
    data = {
        "customerPage": customerPage,
        "requestArgs": getArgsExcludePage(request),
    }
    # t2 = time.clock()
    # logger.error("customer/queryCustomerPay cost time: %f"%(t2-t1))
    return render(request, 'customer/queryCustomerPay.html', data)

@login_required()
def editSpot(request):
    try:
        customer = Customer.objects.get(id=request.POST.get('id'))
        spot = request.POST.get('spot')
        customer.spotStatus = spot
        customer.save()
    except Exception as e:
        print(e.__str__())
    return HttpResponse("")

@login_required()
def handleSpotCustomer(request):
    data = {}
    try:
        customer = Customer.objects.get(id=request.POST.get('spotCustomerId'))
        customer.spotTeacher = SpotTeacher.objects.get(id=request.POST.get('spotTeacher'))
        customer.spotCash = request.POST.get('spotCash')
        customer.spotTime = datetime.date.today()
        currentTimeStamp = time.mktime(timezone.now().timetuple())
        if customer.first_trade:
            firstTradeTimeStamp = time.mktime(customer.first_trade.timetuple())
        else:
            raise Exception("nofirsttrade")
        spotDay = (currentTimeStamp - firstTradeTimeStamp) / 86400 + 1
        customer.spotDay = spotDay
        customer.spotMessage = request.POST.get('spotMessage', '')
        customer.spotStatus = 'D'
        customer.save()
        spot = Spot.objects.create(customer=customer)
        spot.create = timezone.now()
        spot.type = 0
        spot.cash = request.POST.get('spotCash')
        spot.save()
        data['msg'] = "操作成功"
        data['msgLevel'] = "info"
    except Exception as e:
        print(e.__str__())
        if e.__str__() == 'nofirsttrade':
            data['msg'] = "该客户尚无交易记录"
        else:
            data['msg'] = "操作失败"
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def noTradeCustomerReport(request):
    if not request.user.userprofile.title.role_name in ['admin', 'ops', 'teachermanager', 'teacherboss']:
        return HttpResponseRedirect("/")
    customers = Customer.objects.filter(first_trade__isnull=True)
    customers = Customer.objects.exclude(status=98)
    customers = Customer.objects.exclude(status=99)
    customers = Customer.objects.exclude(status=40)
    customers = Customer.objects.exclude(status=10)
    customers = Customer.objects.exclude(status=30)
    if request.user.userprofile.title.role_name == 'teacher':
        teacher = Teacher.objects.get(binduser=request.user)
        customers = customers.filter(teacher=teacher)
    elif request.user.userprofile.title.role_name == 'teachermanager':
        customers = customers.filter(teacher__company=request.user.userprofile.company,
                                     teacher__department=request.user.userprofile.department)
    elif request.user.userprofile.title.role_name == 'teacherboss':
        customers = customers.filter(teacher__company=request.user.userprofile.company)
    else:
        customers = customers
    data = {
        "customers": customers,
    }
    return render(request, 'customer/noTradeCustomerReport.html', data)

@login_required()
def tradeTypeReport(request):
    # t1 = time.clock()
    if not request.user.userprofile.title.role_name in ['admin', 'ops', 'teachermanager', 'teacherboss']:
        return HttpResponseRedirect("/")
    teachers = Teacher.objects.all()
    teachers = teachers.exclude(binduser__isnull=True)
    endDate = request.POST.get('endDate', "")
    if endDate == '':
        endDate = datetime.date.today() + datetime.timedelta(days=1)
    else:
        endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d").date()
    startDate = request.POST.get('startDate', "")
    if startDate == "":
        startDate = datetime.date.today() - datetime.timedelta(days=1)
    else:
        startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
    if request.user.userprofile.title.role_name == 'teachermanager':
        teachers = teachers.filter(company=request.user.userprofile.company, department=request.user.userprofile.department,
                                   group=request.user.userprofile.group)
    elif request.user.userprofile.title.role_name == 'teacherboss':
        teachers = teachers.filter(company=request.user.userprofile.company)
    elif request.user.userprofile.title.role_name == 'teacher':
        teachers = teachers.filter(binduser=request.user)
    else:
        teachers = teachers

    data = {
        "teachers": teachers,
        "startDate": str(startDate),
        "endDate": str(endDate),
    }
    # t2 = time.clock()
    # logger.error("customer/tradeTypeReport cost time: %f"%(t2-t1))
    return render(request, 'customer/tradeTypeReport.html', data)

@login_required()
def getTeacherDetail(request):
    # t1 = time.clock()
    teacherid = request.POST.get('teacher')
    startDate = request.POST.get('startDate')
    endDate = request.POST.get('endDate')
    trades = Trade.objects.filter(customer__teacher_id=teacherid, create__gte=startDate, create__lte=endDate)
    stocks = trades.values('stock', 'stock__stockname', 'stock__stockid').distinct()
    data = {
        "stocks": stocks,
        "teacherid": teacherid,
    }
    # t2 = time.clock()
    # logger.error("customer/getTeacherDetail cost time: %f"%(t2-t1))
    return render(request, 'customer/getTeacherDetail.html', data)

@login_required()
def getStockDetail(request):
    teacherid = request.POST.get('teacherid')
    stockid = request.POST.get('stockid')
    startDate = request.POST.get('startDate')
    endDate = request.POST.get('endDate')
    trades = Trade.objects.filter(customer__teacher_id=teacherid, stock_id=stockid, create__gte=startDate,
                                  create__lte=endDate)
    customers = Customer.objects.filter(teacher_id=teacherid, trade__stock_id=stockid, trade__create__lte=endDate,
                                        trade__create__gte=startDate).distinct()
    highTrade = trades.latest('buyprice')
    lowTrade = trades.earliest('buyprice')

    data = {
        "trades": trades,
        "customers": customers,
        "highTrade": highTrade,
        "lowTrade": lowTrade,
    }
    return render(request, 'customer/getStockDetail.html', data)

@login_required()
def dCustomerReport(request):
    if not request.user.userprofile.title.role_name in ['admin', 'ops', 'teachermanager', 'teacherboss']:
        return HttpResponseRedirect("/")
    teachers = Teacher.objects.all()
    if request.user.userprofile.title.role_name == 'teachermanager':
        teachers = teachers.filter(company=request.user.userprofile.company, department=request.user.userprofile.department)
    elif request.user.userprofile.title.role_name == 'teacherboss':
        teachers = teachers.filter(company=request.user.userprofile.company)
    else:
        teachers = teachers

    days = []
    for i in range(0, 7):
        day = datetime.date.today() - datetime.timedelta(days=i)
        days.insert(0, day)
    data = {
        "teachers": teachers,
        "days": days,
    }
    return render(request, 'customer/dCustomerReport.html', data)

@login_required()
def analyzeReport(request):
    # t1 = time.clock()
    if not request.user.userprofile.title.role_name in ['admin', 'ops', 'teacher', 'teachermanager', 'teacherboss']:
        return HttpResponseRedirect("/")

    startDate = request.GET.get('startDate','')
    endDate = request.GET.get('endDate','')

    if startDate == '':
        startDate = request.POST.get('startDate', datetime.date.today() - datetime.timedelta(days=14))
        endDate = request.POST.get('endDate', datetime.date.today() + datetime.timedelta(days=1))

    data = {
        "startDate": str(startDate),
        "endDate": str(endDate),
    }
    # t2 = time.clock()
    # logger.error("customer/analyzeReport cost time: %f"%(t2-t1))
    return render(request, 'customer/analyzeReport.html', data)


@login_required()
def queryAnalyzeReport(request):
    stocks = Stock.objects.all()
    stockid = request.POST.get('stockid','')
    startDate = request.GET.get('startDate')
    endDate = request.GET.get('endDate')
    sort = request.GET.get('sort','')

    stocks = stocks.filter(stockid__icontains=stockid, trade__create__lte=endDate, trade__create__gte=startDate,
                           trade__status=0).distinct()
    if request.user.userprofile.title.role_name == 'teachermanager':
        stocks = stocks.filter(trade__customer__teacher__company=request.user.userprofile.company,
                               trade__customer__teacher__department=request.user.userprofile.department).distinct()
    elif request.user.userprofile.title.role_name == 'teacherboss':
        stocks = stocks.filter(trade__customer__teacher__company=request.user.userprofile.company).distinct()
    elif request.user.userprofile.title.role_name == 'teacher':
        stocks = stocks.filter(trade__customer__teacher__binduser=request.user).distinct()


    if sort == '1' :
       stocks = stocks.order_by('-stockearncount')
    elif sort == '2':
       stocks = stocks.order_by('-stockearncash')


    p = Paginator(stocks, 20)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        stockPage = p.page(page)
    except (EmptyPage, InvalidPage):
        stockPage = p.page(p.num_pages)


    # data = {
    #     "customerPage": customerPage,
    #     "requestArgs": getArgsExcludePage(request),
    # }
    data = {
        "stockPage": stockPage,
        "startDate": str(startDate),
        "endDate": str(endDate),
        # "requestArgs": getArgsExcludePage(request),
    }
    return render(request, 'customer/queryAnalyzeReport.html', data)

@login_required()
def sortAnalyzeReport(request):
    # t1 = time.clock()
    if not request.user.userprofile.title.role_name in ['admin', 'ops', 'teacher', 'teachermanager', 'teacherboss']:
        return HttpResponseRedirect("/")
    stocks = Stock.objects.all()
    startDate = request.GET.get('startDate','')
    endDate = request.GET.get('endDate','')
    sort = request.GET.get('sort','')

    if startDate == '':
        startDate = request.POST.get('startDate', datetime.date.today() - datetime.timedelta(days=14))
        endDate = request.POST.get('endDate', datetime.date.today()+ datetime.timedelta(days=1))
    stocks = stocks.filter(trade__create__lte=endDate, trade__create__gte=startDate,
                           trade__status=0).distinct()
    if request.user.userprofile.title.role_name == 'teachermanager':
        stocks = stocks.filter(trade__customer__teacher__company=request.user.userprofile.company,
                               trade__customer__teacher__department=request.user.userprofile.department).distinct()
    elif request.user.userprofile.title.role_name == 'teacherboss':
        stocks = stocks.filter(trade__customer__teacher__company=request.user.userprofile.company).distinct()
    elif request.user.userprofile.title.role_name == 'teacher':
        stocks = stocks.filter(trade__customer__teacher__binduser=request.user).distinct()

    if stocks.count():
        for stock in stocks:
            trades = Trade_memory.objects.filter(stockid=stock.stockid,trade__create__gte=startDate,trade__create__lte=endDate)
            earnCount = 0
            earnCash = 0.00
            if trades.count():
                for trade in trades:
                    if trade.income > 0.:
                        earnCount += 1
                        earnCash += float(trade.income)
            earnCash = float('%.2f' % earnCash)
            stock.stockearncount = earnCount
            stock.stockearncash = earnCash
            stock.save()


    # for stock in stocks:
    #     trades = Trade.objects.filter(stockid=stock.stockid, status=0, create__gte=startDate, create__lte=endDate)
    #     if request.user.userprofile.title.role_name == 'teachermanager':
    #         trades = trades.filter(customer__teacher__company=request.user.userprofile.company,
    #                            customer__teacher__department=request.user.userprofile.department)
    #     elif request.user.userprofile.title.role_name == 'teacherboss':
    #         trades = trades.filter(customer__teacher__company=request.user.userprofile.company)
    #     else:
    #         trades = trades
    #     earnCount = 0
    #     earnCash = 0.
    #     try:
    #         sellprice = stock.stockprice
    #         for trade in trades:
    #             trade.sellprice = sellprice
    #             trade.income = (float(sellprice) - float(trade.buyprice)) * trade.buycount
    #             if trade.income > 0:
    #                 earnCount += 1
    #                 earnCash += trade.income
    #             # share = float(trade.share.split('|')[0]) / 10
    #             # trade.commission = trade.income * share
    #     except Exception as e:
    #         print('error')
    #     earnCash = float('%.2f' % earnCash)
    #     stock.stockearncount = earnCount
    #     stock.stockearncash = earnCash
    #     stock.save()

    #  sort
    # stocks = stocks.filter(trade__create__lte=endDate, trade__create__gte=startDate,
    #                        trade__status=0).distinct()
    # if request.user.userprofile.title.role_name == 'teachermanager':
    #     stocks = stocks.filter(trade__customer__teacher__company=request.user.userprofile.company,
    #                            trade__customer__teacher__department=request.user.userprofile.department).distinct()
    # elif request.user.userprofile.title.role_name == 'teacherboss':
    #     stocks = stocks.filter(trade__customer__teacher__company=request.user.userprofile.company).distinct()
    # elif request.user.userprofile.title.role_name == 'teacher':
    #     stocks = stocks.filter(trade__customer__teacher__binduser=request.user).distinct()

    if sort == '1':
       stocks = stocks.order_by('-stockearncount')
    elif sort == '2':
       stocks = stocks.order_by('-stockearncash')

    p = Paginator(stocks, 20)
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    try:
        stockPage = p.page(page)
    except (EmptyPage, InvalidPage):
        stockPage = p.page(p.num_pages)
    data = {
        "stockPage": stockPage,
        "startDate": str(startDate),
        "endDate": str(endDate),
    }
    # t2 = time.clock()
    # logger.error("customer/analyzeReport cost time: %f"%(t2-t1))
    return render(request, 'customer/queryAnalyzeReport.html', data)
    # return HttpResponse(json.dumps(data))

@login_required()
def getStockDetailForAnalyze(request):
    stockid = request.POST.get('stock')
    sellprice = request.POST.get('sellprice')
    startDate = request.POST.get('startDate')
    endDate = request.POST.get('endDate')
    user = request.user
    trades = Trade.objects.filter(stock_id=stockid, status=0, create__gte=startDate, create__lte=endDate)

    if user.userprofile.title.role_name == 'teachermanager':
        trades = trades.filter(customer__teacher__group=user.userprofile.group,
                               customer__teacher__department=user.userprofile.department)
       # trades = trades.filter(realteacheruser__teacher__group=request.user.userprofile.group,
       #                        realteacheruser__teacher__company=request.user.username.company)
    elif user.userprofile.title.role_name == 'teacherboss':
        trades = trades.filter(customer__teacher__company=user.userprofile.company)
        # trades = trades.filter(realteacheruser__teacher__company=request.user.userprofile.company)
    else:
        trades = trades

    try:
        for trade in trades:
            trade.sellprice = sellprice
            trade.income = (float(sellprice) - float(trade.buyprice)) * trade.buycount
            share = float(trade.share.split('|')[0]) / 10
            # trade.profitratio = (float(sellprice) - float(trade.buyprice))/float(trade.buyprice)*100
            trade.profitratio = trade.income / float(trade.buycash) * 100
            trade.profitratio = round(trade.profitratio, 2)
            trade.commission = trade.income * share
    except Exception as e:
        pass
    data = {
        "trades": trades,
        "stockid": stockid,
    }
    return render(request, 'customer/getStockDetailForAnalyze.html', data)

@login_required()
def calcProfitByStockId(request):
    # t1 = time.clock()
    stockid = request.POST.get('stockid')
    startDate = request.POST.get('startDate')
    endDate = request.POST.get('endDate')
    trades = Trade.objects.filter(stock_id=stockid, status=0, create__gte=startDate, create__lte=endDate)
    if request.user.userprofile.title.role_name == 'teachermanager':
        trades = trades.filter(customer__teacher__company=request.user.userprofile.company,
                               customer__teacher__department=request.user.userprofile.department)
    elif request.user.userprofile.title.role_name == 'teacherboss':
        trades = trades.filter(customer__teacher__company=request.user.userprofile.company)
    else:
        trades = trades

    earnCount = 0
    earnCash = 0.
    try:
        sellprice = request.POST.get('sellprice')
        for trade in trades:
            trade.sellprice = sellprice
            trade.income = (float(sellprice) - float(trade.buyprice)) * trade.buycount
            if trade.income > 0:
                earnCount += 1
                earnCash += trade.income
            share = float(trade.share.split('|')[0]) / 10
            trade.commission = trade.income * share
    except Exception as e:
        pass
    earnCash = float('%.2f' % earnCash)
    data = {
        "earnCount": earnCount,
        "earnCash": earnCash,
    }
    # t2 = time.clock()
    # logger.error("customer/calcProfitByStockId cost time: %f"%(t2-t1))
    return HttpResponse(json.dumps(data))

@login_required()
def tradePayManage(request):
    # t1 = time.clock()
    if (not request.user.userprofile.title.role_name in ['admin', 'ops', 'bursar', 'bursarmanager', 'teachermanager']):
        return HttpResponseRedirect("/")
    endDate = request.POST.get('endDate', "")
    if endDate == '':
        endDate = datetime.date.today() + datetime.timedelta(days=1)
    else:
        endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d").date()
    startDate = request.POST.get('startDate', "")
    if startDate == "":
        startDate = datetime.date.today() - datetime.timedelta(days=30)
    else:
        startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
    data = {
        "startDate": str(startDate),
        "endDate": str(endDate),
    }
    # t2 = time.clock()
    # logger.error("customer/tradePayManage cost time: %f"%(t2-t1))
    return render(request, 'customer/tradePayManage.html', data)

def queryTradePayManage(request):
    # t1 = time.clock()
    trades = Trade.objects.filter(status=20).order_by('-dealtime')

    endDate = request.GET.get('endDate', "")
    if endDate == '':
        endDate = datetime.date.today() + datetime.timedelta(days=1)
    else:
        endDate = datetime.datetime.strptime(endDate, "%Y-%m-%d").date()
    startDate = request.GET.get('startDate', "")
    if startDate == "":
        startDate = datetime.date.today() - datetime.timedelta(days=30)
    else:
        startDate = datetime.datetime.strptime(startDate, "%Y-%m-%d").date()
    trades = trades.filter(dealtime__lte=endDate, dealtime__gte=startDate)

    #不同角色
    if request.user.userprofile.title.role_name == 'bursar':
        trades = trades.filter(customer__bursar__binduser=request.user)
    if request.user.userprofile.title.role_name == 'teachermanager':
        user = request.user
        bursurID = 'CW'+user.userprofile.company+user.userprofile.group+user.userprofile.department
        trades = trades.filter(customer__bursar__bursarId=bursurID)
    if request.user.userprofile.title.role_name == 'bursarManager':
        trades = trades.filter(customer__bursar__company=request.user.userprofile.company)

    data = {
        "trades": trades,
    }
    # t2 = time.clock()
    # logger.error("customer/queryTradePayManage cost time: %f"%(t2-t1))
    return render(request, 'customer/queryTradePayManage.html', data)

@login_required()
def resumeDishonestCustomer(request):
    data = {}
    try:
        id = request.POST.get('id')
        customer = Customer.objects.get(id=id)
        customer.honest = True
        if customer.getTradeCount() == 0:
            customer.status = 20
        else:
            customer.status = 40
        customer.save()
        data['msg'] = "操作成功"
        data['msgLevel'] = "info"
    except Exception as e:
        traceback.print_exc()
        data['msg'] = "操作失败"
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def addTeacherCustomer(request):
    # t1 = time.clock()
    data = {}
    try:
        newCustomer = Customer.objects.create(create=timezone.now(), modify=timezone.now())
        teacher = Teacher.objects.get(id=request.POST.get('teacher'))
        newCustomer.teacher = teacher
        teacher.customercount += 1
        teacher.save()
        newCustomer.bursar = teacher.bindbursar
        newCustomer.status = 20
        newCustomer.name = request.POST.get('name', '')

        # #将老师新增的客户绑定在虚拟sale
        sale = Sale.objects.get(saleId='KF'+teacher.company+'888888')
        newCustomer.sales = sale
        
        newCustomer.phone = request.POST.get('phone', '')
        newCustomer.startup = request.POST.get('startup', 0)
        newCustomer.gem = 'gem' in request.POST
        newCustomer.realuser = request.user

        if request.POST.get('saletool') == 'wx':
            newCustomer.wxid = request.POST.get('wxid', '')
            newCustomer.wxname = request.POST.get('wxname', '')
        else:
            newCustomer.qqid = request.POST.get('qqid', '')
            newCustomer.qqname = request.POST.get('qqname', '')


        newCustomer.save()


        # 提交时刷新对应老师的消息
        # teacherUser = newCustomer.teacher.binduser
        # if teacherUser:
        #     transmission, created = Transmission.objects.get_or_create(user=teacherUser)
        #     transmission.transmission = "客户信息有更新，请刷新页面查看。"
        #     transmission.checked = False
        #     transmission.save()

        data['msg'] = "操作成功"
        data['msgLevel'] = "info"
    except Exception as e:
        #出错则删除创建的客户
        newCustomer.delete()

        traceback.print_exc()
        if str(e.__str__()).__contains__('saleId'):
            data['msg'] = "操作失败,开发ID已存在"
        elif str(e.__str__()).__contains__('binduser'):
            data['msg'] = "操作失败,用户已绑定开发，请刷新页面重试"
        elif str(e.__str__()).__contains__('bursar'):
            data['msg'] = "操作失败,指定客户管理专员未绑定财务"
        elif str(e.__str__()).__contains__('manager password'):
            data['msg'] = "部门密钥错误"
        elif str(e.__str__()).__contains__('SaleManagerPassword'):
            data['msg'] = "部门密钥错误"
        else:
            data['msg'] = "操作失败,请联系管理员。错误信息:%s" % e.__str__()
        data['msgLevel'] = "error"
    # t2 = time.clock()
    # logger.error("customer/addTeacherCustomer cost time: %f"%(t2-t1))
    return HttpResponse(json.dumps(data))

# @login_required()
# def stockProfitAnalyze(request):
#
#      stocks = Stock.objects.all()
#      startDate = datetime.date.today() - datetime.timedelta(days=14)
#      endDate = datetime.date.today()+ datetime.timedelta(days=1)
#      stocks = stocks.filter(trade__create__lte=endDate, trade__create__gte=startDate,
#                            trade__status=0).distinct()
#
#      for stock in stocks:
#          trades = Trade.objects.filter(stock_id=stock.id, status=0, create__gte=startDate, create__lte=endDate)
#          try:
#              sellprice = request.POST.get('sellprice')
#              for trade in trades:
#                  trade.sellprice = sellprice
#                  trade.income = (float(sellprice) - float(trade.buyprice)) * trade.buycount
#                  share = float(trade.share.split('|')[0]) / 10
#                  # trade.profitratio = (float(sellprice) - float(trade.buyprice))/float(trade.buyprice)*100
#                  trade.profitratio = trade.income / float(trade.buycash) * 100
#                  trade.profitratio = round(trade.profitratio, 2)
#                  trade.commission = trade.income * share
#          except Exception as e:
#              pass

