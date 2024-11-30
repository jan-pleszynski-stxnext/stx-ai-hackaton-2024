import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL")

llm = ChatOpenAI(model=openai_model, api_key=openai_api_key)
review_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a company representative reviewing a customer's complaint. "
        "Analyze the complaint details and provide a thorough assessment."),
    MessagesPlaceholder(variable_name="messages"),
])
response_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a company AI assistant tasked with drafting responses to customer complaint. "
        "Generate a professional and empathetic response to the customer's complaint."),
    MessagesPlaceholder(variable_name="messages"),
])

generate_response_chain = response_prompt | llm
review_complaint_chain = review_prompt | llm
