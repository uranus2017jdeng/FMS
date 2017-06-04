# coding=utf-8
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from PIL import Image, ImageDraw, ImageFont
import os
import random
import string
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import datetime
import traceback
import json
import time

from shande.settings import BASE_DIR,UPLOAD_ROOT
from super.models import *
from teacher.models import *

from trade.models import *
# from customer.models import *


# Create your views here.
def index(request):
    if request.user.is_authenticated():
        # birthday = time.strftime('%m-%d',time.localtime(time.time()))
        month = time.strftime('%m',time.localtime(time.time()))
        day = time.strftime('%d',time.localtime(time.time()))

        # userprofiles = UserProfile.objects.all()
        # for userprofile in userprofiles:
        #     if userprofile.cid:
        #         a = userprofile.cid
        #         year = userprofile.cid[6:10]
        #         month = userprofile.cid[10:12]
        #         day = userprofile.cid[12:14]
        #         birthday = year + '-' + month +'-'+day
        #         userprofile.birthday = datetime.datetime.strptime(birthday,'%Y-%m-%d')
        #         userprofile.save()


        userprofiles = UserProfile.objects.filter(birthday__month=month, birthday__day=day)


        # for userprofile in userprofiles:
        #     if userprofile.cid:
        #         a = userprofile.cid
        #         year = userprofile.cid[6:10]
        #         month = userprofile.cid[10:12]
        #         day = userprofile.cid[12:14]
        #         birthday = year + '-' + month +'-'+day
        #         userprofile.birthday = datetime.datetime.strptime(birthday,'%Y-%m-%d')
        #         userprofile.save()

        #       if birthdayuser.userprofile.cid[10:14] != birthday:
        #         users = users.exclude(user=birthdayuser)
        #
        if userprofiles.count():
            showContent = 'true'
            showContent = json.dumps(showContent)

        return render(request, 'super/index.html', locals())
    else:
        redirect_to = 'accounts/login/'
        return HttpResponseRedirect(redirect_to)

def login_view(request):
    data = {
        #"accept": request.META['HTTP_ACCEPT'],
    }
    failed = False
    if 'next' in request.GET:
        redirect_to = request.GET['next']
    else:
        redirect_to = '/ops/userManage/'
    if request.method == 'POST':
        if 'captcha' not in request.session:
            redirect_to = '/'
            return HttpResponseRedirect(redirect_to)
        if 'ident' in request.POST and string.upper(request.POST['ident']) == string.upper(request.session['captcha']):
            user = None
            try:
                user = User.objects.get(username=request.POST['username'])
            except Exception as e:
                print(e.__str__())
                print(request.POST['username'])
                error_msg = "用户  %s 不存在" % request.POST['username']
            if user:
                faillocktime = user.userprofile.faillocktime
                if faillocktime:
                    deltatime = (datetime.datetime.now() - faillocktime).total_seconds() - 900
                    if deltatime < 0:
                        error_msg = "用户已锁定，解锁倒计时 %s 秒" % int(deltatime)
                        return render(request, 'super/login_view.html', locals())
                userauth = authenticate(username=request.POST['username'], password=request.POST['password'])
                if userauth is not None:
                    login(request, userauth)
                    # if userauth.userprofile.title.role_name in ['sale', 'saleboss', 'salemanager']:
                    #     # redirect_to = '/customer/customerManage'
                    #     redirect_to = '/'
                    # elif userauth.userprofile.title.role_name in ['teacher', 'teacherboss', 'teachermanager']:
                    #     # redirect_to = '/customer/customerHandle'
                    #     redirect_to = '/'
                    # elif userauth.userprofile.title.role_name in ['spotteacher', 'spotmanager']:
                    #     # redirect_to = '/spot/spotCustomer'
                    #     redirect_to = '/'
                    # elif userauth.userprofile.title.role_name in ['bursar', 'bursarmanager']:
                    #     # redirect_to = '/customer/tradePayManage'
                    #     redirect_to = '/'
                    # elif userauth.userprofile.title.role_name in ['admin', 'ops']:
                    #     # redirect_to = '/ops/userManage'
                    #     redirect_to = '/'
                    # else:
                    #     redirect_to = '/'
                    redirect_to = '/'
                    userauth.userprofile.failcount = 0
                    userauth.userprofile.faillocktime = None
                    userauth.userprofile.save()
                    return HttpResponseRedirect(redirect_to)
                else:
                    failcount = user.userprofile.failcount
                    failcount += 1
                    if failcount > 3:
                        error_msg = "登陆失败超过三次，十五分钟内无法登陆"
                        user.userprofile.failcount = failcount
                        user.userprofile.faillocktime = datetime.datetime.now()
                    else:
                        error_msg = "用户密码错误，登陆失败三次后，将锁定十五分钟"
                        user.userprofile.failcount = failcount
                    user.userprofile.save()
            else:
                error_msg = "用户不存在"
        else:
            error_msg = "验证码错误"
    return render(request, 'super/login_view.html', locals())

