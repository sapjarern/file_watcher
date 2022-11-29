import os
import json
import time
import base64
import socket
import argparse
from sys import exit

from pathlib import Path
from configparser import ConfigParser

import boto3
import paho.mqtt.client as mqtt

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests

from utils import ApiConfig, MQTTConfig, FileConfig


class FileWatcher:
    watchDirectory = "files"

    def __init__(self, path):
        if not Path(path).is_dir() or path == "":
            print("path for watch doesn't exist.")
            exit(1)
        self.watchDirectory = path
        self.observer = Observer()

    def run(self, event_handler):

        self.observer.schedule(event_handler, self.watchDirectory, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


class BaseHandle(FileSystemEventHandler):
    s3_client = boto3.client('s3', aws_access_key_id="AKIAV27WOJCVVCWU5CHE",
                             aws_secret_access_key="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",
                             region_name="ap-southeast-1")

    def upload_file(self, path):
        hostname = socket.gethostname().replace('-', '_')
        with open(path, 'rb') as new_file:
            path = path.replace("\\", "/")
            self.s3_client.upload_fileobj(new_file, 'swd-license-plate', f"{hostname}/{path}")


class WebhookHandler(BaseHandle):

    def __init__(self, endpoint, headers=None):
        self.endpoint = endpoint
        self.headers = {
            "Content-Type": "application/json",
        }
        if headers:
            self.headers.update({**headers})

    # @staticmethod
    # def on_any_event(event):
    #     if event.is_directory:
    #         return None
    #
    #     elif event.event_type == 'created':
    #         # Event is created, you can process it now
    #         print("Watchdog received created event - % s." % event.src_path)
    #     elif event.event_type == 'modified':
    #         # Event is modified, you can process it now
    #         print("Watchdog received modified event - % s." % event.src_path)

    def on_created(self, event):
        print("Created")
        print(f"{event = }")
        if not event.is_directory:
            try:
                path = event.src_path.encode('cp1258').decode('utf_8')
            except ValueError as e:
                path = event.src_path
            requests.post(self.endpoint, json.dumps({"path": path}), headers=self.headers)
            self.upload_file(path)


class MQTTHandler(BaseHandle):

    @staticmethod
    def on_connect(client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        client.subscribe("#")

    @staticmethod
    def on_message(client, userdata, msg):
        print(msg.topic + " " + str(msg.payload))

    def __init__(self, mq_config: MQTTConfig):
        self._mq_client = mqtt.Client()
        self._mq_client.on_connect = self.on_connect
        self._mq_client.on_message = self.on_message
        if mq_config.tls == 'True':
            self._mq_client.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)
        if mq_config.username and mq_config.password:
            self._mq_client.username_pw_set(mq_config.username, mq_config.password)
        self._mq_client.connect(mq_config.host, int(mq_config.port), 60)
        self._base_topic = mq_config.topic

    def on_created(self, event):
        print("Created")
        print(f"{event = }")
        if not event.is_directory:
            try:
                path = event.src_path.encode('cp1258').decode('utf_8')
            except ValueError as e:
                path = event.src_path
                pass
            self._mq_client.publish(topic=f"{self._base_topic}/files", payload=json.dumps({"path": path}))
            self.upload_file(path)


if __name__ == "__main__":
    conf = ConfigParser()
    parser = argparse.ArgumentParser(description='file watch realtime api')
    parser.add_argument('-c', '--config', action='store', help='config file path', type=str)
    parser.add_argument('-g', '--gen', action='store_true', help='Generate config file')
    args = parser.parse_args()

    if args.gen:
        conf["API"] = {
            "endpoint": "",
            "authentication_type": "none",
            ";username": "",
            ";password": "",
            ";token": "",
            ";token_type": "",
        }
        conf["FILE"] = {
            "watch_path": "."
        }
        conf["MQTT"] = {
            "host": "",
            "port": "1883",
            "tls": False,
            "topic": "ark",
            ";username": "",
            ";password": "",
        }
        with open("files_watch.ini", 'w') as file:
            conf.write(file)
        exit(0)

    if not Path(args.config).is_file():
        print("Config file not found.")
        exit(1)

    api_con = ApiConfig()
    file_con = FileConfig()
    mq_con = MQTTConfig()
    conf.read(filenames=args.config, encoding='utf-8')
    if "API" in conf.sections():
        for key in conf["API"]:
            if hasattr(api_con, key):
                setattr(api_con, key, conf["API"][key])

    if "FILE" in conf.sections():
        for key in conf["FILE"]:
            if hasattr(file_con, key):
                setattr(file_con, key, conf["FILE"][key])
    if "MQTT" in conf.sections():
        for key in conf["MQTT"]:
            if hasattr(mq_con, key):
                setattr(mq_con, key, conf["MQTT"][key])

    # url = os.environ.get("ENDPOINT", "https://webhook.site/67a53b3f-f139-4b7b-a19d-1c2ec8f0450e")
    options = dict()
    if api_con.authentication_type != "none":
        if api_con.authentication_type == "token":
            options.update({"Authorization": f"{api_con.token_type} {api_con.token}"})
        elif api_con.authentication_type == "username":
            key = f'{api_con.username}:{api_con.password}'
            options.update({"Authorization": f"Basic {base64.b64encode(bytes(key, 'utf-8'))}"})

    print(f"Send event to \nendpoint: {api_con.endpoint} \nwatch path: {file_con.watch_path}")
    file_handle = WebhookHandler(endpoint=api_con.endpoint, headers=options)
    watch = FileWatcher(path=file_con.watch_path)
    watch.run(file_handle)

print(f"{ord('a')}")
