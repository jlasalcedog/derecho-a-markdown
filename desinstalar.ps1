<#
  Desinstalador: quita "Convertir a Markdown" del menú contextual
  y borra %LOCALAPPDATA%\DerechoAMarkdown. Pregunta si revertir el menú clásico de Windows 11.
#>
$ErrorActionPreference = 'Continue'
$InstallDir = Join-Path $env:LOCALAPPDATA 'DerechoAMarkdown'
$VerbKey    = 'DerechoAMarkdown'
$LegacyVerbKeys = @('MarkItDown')
$LegacyDirs     = @((Join-Path $env:LOCALAPPDATA 'MarkItDownMenu'))
$ClassicClsidKey = 'HKCU\Software\Classes\CLSID\{86ca1aa0-34aa-4e8b-a509-50c905bae2a2}'

Write-Host ""
Write-Host "  Desinstalando Derecho a Markdown..." -ForegroundColor Cyan

$base = 'HKCU:\Software\Classes\SystemFileAssociations'
$n = 0
if (Test-Path $base) {
    Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
        foreach ($nombre in @($VerbKey) + $LegacyVerbKeys) {
            $k = Join-Path $_.PSPath "shell\$nombre"
            if (Test-Path -LiteralPath $k) { Remove-Item -LiteralPath $k -Recurse -Force; $n++ }
        }
    }
}
Write-Host "  [OK] Opción quitada de $n extensiones" -ForegroundColor Green

& reg.exe query $ClassicClsidKey 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    $r = Read-Host "  ¿Volver al menú contextual nuevo de Windows 11? (S/N)"
    if ($r -match '^(s|si|sí|y|yes)$') {
        & reg.exe delete $ClassicClsidKey /f | Out-Null
        Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        if (-not (Get-Process explorer -ErrorAction SilentlyContinue)) { Start-Process explorer.exe }
        Write-Host "  [OK] Menú de Windows 11 restaurado" -ForegroundColor Green
    }
}

foreach ($d in $LegacyDirs) {
    if (Test-Path -LiteralPath $d) { Remove-Item -LiteralPath $d -Recurse -Force -ErrorAction SilentlyContinue }
}

if (Test-Path $InstallDir) {
    # Si este script corre desde la carpeta de instalación, se borra al final vía cmd
    if ($PSScriptRoot -and $PSScriptRoot.StartsWith($InstallDir, [StringComparison]::OrdinalIgnoreCase)) {
        Start-Process cmd.exe -ArgumentList "/c timeout /t 2 >nul & rmdir /s /q `"$InstallDir`"" -WindowStyle Hidden
    } else {
        Remove-Item -LiteralPath $InstallDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  [OK] Carpeta $InstallDir eliminada" -ForegroundColor Green
}
Write-Host ""
Write-Host "  Listo." -ForegroundColor Green
