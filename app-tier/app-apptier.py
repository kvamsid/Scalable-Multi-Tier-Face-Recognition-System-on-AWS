import boto3
import subprocess
# input is the only thing I have that too an image file name == test_000.jpg
# path is known = customPath

region_name = 'us-east-1'

# Create SQS client
sqs = boto3.client('sqs', region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)

request_queue_name = "1229700097-req-queue"
response_queue_name = "1229700097-resp-queue"
req_queue_url = sqs.get_queue_url(QueueName=request_queue_name)['QueueUrl']
resp_queue_url = sqs.get_queue_url(QueueName=response_queue_name)['QueueUrl']

# Send response to web tier
def sendMessage(message):
    response = sqs.send_message(
        QueueUrl=resp_queue_url,
        MessageBody=message
    )
    print("Message sent:", response)

# Create S3 client
s3 = boto3.client('s3', region_name=region_name,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)


defaultPath = "/home/ec2-user/faceRecognition/CSE546-Cloud-Computing/dataset/"

input_bucket_name = "1229700097-in-bucket"
output_bucket_name = "1229700097-out-bucket"
def store_data(fileName):
    inputImagePath = defaultPath+fileName
    inputFileName = inputImagePath.split('/')[-1]
    input_key = inputFileName
    s3.upload_file(inputImagePath, input_bucket_name, input_key)
    output_key = inputFileName.split('.')[0]
    result = subprocess.run(['python', '/home/ec2-user/faceRecognition/CSE546-Cloud-Computing/model/face_recognition.py', inputImagePath],
capture_output = True, text = True).stdout
    sendMessage(output_key+'/'+result)
    s3.put_object(Bucket = output_bucket_name,Key = output_key,Body = result)
    print("Files uploaded successfully")


def receive_messages():
    while True:
        response = sqs.receive_message(
            QueueUrl=req_queue_url,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20
        )
        if 'Messages' in response:
            message = response['Messages'][0]
            store_data(message['Body'])
            sqs.delete_message(QueueUrl=req_queue_url, ReceiptHandle=message['ReceiptHandle'])

receive_messages()