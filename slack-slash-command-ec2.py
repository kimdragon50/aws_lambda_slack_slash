import json
import boto3
import slackweb

def slack_send(url, message):
    slack = slackweb.Slack(url=url)
    # slack.notify(response_type="in_channel", text=message)
    slack.notify(text=message)

def get_client(token):
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=token, WithDecryption=True)
    key = response['Parameter']['Value']
    key = key.split(',')
    return boto3.client(
        'ec2',
        aws_access_key_id=key[0],
        aws_secret_access_key=key[1]
    )

def status(client, tag_key, value):
    info = ""
    ec2_list = client.describe_instances()
    for ec2 in ec2_list['Reservations']:
        name = ""
        resource_env = ""
        ec2_info = ec2['Instances'][0]
        try:
            for tag in ec2_info['Tags']:
                if tag['Key'] == "Name":
                    name = tag['Value']
                elif tag['Key'] == 'Env':
                    resource_env = tag['Value']
            if tag_key == "all":
                info += name + "\t" + ec2_info['InstanceId'] + "\t" + ec2_info['State']['Name'] + "\t" + ec2_info['PrivateIpAddress'] + "\t" + ec2_info['InstanceType'] + "\t" + resource_env +"\n"
            else:
                for tag in ec2_info['Tags']:
                    if tag_key.lower() == tag['Key'].lower():
                        if value.lower() in tag['Value'].lower():
                            info += name + "\t" + ec2_info['InstanceId'] + "\t" + ec2_info['State']['Name'] +"\t" + ec2_info['PrivateIpAddress'] + "\t" + ec2_info['InstanceType'] + "\t" + resource_env +"\n"
        except :
            continue
    print(info)
    return info

def stop(client, tag_key, value):
    response = client.describe_instances()
    ec2_list = []
    for ec2 in response['Reservations']:
        for instance in ec2['Instances']:
            if tag_key == "all":
                ec2_list.append(instance['InstanceId'])
            else:
                try:
                    for tags in instance['Tags']:
                        if tags['Key'].upper() == tag_key.upper():
                            if value.upper() in tags['Value'].upper():
                                print(tags['Value'] + ':' + instance['InstanceId'])
                                ec2_list.append(instance['InstanceId'])
                except :
                    continue
    stop_response = client.stop_instances(InstanceIds=ec2_list)
    stop_instances = stop_response['StoppingInstances']
    result = ""
    for stop_instance in stop_instances:
        result += "Success stop :" + "\t" + stop_instance['InstanceId'] + "\t" + stop_instance['CurrentState']['Name'] + "\n"
    return result

def start(client, tag_key, value):
    response = client.describe_instances()
    ec2_list = []
    for ec2 in response['Reservations']:
        for instance in ec2['Instances']:
            if tag_key == "all":
                ec2_list.append(instance['InstanceId'])
            else:
                try:
                    for tags in instance['Tags']:
                        if tags['Key'].upper() == tag_key.upper():
                            if value.upper() in tags['Value'].upper():
                                print(tags['Value'] + ':' + instance['InstanceId'])
                                ec2_list.append(instance['InstanceId'])
                except:
                    continue
                
    start_response = client.start_instances(InstanceIds=ec2_list)
    start_instances = start_response['StartingInstances']
    result = ""
    for start_instance in start_instances:
        result += "Success start :" + "\t" + start_instance['InstanceId'] + "\t" + start_instance['CurrentState']['Name'] + "\n"
    return result
    
def help():
    message = "***EC2 Commnand 사용법***\n"\
    "명령어 문법은 다음과 같습니다 -> '/ec2 command tag-key tag-value'\n"\
    "ex1) '/ec2 status env dev' -> Env 태그 값에 dev가 포함된 EC2 List를 가져옵니다.\n"\
    "ex2) '/ec2 start name test' -> Name 태그 값에 test가 포함된 EC2 서버들을 구동시킵니다.\n"\
    "ex3) '/ec2 status(or start) all -> 모든 EC2 List를 가져옵니다. (or 구동시킵니다.)\n"\
    "status tag[key] tag[value] : 해당 tag의 값에 value값이 포함된 EC2 List를 가져옵니다.\n"\
    "start tag[key] tag[value] : 해당 tag의 값에 value값이 포함된 EC2 서버들을 구동시킵니다.\n"\
    "stop tag[key] tag[value] : 해당 tag의 값에 value값이 포함된 EC2 서버들을 정지시킵니다."
    print(message)
    return message

def do_act(token, act):
    client = get_client(token)
    
    # function = act[0]
    
    if len(act) >= 2:
        tag_key = act[1]
        
        if tag_key == "all":
            value = "all"
        elif tag_key == "help":
            value = ""
        else:
            value = act[2]
    
    if act[0] == "status":
        return status(client, act[1], value)
    elif act[0] == "start":
        return start(client, act[1], value)
    elif act[0] == "stop":
        return stop(client, act[1], value)
    elif act[0] == "help":
        return help()
    else:
        return "Please Check the function"

def lambda_handler(event, context):
    
    act = event['text'].split(' ')
    
    result = do_act(event['token'], act)
    slack_send(event['response_url'], result)
