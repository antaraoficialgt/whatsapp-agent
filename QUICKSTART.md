# Quick Start ⚡ - 5 Minutos para Empezar

La forma más rápida de tener tu WhatsApp Agent funcionando.

## 🎯 Objetivo
Recibir mensajes en WhatsApp y responder automáticamente con IA en menos de 5 minutos.

---

## 1️⃣ Preparar tu Máquina (2 min)

```bash
# Clonar/descargar este proyecto
cd whatsapp-agent

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## 2️⃣ Configurar Variables de Entorno (1 min)

```bash
# Copiar template
cp .env.example .env

# Editar .env con tus valores
nano .env  # o usa tu editor favorito
```

Rellena SOLO estos 3 campos (obligatorios):

```env
CLAUDE_API_KEY=sk-ant-v0-xxx...  # De https://console.anthropic.com
WEBHOOK_VERIFY_TOKEN=cualquier-token-secreto-largo
DATABASE_URL=sqlite:///./conversations.db
```

## 3️⃣ Ejecutar el Servidor (1 min)

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Deberías ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **¡El servidor está corriendo!**

## 4️⃣ Probar Localmente (1 min)

En otra terminal:

```bash
# Health check
curl http://localhost:8000/health

# Deberías recibir:
# {"status":"healthy","service":"WhatsApp Business Agent API"}
```

✅ **¡Funciona!**

---

## 🚀 Desplegar a Producción (5 min extra)

### Opción A: Render.com (RECOMENDADO - Gratis)

1. Sube tu código a GitHub
2. Ve a [render.com](https://render.com)
3. Haz clic en **New > Web Service**
4. Conecta tu repositorio GitHub
5. Configura:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port 8000`
6. Añade variables de entorno (las 3 del paso 2)
7. Haz clic en **Deploy**

Espera a que veas: ✅ **Service is live**

Tu URL será: `https://whatsapp-agent-xxx.onrender.com`

### Opción B: Tu propio VPS

```bash
# SSH a tu servidor
ssh user@your-server.com

# Instalar Python
sudo apt update
sudo apt install python3.11 python3-pip

# Clonar proyecto
git clone https://github.com/tu-usuario/whatsapp-agent.git
cd whatsapp-agent

# Instalar dependencias
pip install -r requirements.txt

# Correr con Gunicorn (para producción)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

---

## 🤖 Registrar tu Primer Cliente

Una vez que tu servidor está en línea:

```bash
curl -X POST https://tu-dominio.com/customers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Negocio",
    "phone_number_id": "1234567890123",
    "access_token": "EAAxxxxxxxxxxxxx",
    "system_prompt": "Eres un asistente amable. Ayuda a los clientes de forma rápida y eficiente."
  }'
```

**Respuesta:**
```json
{
  "api_key": "whatsapp_agent_abc123xyz...",
  ...
}
```

✅ **¡Ya tienes un cliente registrado!**

---

## 📱 Conectar Meta WhatsApp

### 1. En Meta Developers

1. Ve a [developers.facebook.com](https://developers.facebook.com)
2. Selecciona tu app de WhatsApp
3. Ve a **Configuración > Webhooks**
4. Haz clic en **Editar**
5. Rellena:
   - **Callback URL**: `https://tu-dominio.com/webhook`
   - **Verify Token**: El mismo de tu `.env`

### 2. Haz clic en "Verificar y guardar"

Meta hará una solicitud GET a tu `/webhook`. Debería pasar.

### 3. Suscribirse a eventos

En **Webhooks**, selecciona: ✓ `messages`

---

## ✅ Verificar que Funciona

Envía un mensaje a tu número de WhatsApp Business desde cualquier teléfono.

**Deberías recibir una respuesta automática en segundos.**

---

## 🎯 Próximos Pasos

1. **Personalizar system_prompt**
   - Usa `/system-prompts/examples` para ideas
   - Edita el prompt para tu negocio específico

2. **Ver conversaciones**
   ```bash
   curl https://tu-dominio.com/conversations \
     -H "Authorization: Bearer tu-api-key"
   ```

3. **Ver analytics**
   ```bash
   curl https://tu-dominio.com/analytics \
     -H "Authorization: Bearer tu-api-key"
   ```

---

## 🐛 Si Algo No Funciona

### "Connection refused"
```
❌ El servidor no está corriendo
✅ Solución: python -m uvicorn main:app --reload
```

### "Customer not found"
```
❌ El phone_number_id no coincide con el webhook
✅ Solución: Verifica que sean iguales en ambos lugares
```

### "CLAUDE_API_KEY not set"
```
❌ Falta tu API key de Anthropic
✅ Solución: export CLAUDE_API_KEY=sk-ant-v0-xxx...
```

### "Webhook verification failed"
```
❌ El token de verificación no coincide
✅ Solución: Asegúrate que sea exactamente igual en Meta y .env
```

---

## 📚 Documentación Completa

- **README.md** - Guía detallada
- **TESTING.md** - Ejemplos de curl
- **DEPLOYMENT.md** - Guía de despliegue completa
- **ARCHITECTURE.md** - Cómo funciona por dentro

---

## 💰 Costos Estimados/Mes

| Servicio | Costo |
|----------|-------|
| Claude API | $5-15 |
| Render.com | $0 (gratis primeras 750h) |
| Meta WhatsApp | $0-10 |
| **Total** | **$5-25/mes** |

Para un pequeño negocio: muy económico.

---

**¿Listo?** 🚀

Sigue los 4 pasos arriba y tendrás tu WhatsApp Agent corriendo en 5 minutos.

Si tienes dudas, revisa la **Documentación Completa** arriba.

¡Buena suerte! 🎉
