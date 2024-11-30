from typing import List, Sequence
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, MessageGraph
from chains import generate_inquiry_response_chain, generate_classify_inquiry_chain


def classify_inquiry_node(state: Sequence[BaseMessage]):
    return generate_classify_inquiry_chain.invoke({"messages": state})


def inquiry_response_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    res = generate_inquiry_response_chain.invoke({"messages": messages})
    return [HumanMessage(content=res.content)]


def should_continue(state: List[BaseMessage]):
    if len(state) > 4:
        return END
    return "RESPOND"


builder = MessageGraph()
builder.add_node("CLASSIFY", classify_inquiry_node)
builder.add_node("RESPOND", inquiry_response_node)
builder.set_entry_point("CLASSIFY")


builder.add_conditional_edges("CLASSIFY", should_continue)
builder.add_edge("CLASSIFY", "RESPOND")
graph = builder.compile()


if __name__ == "__main__":
    print("Faq Responder")
    inputs = HumanMessage(content="""
        Customer Complaint:
        Please tell me what benefits can I get in the company?
    """)
    response = graph.invoke(inputs)
    print(response)
