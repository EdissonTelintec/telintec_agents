---
modulo: compras
titulo: Compras
rutas: /dashboard/administracion/purchases, /dashboard/administracion/conciliacion-oc-almacen, /dashboard/administracion/gestion-compras, /dashboard/administracion/pedido-proveedor, /dashboard/purchases, /dashboard/operations/purchases
permisos: App.Department.Administrator, App.Department.Administracion, App.Department.Operaciones
resumen: Solicitudes de orden de compra, órdenes de compra y su PDF, conciliación con entradas de almacén, bitácora de gestión de compras, solicitudes de compra y su aprobación.
---

# Compras

Reúne el flujo de compras: pedir material (solicitudes de compra), aprobarlo, convertirlo en orden de compra (OC), conciliarlo con lo que entra a almacén y llevar la bitácora de compras y gastos. Las pantallas de Administración están en el menú **Administracion**; las otras dos, en **Compras** y **Operaciones**.

## Solicitudes de OC (`/dashboard/administracion/purchases/solicitudes`)
- **Para qué sirve:** ver las solicitudes de compra y convertirlas en órdenes de compra.
- **Quién entra:** `App.Department.Administracion`, `App.Department.Administrator`.
- **Cómo se usa:** busca con **Buscar por folio, proveedor, creador o ID...**. Columnas: **Folio**, **Proveedor**, **Estado**, **Artículos**, **Creado por**, **Fecha**, **Entrega**, **Acciones**; la fila más reciente va resaltada. El botón **+** (**Crear Orden de Compra**) abre el formulario **Crear Orden de Compra para** el folio elegido:
  - **Información General**: **Folio** (escribe o elige uno sugerido), **Proveedor \***, **Tiempo de entrega \***, **Estado** (fijo en Pendiente), **Comentario**, **Folio Proveedor**.
  - **Productos**: **Agregar Ítem** abre **Seleccionar Items** (pestañas **Catálogo del Proveedor** e **Inventario de Almacén**); marca y pulsa **Agregar (n) Item(s)**. Cada línea lleva descripción, precio, cantidad, marca, número de parte, **Herramienta** y moneda (MXN o USD).
  - **Datos del Solicitante** y **Datos del Proveedor** (RFC, direcciones, método de pago, condiciones de entrega, etc.).
  - Guarda con **Crear Orden de compra** y confirma en **Confirmar creación**.
- **Estados y reglas:** **Pendiente**, **Autorizado**, **Adquirido**, **Finalizado**, **Cancelado**. Las solicitudes con productos de proveedores de entrega rápida no salen aquí: se autorizan con **Por Autorizar**. El bote (**Eliminar**) la quita de la lista de inmediato, sin pedir confirmación.
- **Problemas frecuentes:** **Selecciona un proveedor** (elígelo antes de agregar productos); **El tiempo de entrega es requerido**; **El precio unitario debe ser mayor a 0**; **El folio es requerido**; **Revisa los datos del formulario** (lista los campos con error); **Sin solicitudes de OC**.

## Órdenes de Compra (`/dashboard/administracion/purchases/ordenes`)
- **Para qué sirve:** consultar las órdenes, crear una nueva, aprobar la pendiente y descargar su PDF.
- **Quién entra:** igual que Solicitudes de OC.
- **Cómo se usa:** busca con **Buscar por folio, proveedor o ID...**. Columnas: **ID**, **Folio**, **Proveedor**, **Estado**, **Total** (MXN), **Artículos**, **Creado por**, **Fecha**, **Entrega**, **Acciones**. El lápiz (**Editar**) abre **Editar Orden** con el formulario de arriba; el icono rojo (**Descargar PDF**) baja `OrdenCompra_<folio>.pdf`. **Crear Orden de Compra** abre **Nueva Orden de Compra**, sin solicitud previa, y se guarda con **Crear Orden**.
- **Estados y reglas:** en una orden existente el botón dice **Aprobar orden de compra** y pide **Confirmar actualización**; al guardar, la orden queda en **Autorizado** aunque hayas elegido otro **Estado**. **Usado en otra O.C.** marca un producto que ya pertenece a otra orden.
- **Problemas frecuentes:** **Ocurrió un error al descargar el PDF.**; **Error al crear la orden**; **Sin órdenes de compra**.

