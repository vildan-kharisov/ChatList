#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль отправки HTTP-запросов к API нейросетей
"""

import json
import time
import requests
from typing import Dict, Optional, Any
from models import Model
import db
import logger


def send_to_openai(model: Model, prompt: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Отправить запрос к OpenAI API
    
    Args:
        model: Объект модели
        prompt: Текст промта
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом: {'response_text': str, 'metadata': dict}
    """
    api_key = model.get_api_key()
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Определяем модель API (gpt-4, gpt-3.5-turbo и т.д.)
    # Для простоты используем модель из URL или по умолчанию
    api_model = 'gpt-3.5-turbo'  # Можно сделать настраиваемым
    
    payload = {
        'model': api_model,
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            model.api_url,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        
        elapsed_time = time.time() - start_time
        data = response.json()
        
        response_text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        usage = data.get('usage', {})
        
        metadata = {
            'tokens_used': usage.get('total_tokens', 0),
            'response_time': round(elapsed_time, 2),
            'model_used': api_model
        }
        
        result = {
            'response_text': response_text,
            'metadata': metadata,
            'success': True
        }
        
        # Логирование
        logger.log_request(model.name, prompt, result, elapsed_time)
        
        return result
    except requests.exceptions.RequestException as e:
        result = {
            'response_text': f'Ошибка запроса: {str(e)}',
            'metadata': {},
            'success': False,
            'error': str(e)
        }
        
        # Логирование ошибки
        logger.log_request(model.name, prompt, result)
        
        return result


def send_to_deepseek(model: Model, prompt: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Отправить запрос к DeepSeek API
    
    Args:
        model: Объект модели
        prompt: Текст промта
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом: {'response_text': str, 'metadata': dict}
    """
    api_key = model.get_api_key()
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            model.api_url,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        
        elapsed_time = time.time() - start_time
        data = response.json()
        
        response_text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        usage = data.get('usage', {})
        
        metadata = {
            'tokens_used': usage.get('total_tokens', 0),
            'response_time': round(elapsed_time, 2),
            'model_used': 'deepseek-chat'
        }
        
        result = {
            'response_text': response_text,
            'metadata': metadata,
            'success': True
        }
        
        # Логирование
        logger.log_request(model.name, prompt, result, elapsed_time)
        
        return result
    except requests.exceptions.RequestException as e:
        result = {
            'response_text': f'Ошибка запроса: {str(e)}',
            'metadata': {},
            'success': False,
            'error': str(e)
        }
        
        # Логирование ошибки
        logger.log_request(model.name, prompt, result)
        
        return result


def send_to_groq(model: Model, prompt: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Отправить запрос к Groq API
    
    Args:
        model: Объект модели
        prompt: Текст промта
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом: {'response_text': str, 'metadata': dict}
    """
    api_key = model.get_api_key()
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            model.api_url,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        
        elapsed_time = time.time() - start_time
        data = response.json()
        
        response_text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        metadata = {
            'response_time': round(elapsed_time, 2),
            'model_used': 'groq'
        }
        
        result = {
            'response_text': response_text,
            'metadata': metadata,
            'success': True
        }
        
        # Логирование
        logger.log_request(model.name, prompt, result, elapsed_time)
        
        return result
    except requests.exceptions.RequestException as e:
        result = {
            'response_text': f'Ошибка запроса: {str(e)}',
            'metadata': {},
            'success': False,
            'error': str(e)
        }
        
        # Логирование ошибки
        logger.log_request(model.name, prompt, result)
        
        return result


def send_to_anthropic(model: Model, prompt: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Отправить запрос к Anthropic (Claude) API
    
    Args:
        model: Объект модели
        prompt: Текст промта
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом: {'response_text': str, 'metadata': dict}
    """
    api_key = model.get_api_key()
    headers = {
        'x-api-key': api_key,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': 'claude-3-sonnet-20240229',
        'max_tokens': 1024,
        'messages': [
            {'role': 'user', 'content': prompt}
        ]
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            model.api_url,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        
        elapsed_time = time.time() - start_time
        data = response.json()
        
        response_text = data.get('content', [{}])[0].get('text', '')
        
        metadata = {
            'response_time': round(elapsed_time, 2),
            'model_used': 'claude-3-sonnet-20240229'
        }
        
        result = {
            'response_text': response_text,
            'metadata': metadata,
            'success': True
        }
        
        # Логирование
        logger.log_request(model.name, prompt, result, elapsed_time)
        
        return result
    except requests.exceptions.RequestException as e:
        result = {
            'response_text': f'Ошибка запроса: {str(e)}',
            'metadata': {},
            'success': False,
            'error': str(e)
        }
        
        # Логирование ошибки
        logger.log_request(model.name, prompt, result)
        
        return result


def send_to_openrouter(model: Model, prompt: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Отправить запрос к OpenRouter API
    
    Args:
        model: Объект модели
        prompt: Текст промта
        timeout: Таймаут запроса в секундах
    
    Returns:
        Словарь с ответом: {'response_text': str, 'metadata': dict}
    """
    api_key = model.get_api_key()
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/chatlist',  # Опционально, для статистики
        'X-Title': 'ChatList'  # Опционально, для статистики
    }
    
    # OpenRouter использует модель из URL или можно указать в настройках
    # По умолчанию используем gpt-3.5-turbo, но можно настроить через api_url
    api_model = 'openai/gpt-3.5-turbo'  # Можно извлечь из настроек модели
    
    payload = {
        'model': api_model,
        'messages': [
            {'role': 'user', 'content': prompt}
        ],
        'temperature': 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(
            model.api_url if model.api_url else 'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=timeout
        )
        response.raise_for_status()
        
        elapsed_time = time.time() - start_time
        data = response.json()
        
        response_text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        usage = data.get('usage', {})
        
        metadata = {
            'tokens_used': usage.get('total_tokens', 0),
            'response_time': round(elapsed_time, 2),
            'model_used': data.get('model', api_model),
            'provider': 'openrouter'
        }
        
        result = {
            'response_text': response_text,
            'metadata': metadata,
            'success': True
        }
        
        # Логирование
        logger.log_request(model.name, prompt, result, elapsed_time)
        
        return result
    except requests.exceptions.RequestException as e:
        result = {
            'response_text': f'Ошибка запроса: {str(e)}',
            'metadata': {},
            'success': False,
            'error': str(e)
        }
        
        # Логирование ошибки
        logger.log_request(model.name, prompt, result)
        
        return result


def send_request(model: Model, prompt: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Универсальная функция-роутер для отправки запросов к разным API
    
    Args:
        model: Объект модели
        prompt: Текст промта
        timeout: Таймаут запроса (если None, берется из настроек)
    
    Returns:
        Словарь с ответом: {'response_text': str, 'metadata': dict, 'success': bool}
    """
    if timeout is None:
        timeout_str = db.get_setting('default_timeout', '30')
        timeout = int(timeout_str)
    
    model_type = model.model_type.lower()
    
    if model_type == 'openai':
        return send_to_openai(model, prompt, timeout)
    elif model_type == 'deepseek':
        return send_to_deepseek(model, prompt, timeout)
    elif model_type == 'groq':
        return send_to_groq(model, prompt, timeout)
    elif model_type == 'anthropic':
        return send_to_anthropic(model, prompt, timeout)
    elif model_type == 'openrouter':
        return send_to_openrouter(model, prompt, timeout)
    else:
        return {
            'response_text': f'Неподдерживаемый тип модели: {model_type}',
            'metadata': {},
            'success': False,
            'error': f'Unknown model type: {model_type}'
        }
