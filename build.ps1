# Скрипт для создания исполняемого файла
# Использование: .\build.ps1

Write-Host "Установка зависимостей..." -ForegroundColor Green
pip install -r requirements.txt

Write-Host "`nСоздание исполняемого файла..." -ForegroundColor Green
python -m PyInstaller --onefile --windowed --name="ChatList" --icon="app.ico" --hidden-import=dotenv --hidden-import=sqlite3 main.py

Write-Host "`nИсполняемый файл создан в папке dist\ChatList.exe" -ForegroundColor Green
