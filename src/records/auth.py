import requests
from cachetools import cached, TTLCache
from src.utils.config import load_config


# Cache the token for 1 hour
token_cache = TTLCache(maxsize=1, ttl=60 * 60)

config = load_config()
API_BASE_URL = config["CCS_SERVER"]["API_BASE_URL"]


@cached(token_cache)
def get_token(
    appKey: str = config["CCS_SERVER"]["APP_KEY"],
    appSecret: str = config["CCS_SERVER"]["APP_SECRET"],
) -> str:
    """
    Get token from CCS Open API

    Args:
        appKey (str, optional): App key. Defaults to CCS_SERVER["APP_KEY"].
        appSecret (str, optional): App secret. Defaults to CCS_SERVER["APP_SECRET"].

    Returns:
        str: A string containing the access token.
    """

    headers = {
        "Content-Type": "application/json",
    }

    params = {
        "appKey": appKey,
        "appSecret": appSecret,
    }

    response = requests.post(
        f"{API_BASE_URL}/oauth2/access-token",
        headers=headers,
        params=params,
    )

    response.raise_for_status()

    if response.json()["message"] != "success":
        raise Exception(f"get token failed: {response.json()['message']}")

    return response.json()["data"]


if __name__ == "__main__":
    token = get_token()
    print(f"TOKEN: {token}")
