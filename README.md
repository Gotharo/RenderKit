# Render de Blender

**Kit flexible para renderizar múltiples archivos `.blend` en la misma carpeta con configuración independiente por archivo.**

---

## Paso a paso

### 1. Prepara la carpeta del proyecto

Coloca el archivo o los archivos `.blend` junto a la carpeta completa `blender_render_kit`:

```text
proyecto\
├── escena.blend
├── escena_RENDERIZADO.blend
└── blender_render_kit\
```

Los archivos cuyo nombre termina en `_RENDERIZADO` antes de `.blend` se omiten. Por ejemplo,
`escena_RENDERIZADO.blend` no se prepara ni se renderiza.

Si todavía no tienes la carpeta del kit, clona el repositorio en cualquier ubicación y copia su
carpeta `blender_render_kit` dentro de `proyecto`:

```powershell
git clone https://github.com/Gotharo/RenderKit.git
Copy-Item -Recurse ".\RenderKit\blender_render_kit" "<ruta_de_proyecto>\blender_render_kit"
```

### 2. Configura Blender

Abre PowerShell en `proyecto`. El script espera Blender 5.2 en esta ruta:

```text
C:\Program Files\Blender Foundation\Blender 5.2\blender.exe
```

Si Blender está instalado en otra ubicación, cambia `$blenderExecutable` al inicio de
`blender_render_kit\prepare_render.ps1`.

### 3. Genera los archivos de configuración

Ejecuta (primera vez solamente):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -GenerateConfigsOnly
```

Se crea un archivo `<nombre_del_blend>_render_user.json` junto a cada `.blend`.

### 4. Edita la configuración JSON

Abre `<nombre_del_blend>_render_user.json` y configura los segmentos.

#### Estructura básica:

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

#### Parámetros:

- **`name`** (ViewLayer): Nombre exacto del View Layer en Blender
- **`segments`**: Lista de rangos de fotogramas
  - **`name`**: Nombre único del segmento
  - **`start`**: Frame inicial (incluido)
  - **`end`**: Frame final (incluido)
  - **`renderizar`**: `true` para renderizar, `false` para omitir

#### Comportamiento de exclusión automática:

- Si un **segmento** tiene `"renderizar": false` → se salta ese segmento
- Si un **view layer** tiene TODOS los segmentos con `"renderizar": false` → se salta el entire view layer
- Si un **view layer** tiene ALGUNOS segmentos en true y otros en false → renderiza SOLO los que tienen true

Ejemplo: View Layer con mezcla de segmentos activos/inactivos:

```json
"segments": [
  { "name": "intro", "start": 1, "end": 120, "renderizar": true },
  { "name": "main", "start": 121, "end": 480, "renderizar": false },
  { "name": "outro", "start": 481, "end": 600, "renderizar": true }
]
```
Resultado: Se renderiza **intro** y **outro**, se salta **main**.

Si TODOS los segmentos están en false, el view layer completo se excluye de la cola.

### 5. Ejecuta el renderizado

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor
```

Escribe `S` cuando pregunte "¿Ejecutar render ahora?" y el renderizado inicia.

Los renders se guardan bajo: `renders\<nombre_del_blend>\<view_layer>\<segment>\`

**Para detener:** presiona **Ctrl+C** en PowerShell. El estado se guarda automáticamente.

---

## Pausa y Reanudación de Renders

Cuando presionas **Ctrl+C**, el script guarda el estado exacto (ViewLayer, Segment, Frame) en `render_state.json`.

En la siguiente ejecución:
1. El script detecta automáticamente `render_state.json`
2. Muestra: ViewLayer, Segment, y frame pausado
3. Si cambiaste rangos/segmentos en el JSON, te pide confirmación
4. Continúa desde el frame exacto donde pausaste

**Workflow típico:**
```powershell
# Iniciar render
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor
# ... renders unos frames ...
# Presionar Ctrl+C → se pausa automáticamente

# Editar JSON si necesitas cambios
# Reanimar:
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor
# Script resume desde donde pausó
```

**Si cambias JSON entre pausa y resume:**
- El script detecta rangos modificados
- Te pregunta si continuar o cancelar
- Puedes abortar, ajustar JSON nuevamente, y reintentar

## Workflow rápido (posterior a configuración inicial)

Si ya tienes `render_user.json` editado y no cambió el archivo `.blend`, puedes agilizar:

```powershell
# 1. Ir a la carpeta del proyecto
cd "<ruta_de_proyecto>"

# 2. Copiar kit actualizado (si actualizaste el código)
Copy-Item -Recurse "..\Coding\blender_render_kit" "." -Force

# 3. Ejecutar directamente sin editor ni dry-run
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor
```

Escribe `S` cuando pregunte "¿Ejecutar render ahora?" y el renderizado inicia inmediatamente.

**Solo necesitas hacer inspección/setup si:**
- Primera vez configurando un `.blend` nuevo
- El `.blend` cambió (agregaste/eliminaste View Layers)
- Después de editar `render_user.json` manualmente

### 6. Marca cada archivo como completado

Solo después de que su render termine correctamente, cambia su nombre agregando `_RENDERIZADO` antes de `.blend`:

```text
escena.blend → escena_RENDERIZADO.blend
```

En la siguiente ejecución, el script ignorará ese archivo y procesará los `.blend` nuevos que no
tengan el sufijo. No agregues el sufijo si el render se canceló o falló.

---

## Características principales

✅ **Render per-frame garantizado**: Exactamente 1 ViewLayer por frame
✅ **Pausa/Resume inteligente**: Continúa desde el frame exacto donde pausó
✅ **Cleanup de frames**: Elimina frames existentes antes de sobrescribir
✅ **Control granular**: Habilita/deshabilita segments con `"renderizar": true/false`
✅ **Multi-archivo**: Renderiza múltiples `.blend` en cola
✅ **Colecciones selectivas**: Renderiza solo colecciones específicas por ViewLayer

---

## Troubleshooting

### "El segment en pausa fue eliminado"

**Causa**: Pausaste un render y después eliminaste ese segment del JSON.

**Solución**: 
- Opción A: Restaura el segment en el JSON
- Opción B: Elimina `render_state.json` para descartar la pausa
  ```powershell
  Remove-Item "render_state.json"
  ```

### "Frame pausado está fuera del rango"

**Causa**: Pausaste en frame 50, pero ahora el segment cubre frames 60-120.

**Solución**: 
- Verifica que el rango en JSON sea correcto
- Elimina `render_state.json` y comienza de nuevo si necesitas cambios drásticos

### Limpiar estado de pausa manual

Si necesitas descartar una pausa guardada:

```powershell
Remove-Item "render_state.json"
Remove-Item "render_jobs_backup.json"
```

Luego ejecuta el render normalmente — comenzará desde el inicio.

### After Effects muestra artefactos

**Causa**: Estabas sobrescribiendo frames sobre existentes.

**Solución**: El nuevo sistema limpia automáticamente frames antes de renderizar.

### "No puedo eliminar: archivo locked"

**Causa**: Otro proceso (ej: After Effects) tiene abierto el archivo.

**Solución**: Cierra el archivo en el otro programa y vuelve a intentar.

---

## Notas técnicas

- Cada ViewLayer se renderiza de forma aislada (sin contaminación)
- El estado de pausa se guarda en `render_state.json`
- Frame step (saltos de frames) se respeta automáticamente
- Los archivos se renombran automáticamente con números de frame (0001, 0002, etc.)
- Formato de salida: Configurable en Blender (EXR, PNG, etc.) - el script se adapta automáticamente
