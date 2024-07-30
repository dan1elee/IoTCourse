import time
import json
from hashlib import md5

from django.http import HttpResponse, JsonResponse

from apis.aep_device_event import QueryDeviceEventList
from apis.aep_device_command import CreateCommand
from apis.aep_device_status import QueryDeviceStatus
from django.shortcuts import render, redirect
from IoT import models
from IoTCourse.wsgi import data

pCfg = {
    'appKey': data.get('appKey', ''),
    'appSecret': data.get('appSecret', ''),
    'masterKey': data.get('masterKey', ''),
    'productId': data.get('productId', ''),
    'deviceId': data.get('deviceId', '')
}

context = {
    'ir_status': '暂未获取',
    'temp': '暂未获取',
    'humidity': '暂未获取',
    'msg': '暂无',
    'intrusion_alert': '0',
    'delay': '0'
}

login = False


# Create your views here.
def default_page(request):
    if not login:
        return redirect('/login/')
    else:
        return redirect('/index/')


def change_pwd(request):
    if not login:
        return redirect('/login/')
    else:
        return render(request, 'change.html')


def about(request):
    if not login:
        return redirect('/login/')
    else:
        return render(request, 'about.html')


def login_page(request):
    if not login:
        return render(request, 'login.html')
    else:
        return redirect('/index/')


def index(request):
    if not login:
        return redirect('/login/')
    else:
        return render(request, 'index.html')


def set_delay(value):
    result = CreateCommand(
        appKey=pCfg['appKey'],
        appSecret=pCfg['appSecret'],
        MasterKey=pCfg['masterKey'],
        body='{'
             '"content": '
             '{'
             '"params": {"delay": "' + str(int(value) * 1000) + '" },'  # 指令参数
                                                                '"serviceIdentifier": "set_delay"'  # 服务定义时的服务标识
                                                                '},'
                                                                '"deviceId": "' + pCfg['deviceId'] + '",'
                                                                                                     '"operator": "20232ndGroup", '
                                                                                                     '"productId": ' +
             pCfg[
                 'productId'] + ', '
                                '"ttl": 7200,'
                                '"deviceGroupId": null,'
                                '"level": 1'
                                '}'
    )
    print('result=' + str(result.decode()))
    res = json.loads(result.decode())
    if res['code'] == 0 and res['msg'] == 'ok':
        data = res['result']['commandStatus']
        print('data :', data)
        if data == '指令已保存':
            print('设置延时指令发送成功')
            context['delay'] = str(value)
            context['msg'] = '设置延时指令发送成功'
        else:
            print('设置延时指令发送失败')
            context['msg'] = '设置延时指令发送失败'
    else:
        print('设置延时指令发送失败')
        context['msg'] = '设置延时指令发送失败'
    return JsonResponse(context)


def clear():
    context['ir_status'] = '暂未获取'
    context['temp'] = '暂未获取'
    context['humidity'] = '暂未获取'
    context['msg'] = '暂无'
    context['intrusion_alert'] = '0'
    return JsonResponse(context)


def get_ir_status():
    start_time = str(int(time.time() - 3600) * 1000)
    end_time = str(int(time.time()) * 1000)
    # 发起请求
    result = QueryDeviceEventList(appKey=pCfg['appKey'], appSecret=pCfg['appSecret'], MasterKey=pCfg['masterKey'],
                                  body=json.dumps({
                                      'productId': pCfg['productId'],
                                      'deviceId': pCfg['deviceId'],
                                      'eventType': 1,  # 非必填
                                      'startTime': start_time,
                                      'endTime': end_time,
                                      'pageSize': 1
                                  }))
    # 解析返回信息
    res = json.loads(result.decode())
    temp = json.loads(QueryDeviceStatus(appKey=pCfg['appKey'], appSecret=pCfg['appSecret'], body=json.dumps(
        {"productId": pCfg['productId'], "deviceId": pCfg['deviceId'], "datasetId": "temperature_data"})).decode())
    humi = json.loads(QueryDeviceStatus(appKey=pCfg['appKey'], appSecret=pCfg['appSecret'], body=json.dumps(
        {"productId": pCfg['productId'], "deviceId": pCfg['deviceId'], "datasetId": "humidity_data"})).decode())
    print(res)
    print("temp=" + str(temp))
    print("humi=" + str(humi))
    if res['code'] == 0 and res['msg'] == 'ok':
        if len(res['result']['list']) == 0:
            context['ir_status'] = '状态无内容'
            context['intrusion_alert'] = '0'
        else:
            # print("res="+res)
            event_content = res['result']['list'][0]['eventContent']
            ir_data = json.loads(event_content)['ir_sensor_data']
            if ir_data == 0:
                print('红外未被遮挡')
                context['ir_status'] = '红外未被遮挡'
                context['intrusion_alert'] = '0'
            else:
                print('红外已被遮挡')
                context['ir_status'] = '红外已被遮挡'
                context['intrusion_alert'] = '1'
                # open_motor()
    else:
        print('未检测到传感器信息')
        context['ir_status'] = '未检测到传感器信息'
        context['intrusion_alert'] = '0'
    if temp['code'] == 0:
        temp_data = temp['deviceStatus']['value']
        context['temp'] = str(int(float(temp_data) * 10) / 10)
    else:
        context['temp'] = '未收到温度信息'
    if humi['code'] == 0:
        humi_data = humi['deviceStatus']['value']
        context['humidity'] = humi_data
    else:
        context['humidity'] = '未收到湿度信息'
    return JsonResponse(context)


