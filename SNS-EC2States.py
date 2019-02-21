# -*- coding: utf-8 -*-

#-------------------------------------------------
#  File Name:     SNS-EC2States
#  Description :  We can get start_time item from select_item.py.  
#                 Fill out the Statistics table and notify administrator via mail
#  Usage :        AWS use DynamoDB stream feature to trig this lambda
#  Author :       mobity
#  date:          2/10/2019
#------------------------------------------------

import json
import boto3
import os,time
import decimal
import select_item

sns= boto3.client('sns')
dynamodb_client = boto3.client('dynamodb')
dynamodb_resource = boto3.resource('dynamodb')
    

def send_mail(event):
    #print "Got Event" + json.dumps(event)
    snsArn=os.environ['sns_arn']
    for record in event['Records']:
        if record['eventName'] != 'INSERT':
            continue
        Owner = record['dynamodb']['NewImage']['Name']['S']
        Time = record['dynamodb']['NewImage']['Time']['S']
        State = record['dynamodb']['NewImage']['States']['S']
        EC2_Name= record['dynamodb']['NewImage']['VM-Name']['S']
        messages = Owner+' is '+State+' '+EC2_Name+' at '+Time
        print messages
        response = sns.publish(
            TargetArn=snsArn,
            Message=json.dumps({
                'default' : json.dumps(messages)
                }),
            MessageStructure='json'
            )

 


def Statistics_item(event):
    table = dynamodb_resource.Table('Statistics')
    time.sleep(10)
    for record in event['Records']:
        EC2_Name= record['dynamodb']['NewImage']['VM-Name']['S']
        print EC2_Name
        start_time=str(get_start_time(EC2_Name))
        Owner = record['dynamodb']['NewImage']['Name']['S']
        EndTime = record['dynamodb']['NewImage']['Time']['S']
        SR_Id =  record['dynamodb']['NewImage']['SR-Number']['S']
        Comment = record['dynamodb']['NewImage']['Comment']['S']
        print Comment
        table.put_item(
            Item={
                'StartTime':start_time,
                'Time': EndTime,
                'Name': Owner,
                'VM-Name': EC2_Name,
                'SR-Number': SR_Id,
                'Comment': Comment
            }
        )

def get_start_time(EC2_Name):
    table = dynamodb_resource.Table('Citrix')
    items=select_item.get_items(table)
    item_running=select_item.get_item(items,keyword=EC2_Name)
    item_last=select_item.sorted_items(item_running)
    return item_last['Time']
    

def lambda_handler(event, context):
    print event
    for record in event['Records']:
        State=record['dynamodb']['NewImage']['States']['S']
        if State !='running':
            Statistics_item(event)
            send_mail(event)
