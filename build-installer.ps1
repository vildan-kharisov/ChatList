# Скрипт для создания инсталлятора с помощью Inno Setup
# Использование: .\build-installer.ps1
# Требования: Inno Setup должен быть установлен
#             Скрипт автоматически найдет Inno Setup или можно указать путь через $env:INNO_SETUP_PATH

# Получение версии из version.py
$version = python -c "import version; print(version.__version__)"
$version = $version.Trim()

Write-Host "Версия приложения: $version" -ForegroundColor Cyan

# Проверка наличия Inno Setup
$innoSetupPath = $null

# Проверка переменной окружения
if ($env:INNO_SETUP_PATH) {
    $innoSetupPath = $env:INNO_SETUP_PATH
    if (-not (Test-Path $innoSetupPath)) {
        Write-Host "Предупреждение: Путь из INNO_SETUP_PATH не найден: $innoSetupPath" -ForegroundColor Yellow
        $innoSetupPath = $null
    }
}

# Поиск Inno Setup в стандартных местах
if (-not $innoSetupPath) {
    $possiblePaths = @(
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
        "C:\Program Files\Inno Setup 5\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles(x86)\Inno Setup 6\ISCC.exe"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $innoSetupPath = $path
            break
        }
    }
}

# Проверка в PATH
if (-not $innoSetupPath) {
    $isccInPath = Get-Command iscc -ErrorAction SilentlyContinue
    if ($isccInPath) {
        $innoSetupPath = $isccInPath.Source
    }
}

# Если все еще не найден
if (-not $innoSetupPath) {
    Write-Host "`nОшибка: Inno Setup не найден!" -ForegroundColor Red
    Write-Host "`nВарианты решения:" -ForegroundColor Yellow
    Write-Host "1. Установите Inno Setup с https://jrsoftware.org/isdl.php" -ForegroundColor White
    Write-Host "2. Укажите путь через переменную окружения:" -ForegroundColor White
    Write-Host "   `$env:INNO_SETUP_PATH = 'C:\Program Files\Inno Setup 6\ISCC.exe'" -ForegroundColor Cyan
    Write-Host "3. Добавьте Inno Setup в PATH системы" -ForegroundColor White
    Write-Host "`nПосле установки запустите скрипт снова." -ForegroundColor Yellow
    exit 1
}

Write-Host "Найден Inno Setup: $innoSetupPath" -ForegroundColor Green

# Проверка наличия собранного exe файла
$exeName = "ChatList-v$version.exe"
$exePath = "dist\$exeName"
if (-not (Test-Path $exePath)) {
    # Пробуем найти ChatList.exe без версии
    $exePath = "dist\ChatList.exe"
    if (-not (Test-Path $exePath)) {
        Write-Host "Ошибка: Исполняемый файл не найден в dist\" -ForegroundColor Red
        Write-Host "Сначала выполните .\build.ps1 для создания исполняемого файла" -ForegroundColor Yellow
        exit 1
    }
    # Переименовываем для соответствия версии
    $newExePath = "dist\$exeName"
    Copy-Item $exePath $newExePath -Force
    Write-Host "Файл переименован в $exeName" -ForegroundColor Green
}

Write-Host "`nСоздание инсталлятора..." -ForegroundColor Green

# Сохранение исходного содержимого setup.iss для восстановления
$originalSetupContent = Get-Content "setup.iss" -Raw

# Обновление версии в setup.iss (замена #define MyAppVersion)
$setupContent = $originalSetupContent
$setupContent = $setupContent -replace '(#define MyAppVersion ")[^"]*(")', "#define MyAppVersion `"$version`""

# Сохранение обновленного файла
$setupContent | Set-Content "setup.iss" -Encoding UTF8 -NoNewline

# Компиляция инсталлятора
& $innoSetupPath "setup.iss"
$compileResult = $LASTEXITCODE

# Восстановление исходного setup.iss
$originalSetupContent | Set-Content "setup.iss" -Encoding UTF8 -NoNewline

if ($compileResult -eq 0) {
    Write-Host "`nИнсталлятор успешно создан в папке installer\ChatList-Setup-v$version.exe" -ForegroundColor Green
} else {
    Write-Host "`nОшибка при создании инсталлятора!" -ForegroundColor Red
    exit 1
}
