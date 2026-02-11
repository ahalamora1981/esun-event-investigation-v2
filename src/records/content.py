import json
import requests
from .auth import get_token
from ..utils.config import load_config


config = load_config()

CCS_API_BASE_URL = config["CCS_SERVER"]["API_BASE_URL"]
CONTENT_END_POINT = config["CCS_SERVER"]["CONTENT_END_POINT"]

COUNT_TOKENS_API_BASE_URL = config["COUNT_TOKENS"]["API_BASE_URL"]
COUNT_TOKENS_END_POINT = config["COUNT_TOKENS"]["END_POINT"]


def get_content(
    record_ids: list[str],
    channel: str,
) -> dict:
    """
    Get the content of the media records.

    Args:
        record_ids (list[str]): List of media record IDs.
        channel (str): Communication channel.
            CALL - 电话
            QTRADE - QTRADE
            IDEAL - IDEAL
            ZOOM - ZOOM
            EMAIL - 邮件
            TM - 腾讯会议
            QY - 企业微信

    Returns:
        dict: Object contains content of the media records.
    """

    if not record_ids:
        return {"data": []}

    headers = {
        "Content-Type": "application/json",
        "access-token": get_token(),
    }
    params = {
        "recordIds": record_ids,
        "channel": channel,
    }
    response = requests.get(
        f"{CCS_API_BASE_URL}{CONTENT_END_POINT}",
        headers=headers,
        params=params,
    )
    if response.status_code != 200:
        print(response.text)
    response.raise_for_status()

    if response.json()["message"] != "success":
        raise Exception(f"get unify text failed: {response.json()['message']}")

    return response.json()


def get_token_count(content: str | None = None) -> int:
    """
    Get the token count of the content.

    Args:
        content (str): Content.

    Returns:
        int: Token count.
    """

    if not content:
        return 0
    
    url = f"{COUNT_TOKENS_API_BASE_URL}{COUNT_TOKENS_END_POINT}"

    payload = {
        "query": content,
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()

    if not response.json()["ok"]:
        raise Exception(f"get token count failed: {response.json()['message']}")

    return response.json()["tokens_length"]


if __name__ == "__main__":
    record_ids = [
        "1984397103421546498",
        "1984759491723354113",
        "1985121879479902210",
    ]
    channel = "CALL"

    content = get_content(record_ids=record_ids, channel=channel)
    print(json.dumps(content, ensure_ascii=False, indent=2))

    token_count = get_token_count(content["data"][0]["content"])
    print(f"Token count: {token_count}")
