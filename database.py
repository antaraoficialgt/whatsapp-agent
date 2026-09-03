import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./conversations.db")

class Database:
    def __init__(self, db_path: str = DATABASE_URL):
        self.db_path = db_path.replace("sqlite:///", "")
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table (para login/autenticación)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                subscription_plan TEXT DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Customers table (empresas/negocios)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                phone_number_id TEXT NOT NULL UNIQUE,
                access_token TEXT NOT NULL,
                system_prompt TEXT,
                api_key TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Conversations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                sender_phone TEXT NOT NULL,
                message_text TEXT NOT NULL,
                response_text TEXT,
                message_id TEXT UNIQUE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_time_ms INTEGER,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)

        # Analytics table (diario)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                messages_count INTEGER DEFAULT 0,
                response_time_avg REAL DEFAULT 0.0,
                date DATE DEFAULT CURRENT_DATE,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                UNIQUE(customer_id, date)
            )
        """)

        # Subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                plan TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                max_customers INTEGER,
                max_messages_per_day INTEGER,
                has_basic_dashboard INTEGER DEFAULT 1,
                has_advanced_dashboard INTEGER DEFAULT 0,
                has_custom_prompts INTEGER DEFAULT 0,
                has_webhooks INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                renewal_date TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Detailed metrics (para reportes por período)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detailed_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                metric_type TEXT,
                period_type TEXT,
                period_value TEXT,
                total_messages INTEGER DEFAULT 0,
                total_conversations INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0.0,
                total_unique_users INTEGER DEFAULT 0,
                satisfaction_score REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                UNIQUE(customer_id, metric_type, period_type, period_value)
            )
        """)

        conn.commit()
        conn.close()

    # ==================== CUSTOMERS ====================
    def create_customer(self, user_id: int = None, name: str = None, phone_number_id: str = None, access_token: str = None,
                       system_prompt: str = None, api_key: str = None) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO customers (user_id, name, phone_number_id, access_token, system_prompt, api_key)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, name, phone_number_id, access_token, system_prompt, api_key))
            conn.commit()
            customer_id = cursor.lastrowid
            return {"id": customer_id, "name": name, "phone_number_id": phone_number_id}
        finally:
            conn.close()

    def get_customer_by_api_key(self, api_key: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM customers WHERE api_key = ?", (api_key,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_customer_by_id(self, customer_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_customer_by_phone_number_id(self, phone_number_id: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM customers WHERE phone_number_id = ?", (phone_number_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_customer(self, customer_id: int, **kwargs) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [customer_id]
            cursor.execute(f"UPDATE customers SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_customers_by_user(self, user_id: int) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM customers WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ==================== CONVERSATIONS ====================
    def save_conversation(self, customer_id: int, sender_phone: str, message_text: str,
                         message_id: str = None, response_text: str = None,
                         response_time_ms: int = None) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO conversations
                (customer_id, sender_phone, message_text, message_id, response_text, response_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (customer_id, sender_phone, message_text, message_id, response_text, response_time_ms))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_conversation_response(self, conversation_id: int, response_text: str,
                                    response_time_ms: int = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE conversations
                SET response_text = ?, response_time_ms = ?
                WHERE id = ?
            """, (response_text, response_time_ms, conversation_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_conversation_history(self, customer_id: int, sender_phone: str, limit: int = 10) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT message_text, response_text, timestamp
                FROM conversations
                WHERE customer_id = ? AND sender_phone = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (customer_id, sender_phone, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows][::-1]  # Reverse to get chronological order
        finally:
            conn.close()

    def get_customer_conversations(self, customer_id: int, limit: int = 50) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM conversations
                WHERE customer_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (customer_id, limit))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ==================== ANALYTICS ====================
    def update_analytics(self, customer_id: int, response_time_ms: int = None) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO analytics (customer_id, messages_count, response_time_avg, date)
                VALUES (?, 1, ?, CURRENT_DATE)
                ON CONFLICT(customer_id, date) DO UPDATE SET
                    messages_count = messages_count + 1,
                    response_time_avg = (response_time_avg * messages_count + ?) / (messages_count + 1)
                WHERE customer_id = ? AND date = CURRENT_DATE
            """, (customer_id, response_time_ms, response_time_ms, customer_id))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_analytics(self, customer_id: int, days: int = 30) -> List[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM analytics
                WHERE customer_id = ? AND date >= date('now', '-' || ? || ' days')
                ORDER BY date DESC
            """, (customer_id, days))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    # ==================== USERS ====================
    def create_user(self, email: str, password_hash: str, name: str) -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO users (email, password_hash, name)
                VALUES (?, ?, ?)
            """, (email, password_hash, name))
            conn.commit()
            user_id = cursor.lastrowid
            return {"id": user_id, "email": email, "name": name}
        finally:
            conn.close()

    def get_user_by_email(self, email: str) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def update_user(self, user_id: int, **kwargs) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            cursor.execute(f"UPDATE users SET {fields}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ==================== SUBSCRIPTIONS ====================
    def create_subscription(self, user_id: int, plan: str = "free") -> Dict:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            plan_config = self._get_plan_config(plan)
            cursor.execute("""
                INSERT INTO subscriptions (user_id, plan, max_customers, max_messages_per_day, has_basic_dashboard, has_advanced_dashboard, has_custom_prompts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, plan, plan_config['max_customers'], plan_config['max_messages_per_day'],
                  plan_config['has_basic_dashboard'], plan_config['has_advanced_dashboard'], plan_config['has_custom_prompts']))
            conn.commit()
            return self.get_subscription_by_user(user_id)
        finally:
            conn.close()

    def get_subscription_by_user(self, user_id: int) -> Optional[Dict]:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM subscriptions WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def upgrade_subscription(self, user_id: int, new_plan: str) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            plan_config = self._get_plan_config(new_plan)
            cursor.execute("""
                UPDATE subscriptions
                SET plan = ?, max_customers = ?, max_messages_per_day = ?,
                    has_basic_dashboard = ?, has_advanced_dashboard = ?, has_custom_prompts = ?
                WHERE user_id = ?
            """, (new_plan, plan_config['max_customers'], plan_config['max_messages_per_day'],
                  plan_config['has_basic_dashboard'], plan_config['has_advanced_dashboard'],
                  plan_config['has_custom_prompts'], user_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ==================== DETAILED METRICS ====================
    def save_detailed_metric(self, customer_id: int, metric_type: str, period_type: str,
                            period_value: str, total_messages: int = 0, total_conversations: int = 0,
                            avg_response_time: float = 0.0, total_unique_users: int = 0) -> bool:
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO detailed_metrics
                (customer_id, metric_type, period_type, period_value, total_messages, total_conversations, avg_response_time, total_unique_users)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(customer_id, metric_type, period_type, period_value) DO UPDATE SET
                    total_messages = ?,
                    total_conversations = ?,
                    avg_response_time = ?,
                    total_unique_users = ?
            """, (customer_id, metric_type, period_type, period_value, total_messages, total_conversations,
                  avg_response_time, total_unique_users, total_messages, total_conversations, avg_response_time, total_unique_users))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_metrics_by_period(self, customer_id: int, period_type: str) -> List[Dict]:
        """Get metrics for a specific period type (daily, weekly, monthly, quarterly, semi-annual, annual)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT * FROM detailed_metrics
                WHERE customer_id = ? AND period_type = ?
                ORDER BY period_value DESC
            """, (customer_id, period_type))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def calculate_metrics(self, customer_id: int) -> None:
        """Calcular y actualizar métricas para todos los períodos"""
        periods = [
            ('daily', 'SELECT DATE(timestamp) as period FROM conversations WHERE customer_id = ? GROUP BY DATE(timestamp)'),
            ('weekly', 'SELECT strftime("%Y-W%W", timestamp) as period FROM conversations WHERE customer_id = ? GROUP BY strftime("%Y-W%W", timestamp)'),
            ('monthly', 'SELECT strftime("%Y-%m", timestamp) as period FROM conversations WHERE customer_id = ? GROUP BY strftime("%Y-%m", timestamp)'),
        ]

        for period_type, query in periods:
            conn = self.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(query, (customer_id,))
                periods_data = cursor.fetchall()

                for row in periods_data:
                    period_value = row[0]
                    # Calcular métricas para este período
                    # ... código para obtener stats
                    pass
            finally:
                conn.close()

    @staticmethod
    def _get_plan_config(plan: str) -> Dict:
        plans = {
            "free": {
                "max_customers": 1,
                "max_messages_per_day": 100,
                "has_basic_dashboard": 1,
                "has_advanced_dashboard": 0,
                "has_custom_prompts": 0,
            },
            "pro": {
                "max_customers": 5,
                "max_messages_per_day": 1000,
                "has_basic_dashboard": 1,
                "has_advanced_dashboard": 1,
                "has_custom_prompts": 1,
            },
            "enterprise": {
                "max_customers": 999,
                "max_messages_per_day": 999999,
                "has_basic_dashboard": 1,
                "has_advanced_dashboard": 1,
                "has_custom_prompts": 1,
            },
        }
        return plans.get(plan, plans["free"])

# Initialize database instance
db = Database()
