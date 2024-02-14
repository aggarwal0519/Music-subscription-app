import json
import boto3
from botocore.exceptions import ClientError
import os


def get_user(username, dynamodb):
    # login system
    table = dynamodb.Table("login")

    try:
        response = table.get_item(Key={"username": username})
    except ClientError as e:
        print(e.response["Error"]["Message"])
    else:
        if "Item" in response:
            return response["Item"]


def get_music(title, dynamodb):
    # music table
    table = dynamodb.Table("music")

    try:
        response = table.scan(FilterExpression="contains(title, :title)", ExpressionAttributeValues={":title": title})
    except ClientError as e:
        print(e.response["Error"]["Message"])
    else:
        return response["Items"][0]


def get_subscribed_user(username, dynamodb):
    # subscription system
    table = dynamodb.Table("subscription")

    try:
        response = table.get_item(Key={"username": username})
    except ClientError as e:
        print(e.response["Error"]["Message"])
    else:
        if "Item" in response:
            return response["Item"]

def process_register(body):
    email = body['email']
    username = body["username"]
    password = body["password"]

    dynamodb = boto3.resource("dynamodb")

    msg = " "

    table = dynamodb.Table("login")

    user = table.get_item(Key={"username": username})
    if "Item" in user:
        # User not found in the table
        msg = "Username or email already exists!"
        return {
            "statusCode": 401,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({"msg": "Username or email already exists!"}),
        }

    register = table.put_item(Item={"username": username, "email": email, "password": password})
    if register:
        return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                },
                "body": json.dumps({'msg': "Registration Complete. Please login to your account!"}),
        }


def process_login(body):
    username = body["username"]
    password = body["password"]

    msg = ""

    dynamodb = boto3.resource("dynamodb")
    user = get_user(username, dynamodb)

    if user:
        if password == user["password"] and username == user["username"]:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                },
                "body": json.dumps({"username": user["username"]}),
            }

        else:
            # Password is incorrect
            msg = "Username or password is invalid!"

    else:
        # User not found in the table
        msg = "Username or password is invalid!"

    # Check if the password matches

    return {
        "statusCode": 401,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps({"msg": "Username or password is invalid!"}),
    }


def process_subscribe(body):
    username = body["username"]
    title = body["title"]
    msg = ""
    statusCode = 401

    dynamodb = boto3.resource("dynamodb")

    print("test 1")

    # Get subscribed user data
    subscribed_user = get_subscribed_user(username=username, dynamodb=dynamodb)

    print("test 2")

    # subscribed user table
    subscribed_user_table = dynamodb.Table("subscription")

    print(subscribed_user)
    if not subscribed_user:
        print("test 3")
        subscribed_user_table.put_item(Item={"username": username, "subscribed_list": [title]})

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({"msg": "ok"}),
        }
    else:
        try:
            # Check if item exists in list before adding it
            subscribed_user_table.update_item(
                Key={"username": username},
                UpdateExpression="SET subscribed_list = list_append(if_not_exists(subscribed_list, :empty_list), :subscribed)",
                ExpressionAttributeValues={":subscribed": [title], ":empty_list": [], ":data": title},
                ConditionExpression="NOT contains(subscribed_list, :data)",
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                print("Already subscribed. Please select another song to subscribe!")
                statusCode = 409
                msg = "Already subscribed. Please select another song to subscribe!"
            else:
                print(e.response["Error"])
                statusCode = 500
                msg = "Internal Server Error"
        else:
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "application/json",
                },
                "body": json.dumps({"msg": "ok"}),
            }

    return {
        "statusCode": statusCode,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps({"msg": msg}),
    }


def query_music(body):
    title = body["title"]
    year = body["year"]
    artist = body["artist"]

    msg = ""
    statusCode = 401

    # load table
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("music")

    # load s3
    s3 = boto3.client("s3")

    # TODO: error handling
    response = table.scan(
        FilterExpression="contains(title, :search) or contains(artist, :search) or contains(#y, :search)",
        ExpressionAttributeNames={"#y": "year"},
        ExpressionAttributeValues={":search": title or artist or year},
    )

    items = response["Items"]
    data = []

    for i in items:
        # Get the file name from the URL
        file_name = os.path.basename(i["img_url"])
        url = s3.generate_presigned_url("get_object", Params={"Bucket": "imgartist", "Key": file_name}, ExpiresIn=100)
        # print(i)
        data.append({"title": i["title"], "year": i["year"], "artist": i["artist"], "url": url})

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(data),
    }


def get_subscribed_music(body):
    username = body["username"]

    msg = ""
    statusCode = 401

    # load dynamodb
    dynamodb = boto3.resource("dynamodb")

    # load s3
    s3 = boto3.client("s3")

    print("test 1")

    # Get subscribed user data
    subscribed_user = get_subscribed_user(username=username, dynamodb=dynamodb)

    print("test 2")

    if subscribed_user:
        data = []

        for title in subscribed_user["subscribed_list"]:
            # get music from db for the title

            print(title)
            music = get_music(title=title, dynamodb=dynamodb)
            print(music)
            file_name = os.path.basename(music["img_url"])
            url = s3.generate_presigned_url(
                "get_object", Params={"Bucket": "imgartist", "Key": file_name}, ExpiresIn=100
            )

            data.append({"title": music["title"], "year": music["year"], "artist": music["artist"], "url": url})

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps(data),
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps([]),
    }


def remove_subscribed_music(body):
    username = body["username"]
    title = body["title"]

    msg = ""
    statusCode = 401

    # load dynamodb
    dynamodb = boto3.resource("dynamodb")

    # load s3
    s3 = boto3.client("s3")

    # Get subscribed user data
    subscribed_user = get_subscribed_user(username=username, dynamodb=dynamodb)

    if subscribed_user:
        subscribed_list = subscribed_user["subscribed_list"]
        if title in subscribed_list:
            subscribed_list.remove(title)

        subscribed_user_table = dynamodb.Table("subscription")
        subscribed_user_table.update_item(
            Key={"username": username},
            UpdateExpression="SET subscribed_list = :subscribed_list",
            ExpressionAttributeValues={":subscribed_list": subscribed_list},
        )

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({"msg": "ok"}),
        }

    return {
        "statusCode": 401,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": "unauthorized",
    }


def lambda_handler(event, context):
    # TODO implement

    body = json.loads(event["body"])
    print(event["path"])
    if event["httpMethod"] == "POST" and event["path"] == "/login":
        response = process_login(body)
        return response

    if event["httpMethod"] == "POST" and event["path"] == "/subscribe":
        response = process_subscribe(body)
        return response

    if event["httpMethod"] == "GET" and event["path"] == "/subscribe":
        response = get_subscribed_music(body)
        return response

    if event["httpMethod"] == "POST" and event["path"] == "/remove-subscribe":
        response = remove_subscribed_music(body)
        return response

    if event["httpMethod"] == "GET" and event["path"] == "/music":
        response = query_music(body)
        return response
