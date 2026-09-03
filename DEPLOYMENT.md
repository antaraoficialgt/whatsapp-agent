# Guía de Despliegue en Render.com 🚀

La forma más fácil y económica de desplegar tu WhatsApp Agent.

## ¿Por qué Render.com?

- ✅ **Gratis por 750 horas/mes** (suficiente para un servicio 24/7)
- ✅ **Sin tarjeta de crédito** requerida
- ✅ **HTTPS automático**
- ✅ **Muy fácil de usar**
- ✅ **Integración con GitHub**

## 📋 Pre-requisitos

1. Proyecto subido a GitHub (público o privado)
2. Cuenta en GitHub
3. Cuenta en [render.com](https://render.com)

---

## 🔧 Paso 1: Preparar el Proyecto

### 1.1 Crear archivo `render.yaml`

En la raíz de tu proyecto, crea:

```yaml
services:
  - type: web
    name: whatsapp-agent
    runtime: python
    pythonVersion: 3.11
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port 8000
    envVars:
      - key: DATABASE_URL
        value: sqlite:///./conversations.db
      - key: LOG_LEVEL
        value: INFO
      - key: DEBUG
        value: "False"
      - key: CLAUDE_API_KEY
        sync: false
      - key: WEBHOOK_VERIFY_TOKEN
        sync: false
      - key: SECRET_KEY
        sync: false
```

### 1.2 Verificar estructura de archivos

```
tu-proyecto/
├── main.py
├── webhook.py
├── claude_agent.py
├── database.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── render.yaml
```

### 1.3 Crear `.gitignore` (si no existe)

```
# Virtual Environment
venv/
env/
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db
```

### 1.4 Subir a GitHub

```bash
git init
git add .
git commit -m "Initial commit: WhatsApp Agent API"
git branch -M main
git remote add origin https://github.com/tu-usuario/whatsapp-agent.git
git push -u origin main
```

---

## 🚀 Paso 2: Deploy en Render.com

### 2.1 Conectar GitHub

1. Ve a [render.com](https://render.com)
2. Haz clic en **Sign up** (o Login si tienes cuenta)
3. Elige **GitHub** como método de autenticación
4. Autoriza Render para acceder a tus repositorios

### 2.2 Crear Web Service

1. En el dashboard de Render, haz clic en **New +**
2. Selecciona **Web Service**
3. Haz clic en **Connect a repository**
4. Busca tu repositorio `whatsapp-agent`
5. Haz clic en **Connect**

### 2.3 Configurar el Servicio

Rellena los campos:

```
Name:                    whatsapp-agent
Environment:             Python 3
Build Command:           pip install -r requirements.txt
Start Command:           uvicorn main:app --host 0.0.0.0 --port 8000
Branch:                  main
Auto-deploy:             ✓ (checked)
```

### 2.4 Agregar Variables de Entorno

Haz clic en **Environment** y añade:

| Key | Value | Notas |
|-----|-------|-------|
| `CLAUDE_API_KEY` | `sk-ant-v0-xxx...` | De console.anthropic.com |
| `WEBHOOK_VERIFY_TOKEN` | `tu-token-secreto-1234` | Cualquier string largo |
| `SECRET_KEY` | `tu-clave-super-fuerte` | Para seguridad de API |
| `DATABASE_URL` | `sqlite:///./conversations.db` | Por defecto está bien |
| `LOG_LEVEL` | `INFO` | O `DEBUG` si necesitas |
| `DEBUG` | `False` | Nunca `True` en producción |
| `HOST` | `0.0.0.0` | Por defecto |
| `PORT` | `8000` | Render mapea automáticamente |

### 2.5 Deploy

Haz clic en **Create Web Service**

Render comenzará a:
1. Clonar tu repositorio
2. Instalar dependencias
3. Iniciar el servidor

Esperamos a que veas: ✅ **Service is live**

---

## 🔗 Paso 3: Obtener tu URL

Después del deploy exitoso, verás algo como:

```
https://whatsapp-agent-abc12.onrender.com
```

Esta es tu **URL pública** que usarás para configurar en Meta.

---

## 📱 Paso 4: Configurar Webhook en Meta

### 4.1 En Meta Developers

1. Ve a [developers.facebook.com](https://developers.facebook.com)
2. Selecciona tu app de WhatsApp
3. Ve a **Configuración > Webhooks**
4. Haz clic en **Editar** o **Configurar**
5. Rellena:
   - **Callback URL**: `https://whatsapp-agent-abc12.onrender.com/webhook`
   - **Verify Token**: El mismo que en tu variable `WEBHOOK_VERIFY_TOKEN`
6. Haz clic en **Verificar y guardar**

Meta hará una solicitud GET a tu `/webhook` y debe responder correctamente.

### 4.2 Suscribirse a Webhooks

Después de verificar:
1. En **Webhooks**, haz clic en **Suscribirse a eventos**
2. Selecciona:
   - ✓ `messages`
   - ✓ `message_template_status_update` (opcional)
   - ✓ `message_template_quality_update` (opcional)
3. Haz clic en **Guardar**

---

## 🔐 Paso 5: Crear tu Primer Cliente

Ahora tu API está en línea. Crea un cliente:

```bash
curl -X POST https://whatsapp-agent-abc12.onrender.com/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Negocio",
    "phone_number_id": "1234567890123",
    "access_token": "EAAxxxxxxxxxxxxx",
    "system_prompt": "Eres un asistente amable que ayuda a los clientes..."
  }'
```

**Respuesta:**
```json
{
  "id": 1,
  "name": "Mi Negocio",
  "phone_number_id": "1234567890123",
  "api_key": "whatsapp_agent_abc123xyz...",
  "message": "Guarda tu API key en un lugar seguro."
}
```

✅ **¡Listo!** Tu sistema está activo.

---

## 📊 Monitoring

### Ver Logs en Render

En tu dashboard de Render:
1. Haz clic en tu servicio
2. Ve a **Logs**
3. Verás el output en tiempo real

Busca:
- `Service is live` ✓
- `Webhook received` cuando lleguen mensajes
- Errores en rojo

### Reiniciar Servicio

Si algo va mal:
1. En tu servicio, haz clic en **Manual Deploy**
2. O en **Restart Service** en el menú

### Ver Métricas

En **Metrics** puedes ver:
- CPU usage
- Memory
- Tiempo de respuesta
- Errores

---

## 🆘 Solución de Problemas

### "Service failed to build"

**Causa**: Error en `requirements.txt`

**Solución**:
```bash
# Verifica localmente
pip install -r requirements.txt

# Si falla, actualiza el archivo y haz push nuevamente
git add requirements.txt
git commit -m "Fix requirements"
git push
```

Render redesplegará automáticamente.

### "Application failed to start"

**Causa**: Error al ejecutar `main.py`

**Solución**:
1. Ve a **Logs** en Render
2. Busca el error específico
3. Verifica:
   - `CLAUDE_API_KEY` está configurado
   - No hay errores de sintaxis
   - Base de datos es escribible

### "Webhook verification failed"

**Causa**: Token incorrecto

**Solución**:
1. Verifica que `WEBHOOK_VERIFY_TOKEN` en Render es exactamente igual al de Meta
2. Reinicia el servicio: **Restart Service**
3. Intenta verificar de nuevo en Meta

### "Message sending fails"

**Causa**: Credenciales de Meta inválidas

**Solución**:
1. Verifica que `access_token` sigue siendo válido
2. Comprueba que `phone_number_id` es correcto
3. Intenta renovar el token en Meta

---

## 💾 Backup de Base de Datos

Render usa almacenamiento efímero por defecto. Si el servicio se reinicia, pierdes la DB.

### Opción 1: SQLite en Render (Simple)

Tu DB se perderá si Render reinicia, pero es suficiente para pruebas.

### Opción 2: PostgreSQL (Recomendado para Producción)

1. En Render, crea un **PostgreSQL Database**
2. Copia la connection string
3. Instala `psycopg2` en `requirements.txt`
4. Modifica `database.py` para usar PostgreSQL

Después de agregarla:

```
PostgreSQL URL: postgresql://user:pass@host:5432/db
```

### Opción 3: Descargar Backup Manual

```bash
# Desde tu máquina local (si tienes SSH)
# O simplemente exporta regularmente
```

---

## 🔄 Auto-Deploy

Render redesplegará automáticamente cada vez que hagas push a `main`:

```bash
# Hacer cambios
vim main.py

# Commit y push
git add .
git commit -m "Update system prompts"
git push origin main

# Render se desplegará automáticamente en ~1 min
```

Verifica en **Logs** que el nuevo deploy fue exitoso.

---

## 📈 Escalamiento

### Plan Gratuito
- **Hasta 750 horas/mes** (suficiente para 24/7)
- Ideal para: Pruebas, pequeños negocios

### Plan Pagado (~$7/mes)
- Horas ilimitadas
- Apoyo prioritario
- Mejor performance

Para cambiar, en tu servicio ve a **Settings > Plan**.

---

## 📞 Monitoreo en Tiempo Real

### Usar UptimeRobot (Gratis)

1. Ve a [uptimerobot.com](https://uptimerobot.com)
2. Crea una cuenta
3. Haz clic en **Add Monitor**
4. Configura:
   - URL: `https://whatsapp-agent-abc12.onrender.com/health`
   - Check every: 5 minutes
5. Te alertará si tu servicio cae

---

## 🎯 Resumen del Despliegue

| Paso | Acción | Tiempo |
|------|--------|--------|
| 1 | Subir a GitHub | 5 min |
| 2 | Deploy en Render | 2 min |
| 3 | Configurar Webhook | 5 min |
| 4 | Crear Cliente | 2 min |
| 5 | Verificar con curl | 2 min |
| **Total** | | **16 min** |

---

## ✅ Checklist de Despliegue

- [ ] Proyecto en GitHub
- [ ] `requirements.txt` incluye todas las dependencias
- [ ] `.env.example` documentado
- [ ] `render.yaml` creado
- [ ] Conectado Render con GitHub
- [ ] Variables de entorno configuradas en Render
- [ ] Deploy exitoso (status: "live")
- [ ] Webhook verificado en Meta
- [ ] Primer cliente creado
- [ ] Mensaje de prueba recibido y respondido
- [ ] Logs mostrado en Render

---

**¡Felicidades!** Tu WhatsApp Agent está en línea 24/7. 🎉

Para cualquier problema, revisa los logs en Render o la sección de "Solución de Problemas" más arriba.
