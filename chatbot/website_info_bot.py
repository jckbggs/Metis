import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    temperature=0.3
)

SITE_CONTEXT = """
Metis is a student support website.

Main pages:
- Home: overview of the website and its student support functions.
- Mitigating Circumstances: guidance about extensions, self-certification, and mitigating circumstances.
- Assignment Brief Info: help understanding assignment briefs and requirements.
- Assignment Calendar: helps users create assignment plans and calendars.
- Assignment Reviewer: intended to review assignments and provide feedback or analysis.
- Login: allows registered users to access personalised features.
- FAQs: answers common questions about the website and support options.
- About Us: explains the purpose of Metis.
- Contact Us: contact page for support or feedback.

Guest users:
- can ask general questions about the website
- can ask general questions about the pages and support options
- cannot access personalised assignment data
- cannot access saved chats or account-specific features
- may have a guest chat limit

Logged-in users:
- can use the website information chatbot without a guest limit
- may access personalised features elsewhere in the system

Rules:
- Do not invent personal assignment data.
- Do not pretend a guest is logged in.
- If the user asks for account-specific help, explain that login is required.
- Be clear, practical, and concise.
""".strip()


class WebsiteInfoBot:
    def reply(self, user_input: str, username: str | None = None, logged_in: bool = False) -> str:
        greeting_context = (
            f"The user is logged in as '{username}'. You may greet them by username."
            if logged_in and username
            else "The user is not logged in."
        )

        system_prompt = f"""
You are the Metis website information chatbot.

Website context:
{SITE_CONTEXT}

Additional context:
{greeting_context}

Your job:
- explain what Metis is
- explain what each page/tab does
- explain what guests can do
- explain what logged-in users can do in general
- greet the user by username only if they are logged in

Rules:
- Do not invent personalised assignment information.
- If asked about account-specific features, explain that login is required unless the user is already logged in.
- Be friendly, clear, and practical.
""".strip()

        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ])
        return response.content