# Схема базы данных ChatList

## Общая информация

База данных: **SQLite**  
Файл БД: `chatlist.db` (создается автоматически при первом запуске)

---

## Таблица: `prompts` (Промты)

Хранит сохраненные пользовательские запросы (промты).

### Структура таблицы

| Поле | Тип | Ограничения | Описание |
|------|-----|--------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор промта |
| `date` | TEXT | NOT NULL | Дата и время создания промта (ISO формат: YYYY-MM-DD HH:MM:SS) |
| `prompt` | TEXT | NOT NULL | Текст промта (запроса к нейросетям) |
| `tags` | TEXT | NULL | Теги для категоризации промтов (через запятую или JSON) |

### Индексы
- `idx_prompts_date` на поле `date` (для быстрого поиска по дате)
- `idx_prompts_tags` на поле `tags` (для поиска по тегам)

### Примеры данных

```sql
id | date                | prompt                    | tags
---|---------------------|---------------------------|------------
1  | 2024-01-15 10:30:00 | Объясни квантовую физику  | physics,education
2  | 2024-01-15 11:00:00 | Напиши код на Python     | programming,code
```

---

## Таблица: `models` (Модели нейросетей)

Хранит информацию о доступных нейросетях и их API-настройках.

### Структура таблицы

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор модели |
| `name` | TEXT | NOT NULL UNIQUE | Название модели (например, "GPT-4", "DeepSeek", "Claude") |
| `api_url` | TEXT | NOT NULL | URL endpoint для API запросов |
| `api_key_env` | TEXT | NOT NULL | Имя переменной окружения, где хранится API-ключ (например, "OPENAI_API_KEY") |
| `model_type` | TEXT | NOT NULL | Тип API провайдера: "openai", "deepseek", "groq", "anthropic" и т.д. |
| `is_active` | INTEGER | NOT NULL DEFAULT 1 | Флаг активности модели (1 - активна, 0 - неактивна) |
| `created_date` | TEXT | NOT NULL | Дата добавления модели |

### Индексы
- `idx_models_name` на поле `name` (уникальность)
- `idx_models_active` на поле `is_active` (для быстрого получения активных моделей)

### Примеры данных

```sql
id | name      | api_url                          | api_key_env      | model_type | is_active | created_date
---|-----------|----------------------------------|------------------|------------|-----------|-------------
1  | GPT-4     | https://api.openai.com/v1/chat  | OPENAI_API_KEY   | openai     | 1         | 2024-01-10
2  | DeepSeek  | https://api.deepseek.com/v1/chat| DEEPSEEK_API_KEY | deepseek   | 1         | 2024-01-10
3  | Claude    | https://api.anthropic.com/v1/... | ANTHROPIC_API_KEY| anthropic  | 0         | 2024-01-11
```

### Примечания
- API-ключи **НЕ** хранятся в БД, только имя переменной окружения
- Фактические ключи должны быть в файле `.env`
- `model_type` используется для выбора правильного формата запроса в `network.py`

---

## Таблица: `results` (Сохраненные результаты)

Хранит результаты запросов к нейросетям, которые пользователь выбрал для сохранения.

### Структура таблицы

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор результата |
| `prompt_id` | INTEGER | NOT NULL | Ссылка на промт из таблицы `prompts` (FOREIGN KEY) |
| `model_id` | INTEGER | NOT NULL | Ссылка на модель из таблицы `models` (FOREIGN KEY) |
| `response_text` | TEXT | NOT NULL | Текст ответа от нейросети |
| `saved_date` | TEXT | NOT NULL | Дата и время сохранения результата (ISO формат) |
| `metadata` | TEXT | NULL | Дополнительные данные в JSON формате (токены, время ответа и т.д.) |

### Внешние ключи (Foreign Keys)
- `prompt_id` → `prompts.id` (ON DELETE CASCADE)
- `model_id` → `models.id` (ON DELETE SET NULL)

### Индексы
- `idx_results_prompt` на поле `prompt_id` (для поиска результатов по промту)
- `idx_results_model` на поле `model_id` (для поиска результатов по модели)
- `idx_results_date` на поле `saved_date` (для сортировки по дате)

