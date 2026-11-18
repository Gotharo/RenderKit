# Render de Blender

**Kit flexible para renderizar múltiples archivos `.blend` con configuración independiente por archivo.**

---

## Paso a paso

### 1. Prepara la carpeta del proyecto

Coloca `.blend` y `blender_render_kit` en la misma carpeta:

```text
proyecto\
├── escena.blend
└── blender_render_kit\
```

Archivos con sufijo `_RENDERIZADO` se omiten automáticamente.

### 2. Configura Blender

Abre PowerShell en `proyecto`. El script espera Blender 5.2 en:
```
C:\Program Files\Blender Foundation\Blender 5.2\blender.exe
```

Si está en otra ubicación, edita `$blenderExecutable` en `prepare_render.ps1`.

### 3. Genera configuración (primera vez)

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -GenerateConfigsOnly
```

Crea:
- `<archivo>_render_user.json` (editable)
- `<archivo>_inspection.json` (caché del .blend)

### 4. Edita la configuración JSON

Abre `<archivo>_render_user.json`:

```json
{
  "schema_version": 1,
  "view_layers": [
    {
      "name": "Master",
      "segments": [
        {
          "name": "segment_01",
          "start": 1,
          "end": 120,
          "renderizar": true
        }
      ]
    }
  ]
}
```

**Parámetros:**
- `name`: Nombre exacto del View Layer en Blender
- `start`, `end`: Rango de frames (incluidos)
- `renderizar`: `true`/`false` para incluir/excluir

**Comportamiento:**
- Segmento con `false` → se salta
- View Layer con TODOS `false` → se salta
- View Layer con ALGUNOS `false` → solo renderiza los `true`

### 5. Ejecuta el render

**Primera vez (con validación):**
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor
```

**Siguientes veces (caché automático, sin validación):**
```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor -SkipDryRun
```

Escribe `S` cuando pregunte "¿Ejecutar render ahora?"

Renders se guardan en: `renders\<archivo>\<view_layer>\<segment>\`

**Para pausar:** presiona **Ctrl+C**. Se guarda automáticamente.

### 6. Marca como completado

Cuando el render termine, renombra:
```
escena.blend → escena_RENDERIZADO.blend
```

---

## Pausa y Reanudación

Presionar **Ctrl+C** guarda el estado exacto (ViewLayer, Segment, Frame) en `render_state.json`.

Ejecutar nuevamente resume desde donde se pausó. Si cambias el JSON entre pausa y resume, el script pide confirmación.

Para descartar una pausa:
```powershell
Remove-Item "render_state.json", "render_jobs_backup.json"
```

---

## Opciones de ejecución

| Caso | Comando |
|------|---------|
| Config inicial | `-GenerateConfigsOnly` |
| Con validación | `-SkipEditor` |
| Sin validación (después de validar una vez) | `-SkipEditor -SkipDryRun` |

**Caché automático:** Si el `.blend` no cambió, la inspección se salta. Regenera automáticamente si cambias el `.blend`.

---

## Características

✅ Render aislado (1 ViewLayer por frame)  
✅ Pausa/Resume inteligente  
✅ Control granular de segmentos  
✅ Multi-archivo en cola  
✅ Caché automático de inspección  
✅ Frame step respetado  
✅ Formato configurable (EXR, PNG, etc.)

---

## Troubleshooting

### Pausa descartada incorrectamente
```powershell
Remove-Item "render_state.json"
```

### Frame locked "No puedo eliminar"
Cierra el archivo en After Effects u otro programa.

### Restaurar inspección
La inspección se genera automáticamente en cada ejecución. El caché se valida por checksum.
