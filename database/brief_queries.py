from database.database import get_connection


def get_brief_for_user(username: str):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT brief_id,
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
            FROM briefs
            WHERE username = %s
            ORDER BY due_date ASC NULLS LAST
            LIMIT 1
            """,
            (username,)
        )
        return cur.fetchone()


def get_marking_criteria_for_brief(brief_id: int):
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT criteria_name,
                   criteria_description,
                   weight,
                   score_min,
                   score_max
            FROM marking_criteria
            WHERE brief_id = %s
            ORDER BY criteria_id ASC
            """,
            (brief_id,)
        )
        return cur.fetchall()