# Скрипт для обновления версии приложения
# Использование: .\update-version.ps1

param(
    [Parameter(Mandatory=$true)]
    [string]$NewVersion
)

Write-Host "Обновление версии до $NewVersion..." -ForegroundColor Cyan

# Обновление version.py
$versionFile = "version.py"
$content = Get-Content $versionFile -Raw
$content = $content -replace "(__version__ = ')[^']*(')", "`$1$NewVersion`$2"
$content | Set-Content $versionFile -NoNewline
Write-Host "✓ Обновлен $versionFile" -ForegroundColor Green

# Обновление docs/index.html
$htmlFile = "docs/index.html"
if (Test-Path $htmlFile) {
    $htmlContent = Get-Content $htmlFile -Raw
    # Обновление версии в заголовке
    $htmlContent = $htmlContent -replace '(Версия )\d+\.\d+\.\d+', "`$1$NewVersion"
    # Обновление ссылок на файлы
    $htmlContent = $htmlContent -replace '(ChatList-Setup-v)\d+\.\d+\.\d+', "`$1$NewVersion"
    $htmlContent = $htmlContent -replace '(ChatList-v)\d+\.\d+\.\d+', "`$1$NewVersion"
    $htmlContent | Set-Content $htmlFile -NoNewline
    Write-Host "✓ Обновлен $htmlFile" -ForegroundColor Green
}

# Обновление RELEASE_NOTES.md (опционально)
$releaseNotesFile = "RELEASE_NOTES.md"
if (Test-Path $releaseNotesFile) {
    $notesContent = Get-Content $releaseNotesFile -Raw
    $notesContent = $notesContent -replace '(# ChatList v)\d+\.\d+\.\d+', "`$1$NewVersion"
    $notesContent = $notesContent -replace '(ChatList-Setup-v)\d+\.\d+\.\d+', "`$1$NewVersion"
    $notesContent | Set-Content $releaseNotesFile -NoNewline
    Write-Host "✓ Обновлен $releaseNotesFile" -ForegroundColor Green
}

Write-Host "`nВерсия успешно обновлена до $NewVersion!" -ForegroundColor Green
Write-Host "Не забудьте:" -ForegroundColor Yellow
Write-Host "  1. Обновить RELEASE_NOTES.md с описанием изменений" -ForegroundColor White
Write-Host "  2. Обновить ссылки в docs/index.html на ваш репозиторий" -ForegroundColor White
Write-Host "  3. Выполнить сборку: .\build.ps1 и .\build-installer.ps1" -ForegroundColor White
