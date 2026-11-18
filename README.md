# Render de Blender - Kit Pro

**Renderiza múltiples archivos `.blend` sin acumulación de ViewLayers. Per-segment Blender resets = renders limpios.**

---

## ⚡ Quick Start

### PASO 1: Carpeta del Proyecto
```
mi_proyecto\
├── archivo_1.blend
├── archivo_2.blend
└── blender_render_kit\
```

### PASO 2: Inspector (Primera vez, UNA SOLA VEZ)

Abre PowerShell en `mi_proyecto` y ejecuta:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -GenerateConfigsOnly
```

**Genera automáticamente:**
- `archivo_1_render_user.json` (editable - configura aquí)
- `archivo_1_inspection.json` (caché del .blend)
- `.archivo_1_inspection_cache.json` (checksum)

**Lo mismo para archivo_2.blend, archivo_3.blend, etc.** (El script detecta todos)

**TIEMPO:** 3-5 min por archivo

---

## 📝 Paso 3: Edita Configuración

Abre cada `*_render_user.json`:

```json
{
  "schema_version": 1,
  "view_layers": [
    {
      "name": "bolas",
      "segments": [
        {
          "name": "segment_01",
          "start": 1696,
          "end": 1700,
          "renderizar": true
        },
        {
          "name": "segment_02",
          "start": 1701,
          "end": 1750,
          "renderizar": true
        }
      ]
    },
    {
      "name": "tapaDEscargaTrommel",
      "segments": [
        {
          "name": "segment_01",
          "start": 1696,
          "end": 1700,
          "renderizar": true
        }
      ]
    }
  ]
}
```

**Parámetros clave:**
- `name`: ViewLayer exacto en Blender
- `start`, `end`: Frame range (incluidos)
- `renderizar`: `true` = incluir, `false` = saltar

---

## 🚀 Paso 4: Render SIN Inspector (Cached)

**La línea de código (copy-paste):**

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor -SkipDryRun
```

**Presiona `S` cuando pregunte "¿Ejecutar render ahora?"**

**Qué ocurre:**
1. ✅ Detecta archivos `.blend`
2. ✅ Verifica caché (Si `.blend` no cambió → inspección saltada ⚡)
3. ✅ Renderiza CADA SEGMENTO con Blender nuevo (sin acumulación)
   - Segmento 1 → Blender limpio → renderiza → cierra
   - Segmento 2 → Blender limpio → renderiza → cierra
   - Segmento 3 → Blender limpio → renderiza → cierra
4. ✅ Guarda renders en: `renders\<archivo>\<viewlayer>\<segment>\`

**TIEMPO:** ⚡ Segundos (caché) + tiempo del render

---

## 🔄 Flujo Completo (Ejemplo Real)

```powershell
# DÍA 1: Inspector (una sola vez)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -GenerateConfigsOnly
# Espera 15 min... archivos JSON creados

# Edita: archivo_1_render_user.json (configura segments)
# Edita: archivo_2_render_user.json (configura segments)

# DÍA 2+: Render sin inspector (siempre esto)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor -SkipDryRun
# Presiona S
# LISTO - renders limpios, sin ViewLayers duplicados
```

---

## 🎯 Características Principales

✅ **Per-Segment Blender Resets** → Cada segmento renderiza con Blender 100% limpio  
✅ **Sin ViewLayers Duplicados** → EXR contiene solo el layer esperado  
✅ **Cache Automático** → Segunda ejecución es rápida (SHA256 checksum)  
✅ **Multi-Archivo** → Renderiza todos los `.blend` en la carpeta  
✅ **Control Granular** → Renderiza/salta segmentos por JSON  
✅ **Pausa/Resume** → Ctrl+C guarda progreso, re-ejecuta continúa  
✅ **Frame Step** → Respetado automáticamente  
✅ **Formato Flexible** → EXR, PNG, etc.

---

## 🧹 Limpiar Caché (Si Necesitas Reinspeccionar)

```powershell
# En mi_proyecto\
Remove-Item ".archivo_1_inspection_cache.json"
Remove-Item "archivo_1_inspection.json" -ErrorAction SilentlyContinue
Remove-Item "blender_render_kit\archivo_1_inspection.json" -ErrorAction SilentlyContinue
Remove-Item "render_state.json" -ErrorAction SilentlyContinue
```

Luego ejecuta inspector nuevamente (se regenera todo).

---

## ⏸️ Pausa y Reanudación

**Pausar durante render:** Presiona **Ctrl+C**  
**Se guarda automáticamente:** `render_state.json` (ViewLayer, Segment, Frame actual)

**Reanudar:** Ejecuta render nuevamente - continúa desde donde pausó

**Descartar pausa:**
```powershell
Remove-Item "render_state.json"
```

---

## 🚨 Troubleshooting

**"Frame locked" error**
- Cierra el archivo en After Effects u otro programa

**Inspección se ejecuta en cada render**
- Limpiar caché (ver sección anterior)

**Segmento renderiza incompleto**
- Verifica `*_render_user.json` - rangos de frames correctos

**Multiple renders del mismo segmento**
- Limpiar `render_state.json`

---

## 📋 Tabla de Referencia

| Situación | Comando | Tiempo |
|-----------|---------|--------|
| **Primera vez (inspector)** | `-GenerateConfigsOnly` | 3-5 min/archivo |
| **Render sin caché** | `-SkipEditor` | 10+ min |
| **Render con caché** | `-SkipEditor -SkipDryRun` | ⚡ Segundos + render |
| **Limpiar todo** | Ver sección "Limpiar Caché" | - |

---

## 🎉 Resultado Esperado

✅ Cada ViewLayer renderiza **limpiamente**  
✅ **CERO ViewLayers duplicados** en EXR  
✅ Renders organizados: `renders\archivo\layer\segment\frames`  
✅ Listo para After Effects
