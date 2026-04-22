from database.database import get_connection

DEMO_BRIEFS = {
    "webdev": {
        "module": "CSY1063 | Web Development",
        "study_level": "undergraduate",
        "module_leader": "Chris Rafferty",
        "weighting": 50.00,
        "word_limit": None,
        "assignment_no": 1,
        "description": "Develop a responsive portfolio website with HTML, CSS, and Git/GitHub management.",
        "ai_policy": "assistive",
        "ai_policy_details": "GenAI may be used in an assistive role but must be acknowledged appropriately.",
        "referencing_style": "Harvard",
        "due_date": "2025-03-16",
        "brief_file_path": "data/briefs/webdev_brief.txt",
        "brief_summary": "Create a responsive portfolio website with required pages, a video demonstration, and GitHub commits.",
        "assignment_type": "coursework",
        "is_group_work": False,
        "is_exam": False,
        "criteria": [
            {
                "criteria_name": "Implementation of pages",
                "criteria_description": "Correct tags, responsive pages, layout, and implementation of required pages.",
                "weight": 30,
                "score_min": 0,
                "score_max": 100,
            },
            {
                "criteria_name": "Responsive design",
                "criteria_description": "Mobile-friendly layout and responsive behaviour.",
                "weight": 20,
                "score_min": 0,
                "score_max": 100,
            },
            {
                "criteria_name": "Validation and code quality",
                "criteria_description": "HTML/CSS validation and code quality.",
                "weight": 20,
                "score_min": 0,
                "score_max": 100,
            },
            {
                "criteria_name": "Site report",
                "criteria_description": "Reflection and technical documentation.",
                "weight": 10,
                "score_min": 0,
                "score_max": 100,
            },
            {
                "criteria_name": "GitHub usage",
                "criteria_description": "Meaningful GitHub commits and version control use.",
                "weight": 15,
                "score_min": 0,
                "score_max": 100,
            },
            {
                "criteria_name": "Video demonstration",
                "criteria_description": "Required video demonstration of the website and decisions.",
                "weight": 5,
                "score_min": 0,
                "score_max": 100,
            },
        ],
    },
    "webprog": {
        "module": "CSY2089 | Web Programming",
        "study_level": "undergraduate",
        "module_leader": "Tom Butler",
        "weighting": 75.00,
        "word_limit": None,
        "assignment_no": 1,
        "description": "Implement a university website with secure administration features and ticketed functionality.",
        "ai_policy": "assistive",
        "ai_policy_details": "AI-assisted code must be documented in comments, including what it does and the prompt used.",
        "referencing_style": None,
        "due_date": "2026-01-22",
        "brief_file_path": "data/briefs/webprog_brief.txt",
        "brief_summary": "Build a university website using the supplied layout and Docker environment, implementing the required tickets.",
        "assignment_type": "coursework",
        "is_group_work": False,
        "is_exam": False,
        "criteria": [
            {
                "criteria_name": "Functionality",
                "criteria_description": "Completion of ticket requirements and working website functionality.",
                "weight": 50,
                "score_min": 0,
                "score_max": 100,
            },
            {
                "criteria_name": "Code quality",
                "criteria_description": "Maintainability, abstraction, separation of concerns, and overall code structure.",
                "weight": 50,
                "score_min": 0,
                "score_max": 100,
            },
        ],
    },
}


def create_demo_brief_for_user(username: str, demo_brief_key: str):
    brief = DEMO_BRIEFS.get(demo_brief_key)
    if not brief:
        return

    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO briefs (
                username,
                module,
                study_level,
                module_leader,
                weighting,
                word_limit,
                assignment_no,
                description,
                ai_policy,
                ai_policy_details,
                referencing_style,
                due_date,
                brief_file_path,
                brief_summary,
                assignment_type,
                is_group_work,
                is_exam
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING brief_id
            """,
            (
                username,
                brief["module"],
                brief["study_level"],
                brief["module_leader"],
                brief["weighting"],
                brief["word_limit"],
                brief["assignment_no"],
                brief["description"],
                brief["ai_policy"],
                brief["ai_policy_details"],
                brief["referencing_style"],
                brief["due_date"],
                brief["brief_file_path"],
                brief["brief_summary"],
                brief["assignment_type"],
                brief["is_group_work"],
                brief["is_exam"],
            ),
        )

        row = cur.fetchone()
        brief_id = row["brief_id"] if isinstance(row, dict) else row[0]

        for criterion in brief["criteria"]:
            cur.execute(
                """
                INSERT INTO marking_criteria (
                    brief_id,
                    criteria_name,
                    criteria_description,
                    weight,
                    score_min,
                    score_max
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    brief_id,
                    criterion["criteria_name"],
                    criterion["criteria_description"],
                    criterion["weight"],
                    criterion["score_min"],
                    criterion["score_max"],
                ),
            )

        conn.commit()