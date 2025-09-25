# coding=utf-8
# 2025.9.23

"""
实现定位和天气智能助手
"""

from qwen_agent.agents import Assistant

from app.agents.weather.config import MCP_TOOLS, LLM_CFG


bot = Assistant(
    llm=LLM_CFG,
    name="助手",
    description="高德地图、天气查询、公网链接部署",
    system_message="你是会天气查询、地图查询、网页部署的助手",
    function_list=MCP_TOOLS
)

messages = []

while True:
    query = input("\nuser question: ")
    if not query.strip():
        print("user question cannot be empty！")
        continue
    messages.append({"role": "user", "content": query})
    bot_response = ""
    is_tool_call = False
    tool_call_info = {}
    for response_chunk in bot.run(messages):
        new_response = response_chunk[-1]
        if "function_call" in new_response:
            is_tool_call = True
            tool_call_info = new_response["function_call"]
        elif "function_call" not in new_response and is_tool_call:
            is_tool_call = False
            print("\n" + "=" * 20)
            print("工具调用信息：", tool_call_info)
            print("工具调用结果：", new_response)
            print("=" * 20)
        elif new_response.get("role") == "assistant" and "content" in new_response:
            incremental_content = new_response["content"][len(bot_response):]
            print(incremental_content, end="", flush=True)
            bot_response += incremental_content
    messages.extend(response_chunk)


