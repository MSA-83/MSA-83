"""Email notification service for Titanium platform."""

import os
from datetime import datetime


class EmailConfig:
    """Email configuration."""

    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.resend.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "resend")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@titanium.ai")
    FROM_NAME = os.getenv("FROM_NAME", "Titanium Platform")


class NotificationType:
    """Types of notifications."""

    WELCOME = "welcome"
    PASSWORD_RESET = "password_reset"
    SUBSCRIPTION_ACTIVATED = "subscription_activated"
    SUBSCRIPTION_EXPIRED = "subscription_expired"
    USAGE_WARNING = "usage_warning"
    SECURITY_ALERT = "security_alert"
    TASK_COMPLETED = "task_completed"
    AGENT_ERROR = "agent_error"


EMAIL_TEMPLATES = {
    NotificationType.WELCOME: {
        "subject": "Welcome to Titanium",
        "html": """
        <h1>Welcome to Titanium, {name}!</h1>
        <p>Your account has been created successfully.</p>
        <p>Get started by exploring our features:</p>
        <ul>
            <li>Chat with our AI assistant</li>
            <li>Upload documents to your memory</li>
            <li>Create agent tasks</li>
        </ul>
        <p>Best regards,<br>The Titanium Team</p>
        """,
    },
    NotificationType.SUBSCRIPTION_ACTIVATED: {
        "subject": "Your {tier} subscription is active",
        "html": """
        <h1>Subscription Activated</h1>
        <p>Your <strong>{tier}</strong> subscription is now active.</p>
        <p>Monthly cost: ${price}</p>
        <p>Billing cycle: {billing_cycle}</p>
        """,
    },
    NotificationType.USAGE_WARNING: {
        "subject": "Usage Warning: {percentage}% of limit reached",
        "html": """
        <h1>Usage Alert</h1>
        <p>You've used <strong>{percentage}%</strong> of your {resource} limit.</p>
        <p>Current usage: {current} / {limit}</p>
        <p>Consider upgrading your plan for more capacity.</p>
        """,
    },
    NotificationType.SECURITY_ALERT: {
        "subject": "Security Alert: {alert_type}",
        "html": """
        <h1>Security Alert</h1>
        <p>We detected unusual activity on your account.</p>
        <p>Type: <strong>{alert_type}</strong></p>
        <p>Time: {timestamp}</p>
        <p>If this wasn't you, please secure your account immediately.</p>
        """,
    },
    NotificationType.TASK_COMPLETED: {
        "subject": "Agent task completed: {task_id}",
        "html": """
        <h1>Task Completed</h1>
        <p>Your agent task <strong>{task_id}</strong> has been completed.</p>
        <p>Type: {agent_type}</p>
        <p>Result: {result_preview}</p>
        """,
    },
}


class EmailNotificationService:
    """Service for sending email notifications."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("RESEND_API_KEY", "")
        self._initialized = bool(self.api_key and self.api_key != "re_test_")
        self._sent_count = 0

    async def send(
        self,
        to: str,
        notification_type: str,
        template_vars: dict,
        reply_to: str | None = None,
    ) -> dict:
        """Send an email notification."""
        template = EMAIL_TEMPLATES.get(notification_type)
        if not template:
            return {"status": "error", "message": f"Unknown template: {notification_type}"}

        subject = template["subject"].format(**template_vars)
        html_content = template["html"].format(**template_vars)

        if not self._initialized:
            return {
                "status": "demo",
                "message": "Email not configured, logging instead",
                "to": to,
                "subject": subject,
            }

        try:
            import aiohttp

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "from": f"{EmailConfig.FROM_NAME} <{EmailConfig.FROM_EMAIL}>",
                "to": [to],
                "subject": subject,
                "html": html_content,
            }

            if reply_to:
                payload["reply_to"] = reply_to

            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    "https://api.resend.com/emails",
                    headers=headers,
                    json=payload,
                ) as response,
            ):
                response.raise_for_status()
                result = await response.json()

            self._sent_count += 1

            return {
                "status": "sent",
                "id": result.get("id"),
                "to": to,
                "subject": subject,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "to": to,
                "subject": subject,
            }

    async def send_welcome(self, email: str, name: str = "User") -> dict:
        """Send welcome email."""
        return await self.send(
            to=email,
            notification_type=NotificationType.WELCOME,
            template_vars={"name": name},
        )

    async def send_subscription_activated(
        self,
        email: str,
        tier: str,
        price: float,
        billing_cycle: str,
    ) -> dict:
        """Send subscription activated email."""
        return await self.send(
            to=email,
            notification_type=NotificationType.SUBSCRIPTION_ACTIVATED,
            template_vars={
                "tier": tier,
                "price": price,
                "billing_cycle": billing_cycle,
            },
        )

    async def send_usage_warning(
        self,
        email: str,
        resource: str,
        current: int,
        limit: int,
    ) -> dict:
        """Send usage warning email."""
        percentage = int((current / limit) * 100) if limit > 0 else 0
        return await self.send(
            to=email,
            notification_type=NotificationType.USAGE_WARNING,
            template_vars={
                "percentage": percentage,
                "resource": resource,
                "current": current,
                "limit": limit,
            },
        )

    async def send_security_alert(
        self,
        email: str,
        alert_type: str,
        timestamp: str | None = None,
    ) -> dict:
        """Send security alert email."""
        return await self.send(
            to=email,
            notification_type=NotificationType.SECURITY_ALERT,
            template_vars={
                "alert_type": alert_type,
                "timestamp": timestamp or datetime.utcnow().isoformat(),
            },
        )

    async def send_task_completed(
        self,
        email: str,
        task_id: str,
        agent_type: str,
        result_preview: str,
    ) -> dict:
        """Send task completed notification."""
        return await self.send(
            to=email,
            notification_type=NotificationType.TASK_COMPLETED,
            template_vars={
                "task_id": task_id,
                "agent_type": agent_type,
                "result_preview": result_preview[:100],
            },
        )

    async def get_stats(self) -> dict:
        """Get email service statistics."""
        return {
            "initialized": self._initialized,
            "sent_count": self._sent_count,
            "provider": "resend" if self._initialized else "none",
        }


email_service = EmailNotificationService()
