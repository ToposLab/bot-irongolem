import sys
import urllib.parse
import requests
import socketio

from sdk.model import User, Chat, Message

SDK_VERSION = 1.1

RESTFUL_API_URL = "https://api.topos.world"
SOCKET_API_URL = "https://messaging-api.topos.world"

sio = socketio.Client()

token: str
user: User

chat_cache: dict[str, Chat] = {}
user_cache: dict[str, User] = {}

print("[Topos] running sdk version %s" % SDK_VERSION)


@sio.on('connect')
def on_connect():
    print("[Topos] socket is connceted")


@sio.on('message')
def on_message(data):
    message = Message(data)
    on_message_binding(message)


def base_url(path: str) -> str:
    return urllib.parse.urljoin(RESTFUL_API_URL, path)


def auth_headers() -> dict:
    return {"authorization": "Bearer %s" % token}


def set_message_handler(message_handler):
    global on_message_binding
    on_message_binding = message_handler

def login(countryCode: int, mobile: str, password: str):
    res = requests.post(base_url('/auth/login'), json={
        "countryCode": countryCode,
        "mobile": mobile,
        "password": password
    })

    if res.status_code != 200 and res.status_code != 201:
        raise Exception(res.json())

    auth_info = res.json()

    global token
    global user

    token = auth_info["token"]
    user = get_user(auth_info["user"]["_id"])

    print("[Topos] logined as %s" % user.id)

    sio_url = SOCKET_API_URL + ("?token=%s" % token)
    try:
        sio.connect(sio_url, transports="websocket")
    except ValueError:
        print("renewed token")


def get_joined_chats() -> list[Chat]:
    res = requests.get(base_url("/chats"), headers=auth_headers())

    if res.status_code != 200 and res.status_code != 201:
        raise Exception(res.json())

    return map(lambda x: Chat(x), res.json())


def get_chat(chat_id: str, ignore_cache: bool = False):
    if (not ignore_cache) and chat_id in chat_cache:
        return chat_cache[chat_id]

    res = requests.get(base_url("/chats/%s" % chat_id), headers=auth_headers())

    if res.status_code != 200 and res.status_code != 201:
        raise Exception(res.json())

    chat = Chat(res.json())
    chat_cache[chat_id] = chat

    return chat


def get_user(user_id: str, ignore_cache: bool = False):
    if (not ignore_cache) and user_id in user_cache:
        return user_cache[user_id]

    res = requests.get(base_url("/users/%s" % user_id), headers=auth_headers())

    if res.status_code != 200 and res.status_code != 201:
        raise Exception(res.json())

    user = User(res.json())
    user_cache[user_id] = user

    return user


def send_text(to_chat_id: str, content: str) -> dict:
    res = requests.post(base_url("/chats/%s/messages" % to_chat_id), headers=auth_headers(), json={
        "type": "text",
        "content": content
    })

    if res.status_code != 200 and res.status_code != 201:
        raise Exception(res.json())

    return res.json()


def send_image(to_chat_id: str, url: str, width: int, height: int) -> dict:
    res = requests.post(base_url("/chats/%s/messages" % to_chat_id), headers=auth_headers(), json={
        "type": "image",
        "content": "[Image]",
        "element": {
            "type": "image",
            "url": url,
            "width": width,
            "height": height
        }
    })

    if res.status_code != 200 and res.status_code != 201:
        raise Exception(res.json())

    return res.json()
