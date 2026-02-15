import json
import time
import asyncio
import requests
from pathlib import Path
from loguru import logger
from datetime import datetime
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
from rich import print
from textwrap import dedent

from src.utils import load_config, setup_logger, dashscope_qwen_openai
from src.records import (
    get_call_recording,
    get_email_records,
    get_qtrade_records,
    get_ideal_records,
)


# 时间相关性参数 (总分100分，根据记录与事件发生时间的距离计算得分)
DEDUCT_PER_HOUR = 20  # 每小时扣减的分数
BEFORE_RATE = 1  # 事件在记录结束时间之后的得分衰减系数（事后通信）
AFTER_RATE = 2  # 事件在记录开始时间之前的得分衰减系数（事前通信）

# 打分权重，总数必须为 100
# WEIGHT_TIME = 30
# WEIGHT_USER = 30
# WEIGHT_CONTENT = 40

# if WEIGHT_TIME + WEIGHT_USER + WEIGHT_CONTENT != 100:
#     raise ValueError("WEIGHT_TIME, WEIGHT_USER, WEIGHT_CONTENT 必须总和为 100")

# 渠道权重，每一项最高 100 分
WEIGHT_CHANNELS = {
    "CALL": 95,
    "EMAIL": 95,
    "QTRADE": 95,
    "IDEAL": 95,
}

# 设置总得分阈值，超过该阈值则认为记录与事件相关
# THRESHOLD_TOTAL_SCORE = 50

USER_MAPPING = {
    "1772917751770292225": "黄金",
    "zhangxuesong": "张雪松",
}

EVENT_NAMES = [
    "230205（23 国开 205）",
    # "250006（25 国开 006）",
    # "AU2406（沪金 2406 合约）",
    # "SC2406（原油 2406 合约）",
]

console = Console()

config = load_config()
setup_logger()

RERANKER_URL = config["RERANKER"]["URL"]
RERANKER_MODEL = config["RERANKER"]["MODEL"]
RERANKER_THRESHOLD = config["RERANKER"]["THRESHOLD"]


