#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль работы с моделями нейросетей
"""

from typing import List, Dict, Optional, Tuple
import db
import config


class Model:
    """Класс для представления модели нейросети"""
    
    def __init__(self, model_data: Dict):
        self.id = model_data.get('id')
        self.name = model_data.get('name')
        self.api_url = model_data.get('api_url')
        self.api_key_env = model_data.get('api_key_env')
        self.model_type = model_data.get('model_type')
        self.is_active = model_data.get('is_active', 1)
        self.created_date = model_data.get('created_date')
    
    def get_api_key(self) -> str:
        """Получить API-ключ из переменных окружения"""
        try:
            return config.get_api_key(self.api_key_env)
        except ValueError as e:
            raise ValueError(f"Ошибка получения API-ключа для модели {self.name}: {e}")
    
    def validate(self) -> Tuple[bool, str]:
        """
        Валидация настроек модели
        
        Returns:
            tuple: (is_valid, error_message)
        """
        if not self.name:
            return False, "Не указано название модели"
        if not self.api_url:
            return False, "Не указан API URL"
        if not self.api_key_env:
            return False, "Не указана переменная окружения для API-ключа"
        if not self.model_type:
            return False, "Не указан тип модели"
        
        # Проверка типа модели
        if not validate_model_type(self.model_type):
            return False, f"Неподдерживаемый тип модели: {self.model_type}"
        
        # Проверка API-ключа
        try:
            api_key = self.get_api_key()
            if not api_key or api_key.strip() == "":
                return False, f"API-ключ не найден или пуст. Проверьте переменную {self.api_key_env} в файле .env.local"
        except ValueError as e:
            return False, str(e)
        
        return True, ""
    
    def to_dict(self) -> Dict:
        """Преобразовать модель в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'api_url': self.api_url,
            'api_key_env': self.api_key_env,
            'model_type': self.model_type,
            'is_active': self.is_active,
            'created_date': self.created_date
        }


def get_active_models() -> List[Model]:
    """Получить список активных моделей"""
    models_data = db.get_active_models()
    return [Model(model_data) for model_data in models_data]


def get_all_models() -> List[Model]:
    """Получить список всех моделей"""
    models_data = db.get_models()
    return [Model(model_data) for model_data in models_data]


def get_model_by_id(model_id: int) -> Optional[Model]:
    """Получить модель по ID"""
    model_data = db.get_model_by_id(model_id)
    if model_data:
        return Model(model_data)
    return None


def create_model(name: str, api_url: str, api_key_env: str, model_type: str, is_active: int = 1) -> Model:
    """Создать новую модель"""
    model_id = db.create_model(name, api_url, api_key_env, model_type, is_active)
    model_data = db.get_model_by_id(model_id)
    return Model(model_data)


def update_model(model_id: int, **kwargs) -> bool:
    """Обновить модель"""
    return db.update_model(model_id, **kwargs)


def delete_model(model_id: int) -> bool:
    """Удалить модель"""
    return db.delete_model(model_id)


def validate_model_type(model_type: str) -> bool:
    """Проверить, поддерживается ли тип модели"""
    supported_types = ['openai', 'deepseek', 'groq', 'anthropic', 'openrouter']
    return model_type.lower() in supported_types
