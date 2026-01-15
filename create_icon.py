from PIL import Image, ImageDraw
import math

def draw_python_logo(draw, center_x, center_y, size):
    """Рисует упрощенный логотип Python в центре."""
    # Размер логотипа относительно размера иконки
    logo_size = int(size * 0.5)
    line_width = max(2, size // 32)
    
    # Цвета Python логотипа
    python_blue = (50, 105, 180)  # Синий цвет Python
    python_yellow = (255, 212, 59)  # Желтый цвет Python
    
    # Рисуем упрощенный логотип Python (две переплетающиеся змеи)
    # Внешний круг для синей змеи (верхняя часть)
    outer_blue_bbox = [
        center_x - logo_size // 2,
        center_y - logo_size // 2,
        center_x + logo_size // 2,
        center_y + logo_size // 2
    ]
    # Рисуем верхнюю половину круга (синяя)
    draw.pieslice(outer_blue_bbox, start=0, end=180, fill=python_blue, outline=python_blue)
    
    # Внешний круг для желтой змеи (нижняя часть)
    outer_yellow_bbox = [
        center_x - logo_size // 2,
        center_y - logo_size // 2,
        center_x + logo_size // 2,
        center_y + logo_size // 2
    ]
    # Рисуем нижнюю половину круга (желтая)
    draw.pieslice(outer_yellow_bbox, start=180, end=360, fill=python_yellow, outline=python_yellow)
    
    # Внутренний круг для создания эффекта переплетения
    inner_size = int(logo_size * 0.6)
    inner_blue_bbox = [
        center_x - inner_size // 2,
        center_y - inner_size // 2,
        center_x + inner_size // 2,
        center_y + inner_size // 2
    ]
    # Внутренняя синяя часть (нижняя половина)
    draw.pieslice(inner_blue_bbox, start=180, end=360, fill=python_blue, outline=python_blue)
    
    inner_yellow_bbox = [
        center_x - inner_size // 2,
        center_y - inner_size // 2,
        center_x + inner_size // 2,
        center_y + inner_size // 2
    ]
    # Внутренняя желтая часть (верхняя половина)
    draw.pieslice(inner_yellow_bbox, start=0, end=180, fill=python_yellow, outline=python_yellow)
    
    # Добавляем точки для глаз (если размер достаточный)
    if size >= 32:
        eye_size = max(2, size // 48)
        # Левая точка (синяя) - на верхней части
        left_eye_x = center_x - logo_size // 4
        left_eye_y = center_y - logo_size // 3
        draw.ellipse([
            left_eye_x - eye_size,
            left_eye_y - eye_size,
            left_eye_x + eye_size,
            left_eye_y + eye_size
        ], fill=(255, 255, 255))  # Белые глаза
        
        # Правая точка (желтая) - на нижней части
        right_eye_x = center_x + logo_size // 4
        right_eye_y = center_y + logo_size // 3
        draw.ellipse([
            right_eye_x - eye_size,
            right_eye_y - eye_size,
            right_eye_x + eye_size,
            right_eye_y + eye_size
        ], fill=(255, 255, 255))  # Белые глаза

def draw_icon(size):
    """Рисует синий круг в красном квадрате с логотипом Python в центре."""
    # Создаем RGB изображение с красным фоном
    img = Image.new("RGB", (size, size), (220, 20, 60))  # Crimson - красный фон
    draw = ImageDraw.Draw(img)
    
    # Вычисляем размеры с отступами (10% от размера с каждой стороны)
    padding = int(size * 0.1)
    circle_size = size - (padding * 2)
    
    # Координаты для круга (центрированный)
    center_x = size // 2
    center_y = size // 2
    radius = circle_size // 2
    
    # Рисуем синий круг
    circle_coords = [
        center_x - radius,
        center_y - radius,
        center_x + radius,
        center_y + radius
    ]
    
    # Синий цвет (DodgerBlue)
    blue_color = (30, 144, 255)
    draw.ellipse(circle_coords, fill=blue_color)
    
    # Рисуем логотип Python в центре
    draw_python_logo(draw, center_x, center_y, size)
    
    return img

# Размеры иконки
sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
icons = [draw_icon(s) for s, _ in sizes]

# Изображения уже в RGB режиме, просто убеждаемся
rgb_icons = []
for icon in icons:
    # Убеждаемся, что изображение в RGB режиме (не палитра)
    if icon.mode != "RGB":
        rgb_img = icon.convert("RGB")
    else:
        rgb_img = icon
    rgb_icons.append(rgb_img)

# Сохранение с явным указанием формата и цветов
# ВАЖНО: Изображения уже в RGB режиме с красным фоном, что гарантирует
# сохранение цветов и избегает автоматической конвертации в градации серого
try:
    rgb_icons[0].save(
        "app.ico",
        format="ICO",
        sizes=sizes,
        append_images=rgb_icons[1:]
    )
    print("[OK] Иконка 'app.ico' создана!")
    print("   Дизайн: синий круг в красном квадрате с логотипом Python в центре")
    print("   Цвета: красный фон (Crimson), синий круг (DodgerBlue), логотип Python")
except Exception as e:
    print(f"[ERROR] Ошибка при сохранении: {e}")
    # Альтернативный способ - сохранить каждое изображение отдельно
    print("Попытка альтернативного метода сохранения...")
    rgb_icons[0].save("app.ico", format="ICO")
    print("[OK] Иконка 'app.ico' создана (только один размер)")