def get_rerank_scores(query: str, documents: list[str]) -> list[dict]:
    payload = {
        "model": RERANKER_MODEL,
        "query": query,
        "documents": documents,
        "top_n": len(documents),
    }
    response = requests.post(RERANKER_URL, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()["results"]


class Weights(BaseModel):
    time: int = Field(..., description="时间权重，范围在 [0, 100] 之间")
    user: int = Field(..., description="用户权重，范围在 [0, 100] 之间")
    content: int = Field(..., description="内容权重，范围在 [0, 100] 之间")


class Event(BaseModel):
    event_name: str = Field(..., description="事件名称")
    event_time: str = Field(
        ..., description="事件发生时间，格式为 '2026-01-19T15:00:00'"
    )
    internal_users: list[str] = Field(..., description="内部用户 ID 列表")
    external_users: list[str] = Field(..., description="外部用户姓名列表")
    relevance: int = Field(..., description="记录与事件的相关性阈值，只获取相关性大于等于该值的记录，范围在 [0, 100] 之间")
    weights: Weights = Field(..., description="打分权重")
    ai_check_record: bool = Field(default=False, description="是否使用 AI 检查记录内容")


# 根据 event 和 record，输出外部用户姓名
def get_external_user_name(record: dict) -> str | None:
    """
    根据 event 和 record，输出外部用户姓名。

    参数:
        event (Event): 包含事件外部用户姓名的对象。
        record (dict): 包含记录用户 ID 的字典。

    返回:
        str: 外部用户姓名。
    """

    if record["channel"] == "CALL":
        external_user = None
    elif record["channel"] == "EMAIL":
        external_user = record["otherUserName"]
    elif record["channel"] == "QTRADE":
        external_user = record["receiver"]
    elif record["channel"] == "IDEAL":
        external_user = record["toName"]
    else:
        raise ValueError(f"未知渠道: {record['channel']}")

    return external_user


# 时间相关性参数 (总分100分，根据记录与事件发生时间的距离计算得分)
def calculate_time_score(event: Event, record: dict) -> float:
    """
    计算记录与事件发生时间的相关性得分。

    参数:
        event (Event): 包含事件时间的对象，格式为 {"time": "2026-01-19T12:00:00"}。
        record (dict): 包含记录开始时间和结束时间的字典，格式为 {"startTime": "2026-01-19T10:00:00", "endTime": "2026-01-19T14:00:00"}。

    返回:
        float: 计算得到的时间得分，范围在 [0, 100] 之间。
    """

    time_score = 100

    time_format = (
        "%Y-%m-%dT%H:%M:%S" if "T" in event.event_time else "%Y-%m-%d %H:%M:%S"
    )
    event_time = datetime.strptime(event.event_time, time_format)

    time_format = (
        "%Y-%m-%dT%H:%M:%S" if "T" in record["startTime"] else "%Y-%m-%d %H:%M:%S"
    )
    record_start_time = datetime.strptime(record["startTime"], time_format)

    # 处理没有结束时间的记录，如果没有结束时间，默认结束时间为开始时间
    if "endTime" in record:
        time_format = (
            "%Y-%m-%dT%H:%M:%S" if "T" in record["endTime"] else "%Y-%m-%d %H:%M:%S"
        )
        record_end_time = datetime.strptime(record["endTime"], time_format)
    else:
        record_end_time = record_start_time

    # 计算记录与事件发生时间的相关性得分
    if record_start_time <= event_time <= record_end_time:
        return time_score
    elif event_time > record_end_time:
        time_diff = (event_time - record_end_time).total_seconds() / 3600
        time_score -= (time_diff * DEDUCT_PER_HOUR) * BEFORE_RATE
    elif event_time < record_start_time:
        time_diff = (record_start_time - event_time).total_seconds() / 3600
        time_score -= (time_diff * DEDUCT_PER_HOUR) * AFTER_RATE

    return max(time_score, 0.0)


# 用户相关性参数 (总分100分，根据记录与事件发生用户的匹配度计算得分)
def calculate_user_score(event: Event, record: dict) -> float:
    """
    计算记录与事件发生用户的用户得分。

    参数:
        event (Event): 包含事件用户的对象，格式为 {"user": "1772917751770292225"}。
        record (dict): 包含记录用户的字典，格式为 {"user": "1772917751770292225"}。

    返回:
        float: 计算得到的用户得分，范围在 [0, 100] 之间。
    """

    # 获取记录中的外部用户姓名
    external_user = get_external_user_name(record)

    # 计算内部用户得分
    if record["userId"] in event.internal_users:
        internal_user_score = 100.0
    else:
        internal_user_score = 0.0
    
    # 计算外部用户得分
    if external_user is None:
        external_user_score = 0.0
    elif external_user in event.external_users:
        external_user_score = 100.0
    else:
        external_user_score = 0.0
    
    # 计算用户得分
    user_score = (internal_user_score + external_user_score) / 2
    
    return max(user_score, 0.0)


# 内容相关性参数 (总分100分，根据记录与事件发生内容的匹配度计算得分)
def calculate_content_score(event: Event, record: dict) -> float:
    """
    计算记录与事件发生内容的内容得分。

    参数:
        event (Event): 包含事件名称的对象，格式为 {"event_name": "AU2406（沪金 2406 合约）"}。
        record (dict): 包含记录内容的字典，格式为 {"content": "2406 合约相关内容"}。

    返回:
        float: 计算得到的内容得分，范围在 [0, 100] 之间。
    """

    if record["content"]:
        try:
            rerank_scores = get_rerank_scores(event.event_name, [record["content"]])
            content_score = rerank_scores[0]["relevance_score"] * 100
        except Exception as e:
            logger.error(f"Rerank error: {e}")
            content_score = 0.0
    return max(content_score, 0.0)


# 综合得分参数 (总分100分，根据时间、用户、内容得分计算综合得分)
def calculate_total_score(event: Event, record: dict) -> dict:
    """
    计算记录与事件发生的综合得分。

    参数:
        event (Event): 包含事件信息的对象，格式为 {"time": "2026-01-19T12:00:00", "user": "1772917751770292225", "event_name": "AU2406（沪金 2406 合约）"}。
        record (dict): 包含记录信息的字典，格式为 {"startTime": "2026-01-19T10:00:00", "endTime": "2026-01-19T14:00:00", "user": "1772917751770292225", "content": "2406 合约相关内容"}。

    返回:
        dict: 包含时间得分、用户得分、内容得分和综合得分的字典，格式为 {"time_score": 80.0, "user_score": 90.0, "content_score": 70.0, "total_score": 83.0}。
    """

    time_score = calculate_time_score(event, record)
    user_score = calculate_user_score(event, record)
    content_score = calculate_content_score(event, record)
    total_score = (
        time_score * (event.weights.time / 100)
        + user_score * (event.weights.user / 100)
        + content_score * (event.weights.content / 100)
    ) * (WEIGHT_CHANNELS[record["channel"]] / 100)

    return {
        "time_score": time_score,
        "user_score": user_score,
        "content_score": content_score,
        "total_score": total_score,
    }


# === 获取记录 ===
async def get_records():
    """
    获取事件相关的记录。

    返回:
        list[dict]: 包含通话记录、邮件记录、QTrade记录和Ideal记录的列表。
    """

    PARTICIPANT_IDS = ",".join(
        [
            "1772917751770292225",  # 黄金
            "zhangxuesong",  # 张雪松
        ]
    )
    START_TIME = "2026-01-19 00:00:00"
    END_TIME = "2026-01-19 23:59:59"
    PAGE = 1
    SIZE = 100

    # === 通话记录 ===
    call_recording_records = await get_call_recording(
        participant_ids=PARTICIPANT_IDS,
        start_time=START_TIME,
        end_time=END_TIME,
        page=PAGE,
        size=SIZE,
        content=True,
    )

    # === 邮件记录 ===
    email_records = await get_email_records(
        participant_ids=PARTICIPANT_IDS,
        start_time=START_TIME,
        end_time=END_TIME,
        page=PAGE,
        size=SIZE,
        content=True,
    )

    # === QTrade记录 ===
    qtrade_records = await get_qtrade_records(
        participant_ids=PARTICIPANT_IDS,
        start_time=START_TIME,
        end_time=END_TIME,
        page=PAGE,
        size=SIZE,
        content=True,
    )

    # === Ideal记录 ===
    ideal_records = await get_ideal_records(
        participant_ids=PARTICIPANT_IDS,
        start_time=START_TIME,
        end_time=END_TIME,
        page=PAGE,
        size=SIZE,
        content=True,
    )

    records = (
        call_recording_records + email_records + qtrade_records + ideal_records
    )
    return records


# === 评估记录风险 ===
def evaluate_record_risk(record: dict, records: list[dict]) -> dict:
    """
    评估记录的风险等级和描述。

    参数:
        record (dict): 包含记录内容的字典，格式为 {"content": "2406 合约相关内容"}。
        records (list[dict]): 包含所有记录内容的列表，每个元素为 {"content": "记录内容"}。

    返回:
        dict: 包含风险等级和描述的字典，格式为 {"risk_level": "高/中/低", "risk_description": "详细描述记录中存在的风险，包括风险类型、影响范围、可能的后果等。"}。
    """ 

    output_format = dedent("""
    ```json
    {
        "risk_level": "高/中/低",
        "risk_description": "详细描述记录中存在的风险，包括风险类型、影响范围、可能的后果等。"
    }
    ```
    """).strip()

    system_prompt_path = Path(__file__).parent.parent / "prompts/evaluate_record_risk.md"
    system_prompt = system_prompt_path.read_text(encoding="utf-8").format(
        records_content="\n\n---\n\n".join([r["content"] for r in records]),
        record_content=record["content"],
        output_format=output_format,
    )

    response = dashscope_qwen_openai.chat.completions.create(
        model=config["DASHSCOPE"]["MODEL"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "执行'记录风险评估任务'"},
        ],
    )
    response_content = response.choices[0].message.content
    response_json = json.loads(response_content.replace("```json", "").replace("```", ""))

    return response_json


