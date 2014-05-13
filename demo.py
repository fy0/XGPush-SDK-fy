#!/usr/bin/env python
#-*- coding: utf-8 -*-
'''

Copyright © 1998 - 2013 Tencent. All Rights Reserved. 腾讯公司 版权所有

'''

import xinge

# 定义通知
def BuildNotification():
    msg = xinge.Message()
    msg.type = xinge.Message.TYPE_NOTIFICATION
    msg.title = 'some title'
    msg.content = 'some content'
    # 消息为离线设备保存的时间，单位为秒。默认为0，表示只推在线设备
    msg.expireTime = 300
    # 定时推送，若不需定时可以不设置
    msg.sendTime = '2012-12-12 18:48:00'
    # 自定义键值对，key和value都必须是字符串
    msg.custom = {'aaa':'111', 'bbb':'222'}
    # 使用多包名推送模式，详细说明参见文档和wiki，如果您不清楚该字段含义，则无需设置
    #msg.multiPkg = 1
    
    # 允许推送时段设置，若不需要可以去掉
    ti1 = xinge.TimeInterval(9, 30, 11, 30)
    ti2 = xinge.TimeInterval(14, 0, 17, 0)
    msg.acceptTime = (ti1, ti2)
    
    # 通知展示样式，仅对通知有效
    # 样式编号为2，响铃，震动，不可从通知栏清除，不影响先前通知
    style = xinge.Style(2, 1, 1, 0, 0)
    msg.style = style
    
    # 点击动作设置，仅对通知有效
    # 以下例子为点击打开url
    action = xinge.ClickAction()
    action.actionType = xinge.ClickAction.TYPE_URL
    action.url = 'http://xg.qq.com'
    # 打开url不需要用户确认
    action.confirmOnUrl = 0
    msg.action = action

    # 以下例子为点击打开intent。例子中的intent将打开拨号界面并键入10086
    # 使用intent.toUri(Intent.URI_INTENT_SCHEME)方法来得到序列化后的intent字符串，自定义intent参数也包含在其中
    #action = xinge.ClickAction()
    #action.actionType = xinge.ClickAction.TYPE_INTENT
    #action.intent = 'intent:10086#Intent;scheme=tel;action=android.intent.action.DIAL;S.key=value;end'
    #msg.action = action
    
    return msg

# 定义透传消息
def BuildMsg():
    msg = xinge.Message()
    msg.type = xinge.Message.TYPE_MESSAGE
    msg.title = 'some title'
    msg.content = 'some content'
    # 消息为离线设备保存的时间，单位为秒。默认为0，表示只推在线设备
    msg.expireTime = 300
    # 定时推送，若不需定时可以不设置
    msg.sendTime = '2012-12-12 18:48:00'
    # 自定义键值对，key和value都必须是字符串
    msg.custom = {'aaa':'111', 'bbb':'222'}
    # 使用多包名推送模式，详细说明参见文档和wiki，如果您不清楚该字段含义，则无需设置
    #msg.multiPkg = 1
    
    # 允许推送时段设置，若不需要可以去掉
    ti1 = xinge.TimeInterval(9, 30, 11, 30)
    ti2 = xinge.TimeInterval(14, 0, 17, 0)
    msg.acceptTime = (ti1, ti2)
    
    return msg

# 定义iOS消息
def BuildIOSMsg():
    msg = xinge.MessageIOS()
    # alert字段可以是字符串或json对象，参见APNS文档
    msg.alert = "alert content"
    # 消息为离线设备保存的时间，单位为秒。默认为0，表示只推在线设备
    msg.expireTime = 300
    # 定时推送，若不需定时可以不设置
    msg.sendTime = '2012-12-12 18:48:00'
    # 自定义键值对，value可以是json允许的类型
    msg.custom = {'aaa':'111', 'bbb':{'b1':1, 'b2':2}}
    
    # 允许推送时段设置，若不需要可以去掉
    ti1 = xinge.TimeInterval(9, 30, 11, 30)
    ti2 = xinge.TimeInterval(14, 0, 17, 0)
    msg.acceptTime = (ti1, ti2)
    
    return msg

# 按token推送
def DemoPushToken(x, msg):
    # 第三个参数environment仅在iOS下有效。ENV_DEV表示推送APNS开发环境
    ret = x.PushSingleDevice('some_token', msg, xinge.XingeApp.ENV_DEV)
    print(ret)

# 按账号推送
def DemoPushAccount(x, msg):
    ret = x.PushSingleAccount(xinge.XingeApp.DEVICE_ALL, '123456', msg, xinge.XingeApp.ENV_DEV)
    print(ret)

# 按app推送
def DemoPushAll(x, msg):
    # 第三个参数environment仅在iOS下有效。ENV_DEV表示推送APNS开发环境
    ret = x.PushAllDevices(xinge.XingeApp.DEVICE_ALL, msg, xinge.XingeApp.ENV_DEV)
    print(ret)

# 按tag推送 
def DemoPushTags(x, msg):
    # 第三个参数environment仅在iOS下有效。ENV_DEV表示推送开发环境
    ret = x.PushTags(xinge.XingeApp.DEVICE_ALL, ('tag1','tag2'), 'AND', msg, xinge.XingeApp.ENV_DEV)
    print(ret)

# 查询群发任务状态
def DemoQueryPushStatus(x):
    # 查询群发id为31和30的消息状态
    ret = x.QueryPushStatus(('31','30'))
    print(ret)

# 查询app覆盖设备数量
def DemoQueryDeviceNum(x):
    ret = x.QueryDeviceCount()
    print(ret)

# 查询tag
def DemoQueryTags(x):
    # 查询头5个tag
    ret = x.QueryTags(0, 5)
    print(ret)

# 取消尚未触发的定时群发任务
def DemoCancelTimingPush(x):
    ret = x.CancelTimingPush('31')
    print(ret)

if '__main__' == __name__:
    # 初始化app对象，设置有效的access id和secret key
    x = xinge.XingeApp(0, 'secret')
    
    # 构建一条消息，可以是通知或者透传消息
    #msg = BuildMsg()
    #msg = BuildNotification()
    
    # 构建iOS消息。注意iOS只有一种消息类型，不分通知/透传
    # iOS推送，调用push接口时切记设置ENV
    msg = BuildIOSMsg()
    
    DemoPushToken(x, msg)
    DemoPushAccount(x, msg)
    DemoPushAll(x, msg)
    DemoPushTags(x, msg)
    DemoQueryPushStatus(x)
    DemoQueryDeviceNum(x)
    DemoQueryTags(x)
    DemoCancelTimingPush(x)
    

