#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import platform
import subprocess
import base64
import requests
import re
import time
import flask
from flask import request, jsonify

if platform.system() == "Windows":
    from PIL import Image  # convert to ico
    from win10toast import ToastNotifier
    toaster = ToastNotifier()

version = "1.0.1"
port = 8000
OSs = ["Windows", "Linux", "MacOS"]
iconpath = {
    "Windows": "/temp/ForwardNotifierIcon",
    "Linux": "/tmp/ForwardNotifierIcon",
    "Darwin": "/tmp/ForwardNotifierIcon",  # macos
    "MacOS": "/tmp/ForwardNotifierIcon"
}


tries = 0
def checkforupadate():
    global tries
    try:
        url = "https://raw.githubusercontent.com/Greg0109/ForwardNotifier/master/ForwardNotifier%20Client%20Tools/Crossplatform%20Server/ForwardNotifierServer.py"
        r = requests.get(url).text
        m = re.search(r'version = .+', r)
        ver = m.group(0).split("=")[1].replace('"', "").replace(" ", "")
        if ver != version:
            sendnotif("Update availabe!",
                      "Run the install script again to update ForwardNotifier", platform.system())
    except requests.exceptions.ConnectionError:
        if tries < 5:
            sendnotif("Couldn't access github", "Trying again in 5 seconds.", platform.system())
            time.sleep(5)
            tries += 1
            checkforupadate()
        else:
            sendnotif("Couldn't access github", "Please check your internet connection or contact the developer.", platform.system())


# send os with the request since it's known by the sender
def sendnotif(Title, Message, OS, icon=None):
    # system = platform.system()
    try:
        try:  # Try to decode
            Title = base64.b64decode(Title.encode("utf-8")).decode("utf-8")
        except:
            print("Title is not base64")
        try:  # Try to decode
            Message = base64.b64decode(Message.encode("utf-8")).decode("utf-8")
        except:
            print("Message is not base64")
        if icon:
            print("Theres an icon!")
            icon = base64.decodebytes(icon.encode("utf-8"))
            open(iconpath[OS], "wb").write(icon)  # send img to correct path

        print("\nSending notification:")
        print("Title:", Title)
        print("Message:", Message)

        if OS == "Windows":
            if icon:
                # try:  # Try to decode
                filename = iconpath[OS]
                img = Image.open(filename)
                img.save(iconpath[OS] + '.ico', format='ICO')
                toaster.show_toast(Title,
                                   Message,
                                   icon_path=iconpath[OS] + ".ico",
                                   duration=5,
                                   threaded=True)
                # except:  # icon not base64 aka ignore
                #     toaster.show_toast(Title,
                #                        Message,
                #                        duration=5,
                #                        threaded=True)
            else:
                toaster.show_toast(Title,
                                   Message,
                                   duration=5,
                                   threaded=True)
        elif OS == "Linux":
            if icon:
                subprocess.call(
                    ["notify-send", "-i", iconpath[OS], Title, Message])
            else:
                subprocess.call(
                    ["notify-send", "-i", "applications-development", Title, Message])
        elif OS == "Darwin" or OS == "MacOS":  # macos
            if icon:
                subprocess.call(["/usr/local/bin/terminal-notifier",
                                 "-sound", "pop", "-appIcon", iconpath[OS], "-title", Title, "-message", Message])
            else:
                subprocess.call(["/usr/local/bin/terminal-notifier",
                                 "-sound", "pop", "-title", Title, "-message", Message])
    except:
        # sendnotif("Error", "unknown error while sending notification",
        #           platform.system())
        pass


def checkbody(body):  # checking the body for a post request, wont be a problem since we send it
    try:
        # try:
        #     body = json.loads(body)
        # except:
        #     return [False, "Unable to parse json"]

        if "Title" not in body:
            return [False, "No 'Title' in body"]
        
        if type(body["Title"]) != str:
            return [False, "'Title' isn't a string"]

        if "Message" not in body:
            return [False, "No 'Message' in body"]

        if type(body["Message"]) != str:
            return [False, "'Message' isn't a string"]

        if "OS" not in body:
            return [False, "No 'OS' in body"]
        
        if type(body["OS"]) != str:
            return [False, "'OS' isn't a string"]
        
        if body["OS"] not in OSs:
            return [False, "'OS' isn't a valid OS"]

        if "img" in body:
            try:
                base64.decodebytes(body["img"].encode("utf-8"))
                return [True, "img"]
            except:
                return [False, "Img not base64"]

        return [True]
    except:
        return [False, "unknown error"]


app = flask.Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': "ForwardNotifierServer, send a post w/ a 'Title', 'Message', 'OS' (Windows, MacOS, Linux), and optionally a base64 encoded image as 'img'"})


@app.route('/', methods=['POST'])
def notif():
    body = request.json
    print("\n", "="*20, "\n")

    check = checkbody(body) # check the body

    if not check[0]:  # body is wrong in some way
        return jsonify({'message': check[1]})

    if "img" in check: # theres an image
        sendnotif(body["Title"], body["Message"],
                  body["OS"], body["img"])
    else:
        sendnotif(body["Title"], body["Message"],
                  body["OS"])

    return jsonify({'message': "Success!"})


app.run(port=port)
checkforupadate()
