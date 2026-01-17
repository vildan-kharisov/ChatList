# Скрипт для создания исполняемого файла
# Использование: .\build.ps1

# Импорт версии из version.py
$version = python -c "import version; print(version.__version__)"
$version = $version.Trim()

Write-Host "Версия приложения: $version" -ForegroundColor Cyan
Write-Host "Установка зависимостей..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host "`nСоздание исполняемого файла..." -ForegroundColor Green
$exeName = "ChatList-v$version"
python -m PyInstaller --onefile --windowed --name="$exeName" --icon="app.ico" --hidden-import=dotenv --hidden-import=sqlite3 --hidden-import=version main.py

Write-Host "`nИсполняемый файл создан в папке dist\$exeName.exe" -ForegroundColor Green
