# 文件说明



## 镜像所需文件：

Dockerfile 

elastalert_modules

elastalert_modules为钉钉报警所需文件



## docker启动配置文件

### config.yaml

config.yaml文件定义：

- rules_folder: 报警规则文件目录
- run_every:
- buffer_time:
- writeback_index: 将报警信息写到elasticsearch中的索引

### rules

此与elastalert的规则配置文件相同

### docker-compose.yaml

docker-compose.yaml文件配置：

- command(optional): 
  - "--verbose"#输入日志信息
  - "--debug" #在命令行显示运行消息
- volumes:
  - "./rules:/rules"
  - "./connfig.yaml:/config.yaml"
  - "./my_alert.py:/usr/local/lib/python2.7/site-package/elastalert_modules/my_alert.py"
  
  第一项：必填
  为规则挂载路径
  注意：其在docker内挂载路径需与config.yaml中配置的相同
  
  第二项：必填
  为报警配置文件
  
  第三项：选填
  自定义报警
  注意：其路径必须在“/usr/local/lib/python2.7/site-package/elastalert_modules/”路径下
- environment:
  ES的地址和端口号
  - ES_HOST: ""
  - ES_PORT: ""
    

## 自定义报警配置文件

my_alert.py

该文件通过改写body = self.create_alert_body(matches)这一句来自定义报警模板



# 运行说明

## 获取镜像

git clone https://github.com/zenland/longging_alert_docker.git

以下涉及的文件均在logging_alert_docker文件夹下

## 配置文件

config.yaml

主要配置:

- rules_folder
- writeback_index

rules/example_test.yaml文件

主要配置: 

- 报警规则

- name(一个规则文件对应一个名字)
- alert
- dingtalk_wehook
- dingtalk_msgtype

docker-compose.yaml文件

主要配置：

- command
- volumes(重要)
- environment



## 运行

docker-compose up



# 例子

以cpu的日志信息为例，elasticsearch监听地址：106.75.229.247：9200

以cpu的日志信息为例

## config.yaml文件

该文件指明将报警规则配置文件在/rules目录下

    rules_folder: /rules
    scan_subdirectiories: false
    
    # How often ElastAlert will query Elasticsearch
    # The unit can be anything from weeks to seconds
    run_every:
      seconds: 10
    
    # ElastAlert will buffer results from the most recent
    # period of time, in case some log sources are not in real time
    buffer_time:
      minutes: 15
    
    # Connect with TLS to Elasticsearch
    use_ssl: false
    
    # The index on es_host which is used for metadata storage
    # This can be a unmapped index, but it is recommended that you run
    # elastalert-create-index to set a mapping
    writeback_index: elastalert_status
    
    # If an alert fails for some reason, ElastAlert will retry
    # sending the alert until this time period has elapsed
    alert_time_limit:
      days: 1
    

## /example_test.yaml文件

该文件指定，规则名字:zxl_test_rule,报警规则:事件"cpu0_p_user: 0"出现次数在50分钟内大于1次，以及报警方式:钉钉,钉钉路径，文本类型

    #Alert when the rate of events exceeds a threshold
    
    # (Optional)
    # Elasticsearch host
    #es_host: 106.75.229.247
    
    # (Optional)
    # Elasticsearch port
    #es_port: 9200
    
    # (OptionaL) Connect with SSL to Elasticsearch
    #use_ssl: True
    
    # (Optional) basic-auth username and password for Elasticsearch
    #es_username: someusername
    #es_password: somepassword
    
    # (Required)
    # Rule name, must be unique
    name: zxl_test_rule
    
    # (Required)
    # Type of alert.
    # the frequency rule type alerts when num_events events occur with timeframe time
    type: frequency
    
    # (Required)
    # Index to search, wildcard supported
    index: logstash-*
    
    # (Required, frequency specific)
    # Alert when this many documents matching the query occur within a timeframe
    num_events: 1
    
    # (Required, frequency specific)
    # num_events must occur within this amount of time to trigger an alert
    timeframe:
      minutes: 50
    
    # (Required)
    # A list of Elasticsearch filters used for find events
    # These filters are joined with AND and nested in a filtered query
    # For more info: http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl.html
    filter:
    - query_string:
        query: "cpu0_p_user: 0"
    
    # (Required)
    # The alert is use when a match is found
    alert:
    #- "email"
    #- "debug"
    - "elastalert_modules.dingtalk_alert.DingTalkAlerter"
    
    dingtalk_webhook: 'https://oapi.dingtalk.com/robot/send?access_token=cda32502388da442f4bfed3bd4b80346c786c272362b0dcdb74a9208ca745c45'
    dingtalk_msgtype: text
    #- "debug"
    #- "command"
    #pipe_match_json: true
    #command: ["/home/jane/alertfile/php_alert.php"]
    # (required, email specific)
    # a list of email addresses to send alerts to
    

## docker-compose.yaml文件

    version: "3"
    services:
      elastalert:
        image: dingding_alert:1.0
        #build: ./
        container_name: elastalert
        command:
        - "--verbose"
        #- "--debug"
        volumes:
        - "./rules:/rules"
        - "./config.yaml:/config.yaml"
        - "./my_alert.py:/usr/local/lib/python2.7/site-packages/elastalert_modules/my_alert.py"
        environment:
          ES_HOST: "106.75.229.247"
          ES_PORT: 9200

## my_alert.py
该文件改写了body=create_alert_body(matches)方法

    #! /usr/bin/env python
    # -*- coding: utf-8 -*-
    
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
            body+='报警测试,这是新的文件:'+'\n'
            for match in matches:
               index+=1
               body+='第'+str(index)+'条消息:\n'
               body+='CPU_P:'+str(match['cpu_p'])+'\n'
               body+='USER_P:'+str(match['user_p'])+'\n'
            return body
    
        def alert(self, matches):
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json;charset=utf-8"
            }
    #        pdb.set_trace()
            #body = self.my_create_alert_body(matches)
            body="这是用于创建的第二个规则"
            payload = {
                "msgtype": self.dingtalk_msgtype,
                "text": {
                    "content": body
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
    


