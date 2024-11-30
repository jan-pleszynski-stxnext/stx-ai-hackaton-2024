from typing import List, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import END, MessageGraph
from chains import generate_inquiry_response_chain, generate_classify_inquiry_chain
from langgraph.checkpoint.memory import MemorySaver

def format_conversation(messages):
    formatted_conversation = []
    for message in messages:
        if isinstance(message, HumanMessage):
            formatted_conversation.append(f"Human:\n{message.content.strip()}")
        elif isinstance(message, AIMessage):
            formatted_conversation.append(f"AI:\n{message.content.strip()}")
    return "\n\n".join(formatted_conversation)


def classify_inquiry_node(state: Sequence[BaseMessage]):
    return generate_classify_inquiry_chain.invoke({"messages": state})


def inquiry_response_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    res = generate_inquiry_response_chain.invoke({"messages": messages})
    return [HumanMessage(content=res.content)]


def no_applicable_response_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    return [HumanMessage(content="Sorry, we don't have any information about that.")]


def should_continue(state: List[BaseMessage]):
    if state and state[-1].content.strip().lower() == "other":
        return "OTHER"
    if len(state) > 2:
        return END

    return "RESPOND"


builder = MessageGraph()
builder.add_node("CLASSIFY", classify_inquiry_node)
builder.add_node("RESPOND", inquiry_response_node)
builder.add_node("OTHER", no_applicable_response_node)
builder.set_entry_point("CLASSIFY")


builder.add_conditional_edges("CLASSIFY", should_continue)
# builder.add_edge("CLASSIFY", "RESPOND")
graph = builder.compile()

checkpointer = MemorySaver()

graph = builder.compile(checkpointer=checkpointer)

if __name__ == "__main__":
    print("Faq Responder")
    inputs = HumanMessage(content="""
        Please tell me if your company has any benefits?
    """)
    response = graph.invoke(inputs, config={"thread_id": 42})
    print(format_conversation(response))
    print("-----------------------")
    print(checkpointer.__dict__)
    print(checkpointer)
    print(checkpointer)

    # second_input = HumanMessage(content="""
    #     "Do you remember what was initial customer complaint?"
    # """)
    # response = graph.invoke(second_input, config={"thread_id": 42})
    # print(format_conversation(response))
