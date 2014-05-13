#!/usr/bin/env python3
# coding:utf-8
'''

Copyright ? 1998 - 2013 Tencent. All Rights Reserved. 腾讯公司 版权所有

py3 supported - fy, 2014
http://github.com/fy0

'''


import time
import hashlib
import requests

try:
    import ujson as json
except:
    import json

ERR_OK = 0
ERR_PARAM = -1
ERR_TIMESTAMP = -2
ERR_SIGN = -3
ERR_INTERNAL = -4
ERR_HTTP = -100
ERR_RETURN_DATA = -101

class TimeInterval(object):
    STR_START = 'start'
    STR_END = 'end'
    STR_HOUR = 'hour'
    STR_MIN = 'min'
    
    def __init__(self, startHour=0, startMin=0, endHour=0, endMin=0):
        self.startHour = startHour
        self.startMin = startMin
        self.endHour = endHour
        self.endMin = endMin
        
    def _isValidTime(self, hour, minute):
        return isinstance(hour, int) and isinstance(minute, int) and hour >= 0 and hour <=23 and minute >=0 and minute <= 59
    
    def _isValidInterval(self):
        return self.endHour * 60 + self.endMin >= self.startHour * 60 + self.startMin
        
    def GetObject(self):
        if not (self._isValidTime(self.startHour, self.startMin) and self._isValidTime(self.endHour, self.endMin)):
            return None
        if not self._isValidInterval():
            return None
        return {
                self.STR_START:{self.STR_HOUR:str(self.startHour), self.STR_MIN:str(self.startMin)},
                self.STR_END:{self.STR_HOUR:str(self.endHour), self.STR_MIN:str(self.endMin)}
            }

class ClickAction(object):
    TYPE_ACTIVITY = 1
    TYPE_URL = 2
    TYPE_INTENT = 3
    
    def __init__(self, actionType=1, url='', confirmOnUrl=0, activity='', intent=''):
        self.actionType = actionType
        self.url = url
        self.confirmOnUrl = confirmOnUrl
        self.activity = activity
        self.intent = intent
        
    def GetObject(self):
        ret = {}
        ret['action_type'] = self.actionType
        if self.TYPE_ACTIVITY == self.actionType:
            ret['activity'] = self.activity
        elif self.TYPE_URL == self.actionType:
            ret['browser'] = {'url':self.url, 'confirm':self.confirmOnUrl}
        elif self.TYPE_INTENT == self.actionType:
            ret['intent'] = self.intent
        
        return ret

class Style(object):
    N_INDEPENDENT = 0
    N_THIS_ONLY = -1

    def __init__(self, builderId=0, ring=0, vibrate=0, clearable=1, nId=N_INDEPENDENT):
        self.builderId = builderId
        self.ring = ring
        self.vibrate = vibrate
        self.clearable = clearable
        self.nId = nId

class Message(object):
    TYPE_NOTIFICATION = 1
    TYPE_MESSAGE = 2
    
    PUSH_SINGLE_PKG = 0
    PUSH_ACCESS_ID = 1
    
    def __init__(self):
        self.title = ""
        self.content = ""
        self.expireTime = 0
        self.sendTime = ""
        self.acceptTime = ()
        self.type = 0
        self.style = None
        self.action = None
        self.custom = {}
        self.multiPkg = self.PUSH_SINGLE_PKG
        self.raw = None
        
    def GetMessageObject(self):
        if self.raw is not None:
            if isinstance(self.raw, str):
                return json.loads(self.raw)
            else:
                return self.raw
        
        message = {}
        message['title'] = self.title
        message['content'] = self.content
        
        # TODO: check custom
        message['custom_content'] = self.custom
        
        acceptTimeObj = self.GetAcceptTimeObject()
        if None == acceptTimeObj:
            return None
        elif acceptTimeObj != []:
            message['accept_time'] = acceptTimeObj
        
        if self.type == self.TYPE_NOTIFICATION:
            if None == self.style:
                style = Style()
            else:
                style = self.style
                
            if isinstance(style, Style):
                message['builder_id'] = style.builderId
                message['ring'] = style.ring
                message['vibrate'] = style.vibrate
                message['clearable'] = style.clearable
                message['n_id'] = style.nId
            else:
                # style error
                return None
            
            if None == self.action:
                action = ClickAction()
            else:
                action = self.action
            
            if isinstance(action, ClickAction):
                message['action'] = action.GetObject()
            else:
                # action error
                return None
        elif self.type == self.TYPE_MESSAGE:
            pass
        else:
            return None
        
        return message
    
    def GetAcceptTimeObject(self):
        ret = []
        for ti in self.acceptTime:
            if isinstance(ti, TimeInterval):
                o = ti.GetObject()
                if o is None:
                    return None
                else:
                    ret.append(ti.GetObject())
            else:
                return None
        return ret
        
