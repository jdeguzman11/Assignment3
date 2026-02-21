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
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        return s
    except Exception:
        return None


def _send_json(sock: socket.socket, message: dict) -> bool:
    try:
        data = json.dummps(message).encode("utf-8")
        sock.sendall(data)
        return True
    except Exception:
        return False


def _recv_json(sock: socket.socket) -> Optional[dict]:
    try:
        file = sock.makefile("r")
        line = file.readline()
        if not line:
            return None
        return json.loads(line)
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

    try:
        if not _send_json(sock, message):
            return False
    finally:
        try:
            sock.close()
        except Exception:
            pass

    return True