### Примеры данных

```sql
id | prompt_id | model_id | response_text              | saved_date           | metadata
---|-----------|----------|---------------------------|----------------------|----------
1  | 1         | 1        | Квантовая физика изучает...| 2024-01-15 10:35:00  | {"tokens": 150}
2  | 1         | 2        | Квантовая механика - это...| 2024-01-15 10:35:05  | {"tokens": 200}
3  | 2         | 1        | Вот пример кода на Python...| 2024-01-15 11:05:00 | {"tokens": 300}
```

---

## Таблица: `settings` (Настройки программы)

Хранит настройки приложения в формате ключ-значение.

### Структура таблицы

| Поле | Тип | Ограничения | Описание |
|------|-----|-------------|----------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Уникальный идентификатор настройки |
| `key` | TEXT | NOT NULL UNIQUE | Ключ настройки |
| `value` | TEXT | NULL | Значение настройки (может быть JSON) |
| `description` | TEXT | NULL | Описание настройки |

### Индексы
- `idx_settings_key` на поле `key` (уникальность и быстрый поиск)

### Примеры данных

```sql
id | key                    | value                    | description
---|------------------------|--------------------------|----------------------------
1  | default_timeout        | 30                       | Таймаут запросов в секундах
2  | max_response_length    | 5000                     | Максимальная длина ответа
3  | auto_save_prompts      | true                     | Автосохранение промтов
4  | theme                  | dark                     | Тема интерфейса
```

### Стандартные настройки
- `default_timeout` - таймаут HTTP-запросов (по умолчанию: 30)
- `max_response_length` - максимальная длина ответа для отображения (по умолчанию: 5000)
- `auto_save_prompts` - автоматически сохранять промты при отправке (по умолчанию: false)
- `theme` - тема интерфейса (по умолчанию: system)

---

## Диаграмма связей

```
prompts (1) ────< (many) results
models  (1) ────< (many) results
settings (standalone)
```

### Описание связей:
- Один промт может иметь множество сохраненных результатов
- Одна модель может иметь множество сохраненных результатов
- Настройки не связаны с другими таблицами

---

## SQL скрипт создания таблиц

```sql
-- Таблица промтов
CREATE TABLE IF NOT EXISTS prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    prompt TEXT NOT NULL,
    tags TEXT
);

CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date);
CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags);

-- Таблица моделей
CREATE TABLE IF NOT EXISTS models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    api_url TEXT NOT NULL,
    api_key_env TEXT NOT NULL,
    model_type TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_date TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);
CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active);

-- Таблица результатов
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    response_text TEXT NOT NULL,
    saved_date TEXT NOT NULL,
    metadata TEXT,
    FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id);
CREATE INDEX IF NOT EXISTS idx_results_model ON results(model_id);
CREATE INDEX IF NOT EXISTS idx_results_date ON results(saved_date);

-- Таблица настроек
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value TEXT,
    description TEXT
);

CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key);

-- Вставка стандартных настроек
INSERT OR IGNORE INTO settings (key, value, description) VALUES
    ('default_timeout', '30', 'Таймаут HTTP-запросов в секундах'),
    ('max_response_length', '5000', 'Максимальная длина ответа для отображения'),
    ('auto_save_prompts', 'false', 'Автоматически сохранять промты при отправке'),
    ('theme', 'system', 'Тема интерфейса');
```

---

## Примечания по реализации

1. **Временная таблица результатов** - не хранится в БД, создается в памяти при каждом запросе и очищается при новом запросе или сохранении.

2. **API-ключи** - хранятся только в файле `.env`, в БД сохраняется только имя переменной окружения.

3. **Даты** - хранятся в текстовом формате ISO 8601 для совместимости и простоты работы.

4. **Метаданные** - поле `metadata` в таблице `results` может содержать JSON с дополнительной информацией (количество токенов, время ответа, модель API и т.д.).

5. **Каскадное удаление** - при удалении промта автоматически удаляются все связанные результаты.

6. **Мягкое удаление моделей** - при удалении модели результаты остаются, но `model_id` устанавливается в NULL (или можно использовать флаг `is_active` для деактивации вместо удаления).
