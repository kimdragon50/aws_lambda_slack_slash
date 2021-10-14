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
        'rds',
        aws_access_key_id=key[0],
        aws_secret_access_key=key[1]
    )

def status(client, tag_key):
    info = ""

    rds_list = client.describe_db_instances()
    print('/rds status [option]: RDS LIST 출력')
    
    for resp in rds_list['DBInstances']:
        db_instance_arn = resp['DBInstanceArn'] #amazon resource name
        db_engine = resp['Engine'] #start, stop시 db타입알기위함.
        db_status_info = resp['DBInstanceStatus']
        db_instance_name = resp['DBInstanceIdentifier'] #dbName
        db_instance_class = resp['DBInstanceClass'] 
        resource_env = ""

        try : 
            for tag_list in resp['TagList'] :

                db_tag_key = tag_list['Key']
                db_tag_value = tag_list['Value']

                if db_tag_key == 'Env':
                        resource_env = db_tag_value

            if tag_key == 'all' :
                info += db_instance_name + "\t" + db_status_info + "\t" + db_instance_class + "\t" + db_engine + "\t" + resource_env +"\n" 
            
            elif tag_key == db_instance_name :
                info += db_instance_name + "\t" + db_status_info + "\t" + db_instance_class + "\t" + db_engine + "\t" + resource_env +"\n"  
            else:
                print("Please check your option")
        
        except :
            continue

    print(info)
    return info

    
def stop(client, tag_key):

    response = client.describe_db_instances()

    result = ""

    print('/rds stop [Name_tag]: RDS stop 출력')

    for rds in response['DBInstances']:
        try : 
            db_instance_name = rds['DBInstanceIdentifier'] #dbName
            db_engine = rds['Engine'] #start, stop시 db타입알기위함.
            db_status_info = rds['DBInstanceStatus']

            if db_status_info == 'available' :
                if tag_key == "all" and db_engine == "aurora":
                    client.stop_db_cluster(DBClusterIdentifier= db_instance_name)
                    result += "Stopping DB instances : "+ db_instance_name +"\n"

                elif tag_key == "all" and db_engine != "aurora":
                    client.stop_db_instance(DBInstanceIdentifier= db_instance_name)
                    result += "Stopping DB instances : "+ db_instance_name +"\n"

                elif tag_key == db_instance_name and db_engine == "aurora":
                    client.stop_db_cluster(DBClusterIdentifier= db_instance_name)
                    result += "Stopping DB instances : "+ db_instance_name +"\n"

                elif tag_key == db_instance_name and db_engine != "aurora":
                    client.stop_db_instance(DBInstanceIdentifier= db_instance_name)
                    result += "Stopping DB instances : "+ db_instance_name +"\n"
            
            
        except :
            return "Failed Stop DB instances"

    return result

def start(client, tag_key):

    response = client.describe_db_instances()

    result = ""

    print('/rds start [Name_tag]: RDS LIST 출력')

    for rds in response['DBInstances']:
        try : 
            db_instance_name = rds['DBInstanceIdentifier'] #dbName
            db_engine = rds['Engine'] #start, stop시 db타입알기위함.
            db_status_info = rds['DBInstanceStatus']

            if db_status_info == 'stopped' :
                if tag_key == "all" and db_engine == "aurora":
                    client.start_db_cluster(DBClusterIdentifier= db_instance_name)
                    result += "Starting DB instances : "+ db_instance_name +"\n"

                elif tag_key == "all" and db_engine != "aurora":
                    client.start_db_instance(DBInstanceIdentifier= db_instance_name)
                    result += "Starting DB instances : "+ db_instance_name +"\n"

                elif tag_key == db_instance_name and db_engine == "aurora":
                    client.start_db_cluster(DBClusterIdentifier= db_instance_name)
                    result += "Starting DB instances : "+ db_instance_name +"\n"

                elif tag_key == db_instance_name and db_engine != "aurora":
                    client.start_db_instance(DBInstanceIdentifier= db_instance_name)
                    result += "Starting DB instances : "+ db_instance_name +"\n"

            
        except :
            return "Failed start DB instances"

    return result


def help():
    
    message = "***RDS Commnand 사용법***\n"\
    "명령어 문법은 다음과 같습니다 -> '/rds command tag-key tag-value'\n"\
    "ex1) '/rds status all' -> 모든 RDS List를 가져옵니다.\n"\
    "ex2) '/rds start test' -> RDS Name에 test가 포함된 RDS 서버를 구동시킵니다.\n"\
    "ex3) '/rds stop test -> RDS Name에 test가 포함된 RDS 서버를 정지 시킵니다.\n"\
    "status name : 해당 name이 포함된 RDS List를 가져옵니다.\n"\
    "start name : 해당 name이 포함된 RDS 서버들을 구동시킵니다.\n"\
    "stop name : 해당 name이 포함된 RDS 서버들을 정지시킵니다."
    
    print(message)
    return message

def do_act(token, act):
    client = get_client(token)

    print (act)
    
    if act[0] == "status":
        return status(client, act[1])
    elif act[0] == "start":
        return start(client, act[1])
    elif act[0] == "stop":
        return stop(client, act[1])
    elif act[0] == "help":
        return help()
    else:
        return "Please Check the function"

def lambda_handler(event, context):
    act = event['text'].split(' ')
    
    print(act)
    
    result = do_act(event['token'], act)
    
    slack_send(event['response_url'], result)

