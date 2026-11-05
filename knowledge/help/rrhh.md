---
modulo: rrhh
titulo: RRHH
rutas: /dashboard/rrhh
permisos: App.Department.RRHH, App.Department.Administrator, App.Department.Director
resumen: Dashboard de RH, expediente del personal, check-ins, nómina por quincena, exámenes médicos, vacaciones y encuestas.
---

# RRHH

Módulo de Recursos Humanos: expediente de empleados, consulta de check-ins, carga y entrega de recibos de nómina, exámenes médicos, vacaciones y encuestas. Lo usa el personal con `App.Department.RRHH` (y Administrador). `App.Department.Director` solo entra al **Dashboard**.

## Dashboard (`/dashboard/rrhh/dashboard`)
- **Para qué sirve:** ver de un vistazo la plantilla, altas y bajas, exámenes por vencer, vacaciones pendientes, encuestas y cumpleaños del mes.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Director`, `App.Department.Administrator`.
- **Cómo se usa:** elige el **Mes**. Los recuadros **Plantilla activa**, **Altas del mes**, **Bajas del mes**, **Exámenes vencidos** (chips **30 d**, **60 d**, **90 d**, **Sin examen**), **Vacaciones pendientes**, **Encuestas pendientes** y **Cumpleaños del mes** abren la lista correspondiente ya filtrada (aviso **Filtrado desde el dashboard: …** con **Quitar filtro**). Debajo: **Plantilla por departamento**, la tabla **Cumpleaños del mes** y las gráficas **Altas y bajas por mes** y **Plantilla activa al cierre de cada mes**.
- **Estados y reglas:** altas, bajas, cumpleaños y encuestas son del mes elegido; plantilla, exámenes y vacaciones son al día. Para Director los recuadros no son clicables. El aviso ámbar **Calidad de datos: N registros de empleados por revisar** lista expedientes por corregir; no afecta los números.
- **Problemas frecuentes:** **No se pudo cargar el resumen de RH** → **Reintentar**; **No se pudieron calcular: …** indica qué recuadro falló.

## Personal (`/dashboard/rrhh/personal`, `/nuevo`, `/editar/<id>`)
- **Para qué sirve:** dar de alta, editar y dar de baja empleados, y crear su usuario del sistema.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:**
  1. En **Gestion de Empleados** busca con **Buscar empleados...**. Columnas: **ID**, **Nombre**, **Apellido**, **Modalidad**, **Telefono**, **Departamento**, **Contrato**, **Estado**, **Lider**, **Acciones** (**Editar**, **Crear usuario del sistema**, **Eliminar**).
  2. **Descargar** baja el Excel de empleados según el selector **Todos / Activos / Inactivos**.
  3. **Nuevo Empleado** abre la ficha: **Nombre**, **Apellido**, **Teléfono**, **Departamento**, **Modalidad** (Telintec / Personal externo), **Estado**, **Correo institucional**, **Correo personal**, **Contrato**, **Líder**, **Fecha de admisión**, **RFC**, **CURP**, **NSS**, contacto de emergencia, **Puesto**, **Fecha de salida**, **Motivo de salida**, **Fecha de nacimiento**, **Legajo**. Guarda con **Crear Empleado** o **Actualizar Empleado**.
  4. Al editar, **Dar de Baja** pide el motivo y confirma con **¿Estás seguro?**: el empleado pasa a inactivo.
  5. **Crear usuario del sistema** (icono de persona con +) solo aparece en empleados activos sin usuario y ofrece únicamente los permisos Común y Básico.
- **Estados y reglas:** se pide al menos un correo; el institucional debe terminar en `@telintec.com.mx`; el recibo de nómina llega a los dos. Fecha y motivo de salida solo se capturan al crear; en edición van bloqueados. La baja deshabilita automáticamente los usuarios del empleado. El alta de usuario la acepta el servidor solo a `App.Department.Administrator`; con RRHH responde error.
- **Problemas frecuentes:** **Faltan datos: …** lista los campos con error; **Eliminar Empleado** no se puede deshacer; **Empleado no encontrado.** al abrir una edición con id inválido.

## Detalles Personal (`/dashboard/rrhh/detalles-empleados`)
- **Para qué sirve:** consultar el **Directorio de Empleados** sin editar.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:** contadores **Total Empleados**, **Empleados Activos**, **Empleados Inactivos**; busca con **Buscar por nombre, puesto o email...**, filtra por **Departamento**, **Estado** y **Modalidad**, cambia entre tarjetas y lista. **Ver detalles** abre la ficha con **Informacion personal**, **Contacto**, **Contacto de emergencia**, **Datos de empleo** y, si está inactivo, **Baja del personal**.
- **Estados y reglas:** solo lectura; **Activo** / **Inactivo**.
- **Problemas frecuentes:** **No se encontraron empleados con estos filtros.**

## Check-ins (`/dashboard/rrhh/checkins`)
- **Para qué sirve:** consultar las entradas y salidas con foto del personal, exportarlas y verlas en el mapa. RH es visualizador: no anula ni corrige desde aquí.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:**
  1. Filtra por **Empleado** (**Todos los empleados**; los inactivos dicen **(inactivo)**), **Periodo** (Desde → Hasta) o los chips **Hoy**, **7 días**, **30 días**; marca **Incluir anulados** si hace falta.
  2. Lee los indicadores **Días con registro**, **Horas trabajadas**, **Registros con foto** y **Sin salida**.
  3. Pestañas: **Resumen por día** (Fecha, Empleado, Entrada, Salida, Jornada, Trabajado, Reg., Estado; la flecha abre las tarjetas de cada registro con foto y ubicación), **Entradas / salidas** (una fila por tramo con Duración) y **Mapa por turno** (pines numerados, cyan entrada y violeta salida; el círculo es la precisión del GPS; clic en un pin abre la foto).
  4. **Excel** y **PDF** descargan con los mismos filtros de la pantalla; el PDF lleva fotos y admite hasta 200 registros.
- **Estados y reglas:** **Completo**, **Sin salida**, **Sin entrada**; **Anulado** se ve atenuado. Las horas suman solo tramos cerrados. El rango por defecto es 30 días (máximo 366); con muchos datos aparece **Se muestran los N registros más recientes…**. La página de registro manual (`/dashboard/rrhh/checkins/nuevo`: Empleado, Entrada/Salida, Fecha, Hora no futura, Motivo obligatorio) ya no tiene botón, pero sigue abriéndose escribiendo la dirección.
- **Problemas frecuentes:** **«Desde» no puede ser después de «Hasta».** deshabilita Excel y PDF; **No hay registros en el rango**; **No se pudo exportar a PDF** si pasa de 200 registros.

## Nómina (`/dashboard/rrhh/nomina`)
- **Para qué sirve:** cargar los recibos PDF/XML de cada quincena y entregarlos a los empleados. Las direcciones antiguas `/payroll` y `/payroll-v2` redirigen aquí.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:**
  1. Elige **Año**, **Mes** y **Quincena**. Pulsa **Cargar archivos**: arrastra los PDF y XML o usa **Elegir archivos** / **Agregar archivos** (las selecciones se acumulan; **Limpiar** empieza de cero). Cada XML se lee para sugerir al empleado; la columna **Origen** dice **Por RFC**, **Por CURP**, **Por nombre** o **Asignado a mano**. Corrige el empleado en la lista si hace falta y pulsa **Subir N archivos** → **Confirmar**.
  2. En **Recibos de la quincena** cada empleado muestra **PDF**, **XML**, **Entrega** y **Acciones**: subir o reemplazar, **Descargar PDF y XML**, **Notificar en el sistema**, enviar por correo, WhatsApp y **Eliminar**. Filtra con **Nombre o ID…** y **Todos / Con archivos / Sin archivos**.
  3. **Notificar a todos (N)** avisa en el sistema a quienes tienen recibo; marca **También por correo** para enviarlo además a sus correos. Al final sale el resumen con los que no tienen usuario para mandarles WhatsApp.
- **Estados y reglas:** subir un archivo del mismo tipo reemplaza al anterior; las filas en ámbar avisan **Sin XML**, dos grupos al mismo empleado o XML de otra quincena, pero no bloquean. Etiquetas de **Entrega**: **Sin usuario**, **Notificado**, **Enviado por WhatsApp** (marca solo en tu navegador; adjunta tú el recibo en el chat), **Enviado por correo**. Solo se notifica a empleados activos. **Otros recibos del mes** agrupa archivos guardados con otro identificador.
- **Problemas frecuentes:** **Sin usuario en el sistema … Envíaselo por WhatsApp**; **No se envió el correo** (empleado sin correo o rechazo del servidor); **Correo pendiente** (correo no configurado en el servidor); **No se pudo notificar** con empleado inactivo.

## Examenes Medicos (`/dashboard/rrhh/examenes-medicos`)
- **Para qué sirve:** llevar el expediente médico y la vigencia del examen de cada empleado.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:** busca con **Buscar empleado...**; los contadores **Vencidos**, **Por vencer** y **No aptos** filtran la tabla (**Ver todos** quita el filtro). Columnas: **Nombre**, **Tipo Sangre**, **Estatus**, **Ultima Fecha**, **Aptitud**, **Vigencia**, **Alergias**, **Acciones** (**Agregar registro**, **Editar**, **Eliminar**). **Nuevo Examen** pide **Fecha**, **Empleado sin registros**, **Tipo de sangre**, **Aptitud**, **Alergias**, **Observaciones** → **Guardar**. **Descargar reporte** baja el Excel.
- **Estados y reglas:** aptitudes **APTO 1 (examen cada 12 meses)**, **APTO 2 (cada 6)**, **APTO 3 (cada 3)**, **NO APTO**, **No determinado**; la vigencia se calcula con esa periodicidad y avisa 30 días antes: **Vencido**, **Vence hoy**, **Vence en N días**, **Al día**, **No apto**, **Sin periodo**, **Sin fecha**. En **Editar** se elige un registro del historial para cambiar su fecha y aptitud.
- **Problemas frecuentes:** **Eliminar todo** borra el expediente completo del empleado y no se puede deshacer.

## Administrar vacaciones (`/dashboard/rrhh/gestion-vacaciones`, `/dashboard/rrhh/vacaciones-info`)
- **Para qué sirve:** registrar por empleado y año los días de vacaciones, su estado y la prima vacacional.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:** en **Administracion de Vacaciones** busca al empleado y elige el año en **Seleccionar Ano**; si no tiene registros, el icono **+** (**Inicializar registro**) crea el primero. El panel **Detalles del año seleccionado** muestra **Ano**, **Estado**, **Comentarios**, **Estado Prima**, **Fecha Pago Prima** y **Fechas de vacaciones**, con iconos **Agregar año**, **Editar** y **Eliminar** (cada uno confirma). El diálogo **Registro de Vacaciones** pide **Estado de vacaciones** (Ej. 12 PTES), **Comentarios**, **Estado de pago**, **Fecha de pago** y los días en el calendario (clic por día; contadores **Hábiles**, **Sábados**, **Domingos**; **Limpiar**) → **Crear registro** / **Guardar cambios**. **Descargar reporte** baja el Excel. `/dashboard/rrhh/vacaciones-info` (sin entrada en el menú) muestra un calendario mensual con los nombres por día y el botón **Ir a hoy**.
- **Estados y reglas:** el estado y la prima son texto libre; un año nuevo nace como **Nuevo** con prima **Pendiente**.
- **Problemas frecuentes:** **Ocurrio un error al actualizar las vacaciones.** → reintenta.

## Encuestas (`/dashboard/rrhh/encuestas`, `/nuevo`, `/modelos`, `/clima`, `/eva360`, `/resultados/<id>`)
- **Para qué sirve:** asignar encuestas a empleados, ver resultados, administrar los modelos de encuesta, los procesos de evaluación 360 y el clima laboral.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:**
  1. La lista **Encuestas** tiene columnas **ID**, **Empleado**, **Estatus**, **Tipo**, **Fecha**, **Resumen** y **Acciones** (**Ver proceso 360**, **Ver resultados**, **Ver informacion**, **Descargar PDF**, **Eliminar**).
  2. **Nueva Encuesta**: **Fecha límite**, **Tipo de encuesta**, **Empleado encuestado** y, en la encuesta de salida, **Motivo de salida** → **Crear una encuesta**. La evaluación 360 no se asigna aquí.
  3. **Nueva evaluación 360**: **Empleado evaluado**, **Fecha límite**, **Autoevaluación (self)**, **Jefe inmediato (superior)**, **Colega (peer)**, **Subordinado** → **Crear proceso 360**. En **Proceso Evaluación 360** ves el **Seguimiento** (Respondido / Pendiente), **Marcar completado**, el radar de **Competencias**, el **Detalle por rol** y **Descargar PDF**.
  4. **Clima laboral** muestra el agregado por año: **Categoría**, **% Positivo**, **Nivel**, **Total**.
  5. **Modelos** lista los cuestionarios (filtros **Todas / Borrador / Activas / Archivadas**): **Tipo**, **Nombre**, **Estado**, **Rúbrica**, **Secciones**, **Actualizado** y acciones **Editar**, **Crear versión nueva**, **Publicar**, **Archivar**, **Reactivar**. **Nuevo modelo** abre el editor con pestañas **Preguntas** (secciones de tipo **Selección múltiple**, **Opción única**, **Matriz** o **Texto abierto**) y **Avanzado** (JSON y rúbrica) → **Crear modelo** / **Guardar cambios**.
- **Estados y reglas:** **Pendiente** / **Completada**; el PDF solo de encuestas completadas. Un modelo nace en **Borrador** y debe publicarse para asignarse; con encuestas asignadas su template se bloquea: usa **Crear versión nueva** y al publicarla marca **Migrar las encuestas pendientes a esta versión** si quieres que los pendientes contesten la nueva. Un modelo **Protegida** (Norma 035) no se elimina. Se necesitan al menos 2 cuestionarios por proceso 360; el PDF sale **preliminar** hasta cerrar el proceso.
- **Problemas frecuentes:** **No se puede descargar el reporte si la encuesta no esta completada.**; **No hay rubrica para el tipo de encuesta N** (sin rúbrica no hay PDF ni puntaje: **Aún no evaluable**); **Disponible cuando alguien responda** en el PDF 360.

## Fichajes (`/dashboard/rrhh/fichajes`)
- **Para qué sirve:** ya nada. Está oculta del menú y el servidor retiró los datos de fichajes; al abrirla por dirección muestra **Error al cargar los datos**.
- **Quién entra:** `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:** no la uses; las asistencias con foto están en **Check-ins**.
- **Estados y reglas:** sin funciones.
- **Problemas frecuentes:** el error al cargar es esperado.
