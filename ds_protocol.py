# ds_protocol.py

# Justin DeGuzman
# justicd1@uci.edu
# 72329664

import json
from collections import namedtuple

DataTuple = namedtuple("DateTuple", ["type", "token"])


def extract_json(json_msg: str) -> DataTuple:
    try:
        json_obj = json.loads(json_msg)
        type = json_obj["response"]["type"]
        token = json_obj["response"]["message"]
    except json.JSONDecodeError:
        print("Json cannot be decoded.")
        return DataTuple(None, None)

    return DataTuple(type, token)
