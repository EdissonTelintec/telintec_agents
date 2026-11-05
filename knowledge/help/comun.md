---
modulo: comun
titulo: Comun
rutas: /dashboard/comun
permisos: App.Department.Administrator, App.Department.Common, App.Department.Basic, App.Department.RRHH
resumen: Check-in con foto, encuestas y tareas asignadas, y descarga de los recibos de nómina del propio empleado.
---

# Comun

Módulo para todo el personal: aquí registras tus entradas y salidas con foto cuando el biométrico no está disponible, contestas las encuestas que te asigna Recursos Humanos y descargas tus recibos de nómina. Lo ve cualquier usuario con `App.Department.Common`; quien solo tiene `App.Department.Basic` únicamente ve **Check-in**.

## Check-in (`/dashboard/comun/checkin`)
- **Para qué sirve:** registrar tu entrada y tu salida con una foto tomada en el momento. Es el respaldo del biométrico. Un día puede tener varios turnos (entrada → salida); lo que pase de 8 horas se muestra como tiempo extra.
- **Quién entra:** `App.Department.Administrator`, `App.Department.Common`, `App.Department.Basic`, `App.Department.RRHH`. Solo registras sobre ti mismo.
- **Cómo se usa:**
  1. Arriba ves el reloj y la tarjeta del día: **Sin registros hoy**, **Turno N abierto desde HH:MM**, **Jornada cumplida** o **Turno N en tiempo extra**, con la barra **Ordinario … / 8 h · Extra …**. Debajo dice **Siguiente registro: Entrada · Turno 1** (o Salida); tú no eliges el tipo, lo decide el estado del día.
  2. Pulsa **Tomar foto**. En el celular abre la cámara frontal; en la computadora abre el explorador de archivos. Aparece **Preparando la foto…** y luego la vista previa con **✓ Foto lista · HH:MM** y el botón **Repetir**. La foto se reduce sola antes de subirla.
  3. Opcional: marca **Compartir mi ubicación** y acepta el permiso del navegador. El texto pasa por **Buscando…**, **Afinando · ±N m** y **Lista · ±N m** (verde hasta 20 m, ámbar hasta 100 m, rojo arriba). Puedes pulsar **Volver a leer**. Sin marcarla dice **Opcional · no se adjuntará**.
  4. Pulsa **Registrar entrada**, **Registrar salida** o **Registrar entrada extra** (ámbar). En el diálogo **Confirmar creación** pulsa **Confirmar**. Sale el aviso verde **Entrada del turno 1 registrada a las HH:MM.**
  5. En **Mis registros** (últimos 30 días) ves cada día con sus turnos, la línea de tiempo de 06 a 24 h, los totales **Ordinario** y **Extra**, y un icono de imagen por registro que abre tu foto.
- **Estados y reglas:**
  - La hora oficial la pone el servidor, no tu teléfono. No puedes corregir ni borrar un registro: pídelo a RH.
  - El botón queda deshabilitado con **Toma una foto para continuar**, **Esperando la ubicación…** o **La ubicación tiene más de 5 min: vuelve a leerla**.
  - Un turno sin cerrar aparece como **en curso**; un día con **sin salida** o **sin entrada** se marca **Incompleto**. Un registro capturado por RH dice **manual (RH)**.
  - El chip **Tiempo extra** solo informa: el motivo y la aprobación del jefe todavía no se guardan.
  - La ubicación solo funciona en una página segura (https).
- **Problemas frecuentes:**
  - **La foto debe ser JPG, PNG o WEBP.**: elegiste un archivo que no es imagen.
  - **Permiso de ubicación negado…**, **Sin señal de ubicación…** o **La ubicación tardó demasiado…**: se registra sin ubicación; puedes seguir.
  - **No se pudo registrar**: revisa la conexión e inténtalo de nuevo; **Reintentar** recarga tus registros.