class MessageIOS(Message):
    def __init__(self):
        Message.__init__(self)
        self.alert = None
        self.badge = None
        self.sound = None
        self.raw = None
        
    def GetMessageObject(self):
        if self.raw is not None:
            if isinstance(self.raw, str):
                return json.loads(self.raw)
            else:
                return self.raw
            
        message = self.custom
        
        acceptTimeObj = self.GetAcceptTimeObject()
        if None == acceptTimeObj:
            return None
        elif acceptTimeObj != []:
            message['accept_time'] = acceptTimeObj
            
        aps = {}
        if isinstance(self.alert, str) or isinstance(self.alert, dict):
            aps['alert'] = self.alert
        else:
            # alert type error
            return None
        if self.badge is not None:
            aps['badge'] = self.badge
        if self.sound is not None:
            aps['sound'] = self.sound
        message['aps'] = aps
        return message

class MessageStatus(object):
    def __init__(self, status, startTime, finished, total):
        self.status = status
        self.startTime = startTime
        self.finished = finished
        self.total = total
    
    def __str__(self):
        return str(vars(self))
    
    def __repr__(self):
        return self.__str__()

class XingeApp(object):
    DEVICE_ALL = 0
    DEVICE_BROWSER = 1
    DEVICE_PC = 2
    DEVICE_ANDROID = 3
    DEVICE_IOS = 4
    DEVICE_WP = 5
    
    PATH_PUSH_TOKEN = '/v2/push/single_device'
    PATH_PUSH_ACCOUNT = '/v2/push/single_account'
    PATH_PUSH_ALL = '/v2/push/all_device'
    PATH_PUSH_TAGS = '/v2/push/tags_device'
    PATH_GET_PUSH_STATUS = '/v2/push/get_msg_status'
    PATH_GET_DEV_NUM = '/v2/application/get_app_device_num'
    PATH_QUERY_TAGS = '/v2/tags/query_app_tags'
    PATH_CANCEL_TIMING_PUSH = '/v2/push/cancel_timing_task'
    
    ENV_PROD = 1
    ENV_DEV = 2
    
    def __init__(self, accessId, secretKey):
        self.accessId = int(accessId)
        self.secretKey = str(secretKey)
        
    def InitParams(self):
        params = {}
        params['access_id'] = self.accessId
        params['timestamp'] = XingeHelper.GenTimestamp()
        return params
    
    def SetPushParams(self, params, message, environment):
        params['expire_time'] = message.expireTime
        params['send_time'] = message.sendTime
        params['message_type'] = message.type
        params['multi_pkg'] = message.multiPkg
        params['environment'] = environment
        msgObj = message.GetMessageObject()
        if None == msgObj:
            return False
        else:
            params['message'] = json.dumps(msgObj, ensure_ascii=False)
            return True
        
    def Request(self, path, params):
        params['sign'] = XingeHelper.GenSign(path, params, self.secretKey)
        return XingeHelper.Request(path, params)
    
    def PushSingleDevice(self, deviceToken, message, environment=0):
        deviceToken = str(deviceToken)
        if not (isinstance(message, Message) or isinstance(message, MessageIOS)):
            return ERR_PARAM, 'message type error'
        
        params = self.InitParams()
        if False == self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input'
        params['device_token'] = deviceToken
        
        ret = self.Request(self.PATH_PUSH_TOKEN, params)
        return ret[0], ret[1]
    
    def PushSingleAccount(self, deviceType, account, message, environment=0):
        deviceType = int(deviceType)
        account = str(account)
        if not isinstance(message, Message):
            return ERR_PARAM, 'message type error'
        
        params = self.InitParams()
        if False == self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input'
        params['device_type'] = deviceType
        params['account'] = account
        
        ret = self.Request(self.PATH_PUSH_ACCOUNT, params)
        return ret[0], ret[1]
    
    def PushAllDevices(self, deviceType, message, environment=0):
        deviceType = int(deviceType)
        if not (isinstance(message, Message) or isinstance(message, MessageIOS)):
            return ERR_PARAM, 'message type error', None
        
        params = self.InitParams()
        if False == self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input', None
        params['device_type'] = deviceType
        
        ret = self.Request(self.PATH_PUSH_ALL, params)
        result = None
        if ERR_OK == ret[0]:
            if 'push_id' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            else:
                result = ret[2]['push_id']
        return ret[0], ret[1], result
    
    def PushTags(self, deviceType, tagList, tagsOp, message, environment=0):
        deviceType = int(deviceType)
        if not (isinstance(message, Message) or isinstance(message, MessageIOS)):
            return ERR_PARAM, 'message type error', None
        if not isinstance(tagList, (tuple, list)):
            return ERR_PARAM, 'tagList type error', None
        if tagsOp not in ('AND','OR'):
            return ERR_PARAM, 'tagsOp error', None
        
        params = self.InitParams()
        if False == self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input', None
        params['device_type'] = deviceType
        params['tags_list'] = json.dumps([str(tag) for tag in tagList], separators=(',',':'))
        params['tags_op'] = tagsOp
        
        ret = self.Request(self.PATH_PUSH_TAGS, params)
        result = None
        if ERR_OK == ret[0]:
            if 'push_id' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            else:
                result = ret[2]['push_id']
        return ret[0], ret[1], result
    
    def QueryPushStatus(self, pushIdList):
        if not isinstance(pushIdList, (tuple, list)):
            return ERR_PARAM, 'pushIdList type error', None
        
        params = self.InitParams()
        params['push_ids'] = json.dumps([{'push_id':str(pushId)} for pushId in pushIdList], separators=(',',':'))
        
        ret = self.Request(self.PATH_GET_PUSH_STATUS, params)
        result = {}
        if ERR_OK == ret[0]:
            if 'list' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            for status in ret[2]['list']:
                result[status['push_id']] = MessageStatus(status['status'], status['start_time'], status['finished'], status['total'])
            
        return ret[0], ret[1], result
    
    def QueryDeviceCount(self):
        params = self.InitParams()
        ret = self.Request(self.PATH_GET_DEV_NUM, params)
        result = None
        if ERR_OK == ret[0]:
            if 'device_num' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            else:
                result = ret[2]['device_num']
        return ret[0], ret[1], result
    
    def QueryTags(self, start, limit):
        params = self.InitParams()
        params['start'] = int(start)
        params['limit'] = int(limit)
        
        ret = self.Request(self.PATH_QUERY_TAGS, params)
        retCode = ret[0]
        total = None
        tags = []
        if ERR_OK == ret[0]:
            if 'total' not in ret[2]:
                retCode = ERR_RETURN_DATA
            else:
                total = ret[2]['total']
                
            if 'tags' in ret[2]:
                tags = ret[2]['tags']
        return retCode, ret[1], total, tags
    
    def CancelTimingPush(self, pushId):
        params = self.InitParams()
        params['push_id'] = str(pushId)
        
        ret = self.Request(self.PATH_CANCEL_TIMING_PUSH, params)
        return ret[0], ret[1]
        

