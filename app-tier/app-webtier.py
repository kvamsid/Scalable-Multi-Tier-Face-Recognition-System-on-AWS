from flask import Flask, request
import pandas as pd
import boto3
import time
import threading
from threading import Thread, Event

lookup = {}
numberOfRequests = 0
numberOfResponses = 0
statusCheck = True
scalingThreadFlag = True
processingResponseFlag = True
# stop_auto_scale_event = Event()
# stop_response_event = Event()

region_name = 'us-east-1'

# Create SQS client
sqs = boto3.client('sqs', region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)

request_queue_name = "1229700097-req-queue";
response_queue_name = "1229700097-resp-queue";
req_queue_url = sqs.get_queue_url(QueueName=request_queue_name)['QueueUrl']
resp_queue_url = sqs.get_queue_url(QueueName=response_queue_name)['QueueUrl']
app = Flask(__name__)

# Sending a message to SQS queues
def sendMessage(message):
    response = sqs.send_message(
        QueueUrl=req_queue_url,
        MessageBody=message
    )
# Launching EC2 instances
ec2 = boto3.client('ec2', region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)

ami_id = "ami-087a678af4a09bd1d"
script_to_run = """#!/bin/bash
cd /home/ec2-user/faceRecognition/
source myenv/bin/activate
cd CSE546-Cloud-Computing/
python app.py
"""
def launchInstance(instanceName):
    ec2.run_instances(
                    ImageId=ami_id,
                    MinCount=1,
                    MaxCount=1,
                    InstanceType="t2.micro",
                    UserData = script_to_run,
                    KeyName='my_key_pair',
                    TagSpecifications=[{'ResourceType': 'instance',
                                        'Tags': [{'Key': 'Name', 'Value': instanceName},
                                                 {'Key': 'image_classification', 'Value': 'app-tier'}]}]
                )
maxLimit = 20

# API post method
@app.route("/", methods=["POST"])
def imageClassification():
    global numberOfRequests
    global statusCheck
    file = request.files['inputFile']
    fileName = file.filename.split('.')[0]
    numberOfRequests +=1
    statusCheck = True
    if len(file.filename) == 11:
        sendMessage("face_images_100/"+file.filename)           # for 100 images
    else:
        sendMessage("face_images_1000/"+file.filename)          # for 1000 images
    startAutoScaling()
    startResponseProcessing()
    while(fileName not in lookup):
        time.sleep(1)

    return f"{fileName}:{lookup[fileName]}"

def fetchQueueLength():
    response = sqs.get_queue_attributes(
        QueueUrl=req_queue_url,
        AttributeNames=['ApproximateNumberOfMessages']
    )
    return int(response['Attributes']['ApproximateNumberOfMessages'])

def fetchInstancesCount():
    response = ec2.describe_instances(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'pending']},
                 {'Name': 'tag:image_classification', 'Values': ['app-tier']}]
    )
    instances = [instance for reservation in response['Reservations'] for instance in reservation['Instances']]
    return len(instances)

def scaleInstances(requiredCount):
    global numberOfResponses
    global numberOfRequests
    global lookup
    global scalingThreadFlag
    global processingResponseFlag
    global statusCheck
    currentCount = fetchInstancesCount()
    defaultInstanceName = "app-tier-instance"
    if currentCount < requiredCount:
        # Scaling out the instances
        if(statusCheck):
            numberToLaunch = requiredCount - currentCount
            if numberToLaunch > 0:
                for _ in range(numberToLaunch):
                    instanceName = f"{defaultInstanceName}-{currentCount + 1}"
                    launchInstance(instanceName)
                    currentCount += 1
    elif currentCount > requiredCount:
        if(numberOfResponses == numberOfRequests):
            # Scaling in the instances
            instances = ec2.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'pending']},
                         {'Name': 'tag:image_classification', 'Values': ['app-tier']}],
                MaxResults=1000
            )
            appTierInstances = sorted(
                [(instance['InstanceId'], instance['Tags']) for reservation in instances['Reservations'] for instance in reservation['Instances']],
                key=lambda x: [tag['Value'] for tag in x[1] if tag['Key'] == 'Name'][0]
            )
            instancesToTerminate = [instance_id for instance_id, _ in appTierInstances[-(currentCount - requiredCount):]]
            if instancesToTerminate:
                ec2.terminate_instances(InstanceIds=instancesToTerminate)
            lookup.clear()
            time.sleep(10)
            statusCheck = False
            scalingThreadFlag = False
            processingResponseFlag = False

def auto_scale():
    global scalingThreadFlag
    while scalingThreadFlag:
        queueLength = fetchQueueLength()
        desiredInstances = min(maxLimit, queueLength)
        scaleInstances(desiredInstances)
        time.sleep(3)

def startAutoScaling():
    global scalingThreadFlag
    for thread in threading.enumerate():
        if thread.name == "auto_scale" and thread.is_alive():
            return
    auto_scale_thread = Thread(target=auto_scale, name = "auto_scale")
    scalingThreadFlag = True
    auto_scale_thread.start()

def process_responses():
    global processingResponseFlag
    global numberOfResponses
    while processingResponseFlag:
        response = sqs.receive_message(
            QueueUrl=resp_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=1,
        )
        messages = response.get('Messages', [])
        for message in messages:
            resultFromAppTier = message['Body']
            numberOfResponses += 1
            imageFileName = resultFromAppTier.split('/')[0]
            imageResult = resultFromAppTier.split('/')[1]
            lookup[imageFileName] = imageResult
            sqs.delete_message(
                QueueUrl=resp_queue_url,
                 ReceiptHandle=message['ReceiptHandle']
            )
        time.sleep(1)

def startResponseProcessing():
    global processingResponseFlag
    for thread in threading.enumerate():
        if thread.name == "response_process_thread" and thread.is_alive():
            return
    response_thread = Thread(target=process_responses, name = "response_process_thread")
    processingResponseFlag = True
    response_thread.start()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, threaded=True)