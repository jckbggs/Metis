import os
import re
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import RateLimitError
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

MITIGATING_LINK = os.getenv(
    "MITIGATING_LINK",
    "https://sits.northampton.ac.uk/urd/sits.urd/run/siw_lgn"
)
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=MODEL_NAME,
    temperature=0.3
)

WRITER_SYSTEM_PROMPT = """
You are a helpful university support assistant.
Do not invent policy.
Do not guarantee approval.
Be calm, clear, practical, and concise.
Always include the official link exactly as provided.
""".strip()


class MitigatingAgent:
    def __init__(self):
        self.step = "intro"
        self.days_needed: Optional[int] = None

    def reset(self):
        self.step = "intro"
        self.days_needed = None

    def _extract_days(self, text: str) -> Optional[int]:
        match = re.search(r"\b(\d+)\b", text)
        return int(match.group(1)) if match else None

    def _extract_yes_no(self, text: str) -> Optional[bool]:
        text = text.strip().lower()
        if text in {"yes", "y", "yeah", "yep"}:
            return True
        if text in {"no", "n", "nope"}:
            return False
        if "yes" in text:
            return True
        if "no" in text:
            return False
        return None

    def _assess(self, days_needed: int, used_twice: bool) -> dict:
        if days_needed <= 7 and not used_twice:
            return {
                "eligible": True,
                "route": "7_day_self_certification",
                "reason": "The student says they need 7 days or fewer and has not already used self-certification twice this academic year."
            }

        return {
            "eligible": False,
            "route": "formal_mitigating_circumstances",
            "reason": "The student either needs more than 7 days or has already used self-certification twice this academic year."
        }

    def _fallback_reply(self, decision: dict) -> str:
        if decision["eligible"]:
            return (
                "Based on what you told me, you may be eligible to apply for the "
                "7-day self-certification option.\n\n"
                "This is guidance only and not a guarantee of approval.\n\n"
                f"Official link:\n{MITIGATING_LINK}"
            )

        return (
            "Based on what you told me, the 7-day self-certification option may "
            "not apply, so you should check the formal mitigating circumstances process instead.\n\n"
            "This is guidance only and not a guarantee of approval.\n\n"
            f"Official link:\n{MITIGATING_LINK}"
        )

    def _write_reply(self, decision: dict, days_needed: int, used_twice: bool) -> str:
        prompt = f"""
Decision already made by system logic:
- eligible: {decision['eligible']}
- route: {decision['route']}
- days_needed: {days_needed}
- used_self_certification_twice_this_year: {used_twice}
- reason: {decision['reason']}
- official_link: {MITIGATING_LINK}

Write a helpful reply to the student.
""".strip()

        try:
            response = llm.invoke([
                SystemMessage(content=WRITER_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ])
            return response.content
        except RateLimitError:
            return self._fallback_reply(decision)
        except Exception:
            return self._fallback_reply(decision)

    def handle(self, user_input: str) -> str:
        text = user_input.strip().lower()

        if self.step == "intro":
            if text in {"hi", "hello", "hey", "hiya"}:
                return (
                    "Hi. I can help with mitigating circumstances and extension guidance. "
                    "Are you asking about getting extra time for an assignment? Please answer yes or no."
                )

            if "yes" in text or "extension" in text or "mitigating" in text:
                self.step = "days"
                return "How many extra days do you think you need? Please enter a number, like 3, 5, or 10."

            days = self._extract_days(user_input)
            if days is not None and days > 0:
                self.days_needed = days
                self.step = "used_twice"
                return "Have you already used self-certification twice this academic year? Please answer yes or no."

            return (
                "I can help with mitigating circumstances or extension guidance. "
                "Are you asking about extra time for an assignment? Please answer yes or no."
            )

        if self.step == "days":
            days = self._extract_days(user_input)
            if days is None or days <= 0:
                return "How many extra days do you think you need? Please enter a number, like 3, 5, or 10."

            self.days_needed = days
            self.step = "used_twice"
            return "Have you already used self-certification twice this academic year? Please answer yes or no."

        if self.step == "used_twice":
            used_twice = self._extract_yes_no(user_input)
            if used_twice is None:
                return "Please answer yes or no: have you already used self-certification twice this academic year?"

            decision = self._assess(self.days_needed, used_twice)
            reply = self._write_reply(decision, self.days_needed, used_twice)
            self.reset()
            return reply

        self.reset()
        return "I can help with mitigating circumstances or extension guidance."