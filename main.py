from typing import List, Sequence
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import END, MessageGraph
from chains import generate_response_chain, review_complaint_chain


def response_node(state: Sequence[BaseMessage]):
    return generate_response_chain.invoke({"messages": state})


def review_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    res = review_complaint_chain.invoke({"messages": messages})
    return [HumanMessage(content=res.content)]


def should_continue(state: List[BaseMessage]):
    if len(state) > 4:
        return END
    return "RESPOND"


builder = MessageGraph()
builder.add_node("RESPOND", response_node)
builder.add_node("REVIEW", review_node)
builder.set_entry_point("REVIEW")


builder.add_conditional_edges("REVIEW", should_continue)
builder.add_edge("RESPOND", "REVIEW")
graph = builder.compile()


if __name__ == "__main__":
    print("Complaint Response Generator") 
    inputs = HumanMessage(content="""
        Customer Complaint:
        I don’t recognize a charge of $299.99 for ‘TechGadget’ on my statement dated July 15, 2023. 
        I’ve never bought this product and I believe this charge is fraudulent. 
        Please investigate and remove this charge from my account.
    """)
    response = graph.invoke(inputs)
    print(response)
