---
modulo: administracion
titulo: Administración
rutas: /dashboard/administracion
permisos: App.Department.Administrator, App.Department.Administracion
resumen: Catálogos de clientes y proveedores, contratos con sus partidas, cobranza de remisiones, entregas de SM, gastos varios, estado de contratos y estado de cuenta.
---

# Administración

Módulo del personal de Administración: mantiene los catálogos de clientes y proveedores y los contratos con sus partidas, y reúne otras pantallas administrativas.

## Catálogo de Clientes (`/dashboard/administracion/db-management`, `/nuevo`, `/<id>`)
- **Para qué sirve:** consultar, crear, editar y eliminar clientes.
- **Quién entra:** `App.Department.Administracion`, `App.Department.Administrator`.
- **Cómo se usa:** busca con **Buscar cliente...** (columnas **ID**, **Nombre**, **Email**, **Teléfono**, **RFC**, **Dirección**). El lápiz (**Editar**) abre el cliente; el bote (**Eliminar**) pide **Confirmar eliminación**. **Nuevo Cliente** abre **Datos del cliente**: **ID Cliente**, **Nombre \***, **Email**, **Teléfono**, **RFC**, **Dirección**; guarda con **Crear Cliente** o **Actualizar Cliente**.
- **Estados y reglas:** solo **Nombre** es obligatorio; al editar, **ID Cliente** no se cambia. Eliminar no se deshace.
- **Problemas frecuentes:** **No se encontraron clientes** (crea uno con **Nuevo Cliente**); **Ocurrió un error al eliminar el cliente.**

## Catálogo Proveedores (`/dashboard/administracion/catalogo-proveedores`, `/nuevo`, `/<id>`)
- **Para qué sirve:** administrar proveedores y sus artículos (items) con precio.
- **Quién entra:** igual que Catálogo de Clientes.
- **Cómo se usa:** **Buscar proveedores...**; columnas **Nombre**, **Vendedor**, **Email**, **Teléfono**, **Tipo** (**En línea**, **Presencial**, **Materiales**), **Web**, **Marcas**, **RFC**, **Pedido rápido**. Lápiz edita y bote elimina (con confirmación). **Nuevo Proveedor** pide **Nombre \***, **Vendedor**, **Email del Vendedor**, **Teléfono**, **Dirección**, **Web / URL**, **RFC**, **Marcas** (separadas por coma), **Tipo** y **Pedido rápido**. En **Items del Proveedor**: **Agregar Item** (**Nombre del Item \***, **Número de Parte**, **Precio Unitario \***, **Producto Inventario**, **Moneda** MXN o USD) o **Cargar desde Excel** (.xlsx, .xls, .csv); la X quita un item. Nada se guarda hasta **Crear Proveedor** o **Actualizar Proveedor**.
- **Problemas frecuentes:** **No se encontraron items válidos en el archivo.**; **Por favor selecciona un archivo Excel (.xlsx, .xls) o CSV (.csv)**.

## Contratos (`/dashboard/administracion/contratos`, `/nuevo`, `/editar/<id>`)
- **Para qué sirve:** llevar los contratos y sus partidas.
- **Quién entra:** igual que Catálogo de Clientes.
- **Cómo se usa:** la lista trae **Buscar contrato...**, **Nuevo contrato** y las columnas **Abreviación**, **Identificador**, **N° Contrato**, **Pedido Exiros**, **Creación**; lápiz (**Editar contrato**) y bote (**Eliminar contrato**). **Información del contrato** pide **Fecha de emisión**, **Código de cotización**, **Planta**, **Área**, **Ubicación**, **Cliente**, **Número de contrato**, **Identificador del contrato**, **Abreviatura del contrato**, **Descripción**, **Observaciones** y **Número de pedido Exiros**. Las partidas entran por pestañas: **Desde documento** (**Archivo de productos** y **Cargar archivo**), **Desde datos** (**Agregar producto**, con **Partida**, **Descripcion**, **Cantidad**, **UDM**, **Precio Unitario**, **Tipo**, **Marca**, **Numero de Parte**, **Comentario**) y, al editar, **Ver partidas**. La **Lista de productos** muestra el **Total** y permite **Editar producto** o **Eliminar producto**. Cierra con **Crear contrato** o **Actualizar contrato** y confirma.
- **Estados y reglas:** un contrato en varias partes se ve por secciones (**Anterior**, **Siguiente**, **Subtotal**). Al editar, lo quitado se aplica al guardar. Eliminar un contrato borra sus partidas y no se deshace. El archivo de partidas es un Excel `.xlsx` con una tabla cuyos encabezados incluyan **POS.** o **PARTIDA**, **DESCRIPCIÓN** y **PRECIO**; un título dentro de la tabla abre una sección nueva.
- **Problemas frecuentes:** **Revisa las partidas** (indica cuáles); **No se detectaron partidas** (revisa columnas y formato); **Contrato creado con partidas pendientes** o **Contrato guardado con partidas pendientes** (algunas no se guardaron: revisa la lista); **No se encontró el contrato solicitado**.

