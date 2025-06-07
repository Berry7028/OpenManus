"""
Notification Sender Tool

This tool provides comprehensive notification and alerting capabilities including:
- Multi-channel notification delivery (email, SMS, Slack, Discord, etc.)
- Alert management and routing
- Notification templates and formatting
- Delivery tracking and retry mechanisms
- Integration with monitoring systems
- Scheduled and event-driven notifications
"""

import asyncio
import json
import smtplib
import requests
import time
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import os
from .base import BaseTool


class NotificationChannel(Enum):
    EMAIL = "email"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    SMS = "sms"
    TELEGRAM = "telegram"


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class NotificationTemplate:
    name: str
    subject_template: str
    body_template: str
    channel: NotificationChannel
    priority: Priority


class NotificationSender(BaseTool):
    """Tool for comprehensive notification and alerting"""

    def __init__(self):
        super().__init__()
        self.name = "notification_sender"
        self.description = "Comprehensive notification and alerting tool"

        # Notification storage
        self.notification_history = []
        self.failed_notifications = []
        self.templates = {}
        self.channels = {}
        self.subscriptions = {}

        # Configuration
        self.retry_attempts = 3
        self.retry_delay = 5  # seconds
        self.rate_limits = {}

        # Built-in templates
        self._initialize_default_templates()

    def _initialize_default_templates(self):
        """Initialize default notification templates"""
        self.templates = {
            "system_alert": NotificationTemplate(
                name="system_alert",
                subject_template="🚨 System Alert: {alert_type}",
                body_template="Alert Details:\n- Type: {alert_type}\n- Severity: {severity}\n- Message: {message}\n- Time: {timestamp}",
                channel=NotificationChannel.EMAIL,
                priority=Priority.HIGH
            ),
            "deployment_success": NotificationTemplate(
                name="deployment_success",
                subject_template="✅ Deployment Successful: {project_name}",
                body_template="Deployment completed successfully!\n\nProject: {project_name}\nVersion: {version}\nEnvironment: {environment}\nTime: {timestamp}",
                channel=NotificationChannel.SLACK,
                priority=Priority.MEDIUM
            ),
            "error_notification": NotificationTemplate(
                name="error_notification",
                subject_template="❌ Error Alert: {error_type}",
                body_template="Error Details:\n- Type: {error_type}\n- Message: {error_message}\n- Component: {component}\n- Time: {timestamp}\n\nStack Trace:\n{stack_trace}",
                channel=NotificationChannel.EMAIL,
                priority=Priority.CRITICAL
            ),
            "maintenance_reminder": NotificationTemplate(
                name="maintenance_reminder",
                subject_template="🔧 Scheduled Maintenance: {system_name}",
                body_template="Maintenance Window:\n- System: {system_name}\n- Start: {start_time}\n- Duration: {duration}\n- Impact: {impact_description}",
                channel=NotificationChannel.EMAIL,
                priority=Priority.MEDIUM
            )
        }

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute notification sender commands"""
        try:
            if command == "send_notification":
                return await self._send_notification(**kwargs)
            elif command == "configure_channel":
                return await self._configure_channel(**kwargs)
            elif command == "create_template":
                return await self._create_template(**kwargs)
            elif command == "send_alert":
                return await self._send_alert(**kwargs)
            elif command == "bulk_notify":
                return await self._bulk_notify(**kwargs)
            elif command == "subscribe":
                return await self._subscribe(**kwargs)
            elif command == "delivery_status":
                return await self._delivery_status(**kwargs)
            elif command == "notification_history":
                return await self._notification_history(**kwargs)
            elif command == "test_channel":
                return await self._test_channel(**kwargs)
            elif command == "schedule_notification":
                return await self._schedule_notification(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Notification sender error: {str(e)}"}

    async def _send_notification(self, channel: str, recipients: List[str],
                               subject: str, message: str, priority: str = "medium",
                               template_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send notification through specified channel"""
        try:
            channel_enum = NotificationChannel(channel)
        except ValueError:
            return {"error": f"Unsupported channel: {channel}"}

        notification_id = f"notif_{int(time.time())}_{len(self.notification_history)}"

        notification = {
            "id": notification_id,
            "channel": channel,
            "recipients": recipients,
            "subject": subject,
            "message": message,
            "priority": priority,
            "template_data": template_data or {},
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "delivery_attempts": 0
        }

        # Send notification
        result = await self._deliver_notification(notification)

        # Store in history
        notification.update(result)
        self.notification_history.append(notification)

        return {
            "notification_id": notification_id,
            "status": result["status"],
            "delivery_result": result
        }

    async def _deliver_notification(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver notification through appropriate channel"""
        channel = notification["channel"]
        attempts = 0

        while attempts < self.retry_attempts:
            try:
                notification["delivery_attempts"] = attempts + 1

                if channel == "email":
                    result = await self._send_email(notification)
                elif channel == "slack":
                    result = await self._send_slack(notification)
                elif channel == "discord":
                    result = await self._send_discord(notification)
                elif channel == "webhook":
                    result = await self._send_webhook(notification)
                elif channel == "sms":
                    result = await self._send_sms(notification)
                elif channel == "telegram":
                    result = await self._send_telegram(notification)
                else:
                    return {"status": "failed", "error": f"Unsupported channel: {channel}"}

                if result["status"] == "delivered":
                    return result

                attempts += 1
                if attempts < self.retry_attempts:
                    await asyncio.sleep(self.retry_delay)

            except Exception as e:
                attempts += 1
                if attempts >= self.retry_attempts:
                    return {
                        "status": "failed",
                        "error": str(e),
                        "attempts": attempts,
                        "delivered_at": None
                    }
                await asyncio.sleep(self.retry_delay)

        # Add to failed notifications
        self.failed_notifications.append(notification)

        return {
            "status": "failed",
            "error": "Max retry attempts exceeded",
            "attempts": attempts,
            "delivered_at": None
        }

    async def _send_email(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send email notification"""
        if "email" not in self.channels:
            return {"status": "failed", "error": "Email channel not configured"}

        config = self.channels["email"]

        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = config["from_address"]
            msg['Subject'] = notification["subject"]

            # Add recipients
            recipients = notification["recipients"]
            msg['To'] = ", ".join(recipients)

            # Add body
            body = MimeText(notification["message"], 'plain')
            msg.attach(body)

            # Send email
            with smtplib.SMTP(config["smtp_host"], config["smtp_port"]) as server:
                if config.get("use_tls"):
                    server.starttls()

                if config.get("username") and config.get("password"):
                    server.login(config["username"], config["password"])

                server.send_message(msg)

            return {
                "status": "delivered",
                "delivered_at": datetime.now().isoformat(),
                "channel_response": "Email sent successfully"
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "delivered_at": None
            }

    async def _send_slack(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send Slack notification"""
        if "slack" not in self.channels:
            return {"status": "failed", "error": "Slack channel not configured"}

        config = self.channels["slack"]

        try:
            # Prepare Slack message
            slack_data = {
                "text": notification["subject"],
                "attachments": [
                    {
                        "color": self._get_priority_color(notification["priority"]),
                        "fields": [
                            {
                                "title": "Message",
                                "value": notification["message"],
                                "short": False
                            },
                            {
                                "title": "Priority",
                                "value": notification["priority"].upper(),
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": notification["created_at"],
                                "short": True
                            }
                        ]
                    }
                ]
            }

            # Send to each recipient (assuming they are channels)
            for recipient in notification["recipients"]:
                slack_data["channel"] = recipient

                response = requests.post(
                    config["webhook_url"],
                    json=slack_data,
                    timeout=30
                )

                if response.status_code != 200:
                    return {
                        "status": "failed",
                        "error": f"Slack API error: {response.status_code}",
                        "delivered_at": None
                    }

            return {
                "status": "delivered",
                "delivered_at": datetime.now().isoformat(),
                "channel_response": "Slack message sent successfully"
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "delivered_at": None
            }

    async def _send_discord(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send Discord notification"""
        if "discord" not in self.channels:
            return {"status": "failed", "error": "Discord channel not configured"}

        config = self.channels["discord"]

        try:
            # Prepare Discord message
            discord_data = {
                "content": f"**{notification['subject']}**",
                "embeds": [
                    {
                        "title": "Notification Details",
                        "description": notification["message"],
                        "color": int(self._get_priority_color(notification["priority"]).replace("#", ""), 16),
                        "fields": [
                            {
                                "name": "Priority",
                                "value": notification["priority"].upper(),
                                "inline": True
                            },
                            {
                                "name": "Time",
                                "value": notification["created_at"],
                                "inline": True
                            }
                        ],
                        "timestamp": notification["created_at"]
                    }
                ]
            }

            response = requests.post(
                config["webhook_url"],
                json=discord_data,
                timeout=30
            )

            if response.status_code not in [200, 204]:
                return {
                    "status": "failed",
                    "error": f"Discord API error: {response.status_code}",
                    "delivered_at": None
                }

            return {
                "status": "delivered",
                "delivered_at": datetime.now().isoformat(),
                "channel_response": "Discord message sent successfully"
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "delivered_at": None
            }

    async def _send_webhook(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send webhook notification"""
        if "webhook" not in self.channels:
            return {"status": "failed", "error": "Webhook channel not configured"}

        config = self.channels["webhook"]

        try:
            # Prepare webhook payload
            webhook_data = {
                "notification_id": notification.get("id"),
                "subject": notification["subject"],
                "message": notification["message"],
                "priority": notification["priority"],
                "recipients": notification["recipients"],
                "timestamp": notification["created_at"],
                "template_data": notification.get("template_data", {})
            }

            # Add custom headers if configured
            headers = {"Content-Type": "application/json"}
            if "headers" in config:
                headers.update(config["headers"])

            response = requests.post(
                config["url"],
                json=webhook_data,
                headers=headers,
                timeout=30
            )

            if response.status_code not in [200, 201, 202]:
                return {
                    "status": "failed",
                    "error": f"Webhook error: {response.status_code} - {response.text}",
                    "delivered_at": None
                }

            return {
                "status": "delivered",
                "delivered_at": datetime.now().isoformat(),
                "channel_response": f"Webhook delivered: {response.status_code}"
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "delivered_at": None
            }

    async def _send_sms(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send SMS notification (placeholder - requires SMS service integration)"""
        return {
            "status": "failed",
            "error": "SMS sending not implemented - requires SMS service configuration",
            "delivered_at": None
        }

    async def _send_telegram(self, notification: Dict[str, Any]) -> Dict[str, Any]:
        """Send Telegram notification"""
        if "telegram" not in self.channels:
            return {"status": "failed", "error": "Telegram channel not configured"}

        config = self.channels["telegram"]

        try:
            message_text = f"*{notification['subject']}*\n\n{notification['message']}\n\n_Priority: {notification['priority'].upper()}_"

            for recipient in notification["recipients"]:
                telegram_data = {
                    "chat_id": recipient,
                    "text": message_text,
                    "parse_mode": "Markdown"
                }

                response = requests.post(
                    f"https://api.telegram.org/bot{config['bot_token']}/sendMessage",
                    json=telegram_data,
                    timeout=30
                )

                if response.status_code != 200:
                    return {
                        "status": "failed",
                        "error": f"Telegram API error: {response.status_code}",
                        "delivered_at": None
                    }

            return {
                "status": "delivered",
                "delivered_at": datetime.now().isoformat(),
                "channel_response": "Telegram message sent successfully"
            }

        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "delivered_at": None
            }

    def _get_priority_color(self, priority: str) -> str:
        """Get color code for priority level"""
        color_map = {
            "low": "#36a64f",      # Green
            "medium": "#ff9500",   # Orange
            "high": "#ff4444",     # Red
            "critical": "#8b0000"  # Dark Red
        }
        return color_map.get(priority.lower(), "#808080")  # Default gray

    async def _configure_channel(self, channel: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure notification channel"""
        try:
            channel_enum = NotificationChannel(channel)
        except ValueError:
            return {"error": f"Unsupported channel: {channel}"}

        # Validate configuration based on channel type
        if channel == "email":
            required_fields = ["smtp_host", "smtp_port", "from_address"]
            if not all(field in config for field in required_fields):
                return {"error": f"Missing required fields for email: {required_fields}"}

        elif channel == "slack":
            if "webhook_url" not in config:
                return {"error": "Slack webhook URL is required"}

        elif channel == "discord":
            if "webhook_url" not in config:
                return {"error": "Discord webhook URL is required"}

        elif channel == "webhook":
            if "url" not in config:
                return {"error": "Webhook URL is required"}

        elif channel == "telegram":
            if "bot_token" not in config:
                return {"error": "Telegram bot token is required"}

        self.channels[channel] = config

        return {
            "channel": channel,
            "status": "configured",
            "configured_at": datetime.now().isoformat()
        }

    async def _create_template(self, name: str, subject_template: str,
                             body_template: str, channel: str = "email",
                             priority: str = "medium") -> Dict[str, Any]:
        """Create notification template"""
        try:
            channel_enum = NotificationChannel(channel)
            priority_enum = Priority(priority)
        except ValueError as e:
            return {"error": f"Invalid enum value: {str(e)}"}

        template = NotificationTemplate(
            name=name,
            subject_template=subject_template,
            body_template=body_template,
            channel=channel_enum,
            priority=priority_enum
        )

        self.templates[name] = template

        return {
            "template_name": name,
            "status": "created",
            "created_at": datetime.now().isoformat()
        }

    async def _send_alert(self, alert_type: str, severity: str, message: str,
                        recipients: List[str], template: str = "system_alert") -> Dict[str, Any]:
        """Send alert using predefined template"""
        if template not in self.templates:
            return {"error": f"Template '{template}' not found"}

        template_obj = self.templates[template]

        # Prepare template data
        template_data = {
            "alert_type": alert_type,
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }

        # Format subject and body
        subject = template_obj.subject_template.format(**template_data)
        body = template_obj.body_template.format(**template_data)

        # Send notification
        return await self._send_notification(
            channel=template_obj.channel.value,
            recipients=recipients,
            subject=subject,
            message=body,
            priority=template_obj.priority.value,
            template_data=template_data
        )

    async def _bulk_notify(self, notifications: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send multiple notifications"""
        results = []
        successful = 0
        failed = 0

        for notif_data in notifications:
            try:
                result = await self._send_notification(**notif_data)
                results.append(result)

                if result.get("delivery_result", {}).get("status") == "delivered":
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                results.append({"error": str(e)})
                failed += 1

        return {
            "total_notifications": len(notifications),
            "successful": successful,
            "failed": failed,
            "results": results,
            "completed_at": datetime.now().isoformat()
        }

    async def _subscribe(self, recipient: str, channel: str,
                       notification_types: List[str]) -> Dict[str, Any]:
        """Subscribe recipient to notification types"""
        subscription_id = f"sub_{recipient}_{channel}_{int(time.time())}"

        subscription = {
            "id": subscription_id,
            "recipient": recipient,
            "channel": channel,
            "notification_types": notification_types,
            "subscribed_at": datetime.now().isoformat(),
            "active": True
        }

        self.subscriptions[subscription_id] = subscription

        return {
            "subscription_id": subscription_id,
            "status": "subscribed",
            "subscription": subscription
        }

    async def _delivery_status(self, notification_id: str = None) -> Dict[str, Any]:
        """Get delivery status for notifications"""
        if notification_id:
            # Get specific notification
            notification = next(
                (n for n in self.notification_history if n["id"] == notification_id),
                None
            )

            if not notification:
                return {"error": f"Notification '{notification_id}' not found"}

            return {
                "notification_id": notification_id,
                "status": notification["status"],
                "delivery_attempts": notification["delivery_attempts"],
                "created_at": notification["created_at"],
                "delivered_at": notification.get("delivered_at")
            }
        else:
            # Get summary statistics
            total = len(self.notification_history)
            delivered = len([n for n in self.notification_history if n["status"] == "delivered"])
            failed = len([n for n in self.notification_history if n["status"] == "failed"])
            pending = len([n for n in self.notification_history if n["status"] == "pending"])

            return {
                "total_notifications": total,
                "delivered": delivered,
                "failed": failed,
                "pending": pending,
                "delivery_rate": (delivered / total * 100) if total > 0 else 0,
                "checked_at": datetime.now().isoformat()
            }

    async def _notification_history(self, limit: int = 100,
                                  channel: str = None) -> Dict[str, Any]:
        """Get notification history"""
        history = self.notification_history

        if channel:
            history = [n for n in history if n["channel"] == channel]

        # Sort by creation time (newest first)
        history = sorted(history, key=lambda x: x["created_at"], reverse=True)

        # Limit results
        history = history[:limit]

        return {
            "total_count": len(self.notification_history),
            "filtered_count": len(history),
            "notifications": history,
            "retrieved_at": datetime.now().isoformat()
        }

    async def _test_channel(self, channel: str, recipient: str) -> Dict[str, Any]:
        """Test notification channel configuration"""
        test_notification = {
            "channel": channel,
            "recipients": [recipient],
            "subject": "Test Notification",
            "message": "This is a test notification to verify channel configuration.",
            "priority": "low"
        }

        result = await self._send_notification(**test_notification)

        return {
            "channel": channel,
            "test_result": result,
            "tested_at": datetime.now().isoformat()
        }

    async def _schedule_notification(self, schedule_time: str, **notification_data) -> Dict[str, Any]:
        """Schedule notification for future delivery"""
        try:
            schedule_dt = datetime.fromisoformat(schedule_time.replace('Z', '+00:00'))
        except ValueError:
            return {"error": "Invalid schedule time format. Use ISO format."}

        if schedule_dt <= datetime.now():
            return {"error": "Schedule time must be in the future"}

        scheduled_notification = {
            "id": f"sched_{int(time.time())}",
            "schedule_time": schedule_time,
            "notification_data": notification_data,
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }

        # In a real implementation, this would be stored in a persistent queue
        # and processed by a scheduler

        return {
            "schedule_id": scheduled_notification["id"],
            "schedule_time": schedule_time,
            "status": "scheduled",
            "note": "Scheduled notifications require a background scheduler to be implemented"
        }
