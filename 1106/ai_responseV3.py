from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# 기존 작성된 함수 사용
from ai_responseV2 import get_current_date_tz,get_current_time_tz
load_dotenv()
client=OpenAI() 

import json

def get_ai_response_tools(question):
    response = get_first_response_tools(question=question)
    tool_results = []
    for tool in response.choices[0].message.tool_calls:
        fn_name = tool.function.name
        args = json.loads(tool.function.arguments)
        
        # 함수 이름을 문자열로 가져와서 globals() 이용하여 실행하기
        if fn_name:
            result = globals()[fn_name](**args)
            tool_results.append({"name": fn_name, "result": result})
        else:
            tool_results.append({"name": fn_name, "result": f"Unknown function: {fn_name}"})
    
    final_response = get_followup_response_tools(question, tool_results)
    return final_response

def get_followup_response_tools(question,tool_results):
    result_text = "\n".join([f"{t['name']} 결과는 {t['result']} 입니다." for t in tool_results])
    followup_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. using locale language."},
            {"role": "user", "content": f"{question} 에 대해 다음 결과를 이용해 자연스러운 최종 답변을 만들어줘:\n{result_text}"}
        ],
        tools=tools
    )
    return followup_response.choices[0].message.content

def get_first_response_tools(question):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant using locale language."},
            {"role": "user", "content": question}
        ],
        tools=tools,
        tool_choice="auto"
    )
    return response

tools = [
    {
    "type": "function",
    "function": {
                "name": "get_current_time_tz",
                "description": "현재 시간 출력 HH:MM:SS format",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "timezone": {
                            "type": "string",
                            "description": "Time zone in 'Area/Location' format, e.g., 'Asia/Seoul', 'America/New_York'. Default is 'Asia/Seoul'."
                        }
                    },
                    "required": ['timezone']
                }
            }
    },
    { 
        "type": "function",
        "function": {
        "name": "get_current_date_tz",
        "description": "현재 날짜 출력 YYYY 년 MM 월 DD 일 format",
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Time zone in 'Area/Location' format, e.g., 'Asia/Seoul', 'America/New_York'. Default is 'Asia/Seoul'."
                }
            },
            "required": ['timezone']
        }}
    }
]