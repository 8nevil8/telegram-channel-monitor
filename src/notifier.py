"""Notification handler for matched products."""

import logging
from typing import Dict, Optional
from telethon import TelegramClient

logger = logging.getLogger(__name__)


class Notifier:
    """Handles notifications for matched products."""

    def __init__(self, client: TelegramClient, config: Dict):
        """Initialize the notifier.

        Args:
            client: Telethon client instance
            config: Configuration dictionary
        """
        self.client = client
        self.config = config
        self.notification_config = config.get('notifications', {})
        self.telegram_config = self.notification_config.get('telegram', {})
        self.include_link = self.notification_config.get('include_link', True)
        self.include_keywords = self.notification_config.get('include_keywords', True)

    async def send_notification(
        self,
        match_info: Dict,
        message_text: str,
        message_link: Optional[str] = None,
        channel_name: Optional[str] = None,
        message_datetime: Optional[object] = None,
    ):
        """Send notification for a matched product.

        Args:
            match_info: Product match information
            message_text: Original message text
            message_link: Link to the original message
            channel_name: Name of the channel where the message was found
            message_datetime: Datetime of the original message
        """
        if not match_info.get('notify', True):
            return

        if self.telegram_config.get('enabled', True):
            await self._send_telegram_notification(
                match_info, message_text, message_link, channel_name, message_datetime
            )

    async def _send_telegram_notification(
        self,
        match_info: Dict,
        message_text: str,
        message_link: Optional[str] = None,
        channel_name: Optional[str] = None,
        message_datetime: Optional[object] = None,
    ):
        """Send Telegram notification.

        Args:
            match_info: Product match information
            message_text: Original message text
            message_link: Link to the original message
            channel_name: Name of the channel where the message was found
            message_datetime: Datetime of the original message
        """
        try:
            # Build notification message
            notification_parts = []

            # Header
            product_name = match_info.get('product_name', 'Unknown Product')
            notification_parts.append(f"🔔 **Found: {product_name}**\n")

            # Channel name
            if channel_name:
                notification_parts.append(f"📢 **Channel:** {channel_name}")

            # Message datetime
            if message_datetime:
                # Format datetime in a readable way
                formatted_date = message_datetime.strftime('%Y-%m-%d %H:%M:%S')
                notification_parts.append(f"🕒 **Posted:** {formatted_date}")

            # Matched keywords
            if self.include_keywords and match_info.get('matched_keywords'):
                keywords = ', '.join(match_info['matched_keywords'])
                notification_parts.append(f"🔑 **Keywords:** {keywords}")

            # Price
            if match_info.get('price'):
                currency = match_info.get('currency', '$')
                price_value = match_info['price']
                # Format with currency symbol in appropriate position
                if currency == '€':
                    notification_parts.append(f"💰 **Price:** {price_value:.2f}{currency}")
                else:
                    notification_parts.append(f"💰 **Price:** {currency}{price_value:.2f}")

            notification_parts.append("")  # Empty line

            # Original message (truncated if too long)
            max_message_length = 500
            if len(message_text) > max_message_length:
                truncated_text = message_text[:max_message_length] + "..."
            else:
                truncated_text = message_text

            notification_parts.append(f"📝 **Message:**\n{truncated_text}")

            # Link to original message
            if self.include_link and message_link:
                notification_parts.append(f"\n🔗 [View Original Message]({message_link})")

            notification_text = "\n".join(notification_parts)

            # Get chat to send to
            chat_id = self.telegram_config.get('chat_id', 'me')

            # Send notification
            await self.client.send_message(
                chat_id,
                notification_text,
                parse_mode='markdown',
                link_preview=False,
            )

            logger.info(f"       📤 Notification sent to Telegram")

        except Exception as e:
            logger.error(f"❌ Failed to send Telegram notification: {e}", exc_info=True)
