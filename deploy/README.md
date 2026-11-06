# Despliegue en el servidor de prod (Amazon Linux 2023, junto al API)

Guía paso a paso para el usuario (`P-248`). Todo como `ec2-user`; el checkout va en `/home/ec2-user/opt/telintec_agents` y el venv en `/home/ec2-user/opt/env_agents`, al lado de `GUITelintec` y `envg2`. No toca el API, su venv ni la BD.

## 1. Python 3.12 y código

```bash
sudo dnf install -y python3.12
cd /home/ec2-user/opt
git clone https://github.com/EdissonTelintec/telintec_agents.git
/usr/bin/python3.12 -m venv /home/ec2-user/opt/env_agents
/home/ec2-user/opt/env_agents/bin/pip install --upgrade pip
/home/ec2-user/opt/env_agents/bin/pip install -r /home/ec2-user/opt/telintec_agents/requirements.txt
/home/ec2-user/opt/env_agents/bin/python -c "import agents_service.main" 2>&1 | tail -1   # debe quejarse solo de AGENTS_ENVIRONMENT
```

Ese último comando falla a propósito ("AGENTS_ENVIRONMENT debe ser dev o prod") hasta que exista el `.env`: confirma que las dependencias importan.

## 2. `.env` del servicio

`/home/ec2-user/opt/telintec_agents/.env`, con `chmod 600`. Mismas llaves que en dev, con los valores de prod:

```
AGENTS_ENVIRONMENT=prod
DB_HOST=<el HOST_DB_AWS del .env del API>
DB_PORT=3306
DB_USER=agents_svc
DB_PASSWORD=<la del .sql>
DB_CATALOG=sql_telintec
DB_AGENTS=sql_telintec_mod_agents
DB_POOL_SIZE=5
TOKEN_PUBLIC_KEYS_DIR=/home/ec2-user/opt
TOKEN_PUBLIC_KIDS=lambda
OPENAI_API_KEY_SALES=<llave del proyecto de ventas>
OPENAI_API_KEY_ASSISTANT=<llave del proyecto del asistente>
OPENAI_MODEL=gpt-5.4-mini
OPENAI_MODEL_GUARDRAIL=gpt-6-luna
OPENAI_VECTOR_STORE_ID=
CORS_ORIGINS=https://telintec.mx,https://telintec.com.mx,https://main.d2vgjmty2204yz.amplifyapp.com
LIMIT_MESSAGES_PER_CONVERSATION=30
LIMIT_CONVERSATIONS_PER_IP_DAY=20
LIMIT_TOKENS_PER_DAY_SALES=3000000
LIMIT_OUTPUT_TOKENS=1000
LIMIT_TOKENS_PER_DAY_ASSISTANT=1000000
LIMIT_OUTPUT_TOKENS_ASSISTANT=900
SALES_WHATSAPP_URL=https://wa.me/message/TBYVN75NGL4JJ1
SALES_EMAILS=<correos de ventas, separados por coma>
QUOTE_NOTIFY_APPS=administracion,adminpreventa
SES_REGION=
SES_SENDER=
TRUST_PROXY=1
SERVICE_TIMEZONE=America/Mexico_City
CATALOG_DB_USER=catalog_sync
CATALOG_DB_PASSWORD=<la del .sql>
SYSCOM_CLIENT_ID=
SYSCOM_CLIENT_SECRET=
S3_CATALOG_BUCKET=<el S3_ADMIN_BUCKET del API>
TELEGRAM_TOKEN=<el TELEGRAM_TOKEN del .env del API>
TELEGRAM_WEBHOOK_SECRET=<uno nuevo: /usr/bin/python3.12 -c "import secrets; print(secrets.token_urlsafe(32))">
TELEGRAM_WEBHOOK_URL=https://appinterna.telintec.mx/agents/sales/telegram
TELEGRAM_SESSION_HOURS=24
```

`TOKEN_PUBLIC_KEYS_DIR=/home/ec2-user/opt` porque ahí ya está `token_public_lambda.pem` del API; no se copia nada. `OPENAI_VECTOR_STORE_ID` queda vacío: el asistente de la webapp trabaja con las guías locales de `knowledge/help/`; File Search es opcional (`python scripts/sync_kb.py` crea el vector store en el proyecto del asistente e imprime el id para ponerlo aquí).

## 3. Prueba a mano

```bash
sudo dnf install -y curl-minimal      # la instancia no trae curl
cd /home/ec2-user/opt/telintec_agents
/home/ec2-user/opt/env_agents/bin/python -m pytest -q tests/test_config.py tests/test_auth.py tests/test_health.py tests/test_sales_agent.py
/home/ec2-user/opt/env_agents/bin/uvicorn agents_service.main:app --host 127.0.0.1 --port 8100
```

En otra terminal: `curl http://127.0.0.1:8100/agents/health` → `OK`. Luego `Ctrl+C`. Las pruebas que escriben en la BD se saltan solas fuera de `dev`; no correr `RUN_LIVE=1` en prod.

