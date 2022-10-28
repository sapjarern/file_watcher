import os
import json
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests


class FileWatcher:
    watchDirectory = "files"

    def __init__(self):
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


class WebhookHandler(FileSystemEventHandler):

    def __init__(self, endpoint, headers={}):
        self.endpoint = endpoint
        self.headers = {
            "Content-Type": "application/json",
            **headers
        }

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
                pass
            requests.post(self.endpoint, json.dumps({"path": path}), headers=self.headers)


if __name__ == "__main__":
    url = os.environ.get("ENDPOINT", "https://webhook.site/67a53b3f-f139-4b7b-a19d-1c2ec8f0450e")
    options = {}
    if txt_headers := os.environ.get("HEADERS", ""):
        for header in txt_headers.split(","):
            try:
                key, value = header.split(":")
                options.update({key: value})
            except ValueError as e:
                pass
    print(f"Send event to \nendpoint: {url} \nheaders: {txt_headers}")
    file_handle = WebhookHandler(endpoint=url, headers=options)
    watch = FileWatcher()
    watch.run(file_handle)