# === 打印记录 ===
def print_records(new_event: Event, records: list[dict]):
    # 打印事件信息
    console.print(f"[bold magenta]事件名称: {new_event.event_name}[/bold magenta]")
    console.print(f"[bold magenta]事件时间: {new_event.event_time}[/bold magenta]")
    console.print(f"[bold magenta]内部用户: {new_event.internal_users}[/bold magenta]")  
    console.print(f"[bold magenta]外部用户: {new_event.external_users}[/bold magenta]")

    # 用 rich 打印表格
    records_table = Table(show_header=True, header_style="bold magenta")
    records_table.add_column("编号", style="dim", width=4)
    records_table.add_column("时间", width=10)
    records_table.add_column("渠道", width=8)
    records_table.add_column("内部用户", width=8)
    records_table.add_column("外部用户", width=8)
    records_table.add_column("时间", width=6)
    records_table.add_column("用户", width=6)
    records_table.add_column("内容", width=6)
    records_table.add_column("总相关性", width=8, style="green bold")
    records_table.add_column("风险等级", width=8)
    records_table.add_column("风险描述", width=20)

    for i, record in enumerate(records):
        score = record["score"]
        records_table.add_row(
            f"{(i + 1):02d}",
            record["start_time"][-8:],
            record["channel"],
            USER_MAPPING.get(record["internal_user"], record["internal_user"]),
            record["external_user"],
            str(int(score["time_score"])),
            str(int(score["user_score"])),
            str(int(score["content_score"])),
            str(int(score["total_score"])),
            record["risk"]["risk_level"],
            record["risk"]["risk_description"],
        )

    console.print(records_table)

    # print(
    #     "=== All Records (By Participant IDs) ===\n",
    #     json.dumps(all_records, ensure_ascii=False, indent=2),
    # )
    print(f"[OK] 所有记录获取成功, 记录数: {len(records)}")