## Conciliación OC–Almacén (`/dashboard/administracion/conciliacion-oc-almacen`)
- **Para qué sirve:** ver qué órdenes ya tienen entradas registradas en almacén. Solo consulta.
- **Quién entra:** igual que Solicitudes de OC.
- **Cómo se usa:** ajusta **Desde** (por defecto 30 días atrás), **Hasta**, **Status** (**Todos**, **Pendiente**, **Recibido**) y **Buscar folio** (folio o folio de proveedor); **Actualizar** recarga. Columnas: **Folio**, **Folio prov.**, **Proveedor**, **Entrega**, **Recepción**, **Acciones**. El ojo (**Ver detalle**) despliega **Movimientos de almacén** (**Mov.**, **Producto**, **Cant.**, **Fecha**, **Referencia**, **SM**, **Match**) y **SMs relacionadas**, con el avance de cada ítem (surtido/solicitado y porcentaje).
- **Estados y reglas:** **Recepción** dice **con entradas** o **sin entradas**. **Match**: **exacto** (la referencia coincide con el folio) o **parcial** (el folio está dentro de la referencia). Estado de cada SM: **Pendiente**, **Completada**, **Entregada**, **Cancelada**, **Firmada**. El filtro **Recibido** trae las órdenes aprobadas (las que Órdenes de Compra muestra como **Autorizado**), aunque no haya llegado nada; lo que llegó lo dice **Recepción**.
- **Problemas frecuentes:** **No se encontraron OC con los criterios.** (amplía las fechas); **Error al cargar la conciliación** (**Reintentar**); **Sin entradas registradas.**; **Sin SMs vinculadas.**

## Gestión de Compras (`/dashboard/administracion/gestion-compras`, `/nueva`, `/<id>/editar`)
- **Para qué sirve:** bitácora de compras y gastos (formato FO-COM-01 R3), una fila por solicitud, con montos, estatus y aprobación de gerencia.
- **Quién entra:** `App.Department.Administracion`, `App.Department.Administrator`. Solo `App.Department.Administrator` cambia **Estatus de solicitud**, **Fecha de pago**, **Aprobación de gerencia** y **Fecha de aprobación**; para los demás salen con candado.
- **Cómo se usa:**
  - Filtra por **Semana**, **Clasificación**, **Estatus** y **Solicitante**; **Ver canceladas** las incluye y **Limpiar** quita los filtros. Las tarjetas **Total USD**, **Total MXN**, **Pendientes** y **Depósito banco base** se recalculan con el filtro.
  - **Exportar** descarga un CSV de las filas filtradas. **Nueva solicitud** abre **Nueva Solicitud de Compra**.
  - En la tabla, un clic en una celda la edita: **Enter** guarda, **Esc** cancela. Cada fila trae el lápiz (**Editar**), **Cancelar** y **Eliminar**.
  - El formulario tiene **Datos de la solicitud**, **Montos y pago**, **Aprobación de gerencia** y **Análisis**. Obligatorios: **Fecha de solicitud**, **Descripción**, un monto (USD o MXN), **Estatus** y **Aprobación**. Guarda con **Guardar solicitud** o **Guardar cambios**.
- **Estados y reglas:** **Estatus**: **PENDIENTE** (espera el OK de gerencia), **PAGADO**, **URGENTE** (darle prioridad), **POR PAGAR** (con OK, en proceso de pago), **PUEDE ESPERAR** (más de una semana). **Aprobación**: **PENDIENTE** o **AUTORIZADO**. **Cancelar** (**Confirmar cancelación**, con **Motivo (opcional)**) saca la solicitud del listado y no se reactiva desde la aplicación. **Eliminar** (**Confirmar eliminación**) borra la solicitud con su historial y no se deshace. **% de utilidad**, **Costo Ternium con IVA** y **Utilidad** se guardan como se capturan; no se calculan.
- **Problemas frecuentes:** **No se pudieron cargar las solicitudes** (**Reintentar**); **No hay solicitudes de compra con estos filtros**; **La descripción es obligatoria**; **Captura al menos un monto, en USD o en MXN**; **El pago no puede ser anterior a la solicitud**; **No se encontró la solicitud**.

