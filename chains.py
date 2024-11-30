import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL")

llm = ChatOpenAI(model=openai_model, api_key=openai_api_key)
subjects = ["process", "benefits", "details", "other"]
inquiry_classification = ChatPromptTemplate.from_messages([
    ("system", """
    You are an office assistant responsible for responding to user messages. 
Based on the provided input, determine the topic of conversation. 
The available topics are:
- HR process details (Keyword: process)
- Benefits (Keyword: benefits)
- Employment details (Keyword: details)
- Other (Keyword: other)

Please respond with a single word keyword that corresponds to the identified topic.
    """),
    MessagesPlaceholder(variable_name="messages"),
])


inquiry_response = ChatPromptTemplate.from_messages([
    ("system", "You are a company AI assistant tasked with drafting responses to customer complaint. "
        "Generate a professional and empathetic response to the customer's complaint."),
    MessagesPlaceholder(variable_name="messages"),
])

generate_classify_inquiry_chain = inquiry_classification | llm
generate_inquiry_response_chain = inquiry_response | llm
