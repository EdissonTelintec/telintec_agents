---
modulo: vales_y_epp
titulo: Vales y Almacén EPP
rutas: /dashboard/voucher_general, /dashboard/almacen_epp, /dashboard/operations/aproveVoucher
permisos: App.Department.Administrator, App.Department.Voucher, App.Department.voucherSafe, App.Department.voucherTool, App.Department.voucherApprove, App.Department.Epp, App.Department.eppVisual, App.Department.eppApprove, App.Department.Operaciones
resumen: Vales de EPP y de herramientas (crear, editar, anexos, historial), su aprobación por Seguridad y Operaciones, e inventario EPP de consulta.
---

# Vales y Almacén EPP

Aquí se capturan los vales con los que el personal de Operaciones pide equipo de protección personal (EPP) o herramientas y equipo, se aprueban (Seguridad aprueba los de EPP; el jefe de Operaciones los de herramientas) y se consulta el inventario de EPP. El despacho físico lo hace Almacén en **Almacén → Despachar vales** (guía de Almacén). Todas las listas muestran los vales de los últimos 12 meses.

## Vales de EPP (`/dashboard/voucher_general/valeEpp`)
- **Para qué sirve:** lista, crea, edita y elimina vales de seguridad (EPP).
- **Quién entra:** App.Department.Voucher, App.Department.voucherSafe, App.Department.Administrator.
- **Cómo se usa:**
  - Lista: busca con **Buscar empleado, contrato...**; columnas **Contrato** (identificador y abreviatura, ordenable), **Motivo**, **Empleado**, **Emp. Seguridad**, **Almacén**, **Designado** y **Estado**; 10 filas por página. Iconos por fila: lápiz **Editar** y bote **Eliminar** (diálogo **Confirmar acción** → **Confirmar eliminación**).
  - **Nuevo Vale EPP** (`/nuevo`, pantalla **Nuevo Vale de Seguridad**): en **Datos generales** elige **Persona asignada** (solo personal de Operaciones), **Contrato**, **Motivo** (**Reposición**, **Extraviado**, **Nuevo**), **Responsable almacén** (auxiliar almacenista) y **Empleado de Seguridad**. En **Productos de Seguridad** pulsa **Agregar producto**, busca con **Buscar productos...**, elige en **Seleccionar un producto** (solo artículos del inventario EPP) y pulsa **Agregar**; ajusta **Cantidad** y **Observaciones** en la tabla. Termina con **Crear Vale**. Las firmas no se capturan aquí: "Las firmas de aprobación se capturarón al despachar el vale".
  - **Editar** (`/editar/<id>`, pantalla **Editar Vale de Seguridad**): mismo formulario (el motivo se llama **Pérdida o extravío**). En la tabla cada producto tiene **Editar** (cambia el producto) y **Eliminar**: un producto ya guardado queda atenuado y se puede **Restaurar**; uno recién agregado desaparece. Guarda con **Actualizar Vale EPP**. El bloque **Aprobaciones** muestra los nombres de **Responsable**, **Encargado de almacén** y **Personal de Seguridad**.
  - **Historial** (botón con reloj, arriba a la derecha) abre el panel **Historial de cambios**, con filtros por usuario, tipo de acción (**Creación**, **Edición**, **Eliminación**) y fechas **Desde** / **Hasta**.
  - **Anexos** (debajo del formulario): **Subir anexos** admite varios archivos PDF, JPG, PNG, WEBP o ZIP; confirma en **Confirmar creación** y verás **Subiendo 1 de N…**. Cada anexo tiene **Descargar** y **Eliminar** (diálogo **Confirmar eliminación** con **Motivo (opcional)**, que queda en el historial). Subir un archivo con el mismo nombre reemplaza al anterior. Los anexos con etiqueta **Firma** se descargan, pero no se eliminan.
