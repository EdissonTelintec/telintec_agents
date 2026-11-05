---
modulo: usuarios_y_cargos
titulo: Cargos, Usuarios del Sistema y Bitácoras
rutas: /dashboard/roles, /dashboard/usuarios-sistema, /dashboard/bitacoras
permisos: App.Department.Administrator, App.Department.Operaciones, App.Department.Administracion, App.Department.RRHH, App.Department.Bitacoras
resumen: Asignación de titulares y líderes por departamento, alta de usuarios del sistema y bitácora de eventos del personal (faltas, retardos, tiempo extra).
---

# Cargos, Usuarios del Sistema y Bitácoras

Tres pantallas sueltas del menú: **Cargos** define quién es titular o líder de cada puesto (eso decide, por ejemplo, qué contratos ve alguien en Solicitudes de Material y quién edita la tabla de control); **Usuarios del Sistema** crea el usuario de la webapp para un empleado; **Bitácoras** registra eventos del personal por día. Los permisos, contraseñas y bajas de usuarios se administran en la app de usuarios (GUI_System), que lleva el responsable de sistemas: en la webapp solo se lista, se crea y se edita lo que aquí se describe.

## Cargos (`/dashboard/roles`)
- **Para qué sirve:** asignar el **Titular**, los **Otros lideres** y, en Administración, los **Contratos** de cada cargo registrado por departamento.
- **Quién entra:** `App.Department.Operaciones`, `App.Department.Administracion`, `App.Department.RRHH`, `App.Department.Administrator`.
- **Cómo se usa:**
  1. En **Asignacion de Cargos** elige el departamento en **Selecciona el departamento** (solo aparecen los que tienen cargos).
  2. La tabla muestra **ID**, **Nombre**, **Titular** (o **Sin asignar**), **Departamento**, **Contratos** y **Acciones**.
  3. Pulsa el lápiz: en **Editar asignacion de <cargo>** elige el **Titular** (lista de empleados activos del departamento), agrega **Otros lideres** con **Agregar lider secundario** (se quitan con la **×**) y, solo en Administracion, los **Contratos** (**Selecciona un contrato**). Pulsa **Guardar cambios**.
- **Estados y reglas:** desde la webapp no se crean cargos nuevos ni se cambia su nombre; solo se reasignan personas y contratos. Un titular o líder secundario de un cargo con contratos ve y crea SM de esos contratos y puede editar el bloque del solicitante en Control de SM.
- **Problemas frecuentes:** **No hay cargos registrados para este departamento**; **Ocurrio un error al actualizar el cargo...** → reintenta. Si el empleado no aparece en la lista, revisa que esté activo y en ese departamento en RRHH → Personal.

## Usuarios del Sistema (`/dashboard/usuarios-sistema`)
- **Para qué sirve:** ver qué empleados activos tienen usuario de la webapp, crearlo cuando falta y marcar si tienen credenciales biométricas.
- **Quién entra:** `App.Department.Administrator`.
- **Cómo se usa:**
  1. Busca con **Buscar por nombre de empleado...**. Columnas: **Nombre**, **Contrato**, **Departamento**, **User**, **Biocredenciales** (**Sí** / **No**), **Acciones**.
  2. **Crear Usuario** (solo en filas sin usuario) abre **Crear Usuario del Sistema**: muestra **Información del Empleado**; captura el **Nombre de Usuario**; la **Contraseña Generada** sale sola (**Regenerar**, **Copiar**); marca los **Permisos del Usuario** (al menos uno; Administrador no se ofrece aquí) y pulsa **Crear Usuario** → **Confirmar creación de usuario** → **Sí**.
  3. **Editar** abre **Editar Usuario del Sistema**: los datos son de solo lectura; cambia el interruptor **Estado de Biocredenciales** y pulsa **Guardar Cambios**.
- **Estados y reglas:** anota o copia la contraseña antes de crear: **no se volverá a mostrar en pantalla**. El empleado debe cerrar sesión y volver a entrar para que un cambio de permisos le aplique. Cambiar permisos después, restablecer contraseñas o deshabilitar usuarios se hace en la app de usuarios; la baja de un empleado en RRHH deshabilita sus usuarios automáticamente. RRHH → Personal también ofrece **Crear usuario del sistema**, pero solo con permisos Común y Básico y únicamente a un Administrador.
- **Problemas frecuentes:** **Por favor, ingresa un nombre de usuario.** / **selecciona al menos un permiso.**; **El usuario no tiene un user asignado…** (crea primero el usuario); **Error al cargar usuarios del sistema** con el código: avisa a soporte técnico.

## Bitácoras (`/dashboard/bitacoras`)
- **Para qué sirve:** registrar por fecha los eventos de asistencia del personal: faltas, retardos, tiempo extra, salidas tempranas, guardias y extraordinarios. No está en el menú; se abre escribiendo la dirección.
- **Quién entra:** `App.Department.Bitacoras`, `App.Department.Administrator`. Quien además tiene `App.Department.Operaciones` ve todos los contratos y empleados; los demás solo los de su contrato.
- **Cómo se usa:**
  1. La pantalla **Logs** tiene las pestañas **Individual Register** y **Multiple Register** (los textos de esta pantalla están en inglés).
  2. En **Individual Register** elige el contrato (**All Contracts**), el empleado (**All Employees** o uno; sin Operaciones queda fijo tu nombre) y la fecha. La tabla ordena por **Nombre**, **Contrato**, **Evento**, **Timestamp** y **Valor**, y cada fila tiene **Editar** y **Eliminar**.
  3. **Create Event** abre **Create New Event**: **Date** (no futura), **Contract**, **Employee**, **Event Type** (**Normal**, **Falta**, **Retardos**, **Tiempo Extra**, **Salida temprana**, **Guardia pasiva**, **Extraordinario**), **Hours** y **Minutes** (retardos, tiempo extra y salida temprana), **Place** y **Activity** (todos menos falta), **Incidence** para faltas (**ACUERDO**, **PERMISO SIN GOSE**, **FESTIVO**, **VACACIONES**, **INCAPACIDAD**, **SUSPENSION**), **Comment**, **Hour In** / **Hour Out** (extraordinario) y la casilla **Prima** (tiempo extra). Pulsa **Crear Evento**; al editar, **Actualizar Evento**.
  4. En **Multiple Register** elige la fecha, agrega empleados con **Add employee**, llena la tarjeta de cada uno y pulsa **Create All Events (n/m)**.
- **Estados y reglas:** en el registro múltiple cada tarjeta necesita evento, lugar, actividad y horas o minutos mayores a cero; el botón se habilita cuando todas están completas. El evento **falta** se muestra en rojo y **extra** en azul en la tabla.
- **Problemas frecuentes:** **¿Está seguro de que desea eliminar este evento?** confirma el borrado; **Error al crear el evento** / **Error al actualizar el evento** → revisa los campos y reintenta; **Please log in to view this page.** si la sesión expiró.
