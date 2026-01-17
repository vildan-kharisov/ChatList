# Инструкция по публикации ChatList на GitHub

## Подготовка к релизу

### 1. Обновление версии

Перед каждым релизом обновите версию в файле `version.py`:

```python
__version__ = '1.0.1'  # Увеличьте версию
```

### 2. Создание релизных заметок

Создайте файл `RELEASE_NOTES.md` с описанием изменений:

```markdown
## Версия 1.0.1

### Новые возможности
- Добавлена функция X
- Улучшена производительность

### Исправления
- Исправлена ошибка Y
- Улучшена стабильность

### Известные проблемы
- Проблема Z (будет исправлена в следующей версии)
```

### 3. Сборка приложения

Выполните сборку исполняемого файла и инсталлятора:

```powershell
.\build.ps1
.\build-installer.ps1
```

Проверьте, что файлы созданы:
- `dist\ChatList-v1.0.1.exe`
- `installer\ChatList-Setup-v1.0.1.exe`

## Публикация на GitHub Release

### Вариант 1: Ручная публикация (рекомендуется для первого раза)

1. **Перейдите на GitHub** в репозиторий вашего проекта

2. **Создайте новый релиз:**
   - Нажмите на "Releases" в правой панели
   - Или перейдите по адресу: `https://github.com/ВАШ_USERNAME/ВАШ_РЕПОЗИТОРИЙ/releases/new`

3. **Заполните форму релиза:**
   - **Tag version:** `v1.0.1` (соответствует версии в `version.py`)
   - **Release title:** `ChatList v1.0.1`
   - **Description:** Скопируйте содержимое из `RELEASE_NOTES.md`

4. **Загрузите файлы:**
   - Нажмите "Attach binaries by dropping them here or selecting them"
   - Загрузите `installer\ChatList-Setup-v1.0.1.exe`
   - (Опционально) Загрузите `dist\ChatList-v1.0.1.exe` как portable версию

5. **Опубликуйте:**
   - Нажмите "Publish release"

### Вариант 2: Автоматическая публикация через GitHub Actions

1. **Настройте GitHub Actions:**
   - Файл `.github/workflows/release.yml` уже создан
   - При создании тега `v*` автоматически запустится сборка и релиз

2. **Создайте тег и запустите релиз:**
   ```powershell
   git add .
   git commit -m "Release v1.0.1"
   git tag v1.0.1
   git push origin main
   git push origin v1.0.1
   ```

3. **Проверьте статус:**
   - Перейдите в "Actions" на GitHub
   - Дождитесь завершения workflow
   - Релиз будет создан автоматически

## Публикация на GitHub Pages

### 1. Подготовка файлов

1. **Скопируйте HTML-лендинг:**
   - Файл `docs/index.html` уже создан
   - Обновите информацию о версии и изменениях

2. **Обновите версию в лендинге:**
   - Откройте `docs/index.html`
   - Найдите и обновите версию в тексте

### 2. Настройка GitHub Pages

1. **Перейдите в настройки репозитория:**
   - Settings → Pages

2. **Настройте источник:**
   - Source: Deploy from a branch
   - Branch: `main` (или `gh-pages`)
   - Folder: `/docs`

3. **Сохраните настройки**

4. **Проверьте доступность:**
   - Ваш сайт будет доступен по адресу:
   - `https://ВАШ_USERNAME.github.io/ВАШ_РЕПОЗИТОРИЙ/`

### 3. Обновление лендинга

После каждого релиза обновите:
- Версию в `docs/index.html`
- Ссылку на последний релиз
- Список изменений

## Чек-лист перед релизом

- [ ] Версия обновлена в `version.py`
- [ ] Версия обновлена в `docs/index.html`
- [ ] Создан файл `RELEASE_NOTES.md` с описанием изменений
- [ ] Приложение собрано (`.\build.ps1`)
- [ ] Инсталлятор создан (`.\build-installer.ps1`)
- [ ] Приложение протестировано
- [ ] Изменения закоммичены в git
- [ ] Тег создан и запушен (для автоматического релиза)
- [ ] Релиз опубликован на GitHub
- [ ] Лендинг обновлен на GitHub Pages

## Дополнительные рекомендации

### Подпись релизов (опционально)

Для повышения безопасности можно подписать релизы:

```powershell
# Создание GPG ключа (если еще нет)
gpg --full-generate-key

# Экспорт публичного ключа
gpg --armor --export YOUR_EMAIL > public-key.asc

# Добавьте публичный ключ в GitHub: Settings → SSH and GPG keys
```

### Автоматическое обновление версии

Можно создать скрипт для автоматического обновления версии:

```powershell
# update-version.ps1
$newVersion = Read-Host "Введите новую версию (например, 1.0.2)"
(Get-Content version.py) -replace '__version__ = .*', "__version__ = '$newVersion'" | Set-Content version.py
Write-Host "Версия обновлена до $newVersion"
```

## Полезные ссылки

- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)
- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
