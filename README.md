# Render de Blender

## Paso a paso

1. **Prepara la carpeta del proyecto.** Coloca el archivo o los archivos `.blend` junto a la
   carpeta completa `blender_render_kit`:

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

2. **Abre PowerShell en `proyecto`.** En el Explorador de archivos, abre esa carpeta y selecciona
   **Abrir en Terminal**. El script espera Blender 5.2 en esta ruta:

   ```text
   C:\Program Files\Blender Foundation\Blender 5.2\blender.exe
   ```

   Si Blender está instalado en otra ubicación, cambia `$blenderExecutable` al inicio de
   `blender_render_kit\prepare_render.ps1`.

3. **Genera solo los JSON para editarlos después.** Ejecuta:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -GenerateConfigsOnly
   ```

   Si hay varios `.blend`, escribe el número del archivo que quieras preparar o `A` para prepararlos
   todos. Se crea un archivo `<nombre_del_blend>_render_user.json` junto a cada `.blend`, con un
   segmento inicial por View Layer que cubre el rango actual de la escena. Este modo no genera
   informes, no abre el editor y no inicia validaciones ni renders. Si el JSON ya existe, no lo
   sobrescribe.

4. **Edita cada JSON.** Ajusta `start` y `end` para definir los fotogramas. Para añadir otro rango,
   agrega un segmento con un nombre distinto. Por ejemplo:

   ```json
   "segments": [
     { "name": "segment_01", "start": 1, "end": 120 },
     { "name": "segment_02", "start": 121, "end": 240 }
   ]
   ```

   Los fotogramas inicial y final están incluidos. Guarda los cambios.

5. **Ejecuta los renders.** Cuando las configuraciones estén listas, ejecuta:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1" -SkipEditor
   ```

   El script valida todos los JSON con un dry-run antes de iniciar la cola. Si todo está correcto,
   presiona Enter o escribe `S` para renderizar; escribe `N` para cancelar. Omite `-SkipEditor` si
   quieres abrir los JSON y revisarlos antes de la validación.

   Los renders se guardan bajo `renders\<nombre_del_blend>\<view_layer>\<segment>\`. Para detener
   el proceso, presiona **Ctrl+C** en la misma ventana de PowerShell.

6. **Marca cada archivo completado.** Solo después de que su render termine correctamente, cambia
   su nombre agregando `_RENDERIZADO` antes de `.blend`. Por ejemplo:

   ```text
   escena.blend -> escena_RENDERIZADO.blend
   ```

   En la siguiente ejecución, el script ignorará ese archivo y procesará los `.blend` nuevos que no
   tengan el sufijo. No agregues el sufijo si el render se canceló o falló.
