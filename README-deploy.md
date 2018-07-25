## elastalert 

### 1. 根据要修改rules文件夹下规则文件(规则文件名任意)中，要查询的字段的配置
```
filter:
- query_string:
    query: "level: E* OR level: e*" （语法为kibana的查询语法）

```
### 2. 修改my_alert.py, 来定义要告警的信息有哪些,例如以下事例：
```
    def my_create_alert_body(self,matches):
        body=''
        index=0
        body+='**From staging environment** \n'
        body+='**===================** \n'
        for match in matches:
           index+=1
#           body+='**[第'+str(index)+'条消息]:** \n'
           body+='>- **k8s:host:** '+str(match['k8s:host'])+'\n'
           if match.has_key('k8s:app'):
           body+='>- **k8s:app:** '+str(match['k8s:app'])+'\n'
           body+='>- **level:** '+str(match['level'])+'\n'
           body+='>- **message:** '+str(match['message'])
        return body
```

### 3. 修改rules下的对应规则文件中的告警媒介：
```
alert:
- "elastalert_modules.my_alert.DingTalkAlerter" (其中my_alert与第二步的python文件的文件名对应)

dingtalk_webhook: 'https://oapi.dingtalk.com/robot/send?access_token=asd2502388da442f4bfed3bd4b80346c786c272362b0dcdb74a9208ca745c45' (钉钉机器人的webhook地址)
```

### 4. 启动elastalert 服务(docker-compose.yaml文件中配置的默认是与elasticsearch服务在同一台机器上)：
```
docker-compose up -d
```

### 5. 创建elastalert服务所使用的索引：
```
docker exec -it elastalert elastalert-create-index 

```
