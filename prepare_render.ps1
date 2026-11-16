param(
    [switch]$SkipEditor,
    [switch]$OverwriteExisting
)

$script:ResultReported = $false
$script:RenderCancelled = $false
$script:RenderStartedAt = $null
$script:CurrentFrameStopwatch = $null
$script:RenderCurrentFrame = $null
$script:RenderFrameInProgress = $false
$script:RenderCompletedFrames = 0
$script:RenderTotalFrames = 0
$script:RenderCompletedFrameSeconds = 0.0
$script:LastFrameSeconds = $null
$blenderExecutable = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
$workingDirectory = (Get-Location).Path
$kitDirectory = Join-Path $workingDirectory "blender_render_kit"
$inspectorPath = Join-Path $kitDirectory "inspect_blend.py"
$renderBatchPath = Join-Path $kitDirectory "render_batch.py"

function Format-RenderDuration {
    param([double]$Seconds)

    $wholeSeconds = [long][math]::Floor([math]::Max(0, $Seconds))
    $hours = [long][math]::Floor($wholeSeconds / 3600)
    $minutes = [int][math]::Floor(($wholeSeconds % 3600) / 60)
    $remainingSeconds = [int]($wholeSeconds % 60)
    return "{0:00}:{1:00}:{2:00}" -f $hours, $minutes, $remainingSeconds
}

