import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL")

llm = ChatOpenAI(model=openai_model, api_key=openai_api_key)
subjects = ["process", "benefits", "details", "other"]
inquiry_classification = ChatPromptTemplate.from_messages([
    ("system", Path("./prompts/classification.txt").read_text()
    ),
    MessagesPlaceholder(variable_name="messages"),
])


inquiry_response = ChatPromptTemplate.from_messages([
    ("system", Path("./prompts/benefits.txt").read_text()),
    MessagesPlaceholder(variable_name="messages"),
])

generate_classify_inquiry_chain = inquiry_classification | llm
generate_inquiry_response_chain = inquiry_response | llm
