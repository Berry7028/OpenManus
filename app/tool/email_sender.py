"""
Email Sender Tool for sending emails with various features.
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Optional, List
from pathlib import Path

from app.tool.base import BaseTool, ToolResult


class EmailSender(BaseTool):
    """Tool for sending emails with attachments and formatting."""

    name: str = "email_sender"
    description: str = """Send emails with various features.

    Available commands:
    - send: Send a simple email
    - send_html: Send HTML formatted email
    - send_with_attachment: Send email with file attachments
    - send_bulk: Send bulk emails to multiple recipients
    - test_connection: Test SMTP connection
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["send", "send_html", "send_with_attachment", "send_bulk", "test_connection"],
                "type": "string",
            },
            "smtp_server": {
                "description": "SMTP server address (e.g., smtp.gmail.com).",
                "type": "string",
            },
            "smtp_port": {
                "description": "SMTP port (default: 587 for TLS, 465 for SSL).",
                "type": "integer",
            },
            "username": {
                "description": "SMTP username/email.",
                "type": "string",
            },
            "password": {
                "description": "SMTP password or app password.",
                "type": "string",
            },
            "from_email": {
                "description": "Sender email address.",
                "type": "string",
            },
            "to_email": {
                "description": "Recipient email address.",
                "type": "string",
            },
            "to_emails": {
                "description": "Multiple recipient email addresses (comma-separated).",
                "type": "string",
            },
            "cc_emails": {
                "description": "CC email addresses (comma-separated).",
                "type": "string",
            },
            "bcc_emails": {
                "description": "BCC email addresses (comma-separated).",
                "type": "string",
            },
            "subject": {
                "description": "Email subject.",
                "type": "string",
            },
            "body": {
                "description": "Email body text.",
                "type": "string",
            },
            "html_body": {
                "description": "HTML email body.",
                "type": "string",
            },
            "attachments": {
                "description": "File paths for attachments (comma-separated).",
                "type": "string",
            },
            "use_tls": {
                "description": "Use TLS encryption (default: True).",
                "type": "boolean",
            },
            "use_ssl": {
                "description": "Use SSL encryption (default: False).",
                "type": "boolean",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        to_email: Optional[str] = None,
        to_emails: Optional[str] = None,
        cc_emails: Optional[str] = None,
        bcc_emails: Optional[str] = None,
        subject: str = "No Subject",
        body: str = "",
        html_body: Optional[str] = None,
        attachments: Optional[str] = None,
        use_tls: bool = True,
        use_ssl: bool = False,
        **kwargs
    ) -> ToolResult:
        """Execute email sender command."""
        try:
            # Set default port based on encryption
            if smtp_port is None:
                smtp_port = 465 if use_ssl else 587

            if command == "send":
                return self._send_email(
                    smtp_server, smtp_port, username, password, from_email,
                    to_email, to_emails, cc_emails, bcc_emails, subject, body,
                    use_tls, use_ssl
                )
            elif command == "send_html":
                return self._send_html_email(
                    smtp_server, smtp_port, username, password, from_email,
                    to_email, to_emails, cc_emails, bcc_emails, subject, html_body,
                    use_tls, use_ssl
                )
            elif command == "send_with_attachment":
                return self._send_email_with_attachment(
                    smtp_server, smtp_port, username, password, from_email,
                    to_email, to_emails, cc_emails, bcc_emails, subject, body,
                    attachments, use_tls, use_ssl
                )
            elif command == "send_bulk":
                return self._send_bulk_email(
                    smtp_server, smtp_port, username, password, from_email,
                    to_emails, subject, body, use_tls, use_ssl
                )
            elif command == "test_connection":
                return self._test_connection(smtp_server, smtp_port, username, password, use_tls, use_ssl)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing email sender command '{command}': {str(e)}")

    def _create_smtp_connection(self, smtp_server: str, smtp_port: int, username: Optional[str],
                               password: Optional[str], use_tls: bool, use_ssl: bool):
        """Create SMTP connection."""
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                context = ssl.create_default_context()
                server.starttls(context=context)

        if username and password:
            server.login(username, password)

        return server

    def _parse_email_list(self, email_string: Optional[str]) -> List[str]:
        """Parse comma-separated email list."""
        if not email_string:
            return []
        return [email.strip() for email in email_string.split(',') if email.strip()]

    def _send_email(self, smtp_server: str, smtp_port: int, username: Optional[str],
                   password: Optional[str], from_email: Optional[str], to_email: Optional[str],
                   to_emails: Optional[str], cc_emails: Optional[str], bcc_emails: Optional[str],
                   subject: str, body: str, use_tls: bool, use_ssl: bool) -> ToolResult:
        """Send a simple text email."""
        try:
            if not from_email:
                from_email = username

            # Parse recipients
            recipients = []
            if to_email:
                recipients.append(to_email)
            if to_emails:
                recipients.extend(self._parse_email_list(to_emails))

            if not recipients:
                return ToolResult(error="No recipients specified")

            cc_list = self._parse_email_list(cc_emails)
            bcc_list = self._parse_email_list(bcc_emails)

            # Create message
            message = MIMEText(body)
            message["From"] = from_email
            message["To"] = ", ".join(recipients)
            if cc_list:
                message["Cc"] = ", ".join(cc_list)
            message["Subject"] = subject

            # All recipients (including CC and BCC)
            all_recipients = recipients + cc_list + bcc_list

            # Send email
            with self._create_smtp_connection(smtp_server, smtp_port, username, password, use_tls, use_ssl) as server:
                server.sendmail(from_email, all_recipients, message.as_string())

            return ToolResult(output=f"Email sent successfully to {len(all_recipients)} recipient(s):\n"
                                   f"To: {', '.join(recipients)}\n"
                                   f"CC: {', '.join(cc_list) if cc_list else 'None'}\n"
                                   f"BCC: {', '.join(bcc_list) if bcc_list else 'None'}\n"
                                   f"Subject: {subject}")
        except Exception as e:
            return ToolResult(error=f"Error sending email: {str(e)}")

    def _send_html_email(self, smtp_server: str, smtp_port: int, username: Optional[str],
                        password: Optional[str], from_email: Optional[str], to_email: Optional[str],
                        to_emails: Optional[str], cc_emails: Optional[str], bcc_emails: Optional[str],
                        subject: str, html_body: Optional[str], use_tls: bool, use_ssl: bool) -> ToolResult:
        """Send HTML formatted email."""
        try:
            if not html_body:
                return ToolResult(error="HTML body is required for HTML email")

            if not from_email:
                from_email = username

            # Parse recipients
            recipients = []
            if to_email:
                recipients.append(to_email)
            if to_emails:
                recipients.extend(self._parse_email_list(to_emails))

            if not recipients:
                return ToolResult(error="No recipients specified")

            cc_list = self._parse_email_list(cc_emails)
            bcc_list = self._parse_email_list(bcc_emails)

            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = from_email
            message["To"] = ", ".join(recipients)
            if cc_list:
                message["Cc"] = ", ".join(cc_list)
            message["Subject"] = subject

            # Add HTML content
            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # All recipients
            all_recipients = recipients + cc_list + bcc_list

            # Send email
            with self._create_smtp_connection(smtp_server, smtp_port, username, password, use_tls, use_ssl) as server:
                server.sendmail(from_email, all_recipients, message.as_string())

            return ToolResult(output=f"HTML email sent successfully to {len(all_recipients)} recipient(s):\n"
                                   f"To: {', '.join(recipients)}\n"
                                   f"CC: {', '.join(cc_list) if cc_list else 'None'}\n"
                                   f"BCC: {', '.join(bcc_list) if bcc_list else 'None'}\n"
                                   f"Subject: {subject}")
        except Exception as e:
            return ToolResult(error=f"Error sending HTML email: {str(e)}")

    def _send_email_with_attachment(self, smtp_server: str, smtp_port: int, username: Optional[str],
                                   password: Optional[str], from_email: Optional[str], to_email: Optional[str],
                                   to_emails: Optional[str], cc_emails: Optional[str], bcc_emails: Optional[str],
                                   subject: str, body: str, attachments: Optional[str],
                                   use_tls: bool, use_ssl: bool) -> ToolResult:
        """Send email with file attachments."""
        try:
            if not attachments:
                return ToolResult(error="Attachments are required for this command")

            if not from_email:
                from_email = username

            # Parse recipients
            recipients = []
            if to_email:
                recipients.append(to_email)
            if to_emails:
                recipients.extend(self._parse_email_list(to_emails))

            if not recipients:
                return ToolResult(error="No recipients specified")

            cc_list = self._parse_email_list(cc_emails)
            bcc_list = self._parse_email_list(bcc_emails)

            # Parse attachment list
            attachment_files = [f.strip() for f in attachments.split(',') if f.strip()]

            # Validate attachments
            for file_path in attachment_files:
                if not os.path.exists(file_path):
                    return ToolResult(error=f"Attachment file not found: {file_path}")

            # Create message
            message = MIMEMultipart()
            message["From"] = from_email
            message["To"] = ", ".join(recipients)
            if cc_list:
                message["Cc"] = ", ".join(cc_list)
            message["Subject"] = subject

            # Add body
            message.attach(MIMEText(body, "plain"))

            # Add attachments
            attached_files = []
            for file_path in attachment_files:
                try:
                    with open(file_path, "rb") as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())

                    encoders.encode_base64(part)
                    filename = Path(file_path).name
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {filename}',
                    )
                    message.attach(part)
                    attached_files.append(filename)
                except Exception as e:
                    return ToolResult(error=f"Error attaching file {file_path}: {str(e)}")

            # All recipients
            all_recipients = recipients + cc_list + bcc_list

            # Send email
            with self._create_smtp_connection(smtp_server, smtp_port, username, password, use_tls, use_ssl) as server:
                server.sendmail(from_email, all_recipients, message.as_string())

            return ToolResult(output=f"Email with attachments sent successfully to {len(all_recipients)} recipient(s):\n"
                                   f"To: {', '.join(recipients)}\n"
                                   f"CC: {', '.join(cc_list) if cc_list else 'None'}\n"
                                   f"BCC: {', '.join(bcc_list) if bcc_list else 'None'}\n"
                                   f"Subject: {subject}\n"
                                   f"Attachments: {', '.join(attached_files)}")
        except Exception as e:
            return ToolResult(error=f"Error sending email with attachments: {str(e)}")

    def _send_bulk_email(self, smtp_server: str, smtp_port: int, username: Optional[str],
                        password: Optional[str], from_email: Optional[str], to_emails: Optional[str],
                        subject: str, body: str, use_tls: bool, use_ssl: bool) -> ToolResult:
        """Send bulk emails to multiple recipients."""
        try:
            if not to_emails:
                return ToolResult(error="to_emails is required for bulk email")

            if not from_email:
                from_email = username

            # Parse recipients
            recipients = self._parse_email_list(to_emails)

            if not recipients:
                return ToolResult(error="No valid recipients found")

            sent_count = 0
            failed_count = 0
            failed_emails = []

            # Send individual emails to each recipient
            with self._create_smtp_connection(smtp_server, smtp_port, username, password, use_tls, use_ssl) as server:
                for recipient in recipients:
                    try:
                        # Create individual message
                        message = MIMEText(body)
                        message["From"] = from_email
                        message["To"] = recipient
                        message["Subject"] = subject

                        server.sendmail(from_email, [recipient], message.as_string())
                        sent_count += 1
                    except Exception as e:
                        failed_count += 1
                        failed_emails.append(f"{recipient}: {str(e)}")

            output = f"Bulk email completed:\n"
            output += f"Total recipients: {len(recipients)}\n"
            output += f"Successfully sent: {sent_count}\n"
            output += f"Failed: {failed_count}\n"

            if failed_emails:
                output += "\nFailed emails:\n"
                for failure in failed_emails:
                    output += f"  {failure}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error sending bulk email: {str(e)}")

    def _test_connection(self, smtp_server: str, smtp_port: int, username: Optional[str],
                        password: Optional[str], use_tls: bool, use_ssl: bool) -> ToolResult:
        """Test SMTP connection."""
        try:
            with self._create_smtp_connection(smtp_server, smtp_port, username, password, use_tls, use_ssl) as server:
                # Get server info
                server_info = server.noop()

            output = f"SMTP Connection Test Successful!\n"
            output += f"Server: {smtp_server}:{smtp_port}\n"
            output += f"Encryption: {'SSL' if use_ssl else 'TLS' if use_tls else 'None'}\n"
            output += f"Authentication: {'Yes' if username and password else 'No'}\n"
            output += f"Server Response: {server_info}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"SMTP connection test failed: {str(e)}")
