from openai import OpenAI
from dotenv import load_dotenv
from chatbot_function import get_menu,get_order_price,set_order,compelet_order
import json
import inspect  # 함수의 형식을 알아내기 위해서 사용
import uuid     # 임의 문자열 생성
load_dotenv()
client=OpenAI() 

instruction = """
너는 피자 주문을 돕는 챗봇이다.
친절하고 간단명료하게 대화하며, 고객이 원하는 피자를 정확히 주문할 수 있도록 안내한다.
고객이 피자를 주문하려고하면 가격이 적혀있는 메뉴를 보여준다.
1. 고객의 주문 의도를 파악한다 - 주문 내용은 메뉴 이름, 사이즈, 수량이며 그외에는 없음.
주의 : 메뉴 목록에 없는 것은 주문 받으면 안됨.
2. 피자의 종류와 사이즈는 지시한 대로만 가격 안내 해야 함.
3. 고객이 주문을 진행하면 피자의 종류와 사이즈를 이용해서 총 결제금액을 계산하여 알려주고 주문 번호를 생성하여 저장한다.
4. 추가 주문이 없는지 확인하고 추가 주문이 있으면 주문 받은 내용을 추가한다
5. 고객이 주문을 완료하면 주문번호와 주문 내역, 결제금액을 확인한다.
6. 불필요한 잡담은 최소화하고, 주문과 관련된 대화에 집중한다.
7. 항상 정중하고 친근한 말투를 유지한다.
가벼운 인사말과 피자 주문 이외의 다른 요청은 '챗봇 기능과 다른 질문입니다.' 라고 답변해.
"""

# 챗 기록 유지
# chat_history = [{"role":"system", "content":instruction}]

# UI 연동하여 사용자 메시지 처리
def chat_with_bot(user_input,chat_history,orders):
    if not chat_history :
        chat_history.append({"role":"system", "content":instruction})
        
    chat_history.append({"role": "user", "content": user_input})
    response = get_first_chatbot_response(chat_history)
    print(f'log resp : {response}')
    message = response.choices[0].message
    print(f'log  function_call\n↪: {message.function_call}')
    if message.function_call:
        fn_name = message.function_call.name
        # args = json.loads(message["function_call"]["arguments"])
        args = json.loads(message.function_call.arguments)   # dict 타입으로 변경함.
        sig = inspect.signature(globals()[fn_name])   # 함수 인자 중에 orders 있음?
        if 'orders' in sig.parameters: 
            args['orders'] = orders      # orders 를 args 변수에 추가
        print(f'log args\n↪: {args}')
        result = globals()[fn_name](**args)   # 지정한 함수 이름으로 실제 함수 가져와 실행하기
        print(f'log result\n↪: {result}')
        if result is None:
            result = {"result": "No return value"}
        chat_history.append({
            "role": "function",
            "name": fn_name,
            "content": json.dumps(result,ensure_ascii=False),
        })

        final_response =get_followup_chatbot_response(chat_history)
        reply = final_response.choices[0].message.content
    else:
        reply = message.content
    
    # 사용자에게 보낸 응답은 assistant role
    chat_history.append({"role": "assistant", "content": reply})
    print(f'🔄log orders : {orders}')
    return '', chat_history,orders

def get_followup_chatbot_response(chat_history):
    followup_response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=chat_history,
        functions=myfunctions
    )
    return followup_response

def get_first_chatbot_response(chat_history):
  response = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=chat_history,
    functions=myfunctions,
    function_call="auto"  
  )
  return response

# functions (Chat Completions용)
myfunctions = [
    {
        "name": "get_menu",
        "description": "피자 메뉴 목록을 조회합니다.",
        "parameters": {}
    },
    {
        "name": "get_order_price",
        "description": "사용자의 문의에 따라 피자 주문을 위한 가격을 계산합니다..",
        "parameters": {
            "type": "object",
            "properties": {
                "pizza_name": {"type": "string"},
                "pizza_size": {"type": "string"},
                "quantity": {"type": "integer"},
            },
            "required": ["pizza_name", "pizza_size", "quantity"]
        }
    },
    {
        "name": "set_order",
        "description": "피자 주문을 생성하거나 추가합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "pizza_name": {"type": "string"},
                "pizza_size": {"type": "string"},
                "quantity": {"type": "integer"},
                "orders":{"type":"object"}
            },
            "required": ["pizza_name", "pizza_size", "quantity","orders"]
        }
    },
    {
        "name": "complete_order",
        "description": "주문을 완료하고 결제 정보를 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "orders":{"type":"object"}
            },
            "required": ["orders"]
        }
    }
]