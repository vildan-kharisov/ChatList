#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль работы с базой данных SQLite
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any


def get_db_path():
    """Получить путь к базе данных"""
    # Сначала пробуем использовать текущую директорию (для разработки)
    local_db = 'chatlist.db'
    local_db_path = os.path.abspath(local_db)
    
    # Проверяем, можем ли мы писать в текущую директорию
    try:
        # Проверяем права на запись в директории
        test_file = os.path.join(os.path.dirname(local_db_path) or '.', '.test_write_chatlist')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            # Если получилось, используем локальную базу
            return local_db
        except (PermissionError, OSError):
            pass
    except (PermissionError, OSError):
        pass
    
    # Если не получилось, используем пользовательскую директорию
    appdata_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'ChatList')
    try:
        if not os.path.exists(appdata_dir):
            os.makedirs(appdata_dir, exist_ok=True)
        # Проверяем права на запись в пользовательской директории
        test_file = os.path.join(appdata_dir, '.test_write_chatlist')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            db_path = os.path.join(appdata_dir, 'chatlist.db')
            return db_path
        except (PermissionError, OSError):
            pass
    except Exception:
        pass
    
    # В крайнем случае используем временную директорию
    try:
        import tempfile
        temp_dir = os.path.join(tempfile.gettempdir(), 'ChatList')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
        return os.path.join(temp_dir, 'chatlist.db')
    except Exception:
        # Последний вариант - домашняя директория пользователя
        home_dir = os.path.expanduser('~')
        return os.path.join(home_dir, 'chatlist.db')


DB_NAME = get_db_path()