class XingeHelper(object):
    XINGE_HOST = 'openapi.xg.qq.com'
    XINGE_PORT = 80
    TIMEOUT = 30
    HTTP_METHOD = 'POST'
    HTTP_HEADERS = {'HOST' : XINGE_HOST}
    
    STR_RET_CODE = 'ret_code'
    STR_ERR_MSG = 'err_msg'
    STR_RESULT = 'result'
    
    @classmethod
    def SetServer(cls, host=XINGE_HOST, port=XINGE_PORT):
        cls.XINGE_HOST = host
        cls.XINGE_PORT = port
        cls.HTTP_HEADERS = {'HOST' : cls.XINGE_HOST}
    
    @classmethod
    def GenSign(cls, path, params, secretKey):
        ks = sorted(params.keys())
        paramStr = ''.join([('%s=%s' % (k, params[k])) for k in ks])
        signSource = '%s%s%s%s%s' % (cls.HTTP_METHOD, cls.XINGE_HOST, path, paramStr, secretKey)
        try:
            return hashlib.md5(signSource).hexdigest()
        except TypeError: #py3
            return hashlib.md5(bytes(signSource, 'utf-8')).hexdigest()
    
    @classmethod
    def GenTimestamp(cls):
        return int(time.time())
    
    @classmethod
    def Request(cls, path, params):
        ret = None
        url = 'http://%s:%s%s' % (cls.XINGE_HOST, cls.XINGE_PORT, path)

        if cls.HTTP_METHOD == 'GET':
            ret = requests.get(url, timeout=cls.TIMEOUT, params=params, headers=cls.HTTP_HEADERS)
        elif cls.HTTP_METHOD == 'POST':
            ret = requests.post(url, timeout=cls.TIMEOUT, data=params, headers=cls.HTTP_HEADERS)
        else:
            # invalid method
            return ERR_PARAM, '', None

        retCode = ERR_RETURN_DATA
        errMsg = ''
        result = {}
        if 200 != ret.status_code:
            retCode = ERR_HTTP
        else:
            retDict = json.loads(ret.text)
            if(cls.STR_RET_CODE in retDict):
                retCode = retDict[cls.STR_RET_CODE]
            if(cls.STR_ERR_MSG in retDict):
                errMsg = retDict[cls.STR_ERR_MSG]
            if(cls.STR_RESULT in retDict):
                if isinstance(retDict[cls.STR_RESULT], dict):
                    result = retDict[cls.STR_RESULT]
                else:
                    retCode = ERR_RETURN_DATA
        return retCode, errMsg, result
            
        

