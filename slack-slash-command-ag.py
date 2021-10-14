import json
import boto3
import slackweb

def slack_send(url, message):
    slack = slackweb.Slack(url=url)
    # slack.notify(response_type="in_channel", text=message)
    slack.notify(text=message)

def get_client(service_name, token):
    ssm = boto3.client('ssm', region_name="ap-northeast-2")
    response = ssm.get_parameter(Name=token, WithDecryption=True)
    key = response['Parameter']['Value']
    key = key.split(',')

    
    return boto3.client(
        service_name,
        aws_access_key_id=key[0],
        aws_secret_access_key=key[1],
        region_name="ap-northeast-2"
    )

def describe(client, token):
    info = ""
    name_tag = ""
    cnt = 0
    ag_list = client.describe_auto_scaling_groups()
    
    for ag in ag_list['AutoScalingGroups']:
        ag_name = ag['AutoScalingGroupName']
        ag_des_capacity = ag['DesiredCapacity']
        ag_min_capacity = ag['MinSize']
        ag_max_capacity = ag['MaxSize']
        ag_tags = ag['Tags']
        cnt += 1
        
        ag_tag = (item for item in ag_tags if item['Key'] == 'Name')
        name_tag_dict = next(ag_tag, False)
        
        if name_tag_dict != False :
            name_tag = name_tag_dict['Value']
        else :
            name_tag = "Unknown"
     
        
        info += "["+ str(cnt) + "]\t"+ ag_name + "\t(" +name_tag + ")\t" + str(ag_des_capacity) + "\t" + str(ag_min_capacity) + "\t" + str(ag_max_capacity) + "\n"
        ec2_list = ag['Instances']
        try:
            ec2_id_list=[]
            for ec2 in ec2_list:
                ec2_id_list.append(ec2['InstanceId'])
        except :
            continue
    print(info)
    return info
    
def all_ag_name(client, token):
    
    info = ""
    ag_list = client.describe_auto_scaling_groups()
    ag_name_list = []
    cnt = 0
    
    for ag in ag_list['AutoScalingGroups']:
        ag_name = ag['AutoScalingGroupName']
        ag_tags = ag['Tags']
        cnt += 1
        

        ag_tag = (item for item in ag_tags if item['Key'] == 'Name')
        name_tag_dict = next(ag_tag, False)
        
        if name_tag_dict != False :
            name_tag = name_tag_dict['Value']
        else :
            name_tag = "Unknown"

        
        ag_dic = {"Cnt": str(cnt) ,"Name":ag_name,"Tag":name_tag}
        
        ag_name_list.append(ag_dic)
    
    print(ag_name_list)
        
    return ag_name_list

def update(client, name, desire_capacity, min_capacity, max_capacity, token):
    
    asg_names = all_ag_name(client, token)
    
    print(asg_names)
   
    # ags_cnt = 0
    # for ags in ags_names : 
    #     ags_cnt += 1
    #     if ags["Tag"] == name : break
    
    # print(ags_cnt)
    # print(ags_names[ags_cnt]["Name"])
   
    
    ag_name = (item for item in asg_names if item['Cnt'] == name)
    update_ag = next(ag_name, False)
    
    if name == 'all' :
        
        count = 0
        message = ""
        
        message = message + "- Current autuscaling gruops : " + str(asg_names) +"\n\n"+ "- Total ausotscaling groups count : "+ str(len(asg_names)) + "\n\n\n"
        
        for asg in asg_names :
            
            count = count + 1
            
            response = client.update_auto_scaling_group(
            AutoScalingGroupName=asg,
            MinSize=int(min_capacity),
            MaxSize=int(max_capacity),
            DesiredCapacity=int(desire_capacity)
            )
            
            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                message = message + "["+str(count)+"/"+str(len(asg_names))+"] Success "+ asg + " Update Autoscaling Group \n-> " + "Min:" + str(min_capacity) + ", Max:" + str(max_capacity) + ", Desire: "+ str(desire_capacity)+"\n\n"
            else:
                message = message + "[" +str(count)+"/"+str(len(asg_names))+"] Failed "+ asg + " Update Autoscaling Group\n"
                
        print(message)
        
        return message
    
    else:
        response = client.update_auto_scaling_group(
            AutoScalingGroupName=update_ag["Name"],
            MinSize=int(min_capacity),
            MaxSize=int(max_capacity),
            DesiredCapacity=int(desire_capacity)
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return "Success Update "+ "[" + update_ag["Cnt"] + "]" + update_ag["Name"] + "("+ update_ag["Tag"] +")" + "  \n-> " + "Min:" + str(min_capacity) + ", Max:" + str(max_capacity) + ", Desire:"+ str(desire_capacity)
        else:
            return "Failed Update "+ "[" + update_ag["Cnt"] + "]" +update_ag["Name"] + "(" + update_ag["Tag"] + ")" 
    
def help():
    message = "*** AG Commnand 사용법 ***\n"\
    "명령어 문법은 다음과 같습니다 -> '/ag command params'\n"\
    "ex1) '/ag describe' -> Auto Scailing Group을 나열합니다.\n"\
    "ex2) '/ag update 4 1 2 3' -> 4번째 Auto Scailing Group의 용량을 목표1 최소2 최대3 으로 수정\n"\
    "describe : 모든 Auto Scailing Group과 포함된 EC2 List를 가져옵니다.\n"\
    "update name desire_capacity min_capacity max_capacity : 오토스케일링 그룹을 업데이트 합니다."
    #print(message)
    return message

def do_act(token, act):

    client = get_client('autoscaling', token)
    
    function = act[0]
    
    
    if function == "describe":
        return describe(client, token)
    elif function == "update":
        return update(client, act[1], act[2], act[3], act[4], token)
    elif function == "help":
        return help()
    else:
        return "Please Check the function"

def lambda_handler(event, context):
    act = event['text'].split(' ')
   
    result = do_act(event['token'], act)
   
    slack_send(event['response_url'], result)
