---
modulo: sm
titulo: Solicitudes de Material
rutas: /dashboard/sm, /dashboard/operations/sm-approve
permisos: App.Department.Administrator, App.Department.SM, App.Department.SM-URGENT, App.Department.smCreate, App.Department.smControl, App.Department.smDespachar, App.Department.smEntregasAdmin, App.Department.Operaciones
resumen: Crear y dar seguimiento a solicitudes de material (SM): solicitudes, urgentes, tabla de control, entregas, despacho con firmas y aprobación de herramientas.
---

# Solicitudes de Material

Una SM es la lista de materiales que un contrato o área pide al almacén. Aquí se crea, se controla por fases, se consultan sus entregas y Almacén la despacha y firma. `App.Department.SM` y `App.Department.SM-URGENT` abren todo el módulo; los permisos granulares ven solo su entrada: `smCreate` → **Solicitudes**, `smControl` → **Control de SM**, `smDespachar` y `smEntregasAdmin` → **Despacho y firmas**; los cuatro ven **Entregas de SM**.

## Solicitudes (`/dashboard/sm/solicitudes`)
- **Para qué sirve:** crear, editar y cancelar una SM, y descargar su PDF o Excel.
- **Quién entra:** `App.Department.Administrator`, `App.Department.SM`, `App.Department.SM-URGENT`, `App.Department.smCreate`.
- **Cómo se usa:**
  1. En **Información de la Solicitud** elige el **Cliente** (por defecto TERNIUM). En **Folio** usa el lápiz: **Nuevo folio** abre **Seleccionar Folio** con los folios de tus contratos (para TERNIUM y Telintec); con otros clientes **Editar folio** permite escribirlo. Completa **Contrato**, **Fecha crítica**, **Planta**, **Área**, **Responsable**, **N° de orden**, **Proyecto**, **Destino** (Almacén), **Descripción de la actividad** y **Agregar nuevo comentario**.
  2. En **Productos en la Orden** pulsa **Nuevo Producto** (Nombre, Cantidad, Partida, URL, Número de Parte, **Herramienta/Equipo**, Comentarios → **Agregar Producto**) o **Ver Catálogo** (pestañas **General** y **Por Contrato**, filtro, columnas **Nombre**, **# de parte**, **Stock**, botón **Agregar**). En cada renglón ajusta **Cantidad**, **Partida**, **N° de Parte**, **URL** y comentarios; el icono rojo es **Cancelar item**.
  3. Pulsa **Crear SM**. Para cambiar una existente, en **Lista de Solicitudes** pulsa **Editar** (lápiz), modifica y pulsa **Actualizar SM**. **Limpiar** vacía el formulario; **Cancelar SM** pide confirmación; **Ocultar tabla / Mostrar tabla** esconde la lista.
  4. La lista se filtra con **Buscar por folio...**; columnas **Folio**, **Contrato**, **Planta**, **Destino**, **Responsable**, **Ubicación**, **N° Orden**, **Fecha Inicio**, **Fecha Límite** y **Acciones** (**Editar**, **Descargar PDF**, **Descargar Excel**).
- **Estados y reglas:** obligatorios **Folio**, **Cliente**, **Destino**, **Planta** y **Área**. Una SM solo se edita el día que se creó y el siguiente; después el lápiz se deshabilita. Un ítem con despacho o reserva ya no se edita (**No editable**). Un producto marcado **Herramienta/Equipo** requiere aprobación de Operaciones. Las SM **Entregada** van al final en verde. `smCreate` solo ve las SM de sus contratos.
- **Problemas frecuentes:** **Favor de llenar los campos obligatorios: …**; **El período de edición ha expirado…**; **usuario sin contrato en Ternium** o **No se tienen permisos para acceder a los folios.** (pide al administrador que te asigne contrato o permiso).

## Solicitudes Urgentes (`/dashboard/sm/solicitudes-urgentes`)
- **Para qué sirve:** crear una SM con prioridad alta en una sola pantalla.
- **Quién entra:** `App.Department.SM-URGENT`, `App.Department.Administrator`.
- **Cómo se usa:** en **Solicitud Urgente de Material** llena **Cliente**, **Folio** (la lupa carga los folios de tus contratos), **Contrato**, **ID Empleado**, **Estado**, **Planta**, **Área**, **Responsable**, **N° de orden**, **Proyecto**, **Destino**, **Descripción de la actividad** y **Comentarios**; agrega productos con **Nuevo Producto** o **Ver Catálogo** y pulsa **Crear Solicitud Urgente**. **Volver** y **Cancelar** regresan sin guardar.
- **Estados y reglas:** obligatorios folio, contrato, cliente, ID de empleado, planta, área y al menos un producto; la fecha de solicitud y la crítica se fijan en hoy.
- **Problemas frecuentes:** **Error de validación** con el campo faltante (**El folio es requerido.**, **La planta es requerida.**, **Debe agregar al menos un producto.**).

## Control de SM (`/dashboard/sm/sm-control`, `/edit/<id>`, `/pdf/<id>`)
- **Para qué sirve:** seguir cada SM por fases (solicitante, almacén, compras, cierre) y previsualizar su PDF.
- **Quién entra:** `App.Department.Administrator`, `App.Department.SM`, `App.Department.SM-URGENT`, `App.Department.smControl` (el PDF también lo abren los otros granulares).
- **Cómo se usa:**
  1. Filtra por contrato (**Todos los contratos**) y con **Buscar por folio, contrato...**. Columnas: **Folio**, **Contrato**, **Planta**, **Ubicación**, **Fecha**, **Fecha Crítica** (ámbar a 3 días o menos, rojo vencida), **Avance** (%) y **Acciones**.
  2. El ojo abre el resumen **SM — folio** con **Avance**, **Información general**, **Estado de fases** (Fase 1 **Solicitud Inicial**, 2 **Revisión de Almacén**, 3 **Revisión de Compras**, 4 **Estado General**, 5 **Usuario Solicitante**), **Historial**, **Materiales** y **Comentarios**. El icono de documento abre **Previsualización de SM** con **Descargar**.
  3. El lápiz abre **Editar Solicitud #N** con pestañas **Usuario Solicitante** (datos de la SM, **Pedido Urgente**, **Fecha de Cierre de SM**, **Estado Final de la SM**: Recibido / Pendiente), **Almacén** (**Revisado por Almacén**, **Estado Almacén**: Disponible / No Disponible, **Fecha de Notificación a Compras**) y **Compras** (**Revisado por Administración**, **Estado Compras**: En validacion / En proceso de compra / Procesado por almacen / Suministrado, **Fecha de Notificación a Almacen**), más **Agregar nuevo comentario** → **Guardar**.
- **Estados y reglas:** Administrador y `smControl` editan los tres bloques; `App.Department.Administracion` solo **Compras**; quien creó la SM (o su líder) solo **Usuario Solicitante**; el cargo Coordinador de Almacen solo **Almacén**; el resto solo consulta. `smControl` ve todos los contratos. Las fechas de solicitud y crítica no se editan aquí.
- **Problemas frecuentes:** **No tienes permisos para editar esta solicitud**; **Error al cargar permisos** → **Reintentar**; **Solicitud no encontrada**.

## Entregas de SM (`/dashboard/sm/entregas-de-sm`)
- **Para qué sirve:** consultar, sin editar, las entregas registradas de una SM pendiente.
- **Quién entra:** `App.Department.Administrator`, `App.Department.SM`, `App.Department.SM-URGENT` y los cuatro granulares.
- **Cómo se usa:** elige una SM en **Selecciona una SM para visualizar**; verás **Información de la SM** y la tabla **Ítems y Entregas** (**#**, **Descripción**, **Cantidad**, **Unidad**, **Entregado**, **Estado Stock**, **Entregas** con fecha, estado, cantidad y folios). **Descargar listado** baja un PDF con el listado **(por confirmar)**.
- **Estados y reglas:** solo aparecen SM en **Pendiente**. **Estado Stock**: **Stock suficiente**, **Parcial**, **Insuficiente**, **Sin info**. Cada entrega muestra **Validación**, **Suministrado** o **Pendiente**; la correspondencia exacta de esas etiquetas con las del Controlador de Entregas difiere entre pantallas **(por confirmar)**.
- **Problemas frecuentes:** **No hay ítems en esta SM**; **No se pudo descargar el PDF**.

## Despacho y firmas (`/dashboard/almacen/procesamiento`)
- **Para qué sirve:** que Almacén despache los ítems de una SM y registre las firmas de entrega. La guía completa está en el módulo **Almacén** (Procesamiento SM).
- **Quién entra:** `App.Department.ALMACEN`, `App.Department.Administrator`, `App.Department.smDespachar`, `App.Department.smEntregasAdmin`.
- **Cómo se usa:** en **Lista de Solicitudes de Material** pulsa **Seleccionar SM**; en **Items de la solicitud** captura la cantidad y pulsa **Despachar** por ítem (también **Reservar** y **Solicitar compra**) o **Despachar Todo**, y confirma en **Confirmar despacho**. **Mostrar Progreso** enseña **Progreso de la SM** e **Historial de eventos**. El icono **Firmas** abre **Firmas de entrega**: dibuja **Firma de quien recibe** (obligatoria) y **Firma de quien entrega (opcional)**, pulsa **Guardar firma** y **Confirmar**; la tabla **Firmas registradas** lista cada entrega (**Quien entrega**: Firmada / Sin firma).
- **Estados y reglas:** la cantidad a despachar debe ser mayor a 0, no mayor a la solicitada ni al máximo disponible. La primera firma marca la SM como firmada; se admiten más entregas (**Registrar entrega 2**, cada una es una fila más del PDF). `smDespachar` no puede firmar ni reservar y `smEntregasAdmin` no puede despachar: el servidor responde error.
- **Problemas frecuentes:** **Falta la firma** (dibuja la de quien recibe); **La cantidad a despachar no puede superar la cantidad máxima disponible…**.

## Controlador de Entregas (`/dashboard/sm/controlador_sms`)
- **Para qué sirve:** programar entregas por ítem y crear órdenes de compra desde la SM. Es la misma pantalla de **Administración → Entregas de SM**; aquí no tiene entrada en el menú.
- **Quién entra:** `App.Department.Administrator`, `App.Department.SM`, `App.Department.SM-URGENT`.
- **Cómo se usa:** busca con **Buscar SM...**, revisa **Información de la Solicitud** y en la tabla (**OC**, **#**, **Descripción**, **Cantidad solicitada**, **UM**, **Suministrado**, **Cantidad faltante por suministrar**, **Entregas**, **Total**, **Link**) pulsa **Agregar entrega** por ítem; marca **OC** y pulsa **Crear orden de compra (N)** para los ítems sin stock; termina con **Guardar entregas**.
- **Estados y reglas:** las tarjetas de entrega tienen estado **Pendiente**, **En proceso** (ítem con orden de compra creada), **Validación**, **Suministrado** y **Autorizado** **(por confirmar)** y un color manual. Consulta la guía de Administración para el detalle.
- **Problemas frecuentes:** **Selecciona al menos un item sin stock para crear la orden de compra.**

## Aprobar SM-Herramientas (`/dashboard/operations/sm-approve`)
- **Para qué sirve:** que Operaciones apruebe los ítems marcados **Herramienta/Equipo** antes de que Almacén los despache.
- **Quién entra:** `App.Department.Operaciones`, `App.Department.Administrator`.
- **Cómo se usa:** en **Aprobación de Solicitudes de Herramientas** busca con **Buscar por folio, contrato...**; cada fila (**Folio**, **Contrato**, **Planta**, **Área**, **Fecha**, **Ítem**) se expande para ver **Información de la Solicitud** y **Detalle del Ítem**; pulsa **Aprobar**.
- **Estados y reglas:** el encabezado cuenta **N ítems pendientes de aprobación**; al aprobar, el ítem desaparece de la lista.
- **Problemas frecuentes:** **No se pudo aprobar el ítem.** → reintenta; **No hay ítems pendientes de aprobación**.

## Estados de una SM
- **Pendiente**: recién creada; se edita en Solicitudes, se despacha y se programan entregas.
- **Completada**: también admite despacho y entregas; cuándo pasa de Pendiente a Completada lo decide el servidor al despachar **(por confirmar)**.
- **Entregada**: ya no aparece en despacho ni en entregas; se lista al final en Solicitudes.
- **Cancelada**: la cancela quien crea SM con **Cancelar SM**; no se puede deshacer.
- Además, la SM queda **firmada** desde la primera firma de entrega registrada por Almacén.
