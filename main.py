from crypt import methods
import datetime
from email import message
from operator import contains
from flask import Flask, render_template, request, redirect, url_for, session
import json
import requests


import os
from botocore.exceptions import ClientError


app = Flask(__name__)
app.secret_key = "cloud_computing##application"

import boto3
from boto3.dynamodb.conditions import Key, Attr

BASE_URL = "https://1bdi2n4wsa.execute-api.us-east-1.amazonaws.com/prod"


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # API Request
        data = {"username": username, "password": password}
        response = requests.post(BASE_URL + "/login", json=data)

        if response.status_code == 200:
            # if success - Parsing response
            response_data = response.json()
            name = response_data["username"]

            session["username"] = name
            return redirect(url_for("home"))

        if response.status_code == 401:
            # User not found or any other error
            response_data = response.json()
            msg = response_data["msg"]
            return render_template("login.html", error=msg)

    return render_template("login.html")


def get_subscribed_user(dynamodb, name):
    subscribeduser_table = dynamodb.Table("subscription")

    subscribed_user = subscribeduser_table.get_item(Key={"username": name})
    return subscribed_user


def process_submit_button(request):
    data = []
    headings = ("Title", "Year", "Artist", "Images", "Action")
    title = request.form["title"]
    year = request.form["year"]
    artist = request.form["artist"]

    if not title and not year and not artist:
        # headings = "Please fill the query"
        data = []
        headings = "Please enter the query to give results"
        return headings, data

    # API Request
    req_data = {"title": title, "year": year, "artist": artist}
    response = requests.get(BASE_URL + "/music", json=req_data)

    print(response.json)

    if response.status_code == 200:
        # if success - Parsing response
        response_data = response.json()
        return headings, response_data

    else:
        return "No Data Available", data

    return headings, data


def process_subscribe_button(request, name):
    title = request.form["subscribe_button"]

    # API Request
    data = {"title": title, "username": name}
    response = requests.post(BASE_URL + "/subscribe", json=data)
    print(response)


def display_subscribed_music_info(name):
    response_data = []

    # API Request
    data = {"username": name}
    print(data)
    response = requests.get(BASE_URL + "/subscribe", json=data)
    print(response)
    if response.status_code == 200:
        # if success - Parsing response
        response_data = response.json()

    return response_data


@app.route("/home", methods=["GET", "POST"])
def home():
    headings = ""
    data = []
    music_data = []

    if "username" in session:
        name = session["username"]
    else:
        return redirect(url_for("login"))

    
    if request.method == "POST":
        
        # submit button is a key request.form = dictionary
        if "submit_button" in request.form:
            headings, data = process_submit_button(request=request)

        # elif request.form['submit_button'] == 'subscribe':
        elif "subscribe_button" in request.form:
            process_subscribe_button(request=request, name=name)

        elif "remove_button" in request.form:
            title = request.form["remove_button"]
            # API Request
            data = {"username": name, "title": title}
            print(data)
            response = requests.post(BASE_URL + "/remove-subscribe", json=data)

        elif "logout_button" in request.form:
            if "username" in session:
                session.pop("username", None)
            return redirect(url_for("login"))

    music_data = display_subscribed_music_info(name=name)
    fixed_headings = ("Title", "Year", "Artist", "Images", "Action")

    return render_template(
        "home.html", music_data = music_data, name = name, fixed_headings=fixed_headings, headings=headings, data=data
    )


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        data = {'email': email, 'username': username, 'password': password}
        response = requests.post(BASE_URL + "/register", json=data)
        

        if response.status_code == 200:
            # if success - Parsing response
            response_data = response.json()
            msg = response_data["msg"]
            return render_template("register.html", error=msg)

        if response.status_code == 401:
            # User not found or any other error
            response_data = response.json()
            msg = response_data["msg"]
            return render_template("register.html", error=msg)

    return render_template("register.html")



        
        
    



@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "POST":
        if "login_button" in request.form:
            return render_template("login.html")
        if "register_button" in request.form:
            return render_template("register.html")

    return render_template("index.html")


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run()
    
    # app.run(host="127.0.0.1", port=8080, debug=True)

# [END gae_python3_render_template]
# [END gae_python38_render_template]
