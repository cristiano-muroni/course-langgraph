from langchain.tools import tool
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AnyMessage
from langgraph.graph import StateGraph, START, END
from langchain_google_genai import ChatGoogleGenerativeAI
from IPython.display import Image, display
from typing_extensions import TypedDict, Annotated
import operator
from typing import Literal
import os
from dotenv import load_dotenv

load_dotenv()

# 1. CORREÇÃO: Nome do modelo (use gemini-1.5-flash ou gemini-1.5-pro)
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)


# Define tools
@tool
def multiply(a: int, b: int) -> int:
    """Multiply a and b."""
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide a and b."""
    return a / b


# Augment the LLM with tools
tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


# Define state
class MessagesState(TypedDict):
    # Usamos o add_messages do langgraph ou o operator.add para acumular mensagens
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# Define model node
def llm_call(state: MessagesState):
    # Mantendo a lógica de adicionar o SystemMessage no momento da chamada
    system_prompt = SystemMessage(
        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
    )
    # Chamada ao modelo
    response = model_with_tools.invoke([system_prompt] + state["messages"])

    return {
        "messages": [response],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# Define tool node
def tool_node(state: MessagesState):
    result = []
    # O Gemini coloca as tool_calls na última mensagem
    last_message = state["messages"][-1]

    for tool_call in last_message.tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        # CORREÇÃO: O conteúdo do ToolMessage deve ser STRING
        result.append(
            ToolMessage(content=str(observation), tool_call_id=tool_call["id"])
        )

    return {"messages": result}


# Define end logic
def should_continue(state: MessagesState) -> Literal["tool_node", "__end__"]:
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return END


# Build workflow
agent_builder = StateGraph(MessagesState)

agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue)
agent_builder.add_edge("tool_node", "llm_call")

# Compile
agent = agent_builder.compile()

# Invoke
initial_state = {
    "messages": [HumanMessage(content="10 vezes 200, dividido por 4, quanto é?")],
    "llm_calls": 0,
}
result = agent.invoke(initial_state)

# Print results
for m in result["messages"]:
    m.pretty_print()