def logout_view(request):
    logout(request)
    del request.session # 删除session
    redirect_to = '/'
    return HttpResponseRedirect(redirect_to)

def captcha(request):
    image = Image.new('RGB', (147, 49), color=(255, 255, 255))
    # model, size, background color
    font_file = os.path.join(BASE_DIR, 'static/assets/fonts/simsun.ttc')
    font = ImageFont.truetype(font_file, 30)
    # the font object
    draw = ImageDraw.Draw(image)
    rand_str = ''.join(random.sample(string.letters + string.digits, 4))
    # The random string
    draw.text((7, 0), rand_str, fill=(0, 0, 0), font=font)
    # position, content, color, font
    del draw
    request.session['captcha'] = rand_str.lower()
    # store the content in Django's session store
    buf = StringIO()
    # a memory buffer used to store the generated image
    image.save(buf, 'jpeg')
    return HttpResponse(buf.getvalue(), 'image/jpeg')
    # return the image data stream as image/jpeg format, browser will treat it as an image

def siteswitch(request):
    maintaince = Config.objects.get(key="维护模式");
    return HttpResponse(maintaince.value)

def maintaince(request):
    message = Config.objects.get(key="维护公告")
    data = {
        "message": message.value,
    }
    return render(request, 'maintaince.html', data)

def wap(request):
    data = {
        "message": "手机网页暂时无法查看。",
    }
    return render(request, 'wap.html', data)

@login_required()
def userInfo(request):
    if request.user.userprofile.title.role_name == 'teacher':
        teacher = Teacher.objects.get(binduser=request.user)

    return render(request, 'super/userInfo.html', locals())

def modifyPassword(request):
    data = {}
    user = authenticate(username=request.user.username, password=request.POST['currentPassword'])
    if user is not None:
        user.set_password(request.POST['password'])
        try:
            user.save()
            logout(request)
            data['msg'] = "密码更新成功，请重新登陆"
            data['msgLevel'] = "info"
        except Exception as e:
            print(e.__str__)
            data['msg'] = "更新密码失败"
            data['msgLevel'] = "error"
    else:
        data['msg'] = "当前密码错误"
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def titleManage(request):
    if (request.user.userprofile.title.role_name != 'admin'):
        return HttpResponseRedirect("/")
    titles = Title.objects.all()
    data = {
        "titles": titles,
    }
    return render(request, 'super/titleManage.html', locals())

