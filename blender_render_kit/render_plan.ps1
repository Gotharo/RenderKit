# Generate and display render plan verification before rendering

function Show-RenderPlan {
    param([array]$RenderItems, [string]$OutputPath)

    $planData = @{
        fecha = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        total_archivos = $RenderItems.Count
        archivos = @()
        resumen = @{
            total_archivos = $RenderItems.Count
            total_segmentos = 0
            total_frames = 0
        }
    }

    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "          PLAN DE RENDER - VERIFICACION" -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host ""

    for ($i = 0; $i -lt $RenderItems.Count; $i++) {
        $item = $RenderItems[$i]
        $configJson = Get-Content $item.ConfigPath -Raw | ConvertFrom-Json

        $archiveData = @{
            archivo = $item.BlendFile.Name
            viewlayers = @()
        }

        Write-Host "Archivo $($i + 1)/$($RenderItems.Count): $($item.BlendFile.Name)" -ForegroundColor Yellow

        $totalSegments = 0
        $totalFrames = 0

        foreach ($vl in $configJson.view_layers) {
            $vlData = @{
                name = $vl.name
                segmentos = @()
                total_frames = 0
            }

            Write-Host "  [+] $($vl.name)" -ForegroundColor Green

            foreach ($seg in $vl.segments) {
                if ($seg.renderizar -ne $false) {
                    $frameCount = $seg.end - $seg.start + 1
                    Write-Host "    |- $($seg.name): frames $($seg.start)-$($seg.end) ($frameCount frames)"

                    $vlData.segmentos += @{
                        name = $seg.name
                        frames = "$($seg.start)-$($seg.end)"
                        count = $frameCount
                    }
                    $vlData.total_frames += $frameCount
                    $totalSegments++
                    $totalFrames += $frameCount
                }
            }

            $archiveData.viewlayers += $vlData
        }

        $planData.archivos += $archiveData
        $planData.resumen.total_segmentos += $totalSegments
        $planData.resumen.total_frames += $totalFrames

        Write-Host ""
    }

    # Save plan JSON
    $planData | ConvertTo-Json -Depth 10 | Set-Content $OutputPath -Encoding UTF8

    Write-Host "RESUMEN:" -ForegroundColor Cyan
    Write-Host " - Total archivos: $($planData.resumen.total_archivos)"
    Write-Host " - Total segmentos: $($planData.resumen.total_segmentos)"
    Write-Host " - Total frames: $($planData.resumen.total_frames)"
    Write-Host " - Archivo de plan guardado: render_plan.json"
    Write-Host ""
}
