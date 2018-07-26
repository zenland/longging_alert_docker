#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: xuyaoqiang
@contact: xuyaoqiang@gmail.com
@date: 2017-09-14 17:35
@version: 0.0.0
@license:
@copyright:

"""
import json
import requests
from elastalert.alerts import Alerter, DateTimeEncoder
from requests.exceptions import RequestException
from elastalert.util import EAException
import pdb

class DingTalkAlerter(Alerter):
    
    required_options = frozenset(['dingtalk_webhook', 'dingtalk_msgtype'])

    def __init__(self, rule):
        super(DingTalkAlerter, self).__init__(rule)
        self.dingtalk_webhook_url = self.rule['dingtalk_webhook']
        self.dingtalk_msgtype = self.rule.get('dingtalk_msgtype', 'text')
        self.dingtalk_isAtAll = self.rule.get('dingtalk_isAtAll', False)
        self.digtalk_title = self.rule.get('dingtalk_title', '')

    def format_body(self, body):
        return body.encode('utf8')
    def my_create_alert_body(self,matches):
        body=''
        index=0
        body+='**From staging environment** \n'
        body+='**===================** \n'
        for match in matches:
           index+=1
#           body+='**[第'+str(index)+'条消息]:** \n'
           body+='>- **k8s:host:** '+str(match['k8s:host'])+'\n'
	   body+='>- **k8s:app:** '+str(match['k8s:app'])+'\n'
           if match.has_key('k8s:pod_name'):
	       body+='>- **k8s:pod_name:** '+str(match['k8s:pod_name'])+'\n'
           elif match.has_key('service_name'):
	       body+='>- **service_name:** '+str(match['service_name'])+'\n'
           body+='>- **level:** '+str(match['level'])+'\n'
           body+='>- **message:** '+str(match['message'])
        return body
       
    def alert(self, matches):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json;charset=utf-8"
        }
#        pdb.set_trace()
        body = self.my_create_alert_body(matches)
        #body="这是用于创建的第二个规则"
        payload = {
            "msgtype": self.dingtalk_msgtype,
            "markdown": {
		"title": "test",
		"text": body
            },
	    "at": {
	        "isAtAll":False
	    }
        }
        try:
            response = requests.post(self.dingtalk_webhook_url, 
                        data=json.dumps(payload, cls=DateTimeEncoder),
                        headers=headers)
            response.raise_for_status()
        except RequestException as e:
            raise EAException("Error request to Dingtalk: {0}".format(str(e)))

    def get_info(self):
        return {
            "type": "dingtalk",
            "dingtalk_webhook": self.dingtalk_webhook_url
        }
        pass
