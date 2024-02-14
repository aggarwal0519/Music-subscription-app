from decimal import Decimal
import json
import boto3
import os
import requests 
from botocore.exceptions import ClientError

s3 = boto3.client('s3')

with open("a1.json") as json_file:
   
    music_list = json.load(json_file, parse_float=Decimal)


# Define the bucket name and the URL of the files to download
bucket_name = 'imgartist'
for music in music_list['songs']:
    img_url = music['img_url']

# Loop through the list of URLs and download the files
# for url in img_url:
    # Get the file name from the URL
    file_name = os.path.basename(img_url)
    # Download the file from the URL
    response = requests.get(img_url)
    # Upload the file to S3
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=response.content)
