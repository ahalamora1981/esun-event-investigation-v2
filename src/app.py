import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from src.score.score_records import reconstruct_event, Event  # noqa: E402


app = FastAPI(title="Event Investigation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/reconstruct")
async def reconstruct(event: Event) -> dict:
    """
    重构事件相关记录并返回评估结果
    
    Args:
        event: 事件信息
        
    Returns:
        dict: 包含事件信息和相关记录的字典
    """
    
    result = await reconstruct_event(event)
    return result


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
