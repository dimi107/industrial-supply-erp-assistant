import os
from dotenv import load_dotenv
from typing import Annotated
from typing_extensions import TypedDict

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are an ERP assistant for a B2B industrial supply company.
You help sales and operations staff answer questions about inventory, customers, and orders.
Use the available tools to look up real data. Be concise and professional.
Always use tool results to back up your answers — do not guess stock levels or order details."""


def build_agent():
    llm = ChatOpenAI(
        model="openai/gpt-4o-mini",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        temperature=0,
    )
    llm_with_tools = llm.bind_tools(ALL_TOOLS)

    class State(TypedDict):
        messages: Annotated[list[BaseMessage], add_messages]

    def call_llm(state: State):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: State):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(State)
    graph.add_node("llm", call_llm)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_continue)
    graph.add_edge("tools", "llm")

    return graph.compile()


agent = build_agent()


def run(user_message: str, history: list[BaseMessage]) -> tuple[str, list[BaseMessage]]:
    from langchain_core.messages import HumanMessage, AIMessage
    new_history = history + [HumanMessage(content=user_message)]
    result = agent.invoke({"messages": new_history})
    reply = result["messages"][-1].content
    updated_history = result["messages"]
    return reply, updated_history
