"""
Envío de emails SMTP con contenido HTML + texto plano.
Compatible con Gmail (App Password), Outlook, y cualquier servidor SMTP.
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Envía emails usando SMTP con TLS.

    Gmail:   smtp.gmail.com:587  (necesita App Password, no contraseña normal)
    Outlook: smtp.office365.com:587
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        sender_email: str,
        sender_password: str,
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password

    def send(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        plain_body: Optional[str] = None,
        cc: Optional[list[str]] = None,
    ) -> bool:
        """
        Envía un email multipart (HTML + texto plano).
        plain_body se usa como fallback en clientes que no soporten HTML.
        """
        msg = MIMEMultipart("alternative")
        msg["From"] = f"BuscaCasas <{self.sender_email}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = ", ".join(cc)

        # Texto plano (fallback)
        if not plain_body:
            plain_body = (
                "Este email contiene un informe HTML. "
                "Abre este email en un cliente que soporte HTML para ver los resultados."
            )
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))

        # HTML (versión principal)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        recipients = [to_email] + (cc or [])

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, recipients, msg.as_string())

            logger.info(f"Email enviado a {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "Error de autenticacion SMTP. "
                "Verifica email/password. Para Gmail usa una App Password."
            )
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP: {e}")
            return False
        except Exception as e:
            logger.error(f"Error enviando email: {e}")
            return False
