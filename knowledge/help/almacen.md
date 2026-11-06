---
modulo: almacen
titulo: Almacén
rutas: /dashboard/almacen, /dashboard/sucursal, /dashboard/administracion/inventario-almacen
permisos: App.Department.Administrator, App.Department.ALMACEN, App.Department.ALMACEN-VISUAL, App.Department.Sucursal-2
resumen: Inventario y movimientos del almacén principal, reservas, proveedores, traslados a sedes, almacén de sede e inventario de solo lectura.
---

# Almacén

Inventario del almacén principal (productos, entradas, salidas, reservas, proveedores, envíos a sedes), almacén de cada sede e inventario de solo consulta. **Almacén** es del personal de Almacén, **Sucursal** del personal de cada sede e **Inventario de Almacén** es solo lectura.

## Inventario (`/dashboard/almacen/inventario`, `/nuevo`, `/editar/<id>`)
- **Para qué sirve:** consultar, crear, editar y eliminar productos del almacén principal.
- **Quién entra:** `App.Department.ALMACEN`, `App.Department.Administrator`.
- **Cómo se usa:** busca con **Buscar por nombre...**, **Buscar por SKU...** o **Buscar por # de parte...** (con Enter abre el producto, o el alta si no existe) y filtra por **Categoría** y **Proveedor**. Columnas principales: **Nombre**, **Código de barras**, **# de parte**, **Stock**, **Reservado**, **Stock Fisico**, **Tipo**. El lápiz edita, el bote elimina (con confirmación) y los iconos de Excel y PDF descargan el listado. **Crear Producto** pide **Nombre**, **Código de barras** (se sugiere el siguiente), **UDM**, stocks, **Categoría**, **Proveedor**, **Marca**, **Número de parte**, **Ubicación**, casillas **Herramienta**, **Interno**, **EPP** e **Ítem de SM (opcional)**; guarda con **Crear Producto** (o **Actualizar Producto**).
- **Estados y reglas:** **Herramienta** y **EPP** no se combinan y fijan la categoría. **Número de parte** es obligatorio salvo proveedor o marca GENERICO.

## Entradas y Salidas (`/dashboard/almacen/movimientos-entrada`, `/movimientos-salida`)
- **Para qué sirve:** registrar lo que entra o sale y consultar el historial. La vista **Movimientos** (`/dashboard/almacen/movimientos`, fuera del menú) junta ambos y deja elegir el **Tipo** en cada alta.
- **Quién entra:** `App.Department.ALMACEN`, `App.Department.Administrator`.
- **Cómo se usa:** en **Movimientos Individuales** filtra con **Nombre o ID...**, **SKU...**, **# de parte...** o **Ref. o Folio...** (Excel y PDF descargan). **Crear Movimiento** pide **Producto**, **Cantidad**, **Factura** (entrada) o **SM ID** (salida) y **Referencia**; confirma en **Confirmar movimiento**. El lápiz (**Editar Movimiento**) solo cambia **Referencia** y **SM ID**. **Movimientos Múltiples**: **Agregar** productos, captura cantidades y **Generar Movimientos (N)**.
- **Estados y reglas:** entrada exige **Factura** y **Referencia**; salida exige **SM ID** y no puede superar el disponible (**Stock insuficiente. Disponible: N**). Por defecto se ven los **últimos 3 meses**; si son demasiados, solo los más recientes (aviso ámbar). Para otro periodo elige **Desde** y **Hasta** y **Aplicar**; **Últimos 3 meses** regresa.
- **Problemas frecuentes:** **No hay movimientos en los últimos 3 meses**: elige un "Desde" anterior.

## Procesamiento SM (`/dashboard/almacen/procesamiento`)
Almacén despacha los ítems de una Solicitud de Material y registra firmas de entrega. Entran `App.Department.ALMACEN` y `App.Department.Administrator`. Los pasos están en la guía **Solicitudes de Material**, "Despacho y firmas".

## Entregas de SM (`/dashboard/almacen/entregas-de-sm`)
Consulta de solo lectura de las entregas de una SM pendiente: elige la SM, revisa **Ítems y Entregas** y usa **Descargar listado**. Es la pantalla que la guía **Solicitudes de Material** describe en "Entregas de SM". Entran `App.Department.ALMACEN` y `App.Department.Administrator`.

## Despachar vales (`/dashboard/almacen/lista_vouchers`)
- **Para qué sirve:** despachar vales de seguridad (EPP) y de herramientas y equipo, y ver herramientas prestadas.
- **Quién entra:** `App.Department.ALMACEN`, `App.Department.Administrator`.
- **Cómo se usa:** elige **Vale de Seguridad**, **Vale de Herramientas y Equipo** (inicial) o **Herramienetas Prestadas**. La tabla trae **Contrato**, **Transaccion**, **Empleado Solicitante**, **Empleado designado** y **Estado**. El ojo abre **Items de la solicitud** y **Historial de eventos**; pulsa **Aprobar** para despachar. **Herramienetas Prestadas** es consulta: **Herramientas en Préstamo** y **Herramientas Asignadas**, con **Estado de Almacen** (Pendiente, En proceso, Completado).
- **Estados y reglas:** **Aprobar** solo está activo con el vale **Pendiente**; se listan los del último año. La creación y aprobación previas están en la guía **Vales y Almacén EPP**.
- **Problemas frecuentes:** **Ocurrió un error al aprobar el vale**: reintenta. Etiqueta de **Estado** tras despachar **(por confirmar)**.