## Solicitudes de compra (`/dashboard/purchases/applications`, `/nuevo`, `/editar/<id>`)
- **Para qué sirve:** ver y corregir las solicitudes de compra de productos.
- **Quién entra:** `App.Department.Administracion`, `App.Department.Administrator`.
- **Cómo se usa:** busca con **Buscar referencia, estado...**. Columnas: **ID**, **Referencia**, **Creado por**, **Estado**, **Creación**, **Acciones**. El lápiz (**Editar**) abre **Editar solicitud de compra**: **Datos generales** (**Referencia**, **Estado**, **Comentario**) y **Productos** (descripción, cantidad, marca, categoría, número de parte, **Proveedor**, **Herramienta** y **Producto en inventario**, con **Buscar productos en la lista...**). **Agregar ítem** y **Eliminar línea** ajustan los productos; **Actualizar orden** guarda y **Volver a solicitudes** sale.
- **Estados y reglas:** mismos estados que en OC. Existe la pantalla **Nueva solicitud de compra** (**Crear orden**), pero la lista no trae botón para llegar a ella. El bote (**Eliminar**) actúa de inmediato, sin pedir confirmación, y avisa **Solicitud eliminada**, pero la solicitud no se borra: sigue en la lista como **Cancelado**.
- **Problemas frecuentes:** **Sin solicitudes de compra**; **Solicitud no encontrada** (vuelve a la lista y ábrela desde ahí); **Ocurrió un error al actualizar la orden de compra.**; **Revisa los datos del formulario**.

## Aprobar S.C. (`/dashboard/operations/purchases/approve`)
- **Para qué sirve:** autorizar solicitudes de compra pendientes.
- **Quién entra:** `App.Department.Operaciones`, `App.Department.Administrator`.
- **Cómo se usa:** en **Aprobar solicitudes de compra** busca con **Buscar referencia, estado...** y pulsa **Seleccionar** en la fila. Se abre el detalle: **Items de la solicitud** (solo lectura), **Estado de la solicitud** e **Historial de eventos**. **Aprobar** autoriza la solicitud (**Orden actualizada**); **Volver a la lista** regresa sin cambios.
- **Estados y reglas:** **Aprobar** solo se activa con la solicitud en **Pendiente**; al aprobar pasa a **Autorizado**. No hay botón para rechazar. La columna **Aprobado por** muestra a quien creó la solicitud, no a quien la aprueba.
- **Problemas frecuentes:** **Sin solicitudes de compra pendientes**; **Ocurrió un error al actualizar la orden de compra.**

## Órdenes de Compra, vista combinada (fuera del menú) (`/dashboard/administracion/purchases/pos`)
Junta en pestañas (**Solicitudes de OC** y **Órdenes de Compra**) las dos pantallas anteriores. Se llega desde **Crear orden de compra** en Entregas de SM: abre el formulario con los productos de la SM ya cargados y sin **Agregar Ítem**. Al guardar o cancelar intenta volver a Entregas de SM; si tu perfil no tiene acceso a esa ruta, regresas al inicio y la orden ya quedó creada. Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Autorizar Compra (fuera del menú) (`/dashboard/administracion/purchases/pos/fast-order`)
Se abre con **Por Autorizar** en Entregas de SM. Muestra los ítems pendientes de proveedores de entrega rápida, por proveedor y SM, una orden por grupo. Por proveedor: **Folio Proveedor**, **Datos del Proveedor** (**Nombre \***), productos editables y **Ver SMs (n)**, donde se captura **Cant.** y **Folio \*** de cada SM. **Aprobar** y **Confirmar** crean las órdenes y marcan los ítems de la SM como Autorizado. Avisos: **Órdenes creadas**; **Resultado parcial** (algunas fallaron y las SM no se actualizan); **Órdenes creadas, fallo en actualización SM** (revisa el estado a mano); **No hay items fast order pendientes.** Al terminar intenta llevarte a Entregas de SM (misma salvedad de acceso). Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Pedido a proveedor (fuera del menú) (`/dashboard/administracion/pedido-proveedor`)
Pantalla sin uso real: **Pedidos de Proveedor** es un formulario (**ID Proveedor**, **Nombre**, **Correo del Vendedor**, **Teléfono**, **Dirección**, **Marcas**, etc.) con **Limpiar Campos**, **Agregar Proveedor**, **Actualizar Proveedor** y **Eliminar Proveedor**. No lista proveedores, así que **Actualizar** y **Eliminar** no tienen a cuál aplicarse, y **ID Proveedor** y **Marcas** no aceptan texto. Para administrar proveedores usa **Catálogo Proveedores**. Entran `App.Department.Administracion` y `App.Department.Administrator`.