def open_motor():
    result = CreateCommand(
        appKey=pCfg['appKey'],
        appSecret=pCfg['appSecret'],
        MasterKey=pCfg['masterKey'],
        body='{'
             '"content": '
             '{'
             '"params": {"motor_control": "1" },'  # 指令参数
             '"serviceIdentifier": "motor_control_cmd"'  # 服务定义时的服务标识
             '},'
             '"deviceId": "' + pCfg['deviceId'] + '",'
                                                  '"operator": "20232ndGroup", '
                                                  '"productId": ' + pCfg['productId'] + ', '
                                                                                        '"ttl": 7200,'
                                                                                        '"deviceGroupId": null,'
                                                                                        '"level": 1'
                                                                                        '}')
    print('result=' + str(result.decode()))
    res = json.loads(result.decode())
    if res['code'] == 0 and res['msg'] == 'ok':
        data = res['result']['commandStatus']
        print('data :', data)
        if data == '指令已保存':
            print('开启电机指令发送成功')
            context['msg'] = '开启电机指令发送成功'
        else:
            print('开启电机指令发送失败')
            context['msg'] = '开启电机指令发送失败'
    else:
        print('开启电机指令发送失败')
        context['msg'] = '开启电机指令发送失败'
    return JsonResponse(context)


# 关闭电机
def close_motor():
    result = CreateCommand(
        appKey=pCfg['appKey'],
        appSecret=pCfg['appSecret'],
        MasterKey=pCfg['masterKey'],
        body='{'
             '"content": '
             '{'
             '"params": {"motor_control": "0" },'
             '"serviceIdentifier": "motor_control_cmd"'
             '},'
             '"deviceId": "' + pCfg['deviceId'] + '",'
                                                  '"operator": "20232ndGroup", '
                                                  '"productId": ' + pCfg['productId'] + ', '
                                                                                        '"ttl": 7200,'
                                                                                        '"deviceGroupId": null,'
                                                                                        '"level": 1'
                                                                                        '}')
    print('result=' + str(result.decode()))
    res = json.loads(result.decode())
    if res['code'] == 0 and res['msg'] == 'ok':
        data = res['result']['commandStatus']
        print('data :', data)
        if data == '指令已保存':
            print('关闭电机指令发送成功')
            context['msg'] = '关闭电机指令发送成功'
            context['intrusion_alert'] = '0'
        else:
            print('关闭电机指令发送失败')
            context['msg'] = '关闭电机指令发送失败'
    else:
        print('关闭电机指令发送失败')
        context['msg'] = '关闭电机指令发送失败'
    return JsonResponse(context)


def pwd_check(pwd):
    global login
    user_pwd = models.Pwd.objects.filter(user="user").first().password
    print("password: " + user_pwd)
    if pwd == user_pwd:
        login = True
        return JsonResponse({'status': '1'})
    else:
        return JsonResponse({'status': '0'})


def iot_request(request):
    if request.method == 'GET':
        # Handle the GET request and request_type parameter here
        request_type = request.GET.get('request_type')
        if request_type == "1":
            return get_ir_status()
        elif request_type == "2":
            return open_motor()
        elif request_type == "3":
            return close_motor()
        elif request_type == "4":
            value = request.GET.get('value')
            set_delay(value)
        elif request_type == "5":
            return clear()
        elif request_type == "6":
            pwd = request.GET.get('pwd')
            return pwd_check(pwd)
        elif request_type == "7":
            global login
            login = False
            return JsonResponse({'status': '1'})
        elif request_type == "8":
            pwd = request.GET.get('pwd')
            return pwd_set(pwd)
    return JsonResponse(context)


def pwd_set(pwd):
    user_pwd = models.Pwd.objects.filter(user="user").first().password
    if pwd == user_pwd:
        return JsonResponse({'status': '2'})
    else:
        models.Pwd.objects.filter(user="user").update(password=pwd)
        return JsonResponse({'status': '1'})
