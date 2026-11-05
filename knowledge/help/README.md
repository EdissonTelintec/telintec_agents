# Base de conocimiento del asistente de la webapp (`knowledge/help/`)

Un `.md` por módulo del menú de la webapp (`src/constants/nav.ts` del repo `telintec_webapp`). El asistente recibe en su prompt el índice de módulos (título, rutas y una línea de resumen), el documento completo del módulo de la pantalla donde está el usuario (encabezado `X-Page-Context`) y puede leer cualquier otro con la tool `leer_guia`. Si hay vector store (`OPENAI_VECTOR_STORE_ID` en el `.env`), `scripts/sync_kb.py` sube estos mismos archivos para File Search.

Lo redacta el back desde el código del front y sus guías de prueba; **lo revisa el usuario** (`P-243`). El asistente solo explica cómo se usa la webapp: no ejecuta acciones ni consulta datos (eso llega en F4).

## Formato

Encabezado obligatorio al inicio del archivo (una clave por línea, entre dos líneas `---`):

```
---
modulo: cobranza
titulo: Cobranza
rutas: /dashboard/administracion/control-saldos, /dashboard/cobranza
permisos: App.Department.Administrator, App.Department.Administracion, App.Department.adminCobranza
resumen: Control de saldos por contrato y cobranza de remisiones.
---
```

- `modulo`: slug = nombre del archivo sin `.md` (minúsculas, guion bajo).
- `titulo`: el nombre del módulo como aparece en el menú.
- `rutas`: prefijos de ruta de la webapp que cubre el documento, separados por coma; para una pantalla gana el prefijo más largo entre todos los archivos.
- `permisos`: nombres completos del catálogo (`App.Department.<x>`) con los que se ve el módulo (de `src/constants/route-permissions.ts` y `nav.ts`).
- `resumen`: una línea; es lo que ve el asistente en el índice.

Cuerpo:

```
# <Título del módulo>

2 a 4 líneas: para qué sirve el módulo y quién lo usa.

## <Nombre de la pantalla como en el menú> (`/ruta`)
- **Para qué sirve:** ...
- **Quién entra:** permisos con nombre completo del catálogo.
- **Cómo se usa:** pasos en orden; botones, pestañas y filtros con su texto exacto; qué descarga cada botón.
- **Estados y reglas:** qué significa cada estado y qué se puede o no hacer en cada uno.
- **Problemas frecuentes:** mensajes que aparecen y qué hacer.
```

Si una pantalla tiene subpantallas (`/nuevo`, `/editar`, `/[id]`), van dentro de su sección, no como sección aparte.

## Reglas de redacción

- Español neutro, instrucciones directas ("Haz clic en **Nueva solicitud**"). Nada de jerga del código: no mencionar componentes, hooks, endpoints, archivos ni ids de pendientes (`P-NNN`).
- Solo lo verificado en el código del front (`src/components/<dominio>/`, `src/constants/`), en sus guías de prueba (`docs/pruebas/`) o en las docs del API (`GUITelintec/docs/`). Lo que no se pudo confirmar se marca con **(por confirmar)** para que el usuario lo revise.
- Nombres de botones, columnas, pestañas y estados tal como se ven en pantalla.
- Máximo ~1 200 palabras por archivo; si un módulo da para más, resumir cada pantalla, no omitir pantallas.
- Sin datos sensibles: ni contraseñas, ni llaves, ni datos de personas.
- Nueva pantalla en la webapp → actualizar el `.md` de su módulo (y `rutas:` si cambia el prefijo) y, con vector store, correr `python scripts/sync_kb.py`.

## Archivos

| Archivo | Módulo del menú | Rutas |
|---|---|---|
| `inicio.md` | Inicio (entrar, menú, notificaciones, sesión) | `/dashboard`, `/login` |
| `administracion.md` | Administración (catálogos, contratos, control de entregas, cobranza remisión, entregas de SM, gastos varios, estado de contratos y de cuenta) | `/dashboard/administracion` |
| `compras.md` | Compras (solicitudes de OC, órdenes de compra, conciliación OC–Almacén, gestión de compras, solicitudes de compra, aprobar S.C.) | `/dashboard/administracion/purchases`, `/dashboard/administracion/conciliacion-oc-almacen`, `/dashboard/administracion/gestion-compras`, `/dashboard/administracion/pedido-proveedor`, `/dashboard/purchases`, `/dashboard/operations/purchases` |
| `cobranza.md` | Cobranza (control de saldos) | `/dashboard/administracion/control-saldos`, `/dashboard/cobranza` |
| `preventa.md` | Preventa (cotizaciones, cotizaciones CISCO, licitaciones) | `/dashboard/preventa`, `/dashboard/administracion/cotizaciones` |
| `sgi.md` | SGI (formatos ISO) | `/dashboard/sgi` |
| `almacen.md` | Almacén, Sucursal e Inventario de Almacén (visual) | `/dashboard/almacen`, `/dashboard/sucursal`, `/dashboard/administracion/inventario-almacen` |
| `vales_y_epp.md` | Vales y Almacén EPP (vales de EPP y herramientas, herramientas prestadas, aprobar vales, inventario EPP) | `/dashboard/voucher_general`, `/dashboard/almacen_epp`, `/dashboard/operations/aproveVoucher` |
| `control_activos.md` | Control de Activos y Checklist (base de datos de activos, estado de vehículos, checklist vehicular) | `/dashboard/administracion/base-datos-activos`, `/dashboard/administracion/control-estado-vehiculos`, `/dashboard/checklist`, `/dashboard/control-activos` |
| `comun.md` | Común (check-in, tareas/encuestas, mi nómina) | `/dashboard/comun` |
| `rrhh.md` | RRHH (dashboard, personal, check-ins, nómina, exámenes médicos, vacaciones, encuestas) | `/dashboard/rrhh` |
| `sm.md` | Solicitudes de Material (solicitudes, urgentes, control, entregas, despacho y firmas, aprobar SM-herramientas) | `/dashboard/sm`, `/dashboard/operations/sm-approve` |
| `operaciones.md` | Operaciones (aprobaciones centralizadas y confirmación de horas extra) | `/dashboard/operations`, `/dashboard/confirmaciones` |
| `lideres.md` | Líderes (cotización de actividad, tabla de remitos / control de reportes) | `/dashboard/lideres`, `/dashboard/administracion/control-reportes` |
| `usuarios_y_cargos.md` | Cargos, Usuarios del sistema y Bitácoras | `/dashboard/roles`, `/dashboard/usuarios-sistema`, `/dashboard/bitacoras` |