## Tareas (`/dashboard/comun/encuestas`)
- **Para qué sirve:** ver y contestar las encuestas y tareas que RH te asignó (salida, Norma 035, clima laboral, evaluación 360 y modelos nuevos).
- **Quién entra:** `App.Department.Administrator`, `App.Department.Common`, `App.Department.RRHH`.
- **Cómo se usa:**
  1. La pantalla **Mis Tareas** lista tus tareas con las columnas **ID**, **Tarea** (nombre de la encuesta), **Estatus**, **Fecha**, **Detalles** y **Acciones**. Usa **Buscar tarea...** para filtrar.
  2. Pulsa **Abrir** y confirma **¿Deseas iniciar la tarea?** con **Confirmar**.
  3. En el diálogo **Encuesta** ves **Pregunta N de M** y el avance en %. Según la pregunta marcas casillas (**Selecciona todas las que apliquen.**), una sola opción, una fila de opciones por subpregunta o escribes texto libre. Avanza con **Siguiente**; en la última pulsa **Finalizar encuesta**.
  4. Verás **Guardando tus respuestas…** y luego **Encuesta completada**. Pulsa **Cerrar**.
- **Estados y reglas:**
  - **Incompleto** = pendiente de responder; **Completado** = ya enviada. Una tarea completada no se vuelve a abrir (**Tarea ya completada.**).
  - No hay botón para regresar a la pregunta anterior; revisa antes de pulsar **Siguiente**.
  - En algunas encuestas (Norma 035 para más de 50 personas) la primera respuesta puede saltar preguntas que no aplican.
- **Problemas frecuentes:**
  - **No pudimos guardar tus respuestas**: tus respuestas siguen en pantalla; pulsa **Intentar de nuevo** y, si persiste, avisa a Recursos Humanos.
  - **Tareas todavía no soportadas.**: la tarea no es una encuesta; consúltalo con RH.
  - **Ocurrió un error al cargar la encuesta.**: vuelve a abrirla más tarde.

## Mi nómina (`/dashboard/comun/nomina`)
- **Para qué sirve:** descargar tus recibos de nómina (PDF y XML) y ver los avisos que RH te manda cuando sube uno nuevo.
- **Quién entra:** `App.Department.Administrator`, `App.Department.Common`.
- **Cómo se usa:**
  1. La pantalla **Mis Nóminas** muestra arriba el bloque **Avisos de nómina** con cada aviso **Recibo de la 1ª/2ª quincena de …** y su botón **Descargar** (baja un zip con PDF y XML).
  2. Debajo está la tabla de recibos con **ID**, **Año**, **Mes**, **Quincena**, **Archivos** y **Acciones**. Usa **Buscar...** para filtrar.
  3. Pulsa **Descargar**, confirma **¿Deseas descargar estos archivos de nómina?** con **Descargar** y guarda el archivo `Docs-<año>-<mes>-<quincena>.zip`. Sale el aviso **Descarga exitosa**.
- **Estados y reglas:**
  - Los recibos los sube RH; si marcó el envío por correo, el mismo recibo también llega a tus correos registrados (institucional y personal).
  - Un aviso en negritas es uno que no has abierto.
  - Si RH reemplaza un archivo, el aviso viejo deja de servir: descarga desde la tabla, que siempre tiene los vigentes.
- **Problemas frecuentes:**
  - **Este aviso ya no tiene el recibo** / **Este recibo ya no está disponible**: RH lo reemplazó o lo eliminó; usa la tabla o pídeselo a RH.
  - **No encontramos tu recibo**: el archivo no está guardado en el sistema (puede ser anterior a la carga en línea); pídelo a RH.
  - **No pudimos descargar tu recibo**: intenta en unos minutos; si sigue, avisa a Recursos Humanos.

## Vacaciones (`/dashboard/comun/vacaciones`)
- **Para qué sirve:** todavía nada. No está en el menú y al abrirla muestra **Página en Desarrollo — Esta sección aún no está disponible**.
- **Quién entra:** `App.Department.Administrator`, `App.Department.Common`.
- **Cómo se usa:** no aplica; tus vacaciones las administra RH desde su módulo.
- **Estados y reglas:** sin funciones.
- **Problemas frecuentes:** ninguno; si necesitas tus días, consulta a Recursos Humanos.
