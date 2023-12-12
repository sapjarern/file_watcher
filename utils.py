class ApiConfig:
    endpoint = None
    authentication_type = None
    username = None
    password = None
    token = None
    token_type = None

    @property
    def config(self):
        return {
            "endpoint": self.endpoint,
            "authentication_type": self.authentication_type,
            "username": self.username,
            "password": self.password,
            "token": self.token,
            "token_type": self.token_type,
        }


class MQTTConfig:
    host = None
    port = 1883
    tls = False
    topic = None
    username = None
    password = None

    @property
    def config(self):
        return {
            "host": self.host,
            "port": self.port,
            "topic": self.topic,
            "username": self.username,
            "password": self.password,
        }


class FileConfig:
    watch_path = None
