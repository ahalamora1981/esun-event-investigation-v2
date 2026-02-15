import json
import requests

API_URL = "http://localhost:8000/reconstruct"


def test_reconstruct():
    """
    测试事件重构接口
    """
    # 定义测试事件
    event_data = {
        "event_name": "230205（23 国开 205）",
        "event_time": "2026-01-19T14:00:00",
        "internal_users": [
            "1772917751770292225",
        ],
        "external_users": ["韩梅梅", "周子航"],
    }

    print(f"发送请求到: {API_URL}")
    print(f"请求数据: {json.dumps(event_data, ensure_ascii=False, indent=2)}")
    print()

    try:
        response = requests.post(API_URL, json=event_data, timeout=300)
        response.raise_for_status()

        result = response.json()

        print("=" * 60)
        print("响应状态:", response.status_code)
        print("=" * 60)
        print(f"事件名称: {result.get('event', {}).get('event_name')}")
        print(f"事件时间: {result.get('event', {}).get('event_time')}")
        print(f"内部用户: {result.get('event', {}).get('internal_users')}")
        print(f"外部用户: {result.get('event', {}).get('external_users')}")
        print(f"记录数量: {len(result.get('records', []))}")
        print("=" * 60)

        if result.get('records'):
            print("\n前 3 条记录预览:")
            for i, record in enumerate(result['records'][:3], 1):
                print(f"\n记录 {i}:")
                print(f"  时间: {record.get('start_time')} ~ {record.get('end_time')}")
                print(f"  渠道: {record.get('channel')}")
                print(f"  内部用户: {record.get('internal_user')}")
                print(f"  外部用户: {record.get('external_user')}")
                score = record.get('score', {})
                print(f"  时间得分: {score.get('time_score', 0):.2f}")
                print(f"  用户得分: {score.get('user_score', 0):.2f}")
                print(f"  内容得分: {score.get('content_score', 0):.2f}")
                print(f"  总体得分: {score.get('total_score', 0):.2f}")
                risk = record.get('risk', {})
                print(f"  风险等级: {risk.get('risk_level')}")
                print(f"  风险描述: {risk.get('risk_description')}")

        print("\n完整响应:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except requests.exceptions.ConnectionError:
        print(f"错误: 无法连接到 {API_URL}")
        print("请确保 FastAPI 服务正在运行: uv run src/app.py")
    except requests.exceptions.Timeout:
        print("错误: 请求超时")
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
    except json.JSONDecodeError:
        print("错误: 无法解析响应为 JSON")
        print(f"响应内容: {response.text}")


if __name__ == "__main__":
    test_reconstruct()
