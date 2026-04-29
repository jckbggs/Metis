-- Optional cleanup for a fresh manual import
DROP TABLE IF EXISTS review_criteria CASCADE;
DROP TABLE IF EXISTS assignment_reviews CASCADE;
DROP TABLE IF EXISTS criteria_grade_bands CASCADE;
DROP TABLE IF EXISTS marking_criteria CASCADE;
DROP TABLE IF EXISTS calendar_progress CASCADE;
DROP TABLE IF EXISTS calendar_entries CASCADE;
DROP TABLE IF EXISTS calendar_plans CASCADE;
DROP TABLE IF EXISTS saved_chats CASCADE;
DROP TABLE IF EXISTS briefs CASCADE;
DROP TABLE IF EXISTS users CASCADE;

DROP TYPE IF EXISTS chat_role_enum CASCADE;
DROP TYPE IF EXISTS ai_policy_enum CASCADE;
DROP TYPE IF EXISTS study_level_enum CASCADE;

-- ============================================================
-- TYPES
-- ============================================================

CREATE TYPE study_level_enum AS ENUM ('undergraduate', 'postgraduate');
CREATE TYPE ai_policy_enum AS ENUM ('none', 'assistive', 'open');
CREATE TYPE chat_role_enum AS ENUM ('user', 'assistant');

-- ============================================================
-- 1. users
-- ============================================================

CREATE TABLE users (
    username VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    dob DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_users PRIMARY KEY (username)
);

-- ============================================================
-- 2. briefs
-- ============================================================

