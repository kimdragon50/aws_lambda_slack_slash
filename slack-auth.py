import json
import boto3

def check_token(token):
    
    ssm = boto3.client('ssm', region_name="ap-northeast-2")
    response = ssm.get_parameter(Name='slack-token', WithDecryption=True)
    
    key = response['Parameter']['Value']
    key = key.split(',')

    token_list = key
    if token in token_list:
        return True
    else:
        return False

def lambda_handler(event, context):
    print(event)
    token = event['token']
    client = boto3.client('lambda')
    if check_token(token):
        response = client.invoke_async(
            FunctionName='slack-slash-command-'+event['command'][1:].lower(),
            InvokeArgs=json.dumps(event)
        )
        return {
            # "response_type": "in_channel",
            "text": "Check the Slack Token...\nSuccess Authentication!\nIt takes few seconds to process..."
        }
    else:
        return {
            # "response_type": "in_channel",
            "text": "Check the Slack Token...\nFailed Authentication\nPlease Check the Slash Command App Setting"
        }
