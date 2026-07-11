import os
import json
from typing import Optional, List
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from langchain_classic.agents import AgentExecutor
from langchain_classic.agents import create_react_agent
from datetime import date
import tools as app_tools

load_dotenv()

@tool
def get_obligations(input_str: str = "") -> List[dict]:
    """
    Параметр:
    - input_str: JSON строка с полями status и/или category
      например: '{"status": "active"}' или '{"status": "active", "category": "subscription"}'
      или '{}' для всех обязательств

    Возвращает список обязательств.
    """
    status = None
    category = None

    if input_str and input_str.strip() and input_str.strip() != "{}":
        try:
            params = json.loads(input_str)
            status = params.get("status")
            category = params.get("category")
        except json.JSONDecodeError:
            pass

    return app_tools.get_obligations(status, category)

@tool
def convert_currency(input_str: str = "") -> float:
    """
    Конвертирует сумму из одной валюты в другую по актуальному курсу.
    Параметры:
    - amount: сумма для конвертации (число)
    - from_currency: код исходной валюты (USD, EUR, RUB и т.д.)
    - to_currency: код целевой валюты (USD, EUR, RUB и т.д.)
    Возвращает сконвертированную сумму.
    """
    params = json.loads(input_str)
    amount = float(params["amount"])
    from_currency = params["from_currency"]
    to_currency = params["to_currency"]
    return app_tools.convert_currency(amount, from_currency, to_currency)

REACT_PROMPT = PromptTemplate.from_template("""
Ты — финансовый ассистент, который помогает пользователю анализировать расходы на подписки. 
У тебя есть доступ к следующим инструментам: {tools}
Используй строго следующий формат:
Question: вопрос пользователя, на который нужно ответить
Thought: твоё рассуждение о том, что нужно сделать
Action: название инструмента для вызова (только одно из [{tool_names}])
Action Input: параметры для инструмента в JSON-формате
Observation: результат вызова инструмента
... (этот цикл Thought/Action/Action Input/Observation может повторяться)
Thought: достаточно информации для ответа
Final Answer: окончательный ответ пользователю
Важные правила:
1. Всегда начинай с Thought, даже если уверен в ответе.
2. Используй только предоставленные инструменты, не придумывай свои.
3. Если нужна конвертация валют, вызывай convert_currency для каждой пары отдельно.
4. Для запросов о расходах за период (30 дней, неделя), получи все активные обязательства через get_obligations, затем отфильтруй по дате next_payment_date. Текущая дата: {today}.
5. Для вопроса о самой дорогой категории, сгруппируй обязательства по категориям, конвертируй все суммы в одну валюту (например, RUB), сравни.
6. Если инструмент возвращает ошибку, честно сообщи об этом пользователю. НИКОГДА не выдумывай курсы валют или суммы.
7. В Final Answer округляй суммы до двух знаков после запятой и указывай валюту (₽, $, €).
Question: {input}
{agent_scratchpad}
""")

llm = ChatDeepSeek(model="deepseek-chat", temperature=0, api_key=os.getenv("DEEPSEEK_API_KEY"), max_tokens=2000)

tools = [get_obligations, convert_currency]

agent = create_react_agent(llm, tools, prompt=REACT_PROMPT)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=15,
)

if __name__ == "__main__":
    while True:
        try:
            user_input = input("Вопрос: ")
            if user_input.strip().lower() in ("exit", "выход", "quit"):
                break
            result = agent_executor.invoke({"input": user_input, "today": str(date.today())})
            print("Ответ:", result["output"])

        except Exception as e:
            print(f"Error: {str(e)}")