def get_connection():
    """Получить соединение с базой данных"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
    return conn


def init_database():
    """Инициализация базы данных: создание таблиц и индексов"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Таблица промтов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                prompt TEXT NOT NULL,
                tags TEXT
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompts_date ON prompts(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompts_tags ON prompts(tags)')
        
        # Таблица моделей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                api_url TEXT NOT NULL,
                api_key_env TEXT NOT NULL,
                model_type TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_date TEXT NOT NULL
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_models_active ON models(is_active)')
        
        # Таблица результатов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id INTEGER NOT NULL,
                model_id INTEGER NOT NULL,
                response_text TEXT NOT NULL,
                saved_date TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE CASCADE,
                FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE SET NULL
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_prompt ON results(prompt_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_model ON results(model_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_results_date ON results(saved_date)')
        
        # Таблица настроек
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT,
                description TEXT
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_settings_key ON settings(key)')
        
        # Вставка стандартных настроек
        cursor.executemany('''
            INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)
        ''', [
            ('default_timeout', '30', 'Таймаут HTTP-запросов в секундах'),
            ('max_response_length', '5000', 'Максимальная длина ответа для отображения'),
            ('auto_save_prompts', 'false', 'Автоматически сохранять промты при отправке'),
            ('theme', 'system', 'Тема интерфейса')
        ])
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ==================== CRUD операции для prompts ====================

def create_prompt(prompt: str, tags: Optional[str] = None) -> int:
    """Создать новый промт"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO prompts (date, prompt, tags) VALUES (?, ?, ?)
        ''', (date, prompt, tags))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_prompts(search: Optional[str] = None, tags: Optional[str] = None) -> List[Dict]:
    """Получить список промтов с опциональным поиском"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if search:
            cursor.execute('''
                SELECT * FROM prompts 
                WHERE prompt LIKE ? 
                ORDER BY date DESC
            ''', (f'%{search}%',))
        elif tags:
            cursor.execute('''
                SELECT * FROM prompts 
                WHERE tags LIKE ? 
                ORDER BY date DESC
            ''', (f'%{tags}%',))
        else:
            cursor.execute('SELECT * FROM prompts ORDER BY date DESC')
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_prompt_by_id(prompt_id: int) -> Optional[Dict]:
    """Получить промт по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM prompts WHERE id = ?', (prompt_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_prompt(prompt_id: int, prompt: str = None, tags: str = None) -> bool:
    """Обновить промт"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        updates = []
        params = []
        
        if prompt is not None:
            updates.append('prompt = ?')
            params.append(prompt)
        if tags is not None:
            updates.append('tags = ?')
            params.append(tags)
        
        if not updates:
            return False
        
        params.append(prompt_id)
        cursor.execute(f'''
            UPDATE prompts SET {', '.join(updates)} WHERE id = ?
        ''', params)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_prompt(prompt_id: int) -> bool:
    """Удалить промт"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM prompts WHERE id = ?', (prompt_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ==================== CRUD операции для models ====================

def create_model(name: str, api_url: str, api_key_env: str, model_type: str, is_active: int = 1) -> int:
    """Создать новую модель"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        created_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO models (name, api_url, api_key_env, model_type, is_active, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, api_url, api_key_env, model_type, is_active, created_date))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_models() -> List[Dict]:
    """Получить список всех моделей"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM models ORDER BY name')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_active_models() -> List[Dict]:
    """Получить список активных моделей"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM models WHERE is_active = 1 ORDER BY name')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_model_by_id(model_id: int) -> Optional[Dict]:
    """Получить модель по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM models WHERE id = ?', (model_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_model(model_id: int, name: str = None, api_url: str = None, 
                 api_key_env: str = None, model_type: str = None, 
                 is_active: int = None) -> bool:
    """Обновить модель"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        updates = []
        params = []
        
        if name is not None:
            updates.append('name = ?')
            params.append(name)
        if api_url is not None:
            updates.append('api_url = ?')
            params.append(api_url)
        if api_key_env is not None:
            updates.append('api_key_env = ?')
            params.append(api_key_env)
        if model_type is not None:
            updates.append('model_type = ?')
            params.append(model_type)
        if is_active is not None:
            updates.append('is_active = ?')
            params.append(is_active)
        
        if not updates:
            return False
        
        params.append(model_id)
        cursor.execute(f'''
            UPDATE models SET {', '.join(updates)} WHERE id = ?
        ''', params)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_model(model_id: int) -> bool:
    """Удалить модель"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM models WHERE id = ?', (model_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ==================== CRUD операции для results ====================

def save_result(prompt_id: int, model_id: int, response_text: str, metadata: Optional[Dict] = None) -> int:
    """Сохранить результат запроса"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        saved_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        metadata_json = json.dumps(metadata) if metadata else None
        cursor.execute('''
            INSERT INTO results (prompt_id, model_id, response_text, saved_date, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (prompt_id, model_id, response_text, saved_date, metadata_json))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_results(prompt_id: Optional[int] = None, model_id: Optional[int] = None, 
                search: Optional[str] = None) -> List[Dict]:
    """Получить список сохраненных результатов"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = 'SELECT r.*, p.prompt, m.name as model_name FROM results r '
        query += 'LEFT JOIN prompts p ON r.prompt_id = p.id '
        query += 'LEFT JOIN models m ON r.model_id = m.id WHERE 1=1 '
        params = []
        
        if prompt_id:
            query += 'AND r.prompt_id = ? '
            params.append(prompt_id)
        if model_id:
            query += 'AND r.model_id = ? '
            params.append(model_id)
        if search:
            query += 'AND r.response_text LIKE ? '
            params.append(f'%{search}%')
        
        query += 'ORDER BY r.saved_date DESC'
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_result_by_id(result_id: int) -> Optional[Dict]:
    """Получить результат по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT r.*, p.prompt, m.name as model_name 
            FROM results r
            LEFT JOIN prompts p ON r.prompt_id = p.id
            LEFT JOIN models m ON r.model_id = m.id
            WHERE r.id = ?
        ''', (result_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def delete_result(result_id: int) -> bool:
    """Удалить результат"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM results WHERE id = ?', (result_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ==================== Операции для settings ====================

def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Получить значение настройки"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        return row['value'] if row and row['value'] else default
    finally:
        conn.close()


def set_setting(key: str, value: str, description: Optional[str] = None) -> bool:
    """Установить значение настройки"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO settings (key, value, description)
            VALUES (?, ?, ?)
        ''', (key, value, description))
        conn.commit()
        return True
    finally:
        conn.close()


def get_all_settings() -> List[Dict]:
    """Получить все настройки"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM settings ORDER BY key')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
