import sys

from langchain_core.messages import HumanMessage
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from core.llm_factory import create_llm
from functions.machine_functions import run_hostname, run_df, run_du, run_netstat, run_ifconfig, list_files, read_file


llm = create_llm()
tools = [search_google, read_file, list_files, run_ifconfig, run_netstat, run_du, run_df, run_hostname]
llm = llm.bind_tools(tools)


def call_model(state: MessagesState):
    return {"messages": [llm.invoke(state["messages"])]}


def should_continue(state: MessagesState):
    if state["messages"][-1].tool_calls:
        return "tools"
    return END


workflow = StateGraph(MessagesState)
workflow.add_node("agent", call_model)
workflow.add_node("tools", ToolNode(tools))
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue)
workflow.add_edge("tools", "agent")

app = workflow.compile()


def main():
    print("Simple Agent (type 'quit' to exit)")
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user_input and user_input.lower() in ("quit", "exit"):
            print("See ya!")
            sys.exit(0)
        inputs = {"messages": [HumanMessage(content=user_input)]}
        for output in app.stream(inputs):
            for key, value in output.items():
                print(value["messages"][-1].content)
                print("---")


if __name__ == "__main__":
    main()
