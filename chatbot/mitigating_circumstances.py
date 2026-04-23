import json
import os
import re
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

llm = ChatOpenAI(
    api_key=OPENAI_API_KEY,
    model=OPENAI_MODEL,
    temperature=0.2,
)

EXTENSION_TYPES = {"AS", "ES", "DI", "PJ"}
NO_EXTENSION_TYPES = {"EX", "OR", "MC", "TC", "PF", "PR", "PS"}

POLICY_CONTEXT = """
Formal mitigating circumstances rules:
- Extensions must be requested by 23:59 on the original coursework due date.
- Extensions are only for coursework assessment types such as Assignments (AS), Essays (ES), Dissertations (DI), and Individual Projects (PJ).
- Extensions are not normally available for written/oral exams, class based tests, performances, practical skills, or presentations.
- Usual extension length is 7 days; in some cases 14 days may be granted at first opportunity if supported.
- A student may self certify up to two extension requests in an academic year for short term issues; later requests normally need evidence.
- Deferral is for more serious or longer term circumstances and should be requested as soon as possible, no later than 7 days after the assessment date.
- Deferral evidence can be provided later, but must be supplied within 21 days after the original assessment date.
- Unfit to sit applies where the student completed an assessment when they were not fit to do so; apply within 7 days and evidence is required.
- Once a student submits or attends an assessment, they are normally treated as fit to sit unless unfit to sit applies.
- Mitigating circumstances can extend or defer assessment, but do not change marks already awarded.
- For first opportunity assignment type work submitted late without an approved extension, work submitted within 7 days may be capped at a bare pass; after 7 days it may receive non-submission.
""".strip()

GUIDANCE_CONTEXT = """
Student-facing guidance:
- Examples that may count include illness/injury, bereavement, jury service, major family crisis, and severe disruption to personal life.
- Examples that are not normally accepted include planned holidays, moving home, misreading timetables or requirements, computer issues, wrong submission portal, or simply wanting more time to improve the standard of work.
- Supporting statements can help, but should come from appropriate staff or professionals, not family/friends/flatmates.
- If the linked assessment is extension-eligible and the deadline has not passed, extension guidance is usually the first thing to consider.
- If the impact is longer term, or the deadline/assessment has already passed, deferral may be more relevant.
- If the student already submitted or sat while not fit, unfit to sit may be more relevant.
""".strip()