@login_required()
def addTitle(request):
    data = {}
    title = Title()
    title.role_name = request.POST['role_name']
    title.role_desc = request.POST['role_desc']
    try:
        title.save()
        data['msg'] = "新增职位成功"
        data['msgLevel'] = "info"
    except Exception as e:
        print(e.__str__())
        data['msg'] = "新增职位失败"
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def deleteTitle(request):
    data = {}
    titleId = request.POST['titleId']
    try:
        title = Title.objects.get(id=titleId)
        title.delete()
        data['msg'] = "删除职位成功"
        data['msgLevel'] = "info"
    except Exception as e:
        print(e.__str__)
        data['msg'] = "删除职位失败"
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def logoManage(request):
    if (request.user.userprofile.title.role_name != 'admin'):
        return HttpResponseRedirect("/")

    # trades = Trade.objects.all()
    # customers = Customer.objects.all()
    #
    # for customer in customers:
    #     customer.tradecount = trades.filter(customer_id=customer.id).count()
    #     customer.save()

    # # 修改密码
    # # users = User.objects.all()
    # # superprofile = UserProfile.objects.all()
    # # for user in superprofile:
    # #     if user.company == "T":
    # #         user.user.set_password("u000000")
    # #         user.user.save()
    #
    # teachers = Teacher.objects.all()
    # nums = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10']
    # for num in nums:
    #      for teacher in teachers:
    #         # 1组4部
    #         if teacher.teacherId == 'Z0104' + num:
    #             teacher.binduser.set_password('u000000')
    #             teacher.binduser.save()
    #             print(teacher.binduser.username)
    # nums = ['01', '02', '03', '04', '05', '06', '07', '08', '09']
    # for num in nums:
    #     for teacher in teachers:
    #         # 3组3部
    #         if teacher.teacherId == 'Z0303' + num:
    #             teacher.binduser.set_password('u000000')
    #             teacher.binduser.save()
    #             print(teacher.binduser.username)
    #         # 3组1部
    #         if teacher.teacherId == 'Z0301' + num:
    #             teacher.binduser.set_password('u000000')
    #             teacher.binduser.save()
    #             print(teacher.binduser.username)
    # nums = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11']
    # for num in nums:
    #     for teacher in teachers:
    #         # 2组2部
    #         if teacher.teacherId == 'Z0202' + num:
    #             teacher.binduser.set_password('u000000')
    #             teacher.binduser.save()
    #             print(teacher.binduser.username)

    return render(request, 'super/logoManage.html')

@login_required
def logoUpload(request):
    data = {}
    try:
        logofile = request.FILES['file']
        # file = open("super/static/super/images/header.jpg", "wb+")
        # file = open("super/static/super/images/header.jpg", "wb+")
        jpgfile = os.path.join(UPLOAD_ROOT, "/images/header.jpg")
        file = open(jpgfile,"wb+")
        for chunk in logofile.chunks():
            file.write(chunk)
        file.close()
        data['msg'] = "修改LOGO成功"
        data['msgLevel'] = "info"
    except Exception as e:
        print(e.__str__)
        data['msg'] = "删除职位失败"
        data['msgLevel'] = "error"
    return HttpResponse(json.dumps(data))

@login_required()
def getTransmission(request):
    msg = ""
    try:
        transmission = Transmission.objects.get(user=request.user, checked=False)
        msg = transmission.transmission
        transmission.checked = True
        transmission.save()

    except Exception as e:
        hasMessage = False
    if msg:
        hasMessage = True
    else:
        hasMessage = False
    data = {
        "hasMessage": hasMessage,
        "msg": msg,
    }
    return HttpResponse(json.dumps(data))

def demo(request):
    if request.user.is_authenticated():
        # birthday = time.strftime('%m%d',time.localtime(time.time()))
        # users = User.objects.filter(userprofile__cid__contains=birthday)
        # for birthdayuser in users:
        #     if birthdayuser.userprofile.cid[10:14] != birthday:
        #         users = users.exclude(user=birthdayuser)
        trades = Trade.objects.all()
        for trade in trades:
            if trade.status == 0:
                newTrade = Trade_memory.objects.create(trade=trade, stockid=trade.stockid)
        return render(request, 'super/demo.html', locals())
    else:
        redirect_to = 'accounts/login/'
        return HttpResponseRedirect(redirect_to)

@login_required()
def newsPush(request):
    if (request.user.userprofile.title.role_name == 'admin'):
        return render(request, 'ops/systemLog.html')
    else:
        return HttpResponseRedirect("/")

@login_required()
def birthdayNote(request):
    data = {
    }
    if request.user.is_authenticated():

        month = time.strftime('%m',time.localtime(time.time()))
        day = time.strftime('%d',time.localtime(time.time()))

        # users = User.objects.filter(userprofile__cid__contains=birthday)
        users = UserProfile.objects.filter(birthday__month=month, birthday__day=day)

        data = {
            'users': users,
        }


        return render(request, 'super/birthdayNote.html', data)
    else:
        redirect_to = 'accounts/login/'
        return HttpResponseRedirect(redirect_to)