CREATE TABLE briefs (
    brief_id SERIAL,
    username VARCHAR(50),
    module VARCHAR(100) NOT NULL,
    study_level study_level_enum NOT NULL DEFAULT 'undergraduate',
    module_leader VARCHAR(100),
    weighting DECIMAL(5,2),
    word_limit INT,
    assignment_no INT NOT NULL,
    description TEXT,
    ai_policy ai_policy_enum NOT NULL DEFAULT 'assistive',
    referencing_style VARCHAR(50),
    external_component_label VARCHAR(100),
    external_component_weight DECIMAL(5,2),
    start_date DATE,
    due_date DATE NOT NULL,
    feedback_date DATE,
    resit_date DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    brief_file_path TEXT,
    brief_summary TEXT,
    ai_policy_details TEXT,
    assignment_type VARCHAR(100),
    is_group_work BOOLEAN,
    is_exam BOOLEAN,
    is_resit BOOLEAN DEFAULT FALSE,

    CONSTRAINT pk_briefs PRIMARY KEY (brief_id),
    CONSTRAINT fk_b_users FOREIGN KEY (username)
        REFERENCES users(username)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ============================================================
-- 3. marking_criteria
-- ============================================================

CREATE TABLE marking_criteria (
    criteria_id SERIAL,
    brief_id INT,
    criteria_name VARCHAR(100) NOT NULL,
    is_standard SMALLINT NOT NULL DEFAULT 0,
    criteria_description TEXT,
    weight DECIMAL(5,2) NOT NULL,
    score_min DECIMAL(5,2) NOT NULL,
    score_max DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_markingcriteria PRIMARY KEY (criteria_id),
    CONSTRAINT fk_mc_briefs FOREIGN KEY (brief_id)
        REFERENCES briefs(brief_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ============================================================
-- 4. criteria_grade_bands
-- ============================================================

CREATE TABLE criteria_grade_bands (
    band_id SERIAL,
    criteria_id INT,
    label VARCHAR(50) NOT NULL,
    band_min DECIMAL(5,2) NOT NULL,
    band_max DECIMAL(5,2) NOT NULL,
    description TEXT,

    CONSTRAINT pk_bands PRIMARY KEY (band_id),
    CONSTRAINT fk_bands_criteria FOREIGN KEY (criteria_id)
        REFERENCES marking_criteria(criteria_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

-- ============================================================
-- 5. assignment_reviews
-- ============================================================

CREATE TABLE assignment_reviews (
    review_id SERIAL,
    username VARCHAR(50) NOT NULL,
    brief_id INT NOT NULL,
    submitted_text TEXT NOT NULL,
    ai_feedback TEXT NOT NULL,
    strengths TEXT,
    weaknesses TEXT,
    suggested_improvements TEXT,
    final_grade DECIMAL(5,2) NOT NULL,
    grade_label VARCHAR(10),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_assignmentreviews PRIMARY KEY (review_id),
    CONSTRAINT fk_ar_users FOREIGN KEY (username)
        REFERENCES users(username)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_ar_briefs FOREIGN KEY (brief_id)
        REFERENCES briefs(brief_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);

-- ============================================================
-- 6. review_criteria
-- ============================================================

CREATE TABLE review_criteria (
    score_id SERIAL,
    review_id INT,
    criteria_id INT,
    score_awarded DECIMAL(5,2) NOT NULL,
    ai_justification TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_reviewcriteria PRIMARY KEY (score_id),
    CONSTRAINT fk_rc_reviews FOREIGN KEY (review_id)
        REFERENCES assignment_reviews(review_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_rc_markingcriteria FOREIGN KEY (criteria_id)
        REFERENCES marking_criteria(criteria_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ============================================================
-- 7. calendar_plans
-- ============================================================

CREATE TABLE calendar_plans (
    plan_id SERIAL,
    username VARCHAR(50),
    brief_id INT,
    review_id INT,
    plan_summary TEXT,
    alert_threshold INT NOT NULL DEFAULT 20,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_calendarplans PRIMARY KEY (plan_id),
    CONSTRAINT fk_cp_users FOREIGN KEY (username)
        REFERENCES users(username)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_cp_brief FOREIGN KEY (brief_id)
        REFERENCES briefs(brief_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT fk_cp_review FOREIGN KEY (review_id)
        REFERENCES assignment_reviews(review_id)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

-- ============================================================
-- 8. calendar_entries
-- ============================================================

CREATE TABLE calendar_entries (
    entry_id SERIAL,
    plan_id INT NOT NULL,
    work_date DATE NOT NULL,
    task_description TEXT,
    target_percent_complete INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_calendarentries PRIMARY KEY (entry_id),
    CONSTRAINT fk_ce_plan FOREIGN KEY (plan_id)
        REFERENCES calendar_plans(plan_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT chk_target_percent CHECK (target_percent_complete BETWEEN 0 AND 100)
);

-- ============================================================
-- 9. calendar_progress
-- ============================================================

CREATE TABLE calendar_progress (
    progress_id SERIAL,
    entry_id INT NOT NULL,
    username VARCHAR(50),
    actual_percent_complete INT NOT NULL,
    student_notes TEXT,
    alert_triggered SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_calendarprogress PRIMARY KEY (progress_id),
    CONSTRAINT fk_cpr_entry FOREIGN KEY (entry_id)
        REFERENCES calendar_entries(entry_id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT fk_cpr_users FOREIGN KEY (username)
        REFERENCES users(username)
        ON UPDATE CASCADE
        ON DELETE SET NULL,
    CONSTRAINT chk_actual_percent CHECK (actual_percent_complete BETWEEN 0 AND 100)
);

-- ============================================================
-- 10. saved_chats
-- ============================================================

CREATE TABLE saved_chats (
    chat_id SERIAL,
    username VARCHAR(50),
    bot_id VARCHAR(30) NOT NULL,
    conversation_id INT NOT NULL,
    role chat_role_enum NOT NULL,
    message TEXT NOT NULL,
    message_order INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_chats PRIMARY KEY (chat_id),
    CONSTRAINT fk_s_users FOREIGN KEY (username)
        REFERENCES users(username)
        ON UPDATE CASCADE
        ON DELETE SET NULL
);