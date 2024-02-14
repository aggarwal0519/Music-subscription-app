from decimal import Decimal
import json
import boto3

dynamodb = boto3.resource("dynamodb")


def load_music(songs):
    table = dynamodb.Table("music")

    # batch_writer makes the program faster by writing it in bulk
    with table.batch_writer() as writer:
        for song in songs:
            # title = song['title']
            # artist = song['artist']
            # year = song['year']
            # web_url = song['web_url']
            # img_url = song ['img_url']
            # print("Adding movie:", title, artist,year,web_url,img_url)
            writer.put_item(Item=song)


if __name__ == "__main__":
    with open("a1.json") as json_file:
        music_list = json.load(json_file, parse_float=Decimal)

    # music_list acts as a dictionary in json file hence getting the value for songs

    load_music(music_list["songs"])
