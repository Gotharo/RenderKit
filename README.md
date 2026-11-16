# Kit de renderizado de Blender

Esta carpeta contiene un conjunto reutilizable de archivos para configurar y ejecutar renders de
Blender en segundo plano, sin interfaz gráfica. Para cada archivo que quieras procesar, copia la
carpeta completa `blender_render_kit` junto al `.blend`. El uso recomendado es el
[flujo guiado desde PowerShell](#flujo-guiado-desde-powershell): detecta el archivo, prepara la
configuración y ejecuta el dry-run con un solo comando. Antes de renderizar, solicita una
confirmación explícita.

Para obtener el kit desde GitHub directamente junto a un archivo `.blend`, clónalo desde la
carpeta del proyecto usando el nombre que espera el script:

```powershell
git clone https://github.com/Gotharo/RenderKit.git blender_render_kit
```

## Archivos

- `render_master.json`: define el comportamiento compartido, la estructura de las carpetas de
  salida y el nombre del archivo de configuración de usuario.
- `render_user.json`: configuración manual alternativa, con los nombres de las View Layers, las
  colecciones que se incluirán y los segmentos de fotogramas.
- `render_batch.py`: valida ambos archivos JSON y renderiza los segmentos configurados.
- `inspect_blend.py`: genera junto al `.blend` un informe `<blend_name>_inspection.json` y una
  configuración editable `<blend_name>_render_user.json`.
- `prepare_render.ps1`: detecta el `.blend`, ejecuta la inspección, abre la configuración para
  editarla, realiza el dry-run y pregunta antes de iniciar un render.

## Configuración maestra

- `schema_version`: versión del formato de configuración; actualmente es `1`.
- `user_config_filename`: nombre del JSON de usuario que se carga desde esta carpeta del kit.
- `scene`: nombre exacto de la escena de Blender, o `null` para usar la escena activa.
- `output_root`: carpeta raíz de los renders. Si la ruta empieza con `//`, se interpreta como
  relativa a la carpeta del archivo `.blend`. La carpeta de salida debe permanecer dentro de la
  carpeta del `.blend`.
- `output_directory_pattern`: patrón de subcarpetas bajo la carpeta raíz. Admite los marcadores
  `{blend_name}`, `{view_layer}` y `{segment}`.
- `filename_pattern`: patrón del nombre de los archivos de salida. Admite los mismos marcadores;
  `####` se sustituye por el número de fotograma.

La estructura de salida predeterminada es:

`renders/<blend_name>/<view_layer>/<segment>/<view_layer>_<segment>_####.<format>`

El formato de imagen se toma del archivo `.blend`, no de ninguno de los dos JSON.
Para cada trabajo, el ejecutor habilita para render únicamente su View Layer y restaura los estados
originales al terminar. Así, `OPEN_EXR_MULTILAYER` conserva los pases de esa View Layer sin incluir
las demás en el mismo EXR. No se usa la opción `Render Single Layer` de la interfaz porque Blender
la ignora al renderizar desde la línea de comandos.

## Configuración de usuario

Cada elemento de `view_layers` contiene:

- `name`: nombre exacto de la View Layer en la escena seleccionada.
- `include_collections` (opcional): nombres o rutas completas de las colecciones que se incluirán.
  Si se omite, se conserva el estado de exclusión guardado para esa View Layer en el `.blend`. Si se
  especifica, las demás colecciones se excluyen. Si hay nombres repetidos, utiliza la ruta completa.
- `segments`: uno o más rangos de render. Cada segmento tiene un `name` único y números de
  fotograma `start` y `end`; ambos extremos están incluidos.

Para añadir otro rango a una View Layer, añade otro segmento con un nombre distinto. Cada segmento
se guarda en su propia carpeta de salida para evitar que sus fotogramas sobrescriban los de otro
segmento. Se permiten rangos solapados, pero el ejecutor los señala durante la validación.

Si una colección incluida está anidada, sus colecciones padre deben permanecer disponibles para que
Blender pueda llegar a ella. Por ello, también podrían incluirse objetos que pertenezcan a esas
colecciones padre.

## Inspección manual (opcional)

Puedes generar un JSON con las escenas, el rango de fotogramas del timeline, los nombres de las
View Layers y el estado de sus colecciones:

1. Copia la carpeta completa `blender_render_kit` junto al `.blend`. La estructura debe quedar así:

   ```text
   carpeta_del_proyecto\
   ├── testing_001.blend
   └── blender_render_kit\
       ├── inspect_blend.py
       ├── prepare_render.ps1
       ├── render_batch.py
       ├── render_master.json
       └── render_user.json
   ```

2. Abre PowerShell en `carpeta_del_proyecto`, la carpeta que contiene tanto el `.blend` como
   `blender_render_kit`. Puedes abrirla en el Explorador de archivos y elegir **Abrir en Terminal**.
   Comprueba la carpeta actual y su contenido:

   ```powershell
   Get-Location
   Get-ChildItem
   ```

3. Asigna la ruta de Blender y el nombre del archivo `.blend`. Cambia la ruta de Blender si tienes
   otra versión instalada y cambia el nombre del `.blend` por el de tu archivo:

   ```powershell
   $blender = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
   $blend = ".\testing_001.blend"
   ```

   Para ver los resultados y errores en esta misma consola, se usa `blender.exe`. Aunque
   `blender-launcher.exe` está en la misma carpeta de instalación, no entrega la salida de consola
   que necesitan estos comandos.

4. Ejecuta el inspector usando su ruta relativa dentro del kit:

   ```powershell
   & $blender -b --factory-startup $blend --python ".\blender_render_kit\inspect_blend.py"
   ```

   `-b` inicia Blender sin interfaz gráfica y `--python` ejecuta el inspector. `--factory-startup`
   evita cargar preferencias o configuraciones de inicio del usuario. El inspector verifica que el
   kit usado esté junto al `.blend`.

5. El inspector genera dos archivos junto al `.blend`:
   - `<nombre_del_archivo>_inspection.json`, con las escenas, colecciones y rangos del timeline.
   - `<nombre_del_archivo>_render_user.json`, una configuración lista para editar. Incluye los
     nombres exactos de las View Layers de la escena seleccionada en `render_master.json` (o de la
     escena activa si `scene` es `null`) y crea un segmento inicial por View Layer que cubre todo el
     rango de esa escena.

   La configuración generada omite `include_collections`, por lo que se conservan las colecciones
   tal como están configuradas en el `.blend`. El inspector no sobrescribe una configuración
   existente. Para generar una nueva, primero renombra o mueve la anterior.

   En el informe de inspección, `frame_range.start` y `frame_range.end` indican el rango del
   timeline. Dentro de cada View Layer, `collections` muestra el árbol de colecciones:
   - `exclude`: estado `Exclude` de esa colección en esa View Layer.
   - `effectively_excluded`: indica si está excluida directamente o por una colección padre.
   - `state`: `included` o `excluded`, considerando también el estado de los padres.

Este comando solo inspecciona el archivo: no renderiza ni guarda cambios en el `.blend`.

## Flujo guiado desde PowerShell

1. Copia la carpeta completa `blender_render_kit` junto al `.blend`. Abre PowerShell en la carpeta
   que contiene ambos:

   ```text
   carpeta_del_proyecto\
   ├── escena.blend
   └── blender_render_kit\
   ```

2. Ejecuta un solo comando:

   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\blender_render_kit\prepare_render.ps1"
   ```

   Esto ejecuta el script en un proceso de PowerShell temporal; no cambia la politica permanente
   del sistema.

3. El script detecta automáticamente el único `.blend` de la carpeta. Si encuentra varios, muestra
   una lista numerada para que elijas. Luego ejecuta la inspección y crea el informe
   `<nombre_del_blend>_inspection.json` y la configuración `<nombre_del_blend>_render_user.json`.
   Si esta configuración ya existe, la conserva y no la sobrescribe.

4. Se abre la configuración en la aplicación asociada a los archivos JSON. Edita los segmentos y
   rangos, guarda el archivo, cierra el editor y vuelve a PowerShell; presiona Enter para continuar.
   Los nombres de las View Layers ya están completados. Si dejas `include_collections` fuera, el
   render conserva los estados de colección guardados en el `.blend`. Si ya editaste la configuración
   y no necesitas abrirla otra vez, puedes añadir `-SkipEditor` al final del comando del paso 2.

5. El script ejecuta el dry-run automáticamente. En la consola muestra solo los nombres de las View
   Layers, las colecciones incluidas y excluidas, los segmentos, los rangos y las rutas de salida.
   Termina con `RESULTADO: OK` o `RESULTADO: ERROR`. **El dry-run no renderiza ni crea archivos de
   imagen.**

6. Si el dry-run termina correctamente, el script pregunta `Ejecutar render ahora? (S/N; Enter = Si)`.
   Responde `S`, `SI` o presiona Enter para iniciar el render. Responde `N` o `NO` para cancelar.
   Si confirmas, PowerShell muestra una sola barra de progreso, en lugar de imprimir el
   detalle de todos los fotogramas. La barra informa la hora actual, la duración del último
   fotograma, el promedio por fotograma, el tiempo transcurrido del fotograma actual, el tiempo
   restante estimado y la hora estimada de término. Se actualiza mientras Blender reporta el
   progreso y al guardarse cada fotograma. Durante el primero, el promedio y la estimación aparecen
   como `calculando`. Las estimaciones se basan en los fotogramas completados y pueden variar si
   cambia la complejidad de los siguientes. Las imágenes se guardan en
   `renders\<nombre_del_blend>\<view_layer>\<segment>\` dentro de la carpeta del proyecto.

   Para detener un render en curso, presiona **Ctrl+C** en la misma ventana de PowerShell. Es la
   interrupción estándar para un proceso de consola; `Esc` no está disponible porque Blender se
   ejecuta en segundo plano, sin interfaz gráfica. Los fotogramas ya guardados permanecen en disco;
   el fotograma que se estaba procesando podría no completarse.

   Al ejecutar el render, los fotogramas existentes de los segmentos configurados se sobrescriben
   automáticamente. Solo se reemplazan las salidas correspondientes a este `.blend`; no se borran
   carpetas ni renders de otros proyectos. Si reduces un rango, los fotogramas anteriores que queden
   fuera del nuevo rango no se eliminan. La secuencia se vuelve a renderizar completa; no se reanuda
   desde el fotograma donde se interrumpió.

El script usa `blender.exe` para poder capturar y filtrar la salida de consola; `blender-launcher.exe`
no entrega esa salida. Los scripts no guardan cambios en el archivo `.blend`.
