#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль конфигурации и работы с переменными окружения
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env и .env.local файлов
# .env.local имеет приоритет над .env
load_dotenv('.env')  # Сначала загружаем .env
load_dotenv('.env.local', override=True)  # Затем перезаписываем значениями из .env.local


def get_api_key(env_var_name: str) -> str:
    """
    Получить API-ключ по имени переменной окружения
    
    Args:
        env_var_name: Имя переменной окружения (например, "OPENAI_API_KEY")
    
    Returns:
        Значение API-ключа или пустая строка, если не найдено
    
    Raises:
        ValueError: Если переменная окружения не установлена
    """
    api_key = os.getenv(env_var_name)
    if not api_key:
        raise ValueError(f"Переменная окружения {env_var_name} не установлена. Проверьте файл .env")
    return api_key


def get_setting(key: str, default: str = None) -> str:
    """
    Получить значение настройки из переменных окружения
    
    Args:
        key: Ключ настройки
        default: Значение по умолчанию
    
    Returns:
        Значение настройки или default
    """
    return os.getenv(key, default)
