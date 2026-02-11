import json
import time
import requests
import asyncio
# from loguru import logger
from .auth import get_token
from ..utils import load_config
from .content import get_content


config = load_config()
API_BASE_URL = config["CCS_SERVER"]["API_BASE_URL"]
END_POINT = config["CCS_SERVER"]["IDEAL_END_POINT"]
CHANNEL = "IDEAL"


async def get_ideal_records(
    participant_ids: str,
    start_time: str,
    end_time: str,
    page: int = 1,
    size: int = 10,
    extension: str | None = None,
    communication_type: str | None = None,  # 通信类型（internal/external/unknown）
    content: bool = False,
) -> list[dict]:
    """
    Get the Ideal records.

    Args:
        participant_ids (str, mandatory): Comma-separated participant IDs.
        start_time (str, mandatory): Start time, format "2025-10-01 00:00:00".
        end_time (str, mandatory): End time, format "2025-10-31 23:59:59".
        page (int, optional): Page number. Defaults to 1.
        size (int, optional): Page size. Defaults to 10.
        extension (str | None, optional): Extension number. Defaults to None.
        communication_type (str | None, optional): Communication type. Defaults to None.

    Returns:
        list[dict]: List of Ideal records.
    """

    headers = {
        "Content-Type": "application/json",
        "access-token": get_token(),
    }
    params = {
        "startTime": start_time,
        "endTime": end_time,
        "page": page,
        "size": size,
    }
    if extension:
        params["extension"] = extension
    if communication_type:
        params["communicationType"] = communication_type

    records = []
    for participant_id in participant_ids.split(","):
        params["participantId"] = participant_id
        response = requests.get(
            f"{API_BASE_URL}{END_POINT}",
            headers=headers,
            params=params,
        )
        response.raise_for_status()

        if response.json()["message"] != "success":
            raise Exception(f"get call cdr records failed: {response.json()['message']}")

        for record in response.json()["data"]["records"]:
            if record["id"] not in [r["id"] for r in records]:
                records.append(record)

    if content:
        record_ids = [record["id"] for record in records]
        content = get_content(record_ids=record_ids, channel=CHANNEL)
        records = [
            {
                **record,
                "content": content["data"][i]["content"],
                "channel": CHANNEL,
            }
            for i, record in enumerate(records)
        ]
    
    return records


async def main():
    USER_HUANGJ = "1772917751770292225" # 黄金
    USER_ZHANGXS = "zhangxuesong"  # 张雪松
    PARTICIPANT_IDs = ",".join([
        USER_HUANGJ, 
        USER_ZHANGXS,
    ])

    START_TIME = "2026-01-19 00:00:00"
    END_TIME = "2026-01-19 23:59:59"
    # COMMUNICATION_TYPE = "internal"
    # EXTENSION = "7950"

    records = await get_ideal_records(
        participant_ids=PARTICIPANT_IDs,
        start_time=START_TIME,
        end_time=END_TIME,
        page=1,
        size=100,
        # extension=EXTENSION,
        # communication_type=COMMUNICATION_TYPE,
        content=True,
    )
    print(
        "=== Ideal Records ===\n",
        json.dumps(records, ensure_ascii=False, indent=2),
    )
    print(f"[OK] Ideal记录数: {len(records)}")


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f"[OK] 理想记录获取耗时: {end_time - start_time:.2f} seconds")
