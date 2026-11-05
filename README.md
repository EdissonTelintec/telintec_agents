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

Copiar `.env.example` a `.env` (en el repo, o en la carpeta padre como el API en prod) y llenarlo. `AGENTS_ENVIRONMENT` tiene que ser `dev` o `prod`; sin eso el servicio no arranca. Las variables del sistema ganan sobre el archivo.

## Correr

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt     # Linux: .venv/bin/pip
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
