# coding=utf-8
# 2025.9.23

"""
天气助手配置
"""
from app.config import get_settings

# LLM
LLM_CFG = {
    "model": "qwen-plus-latest",
    "model_server": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "api_key": get_settings().aliyun_api_key,
}

# MCP列表
MCP_TOOLS = [
    {
        "mcpServers": {
            "amap-maps": {
                "url": "https://dashscope.aliyuncs.com/api/v1/mcps/amap-maps/sse",
                "headers": {
                    "Authorization": f"Bearer {get_settings().aliyun_api_key}"
                }
            }
        }
    }
]