async def reconstruct_event(new_event: Event):    
    # === 获取记录 ===
    records = await get_records()

    # === 计算得分 ===
    for i, record in enumerate(records):
        score = calculate_total_score(new_event, record)
        records[i]["score"] = score

    # 按总分对记录排序, 只保留总分大于等于阈值的记录
    records = [
        record
        for record in records
        if record["score"]["total_score"] >= new_event.relevance
    ]

    # 按开始时间排序，开始时间是一个字符串，需要考虑先转换成datetime再排序
    records.sort(key=lambda x: datetime.fromisoformat(x["startTime"]))

    if new_event.ai_check_record:
        # === 评估记录风险 ===
        for i, record in enumerate(records):
            risk = evaluate_record_risk(record, records)
            records[i]["risk"] = risk
            print(risk)
    else:
        for record in records:
            record["risk"] = {
                "risk_level": None,
                "risk_description": None,
            }

    new_records = []
    for record in records:
        if "endTime" not in record:
            end_time = record["startTime"]
        else:
            end_time = record["endTime"]

        internal_user = USER_MAPPING.get(record["userId"], record["userId"])
        external_user = get_external_user_name(record)

        new_record = {
            "internal_user": internal_user,
            "external_user": external_user,
            "start_time": record["startTime"],
            "end_time": end_time,
            "channel": record["channel"],
            "content": record["content"],
            "score": record["score"],
            "risk": record["risk"],
        }
        new_records.append(new_record)

    # === 打印记录 ===
    print_records(new_event, new_records)

    result = {
        "event": new_event.model_dump(),
        "records": new_records,
    }

    # === 保存记录 ===
    output_fold = Path(__file__).parent.parent / "output"
    output_fold.mkdir(parents=True, exist_ok=True)
    result_path = output_fold / f"result_{time.strftime('%Y%m%d_%H%M%S')}.json"

    with open(result_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result

if __name__ == "__main__":
    # === 初始化事件 ===
    new_event = Event(
        event_name="230205（23 国开 205）",
        event_time="2026-01-19T14:00:00",
        internal_users=[
            "1772917751770292225",
        ],
        external_users=["韩梅梅", "周子航"],
    )

    start_time = time.time()
    asyncio.run(reconstruct_event(new_event))
    end_time = time.time()
    print(f"[OK] 总耗时: {end_time - start_time:.2f} seconds")
