import json
import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0.2,
)


class AssignmentBriefBot:
    def _load_brief_text(self, brief_file_path: str) -> str:
        if not brief_file_path:
            return ""

        path = Path(brief_file_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent.parent / brief_file_path

        if not path.exists():
            return ""

        return path.read_text(encoding="utf-8", errors="ignore")

    def _clean_dict(self, data: dict) -> dict:
        return {k: (None if v is None else str(v)) for k, v in data.items()}

    def reply(
        self,
        user_input: str,
        username: str,
        brief: dict | None,
        criteria_rows: list[dict],
    ) -> str:
        if not brief:
            return f"Hi {username}. I could not find an assignment brief linked to your account."

        brief_text = self._load_brief_text(brief.get("brief_file_path", ""))

        brief_context = self._clean_dict(brief)
        criteria_context = [self._clean_dict(row) for row in criteria_rows]

        system_prompt = f"""
You are a helpful assignment brief assistant for the Metis website.

The logged-in user is: {username}

You must answer ONLY using the information below.

Brief database fields:
{json.dumps(brief_context, indent=2, default=str)}

Marking criteria:
{json.dumps(criteria_context, indent=2, default=str)}

Full brief text:
{brief_text}

Rules:
- Use the database fields first for exact facts like deadline, word limit, AI policy, referencing style, and whether the work is group or individual.
- Use the full brief text for broader explanation and summaries.
- Use the marking criteria to explain how the assignment is assessed.
- If is_resit is true, treat the linked brief as a resit or second-opportunity brief.
- If information is missing, say that you could not find it.
- Do not invent details.
- Be clear, natural, and student-friendly.
- Greet the user by username.

Response style:
- Keep answers short and practical.
- Use 2 to 4 sentences for most replies.
- Keep replies under 100 words unless the user asks for more detail.
- If the user asks a direct factual question, answer that fact first.
""".strip()

        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]
        )

        return response.content