## 4. systemd

```bash
sudo cp deploy/telintec-agents.service deploy/telintec-agents-purge.service deploy/telintec-agents-purge.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telintec-agents
sudo systemctl enable --now telintec-agents-purge.timer
systemctl status telintec-agents --no-pager
journalctl -u telintec-agents -n 50 --no-pager
curl http://127.0.0.1:8100/agents/health
```

## 5. nginx

nginx no hace TLS (el `server` de 443 de `nginx.conf` está comentado): el HTTPS de `appinterna.telintec.mx` lo termina un balanceador delante de la EC2, que reenvía por el 80. El `server {}` del API es `/etc/nginx/sites-available/chatbot` (`location /GUI` y `/chatbot`, `server_name` = DNS público de la EC2); recibe el tráfico de `appinterna` porque es el primer `server` del 80 (`sites-enabled/*` se incluye antes del `server_name _` de `nginx.conf`).

Con el balanceador delante, `$remote_addr` es la IP del balanceador: sin `real_ip`, el `limit_req` y los topes por IP contarían a todos los visitantes como uno solo.

```bash
sudo tail -n 5 /var/log/nginx/access.log         # 1a columna: el balanceador (172.31.x.x); la última ($http_x_forwarded_for): el visitante
nginx -V 2>&1 | tr ' ' '\n' | grep realip        # debe imprimir --with-http_realip_module
ls -l /etc/nginx/sites-enabled/                  # confirmar que chatbot está habilitado
sudo cp /etc/nginx/sites-available/chatbot /home/ec2-user/chatbot.nginx.bak   # respaldo fuera de /etc/nginx
sudo nano /etc/nginx/sites-available/chatbot
#   arriba, fuera del server {}:
#       limit_req_zone $binary_remote_addr zone=agents:10m rate=30r/m;
#   dentro del server {}, antes de los location (IP real del visitante; también la ve el API):
#       set_real_ip_from 172.31.0.0/16;
#       real_ip_header X-Forwarded-For;
#       real_ip_recursive on;
#   dentro del server {}, junto a location /chatbot: los dos location de deploy/nginx-agents.conf
#   (/agents/ con limit_req y = /agents/sales/telegram sin él)
sudo nginx -t && sudo systemctl reload nginx
curl https://appinterna.telintec.mx/agents/health      # desde fuera → OK
sudo tail -n 3 /var/log/nginx/access.log               # ahora la 1a columna debe ser la IP pública de quien hizo el curl
```

`172.31.0.0/16` es la VPC por defecto (la EC2 es `172.31.9.67`). Si la primera columna del log no es una `172.31.x.x` (por ejemplo, CloudFront directo a la EC2), el `set_real_ip_from` es otro: revisarlo antes de abrir al público.

Si el `curl` externo da 502 y `getenforce` dice `Enforcing`: `sudo setsebool -P httpd_can_network_connect 1` (nginx hablando a un puerto TCP local; el API usa socket unix y no lo necesitaba).

## 6. Telegram: apuntar el bot al servicio nuevo

Hasta aquí el bot `@telintec_AI_bot` sigue mandando sus mensajes al chatbot viejo (`/chatbot/telegram`). Con `/agents/health` respondiendo desde fuera:

```bash
cd /home/ec2-user/opt/telintec_agents
/home/ec2-user/opt/env_agents/bin/python scripts/telegram_webhook.py info        # webhook actual: .../chatbot/telegram
/home/ec2-user/opt/env_agents/bin/python scripts/telegram_webhook.py set --yes   # usa TELEGRAM_WEBHOOK_URL y el secreto del .env
```

Luego escribirle `/start` al bot desde Telegram y una pregunta de producto. `journalctl -u telintec-agents -n 30 --no-pager` debe mostrar el `POST /agents/sales/telegram` con 200; si `info` muestra un `último error`, casi siempre es el secreto (403: el `.env` del servicio no tiene el mismo que se mandó a Telegram, basta repetir `set --yes` tras corregirlo) o nginx (502). Desde este paso el chatbot viejo ya no recibe Telegram, así que el 7 va enseguida.

## 7. Unidad `chatbot` vieja

```bash
systemctl status chatbot --no-pager     # ver qué era
sudo systemctl disable --now chatbot
```

No borrar su carpeta ni su venv hasta `P-250`.

## 8. Actualizar después

```bash
cd /home/ec2-user/opt/telintec_agents && git pull
/home/ec2-user/opt/env_agents/bin/pip install -r requirements.txt
sudo systemctl restart telintec-agents && curl http://127.0.0.1:8100/agents/health
# solo si OPENAI_VECTOR_STORE_ID esta en el .env y cambiaron las guias de knowledge/help/:
/home/ec2-user/opt/env_agents/bin/python scripts/sync_kb.py
```

El `.env` se lee al arrancar: cualquier cambio en él pide `restart`.
