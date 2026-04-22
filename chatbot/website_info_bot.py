import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    temperature=0.3
)

SITE_CONTEXT = """
Metis is a student support website designed to help students understand academic requirements and access support tools.

Main purpose of the website:
- help students understand assignment briefs
- provide guidance about mitigating circumstances
- provide planning support through assignment calendar features
- explain the website and available support options

Core website functions:
- Website Information chatbot: explains what the website is, what pages do, and what support is available
- Assignment Brief Info: helps users understand assignment briefs, requirements, deadlines, AI policy, and marking criteria
- Mitigating Circumstances: gives guidance about extensions, self-certification, and mitigating circumstances
- Assignment Calendar: helps users create assignment plans and calendars
- Login and account features: allow access to personalised features

Supporting / informational pages:
- Home: overview of the website and student support functions
- FAQs: answers common questions
- About Us: explains the purpose of Metis
- Contact Us: allows users to get in touch for support or feedback

Guest users:
- can ask general questions about the website
- can ask general questions about the pages and support options
- cannot access personalised assignment data
- cannot access saved chats or account specific features
- may have a guest chat limit

Logged-in users:
- can use the website information chatbot without a guest limit
- may access personalised features elsewhere in the system

Rules:
- Do not invent personal assignment data.
- Do not pretend a guest is logged in.
- If the user asks for account-specific help, explain that login is required.
- When the user asks about the main functions of the website, focus on the core functions first, not supporting pages.
- FAQs, About Us, Contact Us, and Home should usually be described as supporting or informational pages, not the main functional purpose of the system.
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
- explain the main purpose and core functions of the website
- explain what each page/tab does
- explain what guests can do
- explain what logged-in users can do in general
- greet the user by username only if they are logged in

Instructions for answering:
- If asked about the main functions of the website, prioritise the core student-support functions.
- Only mention FAQs, About Us, Contact Us, and Home as secondary/supporting pages unless the user asks specifically about them.
- Keep answers practical and easy to understand.

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