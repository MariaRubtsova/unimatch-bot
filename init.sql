CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    username VARCHAR(255),
    first_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS programs (
    id SERIAL PRIMARY KEY,
    university_name TEXT NOT NULL,
    program_name TEXT NOT NULL,
    country TEXT NOT NULL,
    field TEXT NOT NULL,
    degree_type TEXT NOT NULL,
    min_gpa FLOAT NOT NULL DEFAULT 0,
    avg_gpa FLOAT,
    min_ielts FLOAT NOT NULL DEFAULT 0,
    avg_ielts FLOAT,
    tuition_year INTEGER,
    deadline DATE,
    url TEXT,
    requirements_text TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_deadlines (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    deadline DATE NOT NULL,
    notified_30 BOOLEAN NOT NULL DEFAULT false,
    notified_7 BOOLEAN NOT NULL DEFAULT false,
    notified_1 BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS checklist_items (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    program_id INTEGER NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    item_name TEXT NOT NULL,
    hint TEXT,
    is_done BOOLEAN NOT NULL DEFAULT false,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_templates (
    id SERIAL PRIMARY KEY,
    degree_type TEXT NOT NULL,
    item_name TEXT NOT NULL,
    hint TEXT,
    order_index INTEGER NOT NULL DEFAULT 0
);

INSERT INTO document_templates (degree_type, item_name, hint, order_index) VALUES
    ('all', 'Диплом + транскрипт', 'Нотариально заверенный перевод', 1),
    ('all', 'CV / резюме', 'На английском языке, 1–2 страницы', 2),
    ('all', 'IELTS / TOEFL', 'Оригинал сертификата', 3),
    ('all', 'Загранпаспорт', 'Скан всех страниц', 4),
    ('master', 'Мотивационное письмо', 'Statement of purpose, 500–1000 слов', 5),
    ('master', 'Рекомендательное письмо 1', 'От преподавателя или научного руководителя', 6),
    ('master', 'Рекомендательное письмо 2', 'От работодателя или второго преподавателя', 7),
    ('mba', 'Statement of Purpose', 'Фокус на карьерных целях', 5),
    ('mba', 'GMAT / GRE', 'Сертификат теста', 6),
    ('mba', 'Рекомендательное письмо 1', '', 7),
    ('mba', 'Рекомендательное письмо 2', '', 8),
    ('mba', 'Рекомендательное письмо 3', '', 9),
    ('phd', 'Research Proposal', '3–5 страниц с описанием исследования', 5),
    ('phd', 'Мотивационное письмо', '', 6),
    ('phd', 'Рекомендательное письмо 1', '', 7),
    ('phd', 'Рекомендательное письмо 2', '', 8),
    ('phd', 'Публикации (при наличии)', 'Статьи, препринты, конференции', 9)
ON CONFLICT DO NOTHING;

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('001') ON CONFLICT DO NOTHING;