- **Estados y reglas:** **Estado** es la aprobación de Seguridad: **Pendiente**, **Aprobado** o **Rechazado**. Motivos: **Reposición**, **Pérdida / Extravío**, **Nuevo**. Un vale necesita contrato y al menos un producto con cantidad mayor a 0. Guardar el vale no borra sus anexos ni su historial.
- **Problemas frecuentes:** "Selecciona un contrato válido", "Debe agregar al menos un item" o "Cantidad requerida": completa el dato. "Debes seleccionar un producto válido.": elige un producto antes de **Agregar**. "Vale no encontrado": usa **Volver a la lista** y ábrelo desde ahí. "Existen productos sin ID de inventario cargados en este vale": el vale trae productos antiguos sin referencia al inventario; vuelve a agregarlos. Un archivo con "firma-…" en el nombre o con otra extensión no se sube (aviso "Un archivo no se puede subir"): renómbralo. Un anexo recién subido no muestra **Descargar** ni **Eliminar** hasta que la lista se relee.

## Vales de herramientas (`/dashboard/voucher_general/valeEpp/despachado-herramientas`)
- **Para qué sirve:** lista, crea, edita y elimina vales de herramientas y equipo (asignación o préstamo).
- **Quién entra:** App.Department.Voucher, App.Department.voucherTool, App.Department.Administrator.
- **Cómo se usa:**
  - Lista: **Buscar empleado, contrato...**; columnas **Contrato**, **Puesto**, **Tipo** (**Asignación** / **Préstamo**), **Usuario**, **Superior**, **Almacenista**, **Designado** y **Estado**; iconos **Editar** y **Eliminar** (**Confirmar acción** → **Confirmar eliminación**).
  - **Nuevo Vale Herramientas** (`/nuevoTool`, pantalla **Nuevo Vale de Herramientas y Equipo**): en **Requisitos generales** llena **Persona asignada**, **Contrato**, **Puesto del solicitante** (texto obligatorio), **Tipo de solicitud** (**Asignación** o **Préstamo**), **Responsable operaciones** (jefes de Operaciones) y **Responsable almacén**. En **Productos de Equipo o Herramienta** usa **Agregar producto** (solo muestra artículos marcados como herramienta). **Aprobaciones** muestra **Responsable**, **Encargado de almacén** y **Jefe inmediato**. Pulsa **Crear Vale**.
  - **Editar** (`/editarTool/<id>`, pantalla **Editar Vale de Herramientas**): **Datos generales** (el jefe se llama **Superior/jefe inmediato**), tabla **Productos de Herramientas y Equipos** con **Editar**, **Eliminar** / **Restaurar** y **Agregar producto**; guarda con **Actualizar Vale**. **Historial** y **Anexos** funcionan igual que en Vales de EPP.
- **Estados y reglas:** el **Estado** de la lista es el de almacén: **Pendiente**, **Aprobado** o **Rechazado**. Primero aprueba el jefe de Operaciones (**Aprobar vales**) y después despacha Almacén. Al guardar la edición, el vale se envía como aprobado por el superior y por almacén **(por confirmar)**.
- **Problemas frecuentes:** "Puesto requerido": escribe el puesto. Tras **Crear Vale** o al pulsar **Volver a la lista** desde el alta, la webapp lleva a **Vales de EPP**; si solo tienes `voucherTool` te regresa al inicio: abre **Vales de herramientas** desde el menú. Un vale ya despachado por Almacén puede mostrarse como **Rechazado** en esta lista **(por confirmar)**.

## Herramientas prestadas (`/dashboard/voucher_general/valeEpp/herramientas-prestadas`)
- **Para qué sirve:** consulta, sin editar, qué herramientas están en préstamo y cuáles asignadas.
- **Quién entra:** App.Department.Voucher, App.Department.voucherTool, App.Department.Administrator.
- **Cómo se usa:** dos bloques, **Herramientas en Préstamo** y **Herramientas Asignadas**, cada uno con su contador de registros, buscador **Buscar empleado, contrato...** y las columnas de Vales de herramientas más **Estado Almacén**.
- **Estados y reglas:** **Estado Almacén**: **Pendiente**, **En proceso** o **Completado**. No hay botones de crear, editar ni eliminar.
- **Problemas frecuentes:** "No se encontraron vales de herramientas": no hay vales de ese tipo en los últimos 12 meses o la búsqueda no coincide.

