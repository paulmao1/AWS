# -*- coding: utf-8 -*-

#-------------------------------------------------
#  File Name:     select_item
#  Description :  Use python list to sort DynamoDB items.  
#  Usage :        It's invoked by SNS-EC2States
#  Author :       mobity
#  date:          2/10/2019
#------------------------------------------------
import json
import boto3
import operator

dynamodb=boto3.resource('dynamodb')


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError ("Type not serializable")
    
def get_items(table):
    records=table.scan()
    for key in records:
        if key == 'Items':
            record=records[key]
            record_dump = json.dumps(record,default=json_serial)
            return json.loads(record_dump)

def get_item(items,keyword):
    running=[]
    stopping=[]
    for item in items:
        if 'running' in item.values():
            running.append(item)
        if 'stopping' in item.values():
            stopping.append(item)
    for i in running:
        if keyword not in i['VM-Name']:
            running.remove(i) 
        else:
            continue
    return running

def sorted_items(item_running):
    sorted_item=sorted(item_running,key=operator.itemgetter('Time'))
    item_last=sorted_item[-1]
    return item_last


def lambda_handler(event, context):
    table=dynamodb.Table('Citrix')
    items=get_items(table)
    item_running=get_item(items)
    print item_running
    item_last=sorted_items(item_running)
    print item_last
