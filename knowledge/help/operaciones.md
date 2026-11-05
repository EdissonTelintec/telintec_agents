---
modulo: operaciones
titulo: Operaciones
rutas: /dashboard/operations, /dashboard/confirmaciones
permisos: App.Department.Operaciones, App.Department.Administrator
resumen: Aprobaciones de Operaciones: ítems de SM con herramientas, solicitudes de compra, vales de herramientas y confirmaciones de horas extra.
---

# Operaciones

Aquí los responsables de Operaciones aprueban lo que el personal solicita antes de que Almacén o Compras lo procesen: ítems de solicitudes de material que requieren visto bueno, solicitudes de compra, vales de herramientas y equipo, y las confirmaciones de tiempo extra. Cada pantalla solo aprueba; ninguna tiene botón de rechazo. El detalle de cada flujo está en su módulo de origen: Solicitudes de Material, Compras y Vales.

## Aprobar SM-Herramientas (`/dashboard/operations/sm-approve`)
- **Para qué sirve:** aprobar, uno por uno, los ítems de las solicitudes de material marcados como pendientes de aprobación (pantalla "Aprobación de Solicitudes de Herramientas").
- **Quién entra:** App.Department.Operaciones, App.Department.Administrator.
- **Cómo se usa:** el encabezado dice cuántos ítems están pendientes. Busca con "Buscar por folio, contrato..."; la tabla muestra **Folio**, **Contrato**, **Planta**, **Área**, **Fecha**, **Ítem** y **Acciones**. Haz clic en la fila (o en la flecha) para ver "Información de la Solicitud" (Destino, Orden / Cotización, Fecha Crítica, Contacto Contrato, Proyecto, Descripción de Actividad, Comentario SM) y "Detalle del Ítem" (Cantidad Solicitada, Stock, Despachado, SKU, Partida, Comentario del Ítem, URL). Pulsa **Aprobar**: sale "Ítem aprobado" y la fila desaparece; el ítem deja de requerir aprobación y la SM sigue su proceso en Almacén **(por confirmar)**. Detalle del flujo de SM en el módulo Solicitudes de Material.
- **Estados y reglas:** solo se listan ítems pendientes de aprobación; 10 por página.
- **Problemas frecuentes:** "No hay ítems pendientes de aprobación" · "Error al cargar las solicitudes" con **Reintentar** · "Sin conexión a internet. Verifica tu conexión y vuelve a intentar." · "No se pudo aprobar el ítem."

## Aprobar S.C. (`/dashboard/operations/purchases/approve`)
- **Para qué sirve:** autorizar solicitudes de compra ("Aprobar solicitudes de compra").
- **Quién entra:** App.Department.Operaciones, App.Department.Administrator.
- **Cómo se usa:** la tabla muestra **ID**, **Referencia**, **Creado por**, **Aprobado por**, **Estado**, **Creación** y **Acciones**, con el buscador "Buscar referencia, estado..." y el contador **Total**. Pulsa **Seleccionar** en una fila: arriba aparece el panel con **Items de la solicitud** (Nombre, Cantidad, Marca, Herramienta), **Estado de la solicitud** e **Historial de eventos**. Pulsa **Aprobar**: sale "Orden actualizada" y la solicitud pasa a **Autorizado** para que Compras la gestione (módulo Compras). **Volver a la lista** cierra el panel.
- **Estados y reglas:** **Pendiente**, **Autorizado**, **Adquirido**, **Finalizado**, **Cancelado**. **Aprobar** solo está activo cuando la solicitud está en Pendiente.
- **Problemas frecuentes:** "Sin solicitudes de compra pendientes" · "Ocurrió un error al actualizar la orden de compra."

## Aprobar Vales (`/dashboard/operations/aproveVoucher`)
- **Para qué sirve:** autorizar vales de herramientas y equipo ("Aprobar vales (operaciones)") y consultar las herramientas prestadas y asignadas.
- **Quién entra:** App.Department.Operaciones, App.Department.Administrator.
- **Cómo se usa:** pestaña **Vale de Herramientas y Equipo**: tabla con **Contrato**, **Transaccion**, **Empleado Solicitante**, **Empleado designado**, **Estado** y **Acciones** (ojo). Al abrir un vale se ven **Items de la solicitud** (Nombre, Cantidad, Observaciones, Unidad) y el **Historial de eventos**; pulsa **Aprobar Vale** → "Orden actualizada". Después Almacén lo despacha desde Almacén → Despachar vales **(por confirmar)**; detalle en el módulo Vales. Pestaña **Herramientas en Préstamo**: listas de solo lectura "Herramientas en Préstamo" y "Herramientas Asignadas" con la columna **Estado de Almacen** (Pendiente, En proceso, Completado). Se muestran los vales del último año.
- **Estados y reglas:** **Pendiente** / **Aprobado**; **Aprobar Vale** solo está activo en Pendiente.
- **Problemas frecuentes:** "No se encontraron resultados." · "Acceso denegado. Por favor inicia sesión." · "Ocurrió un error al actualizar la orden de compra." (es el mismo aviso aunque sea un vale).

## Confirmacion de horas extra (`/dashboard/confirmaciones`)
- **Para qué sirve:** aprobar las confirmaciones de tiempo extra del personal, por día ("Confirmaciones").
- **Quién entra:** App.Department.Operaciones, App.Department.Administrator.
- **Cómo se usa:** elige el día con el botón de fecha (hoy por defecto) y busca con "Buscar por nombre...". La tabla muestra **Nombre**, **Contrato**, **Fecha**, **Comentario** y **Accion**. Pulsa **Ver detalles**: la ventana muestra Valor, Fecha, Contrato, Incidencia, Actividad, Lugar y Comentario; pulsa **Aprobar** → "Confirmación aprobada". Las ya aprobadas muestran **Aprobado** y el comentario "Tiempo extra autorizado". **Cerrar** sale sin aprobar.
- **Estados y reglas:** una confirmación aprobada no se vuelve a aprobar ni se revierte desde aquí.
- **Problemas frecuentes:** "No se encontraron confirmaciones para esta fecha." · "Error al cargar las confirmaciones" · "Hubo un error al aprobar la confirmación." · "No se pudo obtener el ID del usuario." (vuelve a iniciar sesión).