class MitigatingCircumstancesBot:
    def _load_brief_text(self, brief_file_path: str | None) -> str:
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

    def _coerce_date(self, value) -> date | None:
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()

        text = str(value).strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def _extract_assessment_code(self, brief: dict | None, brief_text: str, user_input: str) -> str | None:
        search_sources = []

        if brief:
            search_sources.extend(
                [
                    brief.get("description"),
                    brief.get("brief_summary"),
                    brief.get("assignment_type"),
                ]
            )

        search_sources.append(brief_text)
        search_sources.append(user_input)

        for source in search_sources:
            if not source:
                continue

            match = re.search(r"\b(AS|ES|DI|PJ|EX|OR|MC|TC|PF|PR|PS)\s*\d*\b", str(source), re.IGNORECASE)
            if match:
                return match.group(1).upper()

            # fallback words if exact code is missing
            text = str(source).lower()
            if "exam" in text:
                return "EX"
            if "presentation" in text:
                return "PS"
            if "performance" in text:
                return "PF"
            if "practical" in text:
                return "PR"
            if "test" in text:
                return "TC"
            if "dissertation" in text:
                return "DI"
            if "essay" in text:
                return "ES"
            if "project" in text:
                return "PJ"
            if "assignment" in text or "coursework" in text:
                return "AS"

        return None

    def _timing_state(self, due_date: date | None) -> str:
        if not due_date:
            return "unknown"

        today = date.today()

        if today <= due_date:
            return "before_or_on_due_date"

        days_after = (today - due_date).days
        if days_after <= 7:
            return "within_7_days_after_due_date"

        return "more_than_7_days_after_due_date"

    def _submitted_already(self, user_input: str) -> bool:
        text = user_input.lower()
        keywords = [
            "already submitted",
            "i submitted",
            "i have submitted",
            "handed in",
            "turned in",
            "already handed in",
            "already sat",
            "i sat the exam",
            "i did the presentation",
            "i completed the exam",
        ]
        return any(k in text for k in keywords)

    def _long_term_issue(self, user_input: str) -> bool:
        text = user_input.lower()
        keywords = [
            "ongoing",
            "long term",
            "for weeks",
            "for months",
            "chronic",
            "serious",
            "hospital",
            "mental health crisis",
            "bereavement",
            "family crisis",
        ]
        return any(k in text for k in keywords)

    def _build_rule_flags(self, user_input: str, brief: dict | None, brief_text: str) -> dict:
        assessment_code = self._extract_assessment_code(brief, brief_text, user_input)
        due_date = self._coerce_date(brief.get("due_date")) if brief else None
        timing_state = self._timing_state(due_date)
        submitted_already = self._submitted_already(user_input)
        long_term_issue = self._long_term_issue(user_input)

        extension_allowed = None
        if assessment_code:
            if assessment_code in EXTENSION_TYPES:
                extension_allowed = True
            elif assessment_code in NO_EXTENSION_TYPES:
                extension_allowed = False

        likely_route = "general_guidance"

        if submitted_already:
            likely_route = "unfit_to_sit_or_deferral"
        elif extension_allowed is True and timing_state == "before_or_on_due_date":
            likely_route = "extension"
        elif extension_allowed is True and timing_state == "within_7_days_after_due_date":
            likely_route = "late_submission_or_deferral"
        elif extension_allowed is False:
            likely_route = "deferral_or_local_arrangements"
        elif long_term_issue:
            likely_route = "deferral"
        else:
            likely_route = "general_guidance"

        return {
            "assessment_code": assessment_code,
            "due_date": None if due_date is None else due_date.isoformat(),
            "timing_state": timing_state,
            "submitted_already": submitted_already,
            "long_term_issue_keywords_detected": long_term_issue,
            "extension_allowed_for_assessment_type": extension_allowed,
            "likely_route": likely_route,
        }

    def reply(
        self,
        user_input: str,
        username: str | None = None,
        brief: dict | None = None,
    ) -> str:
        brief_text = self._load_brief_text(brief.get("brief_file_path")) if brief else ""
        brief_context = self._clean_dict(brief) if brief else {}
        rule_flags = self._build_rule_flags(user_input, brief, brief_text)

        user_context = (
            f"The user is logged in as '{username}'."
            if username
            else "The user is not logged in, so only general guidance is available."
        )

        system_prompt = f"""
You are the Metis mitigating circumstances assistant.

{user_context}

Use the following formal rules and student guidance.

Policy summary:
{POLICY_CONTEXT}

Guidance summary:
{GUIDANCE_CONTEXT}

Linked brief data:
{json.dumps(brief_context, indent=2, default=str)}

Linked brief full text:
{brief_text}

Computed rule flags:
{json.dumps(rule_flags, indent=2, default=str)}

Your task:
- Give practical, student friendly guidance based on the policy and the linked assignment when available.
- Use the computed rule flags first.
- If the linked assignment appears to be an extension eligible coursework type, explain that an extension may be possible.
- If the assessment type does not normally allow extensions, say that clearly and point toward deferral or local arrangements where relevant.
- If the user seems to have already submitted or attended, consider fit to sit and unfit to sit guidance.
- If timing suggests late submission within 7 days for first opportunity coursework, explain the capped mark risk carefully.
- If critical information is missing, say what extra information matters.
- Do not claim to make the final university decision.
- Do not say "you are definitely eligible."
- Prefer phrases like "may be possible", "appears more likely", or "based on the policy".
- Do not invent university rules that are not in the provided summaries.

Response style:
- Keep answers short and practical.
- Use 2 to 4 sentences for most replies.
- Keep replies under 90 words unless the user asks for more detail.
- If the user asks a yes/no question, answer yes or no first.
- Do not use numbered lists unless the user asks for steps.
- Do not repeat policy wording unless necessary.
- End with one short next step suggestion only if useful.
""".strip()

        response = llm.invoke(
            [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]
        )
        return response.content