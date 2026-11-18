---
name: double_viewlayer_solution
description: Solved critical issue where multiple viewlayers accumulated in EXR files during sequential renders
metadata:
  type: project
---

# GRAN LOGRO: Solución de ViewLayers Duplicados en Renders Secuenciales

## El Problema Original
Cuando se renderizaban múltiples segmentos secuencialmente:
- **Segmento 1 (bolas)**: EXR contiene solo "bolas" ✓
- **Segmento 2 (tapaDEscargaTrommel)**: EXR contiene "bolas" + "tapaDEscargaTrommel" ✗
- **Segmento 3+**: Seguía acumulando más viewlayers

**Root Cause**: Blender mantiene su estado render en memoria. Las viewlayers activadas/desactivadas persisten entre renders secuenciales, causando que intente renderizar múltiples layers al mismo EXR.

## Fallos y Errores Importantes Aprendidos

### 1. **Error Crítico: Importación de Función Inexistente**
- Intentamos importar `has_more_segments` que no existía
- **Lección**: Siempre verificar que las funciones existan antes de importarlas. Falta de visibilidad del error porque Blender background mode no muestra output.

### 2. **Bug: Rutas de Archivos Inconsistentes**
- `inspect_blend.py` guardaba inspection.json en kit_directory
- `check_inspection_cache.py` buscaba en kit_directory
- Pero `inspection_cache.py` esperaba en blend_path.parent
- **Lección**: Las rutas de archivos deben ser coherentes GLOBALMENTE. Una inconsistencia en un lugar se propaga a todos lados.

### 3. **Error: PowerShell No Detectaba Fin de Rendering**
- PowerShell no sabía si había más segmentos
- Siempre asumía que sí, causando loop infinito
- **Lección**: Necesitamos comunicación explícita entre Python y PowerShell. Mensajes de status claros son críticos.

### 4. **Bug: render_state.json No Se Generaba**
- Solo se generaba al pausar (Ctrl+C), no al completar normalmente
- PowerShell no sabía qué segmento se acababa de completar
- **Lección**: El archivo de estado debe actualizarse en TODOS los casos, no solo en pausas.

## La Solución Final: Per-Segment Blender Resets

### Arquitectura Implementada
```
PowerShell loop:
  ├─ Segmento 1: Blender nuevo → renderiza → cierra
  ├─ Detecta "MAS_SEGMENTOS"
  ├─ Segmento 2: Blender nuevo (LIMPIO) → renderiza → cierra
  ├─ Detecta "MAS_SEGMENTOS"
  └─ Segmento 3: Blender nuevo (LIMPIO) → renderiza → cierra
```

### Componentes Clave

**1. segment_state.py**
- Lee render_state.json
- Calcula cuál es el PRÓXIMO segmento a renderizar
- Filtra jobs para renderizar solo ese

**2. segment_progress.py** (Agregado últimamente)
- Guarda render_state.json DESPUÉS de completar cada segmento
- Permite que próxima ejecución sepa dónde continuar

**3. render_batch.py**
- Filtra jobs (solo próximo segmento)
- Imprime "RENDER_STATUS: MAS_SEGMENTOS" o "TODO_COMPLETO"
- Llama save_segment_completion() al terminar

**4. prepare_render.ps1**
- Loop que re-ejecuta Blender por segmento
- Lee status de Python
- Continúa o para según corresponda

## Lecciones Críticas de Este Proceso

### 1. **Visibilidad de Errores en Blender Headless**
- Blender background mode no muestra output de Python
- Usamos --log-file para capturar mensajes
- **Lección**: Log es crucial en headless rendering

### 2. **Comunicación Entre Procesos**
- PowerShell ↔ Python requiere mensajes explícitos
- Stdout es suficiente si formatos son claros
- **Lección**: Protocolos de comunicación deben ser simples y predecibles

### 3. **Importancia de Mantener Código Existente**
- El usuario enfatizó: "No borres nada, solo agrega módulos"
- **Lección**: En sistemas complejos, agregar > modificar
- Nuevos módulos = riesgo controlado

### 4. **Caché Corrupto es Peor Que No Tener Caché**
- El caché metadata con rutas incorrectas rompió todo
- Hubo que limpiar completamente
- **Lección**: Validar integridad de caché, no solo existencia

## Resultado
✅ Cada segmento renderiza con Blender 100% limpio  
✅ No hay viewlayers duplicados  
✅ Renders se completan correctamente  
✅ Cache de inspección funciona (segunda ejecución es rápida)  
✅ Per-segment execution es "totalmente viable" (~18s overhead para 6 segmentos)

## Commits Importantes
- `5593deb`: Per-segment execution architecture
- `22f8bb6`: Fixed cache directory lookup
- `54b6b54`: Segment completion tracking

**Fecha**: 2026-11-18  
**Duración**: Sesión larga de debugging sistemático  
**Éxito**: TOTAL ✓✓✓
