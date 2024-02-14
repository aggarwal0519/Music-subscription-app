

import boto3
dynamodb = boto3.resource('dynamodb')




def create_music_table():
  
        dynamodb = boto3.resource('dynamodb')

# Creating table and their attributes

        table = dynamodb.create_table(TableName  = 'music', KeySchema=[
        {
        'AttributeName': 'title',
        'KeyType': 'HASH' # Partition key
        },
        {
        'AttributeName': 'artist',
        'KeyType': 'RANGE' # Sort key
        },
        ],AttributeDefinitions=[

        {'AttributeName': 'title', 'AttributeType': 'S'},
        {'AttributeName': 'artist', 'AttributeType': 'S'},
        # {'AttributeName': 'year', 'AttributeType': 'N'},
        # {'AttributeName': 'web_url', 'AttributeType': 'S'},
        # {'AttributeName': 'image_url', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput = {
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }

        )
        if table.wait_until_exists():
            print("The table music already exists")
        else:
            # table.wait_until_exists()
            return table
 


if __name__ == '__main__':


    music = create_music_table()
    print("Table status:", music.table_status)
    

    