## Reservaciones (`/dashboard/almacen/reservaciones`)
- **Para qué sirve:** ver y corregir las reservas de producto ligadas a una SM.
- **Quién entra:** `App.Department.ALMACEN`, `App.Department.Administrator`.
- **Cómo se usa:** muestra **Todos los estados**; el selector filtra por **Pendiente**, **Aprobada**, **Rechazada** o **Completada**. Busca con **Buscar por ID, Producto, SM...** y recarga con **Actualizar**. Cada fila tiene **Ver detalles**, **Editar** y **Eliminar**. **Editar Reservacion** cambia **Cantidad**, **Estado**, **Cambiar SM Asociada (opcional)** y **Nuevo Comentario (opcional)**; **Guardar Cambios**. **Eliminar Reservacion** no se deshace.
- **Estados y reglas:** los recuadros de arriba cuentan el **Total** cargado y cuántas hay **Pendiente**, **Aprobada** y **Rechazada**; el filtro y la búsqueda solo acotan lo que se ve.
- **Problemas frecuentes:** **Error al cargar las reservaciones**: pulsa **Actualizar**.

## Proveedores (`/dashboard/almacen/proveedores`, `/nuevo`)
- **Para qué sirve:** consultar el catálogo y dar de alta proveedores.
- **Quién entra:** `App.Department.ALMACEN`, `App.Department.Administrator`.
- **Cómo se usa:** **Buscar proveedores...** (columnas **Nombre**, **Vendedor**, **Email**, **Teléfono**, **Marcas**, **RFC**). **Nuevo Proveedor**: solo **Nombre \*** es obligatorio; **Crear Proveedor**.

## Traslados a sedes (`/dashboard/almacen/traslados`, `/nuevo`, `/<id>`, `/<id>/resolver`)
- **Para qué sirve:** enviar producto del principal a una sede y seguirlo hasta su recepción.
- **Quién entra:** `App.Department.ALMACEN`, `App.Department.Administrator`.
- **Cómo se usa:** la lista filtra por folio, **Estatus**, **Sede destino**, **Desde** y **Hasta**; el ojo abre el detalle. **Nuevo traslado**: **Sede destino**, busca y **Agregar** productos, **Cantidad**, **Comentario general** y **Enviar traslado** (**Confirmar creación**). El folio es `TRS-####`.
- **Estados y reglas:** al enviar se descuenta el stock del principal. **En tránsito**: se puede **Cancelar traslado** y las piezas regresan. **Recibido**. **Recibido con diferencias**: llegó menos; aparece **Resolver diferencia**, donde cada faltante se marca **Reingreso** (la pieza regresó y vuelve al stock del principal) o **Merma** (se perdió o dañó; solo queda registrada), con **Marcar todos**. Se resuelve todo a la vez, una sola vez y sin deshacer; el traslado pasa a **Diferencia resuelta** con columna **Resolución**. **Cancelado**.
- **Problemas frecuentes:** **Supera el disponible**: baja la cantidad; **Elige reingreso o merma**: falta decidir un producto.

## Inventario de sede (`/dashboard/sucursal/inventario`)
- **Para qué sirve:** ver existencias de la sede y, de referencia, las del principal.
- **Quién entra:** `App.Department.Sucursal-2` (su sede), `App.Department.ALMACEN`, `App.Department.Administrator`.
- **Cómo se usa:** si hay varias sedes elige en **Sede**. **Buscar por SKU, producto o categoría**; **Solo con existencia** viene activo. Columnas: **SKU**, **Producto**, **UDM**, **Categoría**, **Stock sede**, **Stock principal**.
- **Estados y reglas:** el personal de la sede opera; Almacén principal solo consulta y el sistema le rechaza escribir (**Solo consulta**).

## Movimientos de sede (`/dashboard/sucursal/movimientos`, `/nuevo`, `/editar/<id>`)
- **Para qué sirve:** registrar entradas y salidas de la sede.
- **Quién entra:** como Inventario de sede; solo el personal de la sede escribe.
- **Cómo se usa:** mismo periodo de 3 meses (**Desde**, **Hasta**, **Aplicar**); filtra **Todos / Entradas / Salidas**. **Nuevo movimiento**: producto, **Tipo de movimiento**, **Cantidad**, **Fecha (opcional)** (vacía = ahora), **Referencia**, **Comentario**; **Guardar movimiento**. El lápiz (**Guardar cambios**) y el bote (**Confirmar eliminación**) corrigen.
- **Estados y reglas:** el stock de la sede nunca queda negativo: se rechaza toda salida, edición o borrado que lo deje así. Los movimientos **Traslado** nacieron de una recepción y no se editan ni borran.
- **Problemas frecuentes:** **Stock insuficiente en la sede…**.

## Recepción de traslados (`/dashboard/sucursal/traslados`, `/<id>`, `/<id>/recibir`)
- **Para qué sirve:** que la sede confirme lo que llegó.
- **Quién entra:** como Inventario de sede; solo la sede destino recibe.
- **Cómo se usa:** en **Traslados recibidos** el **Estatus** inicia en **En tránsito**. Pulsa **Recibir**: captura **Recibido** por producto (inicia igual al enviado), comentarios y **Comentario general**, y **Confirmar recepción**.
- **Estados y reglas:** la recepción es única, no se repite. Con diferencias queda **Recibido con diferencias** y el principal lo resuelve; sin ellas, **Recibido**.
- **Problemas frecuentes:** **La recepción se confirma una sola vez**.

## Inventario de Almacén (`/dashboard/administracion/inventario-almacen`)
- **Para qué sirve:** consultar el inventario sin modificarlo.
- **Quién entra:** `App.Department.ALMACEN-VISUAL`, `App.Department.Administrator`.
- **Cómo se usa:** busca por nombre, código de barras o número de parte; filtra por categoría y proveedor; **Descargar Excel** y **Descargar PDF**.
- **Estados y reglas:** no permite crear ni editar.
