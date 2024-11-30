from typing import List, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, MessageGraph
from chains import generate_inquiry_response_chain, generate_classify_inquiry_chain, \
    response_chains_by_subject


def is_subject(message):
    return message.content.strip().lower() in ["process", "benefits", "details", "other"]

def get_subject(message):
    return message.content.strip().lower()

def format_conversation(messages):
    formatted_conversation = []
    for message in messages:
        if isinstance(message, HumanMessage):
            formatted_conversation.append(f"Human:\n{message.content.strip()}")
        elif isinstance(message, AIMessage):
            formatted_conversation.append(f"AI:\n{message.content.strip()}")
    return "\n\n".join(formatted_conversation)


def classify_inquiry_node(state: Sequence[BaseMessage]):
    state = [msg for msg in state if not is_subject(msg)]
    return generate_classify_inquiry_chain.invoke({"messages": state})

def inquiry_response_node_factory(subject: str):
    def inquiry_response_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
        res = response_chains_by_subject[subject].invoke({"messages": messages})
        return [AIMessage(content=res.content)]
    return inquiry_response_node


def no_applicable_response_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    return [AIMessage(content="Sorry, we don't have any information about that.")]


def select_respond_node(state: List[BaseMessage]):
    # Last message in the state should contain the subject
    return get_subject(state[-1])


builder = MessageGraph()
builder.add_node("CLASSIFY", classify_inquiry_node)
# Build response nodes per subject
for subject in response_chains_by_subject.keys():
    builder.add_node(subject, inquiry_response_node_factory(subject))

builder.add_node("other", no_applicable_response_node)

builder.set_entry_point("CLASSIFY")
builder.add_conditional_edges("CLASSIFY", select_respond_node)


with SqliteSaver.from_conn_string("langgraph.db") as checkpointer:

    graph = builder.compile(checkpointer=checkpointer)

    inputs = HumanMessage(content="""Scoping session?""")
    response = graph.invoke(inputs, config={"thread_id": 42})
    print(format_conversation(messages=response))
