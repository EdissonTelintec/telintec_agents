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

## Control de Gastos Varios (`/dashboard/administracion/control-gastos-varios`)
Pantalla reservada: muestra **Sección en desarrollo** y aún no tiene funcionalidad. Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Estado de contratos (fuera del menú) (`/dashboard/administracion/estado-contratos`)
Vista anterior del alta de contratos, con **Emisión**, **Código de Cotización**, **Crear Contrato** y **Eliminar Contrato**, sin lista. Para crear y editar contratos usa **Contratos**. Entran `App.Department.Administracion` y `App.Department.Administrator`.

## Estado de cuenta (fuera del menú) (`/dashboard/administracion/estado-cuenta`)
Pantalla sin uso: tiene **Nombre de la Cuenta**, **Saldo**, **Crear Estado de Cuenta** y **Eliminar Estado de Cuenta**, pero no guarda nada; al intentarlo muestra **Ocurrió un error al crear el estado de cuenta.** Entran `App.Department.Administracion` y `App.Department.Administrator`.
