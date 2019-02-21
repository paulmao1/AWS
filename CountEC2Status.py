# -*- coding: utf-8 -*-

#-------------------------------------------------
#  File Name:     CountEC2Status
#  Description :  Get all the EC2 stats changed records.
#  Usage :    AWS use CloudWatch Event built-in EC2 stats change to trig this lambda
#  Author :       mobity
#  date:          2/09/2019
#------------------------------------------------
import json
import boto3
import time,random
from datetime import datetime


print('Loading function ' + datetime.now().time().isoformat())
ec2 = boto3.resource('ec2')
compute = boto3.client('ec2')
dynamodb_client = boto3.client('dynamodb')
dynamodb_resource = boto3.resource('dynamodb')
	
	
def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")

def remove_empty_from_dict(d):
    """Removes empty keys from dictionary"""
    if type(d) is dict:
        return dict((k, remove_empty_from_dict(v)) for k, v in d.iteritems() if v and remove_empty_from_dict(v))
    elif type(d) is list:
        return [remove_empty_from_dict(v) for v in d if v and remove_empty_from_dict(v)]
    else:
        return d
		
def create_main_table(table_name):
    """Create Citrix table"""
    dynamodb_client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {
                    'AttributeName': 'Time',
                    'AttributeType': 'S'
                },
            ],
            KeySchema=[
                {
                    'AttributeName': 'Time',
                    'KeyType': 'HASH'
                },
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 4,
                'WriteCapacityUnits': 4
            }
        )
    table = dynamodb_resource.Table(table_name)
    table.wait_until_exists()

def create_table(table_name):
    """Create Statistics table"""
    dynamodb_client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {
                    'AttributeName': 'VM-Name',
                    'AttributeType': 'S'
                },
                {
                    'AttributeName' : 'Time',
                    'AttributeType': 'S'
                    
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'VM-Name',
                    'KeyType': 'HASH'
                },
                {
                    'AttributeName': 'Time',
                    'KeyType': 'RANGE'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 4,
                'WriteCapacityUnits': 4
            }
        )
    table = dynamodb_resource.Table(table_name)
    table.wait_until_exists()

def Citrix_item(event):
    # Get the state from the Event stream
    state = event['detail']['state']
	# Get the start time from the Event stream
    start_time=event['time']
	# Get the instance id, region, and tag collection
    instance_id = event['detail']['instance-id']
    region = event['region']
    table = dynamodb_resource.Table('Citrix')
    if state == 'running' or state == 'stopping' or state == 'terminated':
        #time.sleep(10)
        instance = compute.describe_instances(InstanceIds=[instance_id])
        # Remove response metadata from the response
        instance.pop('ResponseMetadata')
        # Remove null values from the response.  You cannot save a dict/JSON document in DynamoDB if it contains null values
        instance = remove_empty_from_dict(instance)
        instance_dump = json.dumps(instance,default=json_serial)
        instance_attributes = json.loads(instance_dump)
        tags = instance_attributes['Reservations'][0]['Instances'][0]['Tags']
        for tag in tags:
            if 'OWNER' in tag.get('Key',{}).lstrip().upper():
			    EC2_Owner=tag.get('Value').lstrip()
            if 'NAME' in tag.get('Key',{}).lstrip().upper():
			    EC2_Name=tag.get('Value').lstrip()
            if 'SR' in tag.get('Key',{}).lstrip().upper():
			    SR_Id=tag.get('Value').lstrip()
            if 'COMMENT' in tag.get('Key',{}).lstrip().upper():
			    Comment=tag.get('Value').lstrip()
        table.put_item(
            Item={
                'Time': start_time,
				'Name': EC2_Owner,
                'Account': 'PaulMao',
				'VM-Name': EC2_Name,
                'SR-Number': SR_Id,
                'States' : state,
                'Comment': Comment
            }
        )
'''
	# Get instance attributes
	# Get IP Address and hostname 
    private_ip = instance['Reservations'][0]['Instances'][0]['PrivateIpAddress']
    private_dns_name = instance['Reservations'][0]['Instances'][0]['PrivateDnsName']
    private_host_name = private_dns_name.split('.')[0]
    try:
        public_ip = instance['Reservations'][0]['Instances'][0]['PublicIpAddress']
        public_dns_name = instance['Reservations'][0]['Instances'][0]['PublicDnsName']
        public_host_name = public_dns_name.split('.')[0]
    except BaseException as e:
        print 'Instance has no public IP or host name', e
	# Get VPC id
	vpc_id = instance['Reservations'][0]['Instances'][0]['VpcId']
    vpc = ec2.Vpc(vpc_id)
	# Get EC2 Name
	Tags = instance['Reservations'][0]['Instances'][0]["Tags"]
	for tag in Tags:
	    if "Name" in tag:
		    vm_name=tag.values()
		if "SR" in tag:
		    sr_id=tag.values()
'''
    

def lambda_handler(event, context):
    tables = dynamodb_client.list_tables()
    if 'Citrix' in tables['TableNames']:
        print 'DynamoDB table already exists'
    else:
        create_main_table('Citrix')
    if 'Statistics' in tables['TableNames']:
        print 'DynamoDB table already exists'
    else:
        create_table('Statistics')
    #time.sleep(random.random())
    Citrix_item(event)




