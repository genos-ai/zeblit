"""
Email service for sending transactional emails.

*Version: 1.0.0*
*Author: AI Development Platform Team*
"""

from typing import List, Dict, Any, Optional, Union
from uuid import UUID
import logging
import httpx

from modules.backend.core.config import settings
from modules.backend.core.exceptions import ServiceError
from modules.backend.models import User

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend."""
    
    def __init__(self):
        """Initialize email service with Resend configuration."""
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
        self.base_url = "https://api.resend.com"
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html: str,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email using Resend.
        
        Args:
            to: Recipient email address(es)
            subject: Email subject
            html: HTML content
            text: Plain text content (optional)
            from_email: Sender email (optional, uses default)
            from_name: Sender name (optional, uses default)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning("Email service not configured")
            return False
        
        try:
            # Prepare email data
            email_data = {
                "from": f"{from_name or settings.EMAIL_FROM_NAME} <{from_email or settings.EMAIL_FROM_ADDRESS}>",
                "to": to if isinstance(to, list) else [to],
                "subject": subject,
                "html": html,
            }
            
            if text:
                email_data["text"] = text
            
            # Send email
            response = self.resend.Emails.send(email_data)
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    async def send_welcome_email(self, user: User) -> str:
        """
        Send welcome email to new user.
        
        Args:
            user: User to welcome
            
        Returns:
            Email ID
        """
        subject = f"Welcome to {settings.APP_NAME}!"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4F46E5;">Welcome to {settings.APP_NAME}, {user.full_name}!</h1>
                
                <p>We're excited to have you join our AI-powered development platform.</p>
                
                <p>With {settings.APP_NAME}, you can:</p>
                <ul>
                    <li>Build applications using natural language</li>
                    <li>Collaborate with 6 specialized AI agents</li>
                    <li>Deploy your projects instantly</li>
                    <li>Track your development progress in real-time</li>
                </ul>
                
                <p>To get started:</p>
                <ol>
                    <li>Create your first project</li>
                    <li>Chat with our AI agents about what you want to build</li>
                    <li>Watch as your application comes to life!</li>
                </ol>
                
                <p style="margin-top: 30px;">
                    <a href="{settings.APP_URL}/projects/new" 
                       style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Create Your First Project
                    </a>
                </p>
                
                <p style="margin-top: 30px; font-size: 14px; color: #666;">
                    If you have any questions, feel free to reach out to our support team.
                </p>
                
                <hr style="margin-top: 40px; border: none; border-top: 1px solid #e5e5e5;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    © {settings.APP_NAME}. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to {settings.APP_NAME}, {user.full_name}!
        
        We're excited to have you join our AI-powered development platform.
        
        With {settings.APP_NAME}, you can:
        - Build applications using natural language
        - Collaborate with 6 specialized AI agents
        - Deploy your projects instantly
        - Track your development progress in real-time
        
        To get started:
        1. Create your first project
        2. Chat with our AI agents about what you want to build
        3. Watch as your application comes to life!
        
        Create your first project: {settings.APP_URL}/projects/new
        
        If you have any questions, feel free to reach out to our support team.
        
        © {settings.APP_NAME}. All rights reserved.
        """
        
        return await self.send_email(
            to=[user.email],
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags={"type": "welcome", "user_id": str(user.id)}
        )
    
    async def send_password_reset_email(
        self,
        user: User,
        reset_token: str
    ) -> str:
        """
        Send password reset email.
        
        Args:
            user: User requesting reset
            reset_token: Password reset token
            
        Returns:
            Email ID
        """
        reset_url = f"{settings.APP_URL}/auth/reset-password?token={reset_token}&email={user.email}"
        subject = f"Reset your {settings.APP_NAME} password"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4F46E5;">Password Reset Request</h1>
                
                <p>Hi {user.full_name},</p>
                
                <p>We received a request to reset your password. If you didn't make this request, 
                   you can safely ignore this email.</p>
                
                <p>To reset your password, click the button below:</p>
                
                <p style="margin-top: 30px;">
                    <a href="{reset_url}" 
                       style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Reset Password
                    </a>
                </p>
                
                <p style="margin-top: 20px; font-size: 14px; color: #666;">
                    This link will expire in 1 hour for security reasons.
                </p>
                
                <p style="font-size: 14px; color: #666;">
                    If the button doesn't work, you can copy and paste this link into your browser:<br>
                    <a href="{reset_url}" style="color: #4F46E5; word-break: break-all;">{reset_url}</a>
                </p>
                
                <hr style="margin-top: 40px; border: none; border-top: 1px solid #e5e5e5;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    © {settings.APP_NAME}. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {user.full_name},
        
        We received a request to reset your password. If you didn't make this request, 
        you can safely ignore this email.
        
        To reset your password, visit this link:
        {reset_url}
        
        This link will expire in 1 hour for security reasons.
        
        © {settings.APP_NAME}. All rights reserved.
        """
        
        return await self.send_email(
            to=[user.email],
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags={"type": "password_reset", "user_id": str(user.id)}
        )
    
    async def send_email_verification(
        self,
        user: User,
        verification_token: str
    ) -> str:
        """
        Send email verification link.
        
        Args:
            user: User to verify
            verification_token: Email verification token
            
        Returns:
            Email ID
        """
        verify_url = f"{settings.APP_URL}/auth/verify-email?token={verification_token}&user_id={user.id}"
        subject = f"Verify your {settings.APP_NAME} email"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4F46E5;">Verify Your Email</h1>
                
                <p>Hi {user.full_name},</p>
                
                <p>Please verify your email address to complete your registration.</p>
                
                <p style="margin-top: 30px;">
                    <a href="{verify_url}" 
                       style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Verify Email
                    </a>
                </p>
                
                <p style="margin-top: 20px; font-size: 14px; color: #666;">
                    If the button doesn't work, you can copy and paste this link into your browser:<br>
                    <a href="{verify_url}" style="color: #4F46E5; word-break: break-all;">{verify_url}</a>
                </p>
                
                <hr style="margin-top: 40px; border: none; border-top: 1px solid #e5e5e5;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    © {settings.APP_NAME}. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Verify Your Email
        
        Hi {user.full_name},
        
        Please verify your email address to complete your registration.
        
        Verify your email: {verify_url}
        
        © {settings.APP_NAME}. All rights reserved.
        """
        
        return await self.send_email(
            to=[user.email],
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags={"type": "email_verification", "user_id": str(user.id)}
        )
    
    async def send_project_invitation(
        self,
        inviter: User,
        invitee_email: str,
        project_name: str,
        project_id: UUID
    ) -> str:
        """
        Send project collaboration invitation.
        
        Args:
            inviter: User sending invitation
            invitee_email: Email to invite
            project_name: Project name
            project_id: Project ID
            
        Returns:
            Email ID
        """
        invite_url = f"{settings.APP_URL}/projects/{project_id}/accept-invite"
        subject = f"{inviter.full_name} invited you to collaborate on {project_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #4F46E5;">Project Collaboration Invitation</h1>
                
                <p>{inviter.full_name} has invited you to collaborate on <strong>{project_name}</strong>.</p>
                
                <p>As a collaborator, you'll be able to:</p>
                <ul>
                    <li>View and edit the project code</li>
                    <li>Chat with AI agents about the project</li>
                    <li>Track development progress</li>
                    <li>Deploy and test the application</li>
                </ul>
                
                <p style="margin-top: 30px;">
                    <a href="{invite_url}" 
                       style="background-color: #4F46E5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">
                        Accept Invitation
                    </a>
                </p>
                
                <p style="margin-top: 20px; font-size: 14px; color: #666;">
                    If you don't have an account yet, you'll be prompted to create one.
                </p>
                
                <hr style="margin-top: 40px; border: none; border-top: 1px solid #e5e5e5;">
                
                <p style="font-size: 12px; color: #999; text-align: center;">
                    © {settings.APP_NAME}. All rights reserved.
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Project Collaboration Invitation
        
        {inviter.full_name} has invited you to collaborate on {project_name}.
        
        As a collaborator, you'll be able to:
        - View and edit the project code
        - Chat with AI agents about the project
        - Track development progress
        - Deploy and test the application
        
        Accept invitation: {invite_url}
        
        If you don't have an account yet, you'll be prompted to create one.
        
        © {settings.APP_NAME}. All rights reserved.
        """
        
        return await self.send_email(
            to=[invitee_email],
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            tags={
                "type": "project_invitation",
                "project_id": str(project_id),
                "inviter_id": str(inviter.id)
            }
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose() 