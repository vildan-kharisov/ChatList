#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль логирования запросов к API
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any


LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'chatlist.log')


def setup_logger():
    """Настройка логгера"""
    # Создание директории для логов
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # Настройка формата логирования
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Настройка логгера
    logger = logging.getLogger('ChatList')
    logger.setLevel(logging.INFO)
    
    # Очистка существующих обработчиков
    logger.handlers.clear()
    
    # Обработчик для файла
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Обработчик для консоли (опционально)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
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
