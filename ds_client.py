# ds_client.py

# Justin DeGuzman
# justicd1@uci.edu
# 72329664

import socket
from typing import Optional
import json
import time


def _connect(host: str, port: int) -> Optional[socket.socket]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        return sock
    except Exception:
        return None


def _send_json(sock: socket.socket, message: dict) -> bool:
    try:
        json_msg = json.dumps(message) + "\r\n"
        sock.sendall(json_msg.encode("utf-8"))
        return True
    except Exception:
        return False


def _recv_json(sock: socket.socket) -> Optional[dict]:
    try:
        data = sock.recv(4096).decode("utf-8")
        return json.loads(data)
    except Exception:
        return None


def send(
    server: str,
    port: int,
    username: str,
    password: str,
    message: str,
    bio: str = None
) -> bool:
    '''
    The send function joins a ds server and sends a message, bio, or both
    :param server: The ip address for the ICS 32 DS server.
    :param port: The port where the ICS 32 DS server is accepting connections.
    :param username: The user name to be assigned to the message.
    :param password: The password associated with the username.
    :param message: The message to be sent to the server.
    :param bio: Optional, a bio for the user.
    '''
    sock = _connect(server, port)
    if sock is None:
        return False

    # join request
    join_msg = {
        "join": {
            "username": username,
            "password": password
        }
    }

    if not _send_json(sock, join_msg):
        sock.close()
        return False

    join_resp = _recv_json(sock)
    if join_resp is None:
        sock.close()
        return False

    # send post message
    post_msg = {
        "post": {
            "entry": message
        }
    }

    if bio is not None:
        post_msg["post"]["bio"] = bio

    if not _send_json(sock, post_msg):
        sock.close()
        return False

    post_resp = _recv_json(sock)
    if post_resp is None:
        sock.close()
        return False

    sock.close()
    return True