function Update-RenderProgress {
    if ($null -eq $script:RenderStartedAt -or $script:RenderTotalFrames -le 0) {
        return
    }

    $now = Get-Date
    $currentFrameSeconds = $script:CurrentFrameStopwatch.Elapsed.TotalSeconds
    $averageFrameSeconds = $null
    $remainingSeconds = $null
    if ($script:RenderCompletedFrames -gt 0) {
        $averageFrameSeconds = (
            $script:RenderCompletedFrameSeconds / $script:RenderCompletedFrames
        )
        if ($script:RenderCompletedFrames -ge $script:RenderTotalFrames) {
            $remainingSeconds = 0.0
        }
        elseif ($script:RenderFrameInProgress) {
            $currentFrameRemaining = [math]::Max(
                0,
                $averageFrameSeconds - $currentFrameSeconds
            )
            $futureFrames = [math]::Max(
                0,
                $script:RenderTotalFrames - $script:RenderCompletedFrames - 1
            )
            $remainingSeconds = $currentFrameRemaining + (
                $futureFrames * $averageFrameSeconds
            )
        }
        else {
            $remainingSeconds = (
                $script:RenderTotalFrames - $script:RenderCompletedFrames
            ) * $averageFrameSeconds
        }
    }

    $lastFrameText = "calculando"
    if ($null -ne $script:LastFrameSeconds) {
        $lastFrameText = Format-RenderDuration $script:LastFrameSeconds
    }
    $averageText = "calculando"
    if ($null -ne $averageFrameSeconds) {
        $averageText = Format-RenderDuration $averageFrameSeconds
    }
    if ($script:RenderFrameInProgress) {
        $currentFrameText = "{0} ({1})" -f (
            $script:RenderCurrentFrame,
            (Format-RenderDuration $currentFrameSeconds)
        )
    }
    elseif ($script:RenderCompletedFrames -eq 0) {
        $currentFrameText = "preparando $(Format-RenderDuration $currentFrameSeconds)"
    }
    else {
        $currentFrameText = "entre fotogramas"
    }
    $remainingText = "calculando"
    $finishText = "calculando"
    if ($null -ne $remainingSeconds) {
        $remainingText = Format-RenderDuration $remainingSeconds
        $finishText = $now.AddSeconds($remainingSeconds).ToString("HH:mm:ss")
    }

    $percentComplete = 100.0 * $script:RenderCompletedFrames / $script:RenderTotalFrames
    if (
        $script:RenderFrameInProgress -and
        $null -ne $averageFrameSeconds -and
        $script:RenderCompletedFrames -lt $script:RenderTotalFrames
    ) {
        $partialFrame = [math]::Min(
            0.99,
            $currentFrameSeconds / $averageFrameSeconds
        )
        $percentComplete = 100.0 * (
            $script:RenderCompletedFrames + $partialFrame
        ) / $script:RenderTotalFrames
    }

    $status = (
        "Hora {0} | ultimo {1} | promedio {2}/fotograma | actual {3} | " +
        "restante ~{4} | fin ~{5}"
    ) -f (
        $now.ToString("HH:mm:ss"),
        $lastFrameText,
        $averageText,
        $currentFrameText,
        $remainingText,
        $finishText
    )
    Write-Progress `
        -Activity ("Render de Blender ({0}/{1})" -f $script:RenderCompletedFrames, $script:RenderTotalFrames) `
        -Status $status `
        -PercentComplete ([int][math]::Min(100, $percentComplete))
}

function Invoke-Blender {
    param([string[]]$Arguments)

    try {
        & $script:BlenderExecutable @Arguments 2>&1 | ForEach-Object {
            $line = $_.ToString()
            $startMatch = [regex]::Match($line, "^RENDER_START\|(\d+)$")
            if ($startMatch.Success) {
                $script:RenderStartedAt = Get-Date
                $script:CurrentFrameStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
                $script:RenderCurrentFrame = $null
                $script:RenderFrameInProgress = $false
                $script:RenderCompletedFrames = 0
                $script:RenderTotalFrames = [int]$startMatch.Groups[1].Value
                $script:RenderCompletedFrameSeconds = 0.0
                $script:LastFrameSeconds = $null
                Update-RenderProgress
            }
            elseif ($line -match "^RENDER_FRAME_START\|(-?\d+)$") {
                $script:RenderCurrentFrame = [int]$Matches[1]
                $script:RenderFrameInProgress = $true
                $script:CurrentFrameStopwatch.Restart()
                Update-RenderProgress
            }
            elseif ($line -eq "RENDER_HEARTBEAT") {
                Update-RenderProgress
            }
            else {
                $progressMatch = [regex]::Match(
                    $line,
                    "^RENDER_PROGRESS\|(\d+)\|(\d+)\|(-?\d+)\|([0-9]+(?:\.[0-9]+)?)\|([0-9]+(?:\.[0-9]+)?)$"
                )
                if ($progressMatch.Success) {
                    $script:RenderCompletedFrames = [int]$progressMatch.Groups[1].Value
                    $script:RenderTotalFrames = [int]$progressMatch.Groups[2].Value
                    $script:LastFrameSeconds = [double]::Parse(
                        $progressMatch.Groups[4].Value,
                        [Globalization.CultureInfo]::InvariantCulture
                    )
                    $script:RenderCompletedFrameSeconds = [double]::Parse(
                        $progressMatch.Groups[5].Value,
                        [Globalization.CultureInfo]::InvariantCulture
                    )
                    $script:CurrentFrameStopwatch.Stop()
                    $script:CurrentFrameStopwatch.Reset()
                    $script:RenderCurrentFrame = $null
                    $script:RenderFrameInProgress = $false
                    Update-RenderProgress
                }
                elseif (
                    $line -match "RESULTADO:|INFORME:|CONFIGURACION:|^View Layer:|Colecciones incluidas:|Colecciones excluidas:|Segmento:|^Plan:|^Warning:|^Will overwrite|^\[[0-9]+/[0-9]+\] Rendering"
                ) {
                    Write-Host $line
                    if ($line -match "RESULTADO: ERROR") {
                        $script:ResultReported = $true
                    }
                    if ($line -match "RESULTADO: CANCELADO") {
                        $script:RenderCancelled = $true
                        $script:ResultReported = $true
                    }
                }
            }
        }
    }
    catch [System.Management.Automation.PipelineStoppedException] {
        $script:RenderCancelled = $true
        throw
    }
    finally {
        $exitCode = $LASTEXITCODE
        Write-Progress -Activity "Render de Blender" -Completed
    }

    if ($exitCode -ne 0) {
        if ($exitCode -eq 130 -or $exitCode -eq -1073741510) {
            $script:RenderCancelled = $true
        }
        throw "Blender termino con codigo $exitCode."
    }
}

try {
    if (-not (Test-Path -LiteralPath $blenderExecutable -PathType Leaf)) {
        throw "No se encontro Blender en: $blenderExecutable"
    }
    if (-not (Test-Path -LiteralPath $inspectorPath -PathType Leaf)) {
        throw "No se encontro inspect_blend.py en: $inspectorPath"
    }
    if (-not (Test-Path -LiteralPath $renderBatchPath -PathType Leaf)) {
        throw "No se encontro render_batch.py en: $renderBatchPath"
    }

    $blendFiles = @(
        Get-ChildItem -LiteralPath $workingDirectory -Filter "*.blend" -File
    )
    if ($blendFiles.Count -eq 0) {
        throw "No se encontro ningun archivo .blend en la carpeta actual."
    }

    if ($blendFiles.Count -eq 1) {
        $blendFile = $blendFiles[0]
        Write-Host "Archivo Blender detectado: $($blendFile.Name)"
    }
    else {
        Write-Host "Hay varios archivos .blend en la carpeta actual:"
        for ($index = 0; $index -lt $blendFiles.Count; $index++) {
            Write-Host ("  {0}. {1}" -f ($index + 1), $blendFiles[$index].Name)
        }

        [int]$selection = 0
        do {
            $answer = Read-Host "Escribe el numero del archivo que quieres preparar"
            $validNumber = [int]::TryParse($answer, [ref]$selection)
        } while (
            -not $validNumber -or
            $selection -lt 1 -or
            $selection -gt $blendFiles.Count
        )
        $blendFile = $blendFiles[$selection - 1]
    }

    $blendPath = $blendFile.FullName
    $userConfigPath = Join-Path $workingDirectory (
        "{0}_render_user.json" -f $blendFile.BaseName
    )

    Write-Host "Inspeccionando el archivo y preparando su configuracion..."
    Invoke-Blender -Arguments @(
        "-b",
        "--factory-startup",
        $blendPath,
        "--python",
        $inspectorPath
    )

    if (-not (Test-Path -LiteralPath $userConfigPath -PathType Leaf)) {
        throw "El inspector no genero la configuracion esperada: $userConfigPath"
    }

    if (-not $SkipEditor) {
        Write-Host "Edita los segmentos y rangos en: $userConfigPath"
        Write-Host "Guarda el archivo y vuelve a PowerShell para continuar."
        Invoke-Item -LiteralPath $userConfigPath
        Read-Host "Presiona Enter cuando hayas terminado de editar"
    }

    try {
        Get-Content -LiteralPath $userConfigPath -Raw |
            ConvertFrom-Json -ErrorAction Stop |
            Out-Null
    }
    catch {
        $script:ResultReported = $true
        Write-Host "RESULTADO: ERROR - El JSON de render no es valido: $($_.Exception.Message)"
        exit 1
    }

    Write-Host "Validando segmentos y colecciones con dry-run..."
    $dryRunArguments = @(
        "-b",
        $blendPath,
        "--python",
        $renderBatchPath,
        "--",
        $userConfigPath,
        "--dry-run"
    )
    Invoke-Blender -Arguments $dryRunArguments

    do {
        $renderAnswer = (Read-Host "Ejecutar render ahora? (S/N; Enter = Si)").Trim().ToUpperInvariant()
        if ($renderAnswer -and @("S", "SI", "N", "NO") -notcontains $renderAnswer) {
            Write-Host "Respuesta no valida. Escribe S o N."
        }
    } while ($renderAnswer -and @("S", "SI", "N", "NO") -notcontains $renderAnswer)

    if (-not $renderAnswer -or $renderAnswer -eq "S" -or $renderAnswer -eq "SI") {
        Write-Host "Confirmado. Iniciando el render..."
        $renderArguments = @(
            "-b",
            $blendPath,
            "--python",
            $renderBatchPath,
            "--",
            $userConfigPath
        )
        Invoke-Blender -Arguments $renderArguments
    }
    else {
        Write-Host "No se inicio ningun render."
    }
}
catch {
    if ($script:RenderCancelled) {
        if (-not $script:ResultReported) {
            Write-Host "RESULTADO: CANCELADO - Interrumpido por Ctrl+C."
        }
        exit 130
    }
    if (-not $script:ResultReported) {
        Write-Host "RESULTADO: ERROR - $($_.Exception.Message)"
    }
    exit 1
}
