# Overview
---
This project is a Python-based automated system designed to process emails and classify inquiries using OpenAI's language model (ChatOpenAI) via LangChain integration. The system checks an email inbox for unread emails, extracts the content, classifies the conversation subject, and generates contextually appropriate responses. The project is built with modularity and scalability in mind, enabling integration with various APIs or systems.

TBD: Add the possibility to send emails with the responses of AI model.

## Features
---

### Email Processing:
- Connects to an email inbox via IMAP.
- Fetches unread emails and extracts their content, including headers and body.

### Conversation System:
- Classifies inquiries into predefined categories (process, benefits, details, other).
- Generates responses tailored to the classified category.

### Persistence:
- Saves conversation states in an SQLite database for continuity across sessions.

### Interaction Graph:
- Utilizes a directed graph structure to manage conversation flows and responses dynamically.

### Dynamic Response Generation:
- Integrates OpenAI's language model for generating intelligent, context-aware responses.

## Workflow
---

1. Email Fetching:

    The system connects to the email inbox via IMAP and retrieves unread emails.
    It parses email content, including headers (Subject, From, Message-ID, etc.) and body.

2. Classification:

    The email body is passed to a classification node that uses an LLM to categorize the inquiry.
    Categories are predefined in ConversationSubjects.

3. Response Generation:

    Based on the classified category, the system generates a context-aware response using subject-specific prompt templates.

4. Persistence:

    The conversation state is stored in an SQLite database to maintain continuity and allow multi-turn conversations.
