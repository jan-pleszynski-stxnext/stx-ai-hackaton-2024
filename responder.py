import os
from enum import StrEnum
from pathlib import Path
from typing import List, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import MessageGraph

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI


load_dotenv()


####### Persistence begin #######


def get_checkpointer():
    return SqliteSaver.from_conn_string("langgraph.db")


####### Persistence end #######


####### Utils begin #######


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


####### Utils end #######


###### LLM begin #######


def get_llm() -> ChatOpenAI:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_model = os.getenv("OPENAI_MODEL")

    return ChatOpenAI(model=openai_model, api_key=openai_api_key)


###### LLM end ########


##### Classification begin #######


def is_subject(message):
    return get_subject(message) in ConversationSubjects


class ConversationSubjects(StrEnum):
    process = "process"
    benefits = "benefits"
    details = "details"
    other = "other"


def classify_inquiry_node(state: Sequence[BaseMessage]):
    """Classify the inquiry into one of the conversation subjects.

    The system prompt for this node asks the LLM to classify the current subject of
    the conversation to one of the ConversationSubjects value.

    The classification works by sending to the LLM the whole conversation state
    without replies from the previous classification nodes. This approach allows the
    user to ask indirect questions about the same subject for example:

    Human: Tell me about the process.

    AI: The process is...

    Human: Tell me more about it.

    AI: More about the process...

    The removal of the previous classification nodes' responses is not necessarily needed,
    but it decreases the noise in the LLM context.
    """

    def get_inquiry_classification_chain() -> ChatPromptTemplate:
        return (
            ChatPromptTemplate.from_messages(
                [
                    ("system", Path("./prompts/classification.txt").read_text()),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
            | get_llm()
        )

    # Filter out responses from previous classification nodes
    state = [msg for msg in state if not is_subject(msg)]
    # Classify the inquiry once again
    return get_inquiry_classification_chain().invoke({"messages": state})


##### Classification end #######


##### Selection begin #######
def select_respond_node(state: List[BaseMessage]):
    """Selects next node to be executed based on the response from the classification node."""
    # Last message in the state should contain the subject
    subject = get_subject(state[-1])
    assert subject in list(ConversationSubjects), f"Invalid subject: {subject}"
    return subject


def no_applicable_response_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
    """Hardcoded response for the case when no applicable response node is found."""
    return [AIMessage(content="Sorry, we don't have any information about that.")]


##### Selection end #######


####### Response begin #######


def inquiry_response_node_factory(subject: str):
    """Factory generating response nodes for each subject.

    Each response node has the same logic which is: 'feed the conversation state to the
    llm and return the response' The system prompt of each response node
    is the knowledge base for the conversation subject. LLM is asked to generate it's
    response based on this knowledge base.
    """

    def get_response_chain_by_subject(subject: str) -> ChatPromptTemplate:
        return (
            ChatPromptTemplate.from_messages(
                [
                    ("system", Path(f"./prompts/{subject}.txt").read_text()),
                    MessagesPlaceholder(variable_name="messages"),
                ]
            )
            | get_llm()
        )

    def inquiry_response_node(messages: Sequence[BaseMessage]) -> List[BaseMessage]:
        # Filter out responses from previous classification nodes
        messages = [msg for msg in messages if not is_subject(msg)]
        res = get_response_chain_by_subject(subject).invoke({"messages": messages})
        return [AIMessage(content=res.content)]

    return inquiry_response_node


####### Response end #######


def build_interaction_graph() -> MessageGraph:
    """Build the interaction graph for the conversation system."""
    builder = MessageGraph()
    builder.add_node("classify", classify_inquiry_node)

    # Build response nodes per subject
    for subject in ConversationSubjects:
        if subject == ConversationSubjects.other:
            builder.add_node(subject, no_applicable_response_node)
        else:
            builder.add_node(subject, inquiry_response_node_factory(subject))

    # Setup relationships between nodes
    builder.set_entry_point("classify")
    builder.add_conditional_edges("classify", select_respond_node)
    return builder


def run(prompt_input: str, thread_id: str, checkpointer: SqliteSaver):
    """Function that abstracts away the conversation system logic and exposes simple
    API for any external system to use. That may be for example email or http api."""
    builder = build_interaction_graph()

    graph = builder.compile(checkpointer=checkpointer)

    inputs = HumanMessage(content=prompt_input)
    return graph.invoke(inputs, config={"thread_id": thread_id})


if __name__ == "__main__":
    with get_checkpointer() as checkpointer:
        print(format_conversation(run("What is the process?", "123", checkpointer)))
