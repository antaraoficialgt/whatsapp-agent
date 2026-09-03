import os
import logging
from fastapi import FastAPI, Request, HTTPException, Header
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from database import db
from webhook import WhatsAppWebhookHandler
from claude_agent import ClaudeAgent
from auth import auth_manager
import secrets

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WhatsApp Business Agent API",
    description="24/7 Customer Service Agent via WhatsApp using Claude AI",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

webhook_handler = WhatsAppWebhookHandler()
claude_agent = ClaudeAgent()

# ==================== PYDANTIC MODELS ====================

class UserRegister(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class CustomerCreate(BaseModel):
    name: str
    phone_number_id: str
    access_token: str
    system_prompt: Optional[str] = None

class CustomerUpdate(BaseModel):
    system_prompt: Optional[str] = None
    access_token: Optional[str] = None

class MessageRequest(BaseModel):
    recipient_phone: str
    message_text: str

# ==================== AUTH HELPERS ====================

def verify_api_key(authorization: str = Header(None)) -> int:
    """Verify customer API key and return customer_id."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, credentials = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")

        customer = db.get_customer_by_api_key(credentials)
        if not customer:
            raise HTTPException(status_code=401, detail="Invalid API key")

        return customer["id"]
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

def verify_user_token(authorization: str = Header(None)) -> dict:
    """Verify user token and return user data."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authorization scheme")

        user = auth_manager.get_user_from_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization format")

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "WhatsApp Business Agent API",
        "version": "2.0.0"
    }

# ==================== AUTH ENDPOINTS ====================

@app.post("/auth/register")
async def register(user_data: UserRegister):
    """Register a new user."""
    try:
        user = auth_manager.create_user(user_data.email, user_data.password, user_data.name)
        if not user:
            raise HTTPException(status_code=400, detail="Email already exists")

        token = auth_manager.create_api_token(user["id"])
        return {
            "user": user,
            "token": token,
            "message": "User registered successfully"
        }
    except Exception as e:
        logger.error(f"Error registering user: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login")
