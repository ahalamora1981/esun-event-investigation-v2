from loguru import logger
from agno.agent import Agent
from agno.models.vllm import VLLM
from agno.models.dashscope import DashScope
from ..utils import load_config
from openai import OpenAI


config = load_config()


vllm_qwen3 = VLLM(
    id=config["VLLM_QWEN3"]["MODEL"],
    base_url=config["VLLM_QWEN3"]["BASE_URL"],
    api_key=config["VLLM_QWEN3"]["API_KEY"],
    temperature=config["VLLM_QWEN3"]["TEMPERATURE"],
)

vllm_qwen3_vl = VLLM(
    id=config["VLLM_QWEN3_VL"]["MODEL"],
    base_url=config["VLLM_QWEN3_VL"]["BASE_URL"],
    api_key=config["VLLM_QWEN3_VL"]["API_KEY"],
    temperature=config["VLLM_QWEN3_VL"]["TEMPERATURE"],
)

dashscope_qwen = DashScope(
    id=config["DASHSCOPE"]["MODEL"],
    base_url=config["DASHSCOPE"]["BASE_URL"],
    api_key=config["DASHSCOPE"]["API_KEY"],
    temperature=config["DASHSCOPE"]["TEMPERATURE"],
)

dashscope_qwen_openai = OpenAI(
    api_key=config["DASHSCOPE"]["API_KEY"],
    base_url=config["DASHSCOPE"]["BASE_URL"],
)

agent = Agent(
    name="AI助手",
    description="你是一个智能助手，能够回答用户的问题；不要思考，直接回答。",
    model=dashscope_qwen,
    markdown=True,
)

if __name__ == "__main__":
    response = agent.run("写一首五言绝句，关于“太阳”", debug_mode=True)
    logger.info(response.content)
    print(response.content)
