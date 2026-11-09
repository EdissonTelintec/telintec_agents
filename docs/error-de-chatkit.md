# Error de ChatKit: el CORS del servicio rechaza `chatkit-frame-instance-id`

> 2026-11-09. Encontrado al probar `P-244` (asistente de la webapp) desde el front local contra el servidor simulado. Afecta también al servicio de producción. **El arreglo es del back** (repo `telintec_agents`); el front no cambia.

## Síntoma

- El panel del asistente carga bien: aparece el saludo "Hola, soy el asistente de la webapp. ¿Qué quieres hacer?", así que el `domainKey` y el script de ChatKit funcionan.
- Al mandar cualquier mensaje (p. ej. `hola`), ChatKit muestra un error y no llega respuesta.
- En la consola del servidor simulado solo aparece el preflight, nunca el `POST`:

```
INFO:     127.0.0.1:57665 - "OPTIONS /agents/assistant/chatkit HTTP/1.1" 400 Bad Request
INFO:     127.0.0.1:57665 - "OPTIONS /agents/assistant/chatkit HTTP/1.1" 400 Bad Request
```

## Causa

ChatKit agrega **por su cuenta** un encabezado que no está en el contrato: `chatkit-frame-instance-id`. El front no lo escribe; lo pone el propio componente de OpenAI en cada petición.

Encabezados reales de la petición `POST /agents/assistant/chatkit`, capturados en el navegador (`threads.create` con el mensaje `hola`, desde `http://localhost:3000/dashboard`):

```
accept-language: es-419
authorization: <JWT crudo, 950 caracteres, sin "Bearer ">
chatkit-frame-instance-id: aae6730d-e59d-4391-94a6-99fb7498f74d
content-type: application/json
x-page-context: /dashboard
```

Como la petición lleva encabezados que no son "simples", el navegador primero manda un `OPTIONS` (preflight) con:

```
Origin: http://localhost:3000
Access-Control-Request-Method: POST
Access-Control-Request-Headers: accept-language,authorization,chatkit-frame-instance-id,content-type,x-page-context
```

El `CORSMiddleware` de FastAPI solo permite `Authorization`, `Content-Type` y `X-Page-Context` (más los encabezados simples como `Accept-Language`). Al ver `chatkit-frame-instance-id` responde **400 `Disallowed CORS headers`** y el navegador cancela el `POST`.

## Reproducción con curl (sin navegador)

Servidor simulado:

```bash
curl -i -X OPTIONS http://127.0.0.1:8100/agents/assistant/chatkit \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: accept-language,authorization,chatkit-frame-instance-id,content-type,x-page-context"
# HTTP/1.1 400 Bad Request
# Disallowed CORS headers
```

Producción (con el origen de Amplify, que sí está en `CORS_ORIGINS`):

```bash
curl -i -X OPTIONS https://appinterna.telintec.mx/agents/assistant/chatkit \
  -H "Origin: https://main.d2vgjmty2204yz.amplifyapp.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: accept-language,authorization,chatkit-frame-instance-id,content-type,x-page-context"
# HTTP/1.1 400 Bad Request
# Disallowed CORS headers
```

Control: el mismo preflight **sin** `chatkit-frame-instance-id` responde `200 OK` en los dos.

| Prueba (preflight) | Simulado | Producción |
|---|---|---|
| `authorization,content-type,x-page-context` | 200 | 200 |
| `+ accept-language` | 200 | 200 |
| `+ chatkit-frame-instance-id` | **400** | **400** |

## Arreglo propuesto (back, `telintec_agents`)

Agregar el encabezado a `allow_headers` en los dos lugares donde se configura el CORS:

- `agents_service/main.py` (servicio real), ~línea 114
- `agents_service/mock.py` (servidor simulado), ~línea 394

```python
allow_headers=["Authorization", "Content-Type", "X-Page-Context", "ChatKit-Frame-Instance-Id"],
```

Notas:

- El servicio no necesita leer el encabezado; solo hay que dejarlo pasar en el CORS.
- Starlette compara los nombres sin distinguir mayúsculas.
- Aplica a los dos agentes: el widget de ventas en telintec.mx (`/agents/sales/chatkit`, `P-241`) usa el mismo componente y le va a pasar lo mismo.
- Sugerencia: una prueba en `tests/` con el preflight que manda ChatKit (los cinco encabezados de arriba), para que no se vuelva a romper si OpenAI agrega otro.
- Después del cambio: reiniciar el simulado y `sudo systemctl restart telintec-agents` en el servidor.

## Cómo verificar que quedó

1. El curl de arriba responde `200 OK` con `access-control-allow-headers` que incluye `ChatKit-Frame-Instance-Id`.
2. En la webapp, abrir el asistente y escribir `hola`: en el simulado contesta con el usuario y la pantalla (`/dashboard`); en la consola del servicio aparecen el `OPTIONS` 200 y el `POST` 200.

## Lo que ya está bien (descartado)

- `domainKey`: el panel carga y muestra el saludo.
- Origen: `http://localhost:3000` pasa en el simulado; el de Amplify pasa en producción.
- `Authorization`: va el JWT crudo, sin `Bearer`.
- `X-Page-Context`: llega la ruta real de la pantalla.
- URL: `NEXT_PUBLIC_AGENTS_URL` correcta (`http://127.0.0.1:8100/agents` en local).
