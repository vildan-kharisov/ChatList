#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль логирования запросов к API
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any
import version


def get_log_dir():
    """Получить путь к директории для логов"""
    # Сначала пробуем создать в текущей директории (для разработки)
    local_log_dir = 'logs'
    try:
        if not os.path.exists(local_log_dir):
            os.makedirs(local_log_dir)
        # Проверяем, можем ли мы писать в эту директорию
        test_file = os.path.join(local_log_dir, '.test_write')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            return local_log_dir
        except (PermissionError, OSError):
            pass
    except (PermissionError, OSError):
        pass
    
    # Если не получилось, используем пользовательскую директорию
    appdata_dir = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'ChatList')
    log_dir = os.path.join(appdata_dir, 'logs')
    try:
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        return log_dir
    except Exception:
        # В крайнем случае используем временную директорию
        import tempfile
        return os.path.join(tempfile.gettempdir(), 'ChatList', 'logs')


LOG_DIR = get_log_dir()
LOG_FILE = os.path.join(LOG_DIR, 'chatlist.log')


def setup_logger():
    """Настройка логгера"""
    # Директория уже создана в get_log_dir()
    
    # Настройка формата логирования
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Настройка логгера
    logger = logging.getLogger('ChatList')
    logger.setLevel(logging.INFO)
    
    # Очистка существующих обработчиков
    logger.handlers.clear()
    
    # Обработчик для файла
    try:
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(log_format, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Если не удалось создать файловый обработчик, продолжаем без него
        pass
    
    # Обработчик для консоли (опционально)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Логирование версии при старте (после настройки обработчиков)
    logger.info(f"ChatList v{version.__version__} - Запуск приложения")
    
    return logger


# Глобальный логгер
logger = setup_logger()


def log_request(model_name: str, prompt: str, response: Dict[str, Any], duration: float = None):
    """
    Логирование запроса к API
    
    Args:
        model_name: Название модели
        prompt: Текст промта
        response: Ответ от API
        duration: Время выполнения запроса в секундах
    """
    success = response.get('success', False)
    response_text = response.get('response_text', '')
    error = response.get('error', '')
    metadata = response.get('metadata', {})
    
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'model': model_name,
        'prompt_length': len(prompt),
        'success': success,
        'response_length': len(response_text) if response_text else 0,
        'duration': duration,
        'tokens_used': metadata.get('tokens_used', 0),
        'error': error if not success else None
    }
    
    if success:
        logger.info(f"Запрос к {model_name}: успешно, токенов: {metadata.get('tokens_used', 0)}, "
                   f"время: {duration:.2f}с" if duration else "")
    else:
        logger.error(f"Запрос к {model_name}: ошибка - {error}")
    
    return log_data


def get_logs(limit: int = 100) -> list:
    """
    Получить последние логи из файла
    
    Args:
        limit: Максимальное количество строк
    
    Returns:
        Список строк логов
    """
    if not os.path.exists(LOG_FILE):
        return []
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            return lines[-limit:] if len(lines) > limit else lines
    except Exception as e:
        logger.error(f"Ошибка чтения логов: {e}")
        return []