## Cobranza Remision (`/dashboard/administracion/cobranza-remision`, `/nueva-diseno`, `/editar-diseno/<id>`, `/ver/<id>`, `/adjuntos/<id>`, `/anexos`, `/nueva`)
- **Para qué sirve:** crear y editar remisiones de actividad, adjuntarles reporte y evidencia fotográfica y descargar el PDF combinado.
- **Quién entra:** `App.Department.Administracion`, `App.Department.Administrator`.
- **Cómo se usa:**
  - **Lista** (**Remisión (Cobranza)**): busca con **Buscar por folio, cliente, contrato, pedido...** o filtra con **Selecciona contrato**. Cada fila trae lápiz (**Editar remisión**), ojo (**Ver documento de remisión**), clip (anexos) y bote (**Eliminar**, con confirmación). **Lista de anexos** reúne los archivos de todas las remisiones.
  - **Crear remisión:** elige el **Contrato \*** y captura **Folio**, **No. pedido**, **Remito**, **Planta**, **Área**, **Ubicación**, **Actividad** (se imprime), **Descripción general** y **Comentarios** (internos); todos son obligatorios. **Agregar / editar partidas** abre **Partidas del contrato**: marca, captura la cantidad y confirma con **Agregar**; el lápiz de cada fila cambia cantidad y precio. **Guardar borrador** conserva la captura en este navegador. **Crear remisión** se ve apagado hasta que la barra dice **Lista para crear**. Después, **Remisión creada** ofrece **Subir anexos ahora** o **Más tarde**.
  - **Editar** usa el mismo formulario (el contrato no cambia) con **Historial**, **Descartar cambios** y **Guardar cambios**. **Ver** es solo lectura, con **Descargar PDF** e **Imprimir**.
  - **Anexos de la remisión:** tres pasos. **Reporte**: un PDF y **Subir reporte**. **Evidencia**: hasta 10 imágenes JPG, PNG o WebP de 10 MB y **Guardar evidencia**. **Documento**: **Generar vista previa**, **Solo remisión** o **Descargar completo**. Elegir un archivo no lo sube: usa el botón del paso. El bote de un anexo pide **Confirmar eliminación**; las firmas no se quitan aquí.
  - **Lista de anexos:** busca archivo, folio o cliente, filtra por **Reportes**, **Evidencia**, **Firmas** u **Otros**, agrupa por folio y **Abrir anexos** va a la remisión.
- **Estados y reglas:** la lista trae todas las remisiones; **Estado** muestra **Abierta** o **Cerrada**. La columna **Anexos** marca **Sin anexos**, **Falta reporte**, **Falta evidencia** o **Completos** (cuentan reporte y evidencia). Máximo 10 partidas con cantidad; cantidad y precio mayores a 0. Existe además un formulario de creación con el diseño anterior, al que solo se llega desde **Remisiones (plantilla anterior)**.
- **Problemas frecuentes:** **Faltan campos obligatorios**; **Límite de partidas**; **Archivos sin subir** (usa el botón del paso antes de avanzar); **Tienes cambios sin guardar** (guarda o descarta antes de ir a Anexos).