async def login(credentials: UserLogin):
    """Login user with email and password."""
    try:
        user = auth_manager.authenticate_user(credentials.email, credentials.password)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = auth_manager.create_api_token(user["id"])
        return {
            "user": user,
            "token": token
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging in: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/me")
async def get_current_user(user: dict = None):
    """Get current user information."""
    user_data = verify_user_token(
        Header(default=None, alias="Authorization")
    )
    return user_data

# ==================== WEBHOOK ENDPOINTS ====================

@app.get("/webhook")
async def verify_webhook(
    hub_mode: str = None,
    hub_challenge: str = None,
    hub_verify_token: str = None
):
    verify_token = os.getenv("WEBHOOK_VERIFY_TOKEN")
    if not verify_token:
        logger.error("WEBHOOK_VERIFY_TOKEN not configured")
        raise HTTPException(status_code=500, detail="Server misconfiguration")

    challenge = webhook_handler.verify_webhook(verify_token, hub_challenge, hub_verify_token)
    if challenge:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(challenge)
    else:
        logger.warning("Webhook verification failed")
        raise HTTPException(status_code=403, detail="Invalid verification token")

@app.post("/webhook")
async def receive_webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Webhook received: {data}")

        success = webhook_handler.handle_webhook(data)
        if success:
            return JSONResponse({"status": "received"}, status_code=200)
        else:
            return JSONResponse({"status": "error"}, status_code=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=400)

# ==================== CUSTOMER ENDPOINTS ====================

@app.post("/customers")
async def create_customer(customer_data: CustomerCreate, authorization: str = Header(None)):
    """Create a new customer (WhatsApp Business account)."""
    user = verify_user_token(authorization)

    try:
        subscription = db.get_subscription_by_user(user["id"])
        existing_customers = db.get_customers_by_user(user["id"])

        if len(existing_customers) >= subscription["max_customers"]:
            raise HTTPException(status_code=403, detail="Customer limit reached for your plan")

        api_key = f"whatsapp_agent_{secrets.token_urlsafe(32)}"
        result = db.create_customer(
            user_id=user["id"],
            name=customer_data.name,
            phone_number_id=customer_data.phone_number_id,
            access_token=customer_data.access_token,
            system_prompt=customer_data.system_prompt,
            api_key=api_key
        )

        logger.info(f"Customer created: {customer_data.name}")
        return {
            "id": result["id"],
            "name": result["name"],
            "phone_number_id": result["phone_number_id"],
            "api_key": api_key,
            "message": "Guarda tu API key en un lugar seguro."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/customers")
async def list_customers(authorization: str = Header(None)):
    """List all customers for authenticated user."""
    user = verify_user_token(authorization)
    try:
        customers = db.get_customers_by_user(user["id"])
        return {"total": len(customers), "customers": customers}
    except Exception as e:
        logger.error(f"Error listing customers: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/customers/{customer_id}")
async def get_customer(customer_id: int, authorization: str = Header(None)):
    """Get customer details."""
    user = verify_user_token(authorization)
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer or customer["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Customer not found")

        return customer
    except Exception as e:
        logger.error(f"Error getting customer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/customers/{customer_id}")
async def update_customer(customer_id: int, customer_update: CustomerUpdate, authorization: str = Header(None)):
    """Update customer configuration."""
    user = verify_user_token(authorization)
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer or customer["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Customer not found")

        update_data = {}
        if customer_update.system_prompt:
            update_data["system_prompt"] = customer_update.system_prompt
        if customer_update.access_token:
            update_data["access_token"] = customer_update.access_token

        success = db.update_customer(customer_id, **update_data)
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")

        return {"status": "updated"}
    except Exception as e:
        logger.error(f"Error updating customer: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== CONVERSATION ENDPOINTS ====================

@app.get("/conversations/{customer_id}")
async def get_conversations(customer_id: int, limit: int = 50, authorization: str = Header(None)):
    """Get recent conversations."""
    user = verify_user_token(authorization)
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer or customer["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Customer not found")

        conversations = db.get_customer_conversations(customer_id, limit=limit)
        return {"total": len(conversations), "conversations": conversations}
    except Exception as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/conversations/{customer_id}/{sender_phone}")
async def get_contact_history(customer_id: int, sender_phone: str, limit: int = 20, authorization: str = Header(None)):
    """Get conversation history with specific contact."""
    user = verify_user_token(authorization)
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer or customer["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Customer not found")

        history = db.get_conversation_history(customer_id, sender_phone, limit=limit)
        return {"sender_phone": sender_phone, "total": len(history), "messages": history}
    except Exception as e:
        logger.error(f"Error getting contact history: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== ANALYTICS ENDPOINTS ====================

@app.get("/analytics/{customer_id}")
async def get_daily_analytics(customer_id: int, days: int = 30, authorization: str = Header(None)):
    """Get daily analytics."""
    user = verify_user_token(authorization)
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer or customer["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Customer not found")

        analytics = db.get_analytics(customer_id, days=days)
        return {"period_days": days, "total_records": len(analytics), "analytics": analytics}
    except Exception as e:
        logger.error(f"Error getting analytics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/analytics/{customer_id}/detailed")
async def get_detailed_analytics(customer_id: int, period_type: str = "monthly", authorization: str = Header(None)):
    """Get detailed analytics by period (daily, weekly, monthly, quarterly, semi-annual, annual)."""
    user = verify_user_token(authorization)
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer or customer["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Customer not found")

        metrics = db.get_metrics_by_period(customer_id, period_type)
        return {"period_type": period_type, "total": len(metrics), "metrics": metrics}
    except Exception as e:
        logger.error(f"Error getting detailed analytics: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== SUBSCRIPTION ENDPOINTS ====================

@app.get("/subscription")
async def get_subscription(authorization: str = Header(None)):
    """Get current user subscription."""
    user = verify_user_token(authorization)
    try:
        subscription = db.get_subscription_by_user(user["id"])
        return subscription
    except Exception as e:
        logger.error(f"Error getting subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/subscription/upgrade")
async def upgrade_subscription(new_plan: str, authorization: str = Header(None)):
    """Upgrade user subscription plan."""
    user = verify_user_token(authorization)
    try:
        success = db.upgrade_subscription(user["id"], new_plan)
        if not success:
            raise HTTPException(status_code=404, detail="User not found")

        subscription = db.get_subscription_by_user(user["id"])
        return {"status": "upgraded", "subscription": subscription}
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/dashboard/basic/{customer_id}")
async def get_basic_dashboard(customer_id: int, authorization: str = Header(None)):
    """Get basic dashboard data (Free & Pro tiers)."""
    user = verify_user_token(authorization)
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer or customer["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Customer not found")

        subscription = db.get_subscription_by_user(user["id"])
        if not subscription["has_basic_dashboard"]:
            raise HTTPException(status_code=403, detail="Access denied for your plan")

        analytics = db.get_analytics(customer_id, days=30)
        conversations = db.get_customer_conversations(customer_id, limit=10)

        total_messages = sum([a["messages_count"] for a in analytics])
        avg_response_time = sum([a["response_time_avg"] for a in analytics]) / len(analytics) if analytics else 0

        return {
            "customer_name": customer["name"],
            "total_messages_month": total_messages,
            "avg_response_time_ms": avg_response_time,
            "daily_analytics": analytics,
            "recent_conversations": conversations
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting basic dashboard: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/dashboard/advanced/{customer_id}")
async def get_advanced_dashboard(customer_id: int, authorization: str = Header(None)):
    """Get advanced dashboard data (Pro & Enterprise tiers)."""
    user = verify_user_token(authorization)
    try:
        customer = db.get_customer_by_id(customer_id)
        if not customer or customer["user_id"] != user["id"]:
            raise HTTPException(status_code=404, detail="Customer not found")

        subscription = db.get_subscription_by_user(user["id"])
        if not subscription["has_advanced_dashboard"]:
            raise HTTPException(status_code=403, detail="Access denied for your plan")

        daily = db.get_metrics_by_period(customer_id, "daily")
        weekly = db.get_metrics_by_period(customer_id, "weekly")
        monthly = db.get_metrics_by_period(customer_id, "monthly")
        quarterly = db.get_metrics_by_period(customer_id, "quarterly")
        semi_annual = db.get_metrics_by_period(customer_id, "semi-annual")
        annual = db.get_metrics_by_period(customer_id, "annual")

        return {
            "customer_name": customer["name"],
            "daily_metrics": daily,
            "weekly_metrics": weekly,
            "monthly_metrics": monthly,
            "quarterly_metrics": quarterly,
            "semi_annual_metrics": semi_annual,
            "annual_metrics": annual
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting advanced dashboard: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# ==================== SYSTEM PROMPTS ====================

@app.get("/system-prompts/examples")
async def get_system_prompt_examples():
    """Get example system prompts."""
    examples = ClaudeAgent.get_system_prompts_examples()
    return examples

# ==================== LEGACY ENDPOINTS (API Key based) ====================

@app.post("/send-message")
async def send_manual_message(message_request: MessageRequest, authorization: str = Header(None)):
    """Send a manual message using customer API key."""
    customer_id = verify_api_key(authorization)

    customer = db.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    success = webhook_handler.send_message(
        customer=customer,
        recipient_phone=message_request.recipient_phone,
        message_text=message_request.message_text
    )

    if success:
        return {"status": "sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send message")

# ==================== ERROR HANDLERS ====================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP Exception: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run(app, host=host, port=port)