## Aprobar vales (`/dashboard/voucher_general/aprovacionEpp`) y Aprobar Vales (`/dashboard/operations/aproveVoucher`)
- **Para qué sirve:** el jefe de Operaciones autoriza los vales de herramientas y equipo. Las dos rutas abren la misma pantalla, **Aprobar vales (operaciones)**.
- **Quién entra:** en Vales: App.Department.Voucher, App.Department.voucherApprove, App.Department.Administrator; en Operaciones: App.Department.Operaciones, App.Department.Administrator.
- **Cómo se usa:** pestaña **Vale de Herramientas y Equipo**: columnas **Contrato**, **Transaccion**, **Empleado Solicitante**, **Empleado designado**, **Estado** y **Acciones**. Pulsa el ojo de la fila: arriba aparecen **Items de la solicitud** (Nombre, Cantidad, Observaciones, Unidad) e **Historial de eventos**; pulsa **Aprobar Vale**. Pestaña **Herramientas en Préstamo**: tablas de solo lectura **Herramientas en Préstamo** y **Herramientas Asignadas** con **Estado de Almacen**.
- **Estados y reglas:** **Estado** es la aprobación del superior: **Pendiente** o **Aprobado**. **Aprobar Vale** se desactiva cuando el vale ya está aprobado. Aprobar no despacha: eso lo hace Almacén.
- **Problemas frecuentes:** al aprobar, el aviso dice "Orden actualizada — La orden fue actualizada correctamente" (se refiere al vale, no a una orden de compra); el error dice "Ocurrió un error al actualizar la orden de compra". La columna **Transaccion** muestra **Asiganacion** también en préstamos; confía en la columna **Tipo** de Vales de herramientas. **Contrato** muestra "Not Found" si el contrato ya no está en el catálogo.

## Inventario EPP (`/dashboard/almacen_epp/inventario_epp`)
- **Para qué sirve:** consulta las existencias de equipo de protección personal.
- **Quién entra:** App.Department.Epp, App.Department.eppVisual, App.Department.Administrator.
- **Cómo se usa:** filtra con **Todas las categorias** y **Todos los proveedores**; busca con **Buscar productos...** (nombre, código de barras o número de parte) o con **Buscar por SKU o # de parte...** (una coincidencia exacta abre el detalle sola). Columnas **Nombre**, **Cod. Barras**, **# de Parte**, **Stock**, **Categoria**, **Proveedor**, **Marca**, **Ubicacion**, **Tipo** (etiquetas **Herramienta**, **Interno**, **EPP**) y **Acciones** (ojo **Ver detalles** → ventana **Detalle del Producto EPP**; cierra con **Cerrar**).
- **Estados y reglas:** solo lectura: aquí no se crean productos ni se registran entradas o salidas; eso se hace en Almacén con su permiso.
- **Problemas frecuentes:** "No se encontraron productos EPP.": quita los filtros o revisa la búsqueda.

## Aprobar vales — Almacén EPP (`/dashboard/almacen_epp/aproove_vouchers_epp`)
- **Para qué sirve:** Seguridad (EPP) aprueba los vales de seguridad antes de que Almacén los despache.
- **Quién entra:** App.Department.Epp, App.Department.eppApprove, App.Department.Administrator.
- **Cómo se usa:** pantalla **Aprobar Vales de Seguridad**, pestaña **Vale de Seguridad**: columnas **Contrato**, **Transaccion**, **Empleado Solicitante**, **Empleado designado**, **Estado** y **Acciones**. Pulsa el ojo: aparecen **Items de la solicitud** e **Historial de eventos**; pulsa **Aprobar**.
- **Estados y reglas:** **Estado**: **Pendiente** o **Aprobado**; el botón se desactiva en vales ya aprobados. La aprobación se refleja en la columna **Estado** de Vales de EPP.
- **Problemas frecuentes:** "Ocurrio un error al aprobar el vale de seguridad.": vuelve a intentar. La columna **Transaccion** no aplica a los vales de EPP (el formulario no la pide).
