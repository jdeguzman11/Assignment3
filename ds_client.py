# Justin DeGuzman
# justicd1@uci.edu
# 72329664

# ds_client.py

import socket
from typing import Optional, TextIO
import json
import time

import ds_protocol


def _connect(host: str, port: int) -> Optional[socket.socket]:
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((host, port))
        return sock

    except Exception:
        return None


def _send_json(send_file: TextIO, message: dict) -> bool:
    try:
        json_msg = json.dumps(message)
        send_file.write(json_msg + "\r\n")
        send_file.flush()
        return True

    except Exception:
        return False


def _recv_response(recv_file: TextIO) -> ds_protocol.DataTuple:
    try:
        line = recv_file.readline()

        if line == "":
            return ds_protocol.DataTuple(None, None)
        return ds_protocol.extract_json(line.strip())

    except Exception:
        return ds_protocol.DataTuple(None, None)


def _is_blank(s: Optional[str]) -> bool:
    return s is None or s.strip() == ""


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

    send_file = None
    recv_file = None

    try:
        send_file = sock.makefile("w", encoding="utf-8", newline="")
        recv_file = sock.makefile("r", encoding="utf-8", newline="")

        # join
        join_msg = {
            "join": {
                "username": username,
                "password": password,
                "token": ""
            }
        }

        if not _send_json(send_file, join_msg):
            return False

        join_resp = _recv_response(recv_file)
        if join_resp.type != "ok":
            return False

        token = join_resp.token
        if not token:
            return False

        # post
        if not _is_blank(message):
            post_msg = {
                "token": token,
                "post": {
                    "entry": message,
                    "timestamp": str(time.time())
                }
            }

            if not _send_json(send_file, post_msg):
                return False

            post_resp = _recv_response(recv_file)
            if post_resp.type != "ok":
                return False

        # bio
        if not _is_blank(bio):
            bio_msg = {
                "token": token,
                "bio": {
                    "entry": bio,
                    "timestamp": str(time.time())
                }
            }

            if not _send_json(send_file, bio_msg):
                return False

            bio_resp = _recv_response(recv_file)
            if bio_resp.type != "ok":
                return False

        return True

    except Exception:
        return False

    finally:
        try:
            if send_file is not None:
                send_file.close()
        except Exception:
            pass

        try:
            if recv_file is not None:
                recv_file.close()
        except Exception:
            pass

        try:
            sock.close()
        except Exception:
            pass
