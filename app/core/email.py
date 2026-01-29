"""Email service for sending notifications."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails (mock implementation)."""
    
    @staticmethod
    async def send_invitation_email(
        to_email: str,
        organization_name: str,
        inviter_name: str,
        invitation_token: str,
        role: str
    ) -> bool:
        """
        Send invitation email to user.
        
        Args:
            to_email: Recipient email
            organization_name: Name of organization
            inviter_name: Name of person who invited
            invitation_token: Unique invitation token
            role: Role being offered
        
        Returns:
            True if sent successfully
        """
        # TODO: Implement actual email sending (SendGrid, AWS SES, etc.)
        invitation_link = f"https://app.evotrack.com/invitations/accept?token={invitation_token}"
        
        logger.info(
            f"📧 MOCK EMAIL - Invitation sent to {to_email}\n"
            f"   Organization: {organization_name}\n"
            f"   Invited by: {inviter_name}\n"
            f"   Role: {role}\n"
            f"   Link: {invitation_link}\n"
        )
        
        # Mock: always succeeds
        return True
    
    @staticmethod
    async def send_member_removed_email(
        to_email: str,
        organization_name: str,
        removed_by: str
    ) -> bool:
        """
        Send notification when member is removed.
        
        Args:
            to_email: Member's email
            organization_name: Organization name
            removed_by: Who removed them
        
        Returns:
            True if sent successfully
        """
        logger.info(
            f"📧 MOCK EMAIL - Member removed notification to {to_email}\n"
            f"   Organization: {organization_name}\n"
            f"   Removed by: {removed_by}\n"
        )
        
        return True