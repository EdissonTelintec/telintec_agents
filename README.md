# telintec_agents

Servicio de agentes de IA de Telintec, sobre OpenAI (`openai-agents` + ChatKit):

- **Agente virtual de ventas** ("Robotín"): atiende visitantes en telintec.mx y, después, Telegram, WhatsApp, Facebook e Instagram; busca productos en el catálogo, presenta los servicios y levanta solicitudes de cotización que llegan a ventas por correo.
- **Asistente de la webapp**: orienta a los usuarios con sesión sobre el uso de la webapp; después consulta datos y actúa con los permisos del usuario.

Diseño, decisiones y pendientes: `GUITelintec/docs/agentes_openai.md` y `GUITelintec/docs/pendientes.md` (sección "Agentes OpenAI").

## Estado

| Fase | Qué | Estado |
|---|---|---|
| F0 | esqueleto: configuración, health, verificación ES256, Store de ChatKit en MySQL, pruebas | hecho (2026-11-05) |
| F1 | agente virtual de ventas en la web (ChatKit) | pendiente `P-240` |
| F2 | Telegram | pendiente `P-242` |
| F3 | asistente de la webapp | pendiente `P-243` |
| F4 | asistente con permisos | pendiente `P-245` |
| F5 | WhatsApp, Facebook, Instagram, búsqueda semántica | pendiente `P-246` |

## Requisitos

- Python 3.12.
- MySQL con el esquema `sql_telintec_mod_agents` y el usuario `agents_svc` (`GUITelintec/scripts_db_handle/agentes_schema_y_usuario.sql` y `agentes_schema_v2.sql`).
- Las llaves públicas del login (`token_public_<kid>.pem`) en la carpeta del `.env` o en `TOKEN_PUBLIC_KEYS_DIR`.

## Configuración

El servicio lee un `.env` en el repo o en la carpeta padre (como el API en prod); no hay plantilla en el repo: la lista de variables la tiene el lead de back (`CLAUDE.md` local) y `agents_service/config.py` las documenta. `AGENTS_ENVIRONMENT` tiene que ser `dev` o `prod`; sin eso el servicio no arranca. Las variables del sistema ganan sobre el archivo.

## Correr

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Linux: .venv/bin/pip
# .env con las variables (ver Configuración)
.venv/Scripts/uvicorn agents_service.main:app --host 127.0.0.1 --port 8100
curl http://127.0.0.1:8100/agents/health            # OK
```

Pruebas: `python -m pytest` (las del Store usan la BD de dev del `.env`; se saltan si no hay).

## Endpoints (F0)

| Método y ruta | Auth | Respuesta |
|---|---|---|
| `GET /agents/health` | no | `OK` (texto, 200) |
| `GET /agents/assistant/me` | `Authorization: <JWT crudo>` (ES256) | 200 `{"data": {user, emp_id, name, permissions, exp}, "msg": "ok", "error": null}` · 401 `{"data": null, "msg": "No autorizado. Token invalido", "error": "..."}` |

El JWT va crudo, sin `Bearer `, igual que en el API. Tokens HS256 o sin `exp`/`iat` se rechazan.

## Producción (plan, `P-248`)

Unidad systemd `telintec-agents` con uvicorn en `127.0.0.1:8100` en el servidor del API, nginx con `location /agents/` (`proxy_buffering off`, `proxy_read_timeout 120`, `limit_req` por IP) en `appinterna.telintec.mx`. Reemplaza a la unidad `chatbot` vieja. Detalle en `GUITelintec/docs/agentes_openai.md`.

## Servidor simulado (equipo de front)

Sirve para probar la integración de los widgets sin OpenAI, sin MySQL y sin `.env`; no toca prod.

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Linux/Mac: .venv/bin/pip
.venv/Scripts/python scripts/mock_server.py       # http://127.0.0.1:8100/agents
```

En la webapp: `NEXT_PUBLIC_AGENTS_URL=http://127.0.0.1:8100/agents`.

- Tiene las mismas rutas, el mismo protocolo de ChatKit y el mismo 401 con envelope que el servicio. Las conversaciones viven en memoria y se pierden al apagar.
- CORS: acepta cualquier `http://localhost:<puerto>`; para otro origen usa `--origin`. `--delay 0` quita la pausa entre palabras y `--host 0.0.0.0` lo abre a la red local.
- Asistente: manda el JWT del login crudo en `Authorization`, sin `Bearer`. El simulado revisa ES256, `exp`/`iat` y vigencia, **pero no la firma**. Responde con el usuario, los permisos y la guía que le toca a `X-Page-Context`, para confirmar que los encabezados llegan bien.
- Cada caso se provoca con una palabra en el mensaje:

| Palabra | Respuesta |
|---|---|
| cualquier otra | saludo con eco del mensaje (ventas) o del token y la pantalla (asistente), en stream |
| `producto` | lista de productos en markdown con fotos de `ftp3.syscom.mx` (datos de ejemplo) |
| `cotización` | confirmación con folio `SIM-0001`; no guarda nada ni avisa a ventas |
| `markdown` | encabezado, listas, tabla, enlace y cita |
| `guía` | (asistente) resumen de la guía de la pantalla, con cita a la guía |
| `tope`, `fuera de tema`, `error` | los textos fijos del servicio, en un solo evento como en prod |

No simula las respuestas reales, el catálogo real ni el filtro de temas: eso se valida contra prod. El `domainKey` lo valida el widget en el navegador, igual que con prod.

## Guías del asistente de la webapp (equipo de front)

Las guías viven en `knowledge/help/`, una por módulo del menú de la webapp. Formato, reglas de redacción, ejemplo de referencia (`almacen.md`) y pasos para el equipo de front en [`knowledge/help/README.md`](knowledge/help/README.md). Repositorio: `https://github.com/EdissonTelintec/telintec_agents.git`. El front no escribe aquí: redacta en una carpeta dedicada de su propio repositorio y el usuario trae los archivos a `knowledge/help/`.