## Entregas de SM (`/dashboard/administracion/entregas-de-sm`)
- **Para qué sirve:** registrar las entregas de material de cada ítem de una solicitud (SM) y pedir la orden de compra de lo que no hay en stock.
- **Quién entra:** `App.Department.Administracion`, `App.Department.Administrator`.
- **Cómo se usa:** elige la SM en **Buscar SM...** (Pendientes y Completadas). Por ítem ves lo solicitado, **Suministrado** y el faltante. **Agregar entrega** crea una tarjeta con estado, **Cantidad**, **Folio de OC**, **Folio de liberación** y **Comentario**; el lápiz la habilita. Marca **Realizar orden de compra** en los ítems sin stock y pulsa **Crear orden de compra**. **Guardar** o **Guardar entregas** confirma. **Por Autorizar** va a los pedidos rápidos de Compras.
- **Estados y reglas:** **Pendiente** (amarillo): sin atender. **En proceso** (amarillo): ya hay orden de compra y se espera el material; una entrega nueva nace así si el ítem tiene orden. **Validación** (rojo): en revisión. **Suministrado** (verde): entregado. **Autorizado** (verde): compra aprobada. El color manual (paleta, **Cambiar color**, **Quitar color**) manda sobre el del estado.
- **Problemas frecuentes:** **Sin items** (marca al menos un ítem); **Hubo un error al guardar las entregas.**; si **Agregar entrega** está apagado, indica por qué (**No hay cantidad disponible**, **Producto ya despachado, no requiere entrega**).

## Control de Gastos Varios (`/dashboard/administracion/control-gastos-varios`)
Pantalla reservada: muestra **Sección en desarrollo** y aún no tiene funcionalidad. Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Estado de contratos (fuera del menú) (`/dashboard/administracion/estado-contratos`)
Vista anterior del alta de contratos, con **Emisión**, **Código de Cotización**, **Crear Contrato** y **Eliminar Contrato**, sin lista. Para crear y editar contratos usa **Contratos**. Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Estado de cuenta (fuera del menú) (`/dashboard/administracion/estado-cuenta`)
Pantalla sin uso: tiene **Nombre de la Cuenta**, **Saldo**, **Crear Estado de Cuenta** y **Eliminar Estado de Cuenta**, pero no guarda nada; al intentarlo muestra **Ocurrió un error al crear el estado de cuenta.** Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Reportes de material (fuera del menú) (`/dashboard/administracion/reportes-material`)
Pantalla sin uso: formulario con **Nombre del Material**, **Cantidad**, **Unidad**, **Fecha** y **Descripción**, y los botones **Enviar Reporte** y **Limpiar Campos**. **Enviar Reporte** no guarda nada. Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Remisiones (plantilla anterior) (fuera del menú) (`/dashboard/administracion/remisiones`, `/nueva`, `/editar/<id>`)
Vista anterior, reemplazada por **Cobranza Remision**. **Gestión de Remisiones** lista con **Buscar remisiones...** y las acciones **Ver detalles**, **Editar** y **Eliminar**; **Crear Remisión** abre el formulario anterior de Cobranza y **Editar** regresa a su lista. Sus formularios de alta (**Crear nueva remisión**) y de edición tienen el diseño anterior. Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Licitación cerrada (fuera del menú) (`/dashboard/administracion/licitacion-cerrada`)
Pantalla incompleta, sin lista ni edición: solo **Título**, **Descripción**, **Fecha de Inicio**, **Fecha de Fin** y los botones **Crear Licitación** y **Eliminar Licitación**. Por ahora no guarda: al intentarlo muestra **Ocurrió un error al crear la licitación.** Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Items SMS (fuera del menú) (`/dashboard/administracion/controllerSms`)
Vista para corregir los ítems de una SM; para registrar entregas usa **Entregas de SM**. La **Lista de Solicitudes de Material** trae **Editar SM**, que abre **Editar Items** (**Nombre**, **Cantidad**, **Stock**, **Comentario**); **Actualizar items** guarda y **Volver a la lista** regresa. Por ahora falla al cargar y no se puede usar. Entran `App.Department.Administracion` y `App.Department.Administrator`.
