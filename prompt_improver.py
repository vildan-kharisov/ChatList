#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для улучшения промтов с помощью AI
"""

import json
from typing import Dict, List, Optional, Any
from models import Model
import network


def create_improvement_prompt(original_prompt: str, variant_type: str = "improved") -> str:
    """
    Создание системного промта для улучшения
    
    Args:
        original_prompt: Исходный промт пользователя
        variant_type: Тип варианта: "improved", "reformulated", "code", "analysis", "creative"
    
    Returns:
        Системный промт для отправки в модель
    """
    base_instruction = """Ты - эксперт по улучшению промтов для нейросетей. Твоя задача - улучшить данный промт, сделав его более четким, структурированным и эффективным."""
    
    variant_instructions = {
        "improved": "Улучши данный промт, сделав его более четким, структурированным и эффективным. Верни только улучшенную версию без дополнительных комментариев.",
        "reformulated": "Переформулируй данный промт, сохранив его смысл, но изменив формулировку. Верни только переформулированную версию без дополнительных комментариев.",
        "code": "Адаптируй данный промт для задач программирования и работы с кодом. Сделай его более техническим и точным. Верни только адаптированную версию без дополнительных комментариев.",
        "analysis": "Адаптируй данный промт для аналитических задач. Сделай его более структурированным для получения детального анализа. Верни только адаптированную версию без дополнительных комментариев.",
        "creative": "Адаптируй данный промт для креативных задач. Сделай его более вдохновляющим и открытым для творческих интерпретаций. Верни только адаптированную версию без дополнительных комментариев."
    }
    
    instruction = variant_instructions.get(variant_type, variant_instructions["improved"])
    
    system_prompt = f"""{base_instruction}

{instruction}

Исходный промт:
{original_prompt}

Верни только улучшенную версию промта, без дополнительных объяснений или комментариев."""
    
    return system_prompt


def create_multi_variant_prompt(original_prompt: str) -> str:
    """
    Создание промта для получения нескольких вариантов улучшения
    
    Args:
        original_prompt: Исходный промт пользователя
    
    Returns:
        Системный промт для получения нескольких вариантов
    """
    system_prompt = f"""Ты - эксперт по улучшению промтов для нейросетей. 

Исходный промт:
{original_prompt}

Твоя задача:
1. Создать улучшенную версию промта (более четкую и структурированную)
2. Предложить 2-3 варианта переформулировки, сохраняя смысл
3. При необходимости предложить адаптации для разных типов задач (код, анализ, креатив)

Верни ответ в формате JSON:
{{
    "improved": "улучшенная версия промта",
    "variants": [
        "вариант переформулировки 1",
        "вариант переформулировки 2",
        "вариант переформулировки 3"
    ],
    "code_version": "версия для задач программирования (если применимо)",
    "analysis_version": "версия для аналитических задач (если применимо)",
    "creative_version": "версия для креативных задач (если применимо)"
}}

Верни только JSON, без дополнительных комментариев."""
    
    return system_prompt


def improve_prompt(model: Model, original_prompt: str, variant_type: str = "improved") -> Dict[str, Any]:
    """
    Улучшение промта с помощью указанной модели
    
    Args:
        model: Модель для улучшения промта
        original_prompt: Исходный промт
        variant_type: Тип варианта
    
    Returns:
        Словарь с результатом: {'improved_text': str, 'success': bool, 'error': str}
    """
    try:
        improvement_prompt = create_improvement_prompt(original_prompt, variant_type)
        result = network.send_request(model, improvement_prompt)
        
        if result.get('success', False):
            improved_text = result.get('response_text', '').strip()
            # Убираем возможные кавычки в начале и конце
            if improved_text.startswith('"') and improved_text.endswith('"'):
                improved_text = improved_text[1:-1]
            if improved_text.startswith("'") and improved_text.endswith("'"):
                improved_text = improved_text[1:-1]
            
            return {
                'improved_text': improved_text,
                'success': True
            }
        else:
            return {
                'improved_text': original_prompt,
                'success': False,
                'error': result.get('error', 'Неизвестная ошибка')
            }
    except Exception as e:
        return {
            'improved_text': original_prompt,
            'success': False,
            'error': str(e)
        }


def get_prompt_variants(model: Model, original_prompt: str) -> Dict[str, Any]:
    """
    Получение нескольких вариантов улучшения промта
    
    Args:
        model: Модель для улучшения промта
        original_prompt: Исходный промт
    
    Returns:
        Словарь с вариантами:
        {
            'improved': str,
            'variants': List[str],
            'code_version': Optional[str],
            'analysis_version': Optional[str],
            'creative_version': Optional[str],
            'success': bool,
            'error': Optional[str]
        }
    """
    try:
        multi_prompt = create_multi_variant_prompt(original_prompt)
        result = network.send_request(model, multi_prompt)
        
        if not result.get('success', False):
            return {
                'improved': original_prompt,
                'variants': [],
                'code_version': None,
                'analysis_version': None,
                'creative_version': None,
                'success': False,
                'error': result.get('error', 'Неизвестная ошибка')
            }
        
        response_text = result.get('response_text', '').strip()
        
        # Попытка парсинга JSON
        try:
            # Ищем JSON в ответе (может быть обернут в markdown код блоки)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response_text[json_start:json_end]
                parsed = json.loads(json_text)
                
                return {
                    'improved': parsed.get('improved', original_prompt),
                    'variants': parsed.get('variants', [])[:3],  # Максимум 3 варианта
                    'code_version': parsed.get('code_version'),
                    'analysis_version': parsed.get('analysis_version'),
                    'creative_version': parsed.get('creative_version'),
                    'success': True
                }
        except (json.JSONDecodeError, KeyError):
            pass
        
        # Если JSON не распарсился, пытаемся извлечь варианты из текста
        # Разделяем на строки и ищем улучшенную версию
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        
        improved = original_prompt
        variants = []
        
        # Первая непустая строка - обычно улучшенная версия
        if lines:
            improved = lines[0]
            # Остальные строки - варианты
            variants = lines[1:4] if len(lines) > 1 else []
        
        return {
            'improved': improved,
            'variants': variants[:3],
            'code_version': None,
            'analysis_version': None,
            'creative_version': None,
            'success': True
        }
        
    except Exception as e:
        return {
            'improved': original_prompt,
            'variants': [],
            'code_version': None,
            'analysis_version': None,
            'creative_version': None,
            'success': False,
            'error': str(e)
        }
