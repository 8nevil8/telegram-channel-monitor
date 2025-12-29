"""Telegram channel monitoring service."""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
from telethon import TelegramClient, events
from telethon.tl.types import Message

from .matcher import ProductMatcher
from .notifier import Notifier

logger = logging.getLogger(__name__)


class ChannelMonitor:
    """Monitors Telegram channels for specific products."""

    def __init__(self, client: TelegramClient, config: Dict):
        """Initialize the channel monitor.

        Args:
            client: Telethon client instance
            config: Configuration dictionary
        """
        self.client = client
        self.config = config
        self.channels = config.get('channels', [])
        self.matcher = ProductMatcher(config)
        self.notifier = Notifier(client, config)

        # Monitoring settings
        monitoring_config = config.get('monitoring', {})
        self.save_matches = monitoring_config.get('save_matches', True)
        self.matches_file = monitoring_config.get('matches_file', 'logs/matches.json')
        self.max_age_days = monitoring_config.get('max_age_days')

        # Ensure logs directory exists
        Path(self.matches_file).parent.mkdir(parents=True, exist_ok=True)

        self.matched_messages = []

        # Log max age configuration
        if self.max_age_days and self.max_age_days > 0:
            logger.info(f"Age filtering enabled: only messages from past {self.max_age_days} days will be processed")
        else:
            logger.info("Age filtering disabled: all messages will be processed")

    async def start(self):
        """Start monitoring channels."""
        if not self.channels:
            logger.error("No channels configured to monitor")
            return

        logger.info(f"Starting monitor for {len(self.channels)} channel(s)")

        # Validate channels
        valid_channels = await self._validate_channels()

        if not valid_channels:
            logger.error("No valid channels to monitor")
            return

        logger.info(f"Monitoring channels: {valid_channels}")

        # Register event handler for new messages
        @self.client.on(events.NewMessage(chats=valid_channels))
        async def handle_new_message(event):
            await self._process_message(event.message)

        logger.info("Monitor started. Listening for new messages...")
        logger.info("Press Ctrl+C to stop")

        # Keep the client running
        await self.client.run_until_disconnected()

    def _normalize_channel_id(self, channel_id: str) -> str:
        """Normalize channel identifier from various formats.

        Supports:
        - https://t.me/channelname
        - http://t.me/channelname
        - t.me/channelname
        - @channelname
        - channelname
        - -1001234567890 (numeric ID)

        Args:
            channel_id: Channel identifier in any supported format

        Returns:
            Normalized channel identifier (username or numeric ID)
        """
        if isinstance(channel_id, int):
            return channel_id

        channel_str = str(channel_id).strip()

        # Handle numeric IDs
        if channel_str.lstrip('-').isdigit():
            return int(channel_str)

        # Handle t.me URLs
        if 't.me/' in channel_str.lower():
            # Extract username from URL
            # Supports: https://t.me/channel, http://t.me/channel, t.me/channel
            parts = channel_str.split('t.me/')
            if len(parts) > 1:
                username = parts[1].split('/')[0].split('?')[0]  # Remove trailing slash or query params
                return username.strip()

        # Handle @username format - remove @ if present
        if channel_str.startswith('@'):
            return channel_str[1:]

        # Return as-is (plain username or other format)
        return channel_str

    async def _validate_channels(self) -> List:
        """Validate and resolve channel identifiers.

        Returns:
            List of valid channel entities
        """
        valid_channels = []

        for channel_id in self.channels:
            try:
                # Normalize the channel identifier
                normalized_id = self._normalize_channel_id(channel_id)

                # Try to get the channel entity
                entity = await self.client.get_entity(normalized_id)
                valid_channels.append(entity)
                logger.info(f"Successfully connected to channel: {channel_id} (normalized: {normalized_id})")
            except Exception as e:
                logger.error(f"Failed to access channel '{channel_id}': {e}")
                logger.error(
                    f"Make sure you have access to the channel and the ID is correct"
                )

        return valid_channels

    def _is_message_too_old(self, message: Message) -> bool:
        """Check if message is older than the configured max age.

        Args:
            message: Telegram message object

        Returns:
            True if message is too old and should be skipped, False otherwise
        """
        # If max_age_days is not set or is 0, don't filter by age
        if not self.max_age_days or self.max_age_days <= 0:
            return False

        # Check if message has a date
        if not message.date:
            logger.warning(f"Message {message.id} has no date, skipping age check")
            return False

        # Calculate the cutoff date
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=self.max_age_days)

        # Make message date timezone-aware if it isn't already
        message_date = message.date
        if message_date.tzinfo is None:
            message_date = message_date.replace(tzinfo=timezone.utc)

        # Check if message is too old
        is_too_old = message_date < cutoff_date

        if is_too_old:
            logger.debug(
                f"Message from {message_date} is older than {self.max_age_days} days, skipping"
            )

        return is_too_old

    async def _process_message(self, message: Message, stats: Optional[Dict] = None):
        """Process a new message from monitored channels.

        Args:
            message: Telegram message object
            stats: Optional dict to track statistics (messages_scanned, matches_found, etc.)
        """
        try:
            # Track statistics if provided
            if stats is not None:
                stats['messages_scanned'] += 1

            # Get message date for logging
            msg_date = message.date.strftime('%Y-%m-%d %H:%M:%S') if message.date else 'unknown'

            # Check if message is too old
            if self._is_message_too_old(message):
                logger.debug(f"⏭️  Msg #{message.id} ({msg_date}) - Skipped: too old")
                if stats is not None:
                    stats['messages_skipped_old'] += 1
                return

            # Get message text
            message_text = message.message or ""

            if not message_text:
                logger.debug(f"⏭️  Msg #{message.id} ({msg_date}) - Skipped: no text")
                if stats is not None:
                    stats['messages_no_text'] += 1
                return

            # Log message being scanned
            preview_length = 100
            preview = message_text[:preview_length].replace('\n', ' ')
            if len(message_text) > preview_length:
                preview += "..."
            logger.info(f"🔍 Msg #{message.id} ({msg_date}): {preview}")

            # Try to match products
            matches = self.matcher.match_message(message_text)

            if not matches:
                logger.info(f"   ❌ No product matches")
                if stats is not None:
                    stats['messages_no_match'] += 1
                return

            # Get channel name
            channel_name = await self._get_channel_name(message)

            # Get message link
            message_link = await self._get_message_link(message)

            # Get message datetime
            message_datetime = message.date

            # Process each match - SEND SEPARATE NOTIFICATION FOR EACH PRODUCT MATCH
            logger.info(f"   ✅ Found {len(matches)} product match(es)!")

            # Log the full message content when matches are found
            logger.info(f"\n{'='*70}\n📄 FULL MESSAGE CONTENT:\n{'='*70}")
            logger.info(f"{message_text}")
            logger.info(f"{'='*70}\n")

            for idx, match_info in enumerate(matches, 1):
                logger.info(
                    f"   [{idx}/{len(matches)}] 📦 {match_info['product_name']} "
                    f"(keywords: {', '.join(match_info['matched_keywords'])})"
                )
                if match_info.get('price'):
                    logger.info(f"       💰 Price: ${match_info['price']:.2f}")

                # Send notification (separate notification for each product match)
                await self.notifier.send_notification(
                    match_info, message_text, message_link, channel_name, message_datetime
                )

                # Small delay between notifications to avoid rate limiting
                if idx < len(matches):
                    await asyncio.sleep(0.5)

                # Save match
                if self.save_matches:
                    self._save_match(match_info, message_text, message_link, message, channel_name)

                # Track statistics
                if stats is not None:
                    stats['matches_found'] += 1

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)

    async def _get_channel_name(self, message: Message) -> str:
        """Get the channel name/title.

        Args:
            message: Telegram message object

        Returns:
            Channel name (username or title)
        """
        try:
            chat = await message.get_chat()

            # Prefer username for public channels
            if hasattr(chat, 'username') and chat.username:
                return f"@{chat.username}"

            # Fall back to title
            if hasattr(chat, 'title') and chat.title:
                return chat.title

            # Last resort - use chat ID
            return f"Channel {chat.id}"

        except Exception as e:
            logger.error(f"Failed to get channel name: {e}")
            return "Unknown Channel"

    async def _get_message_link(self, message: Message) -> str:
        """Get a link to the message.

        Args:
            message: Telegram message object

        Returns:
            Message link
        """
        try:
            chat = await message.get_chat()

            # For channels with username
            if hasattr(chat, 'username') and chat.username:
                return f"https://t.me/{chat.username}/{message.id}"

            # For private channels/groups (requires chat ID)
            chat_id = str(chat.id)
            if chat_id.startswith('-100'):
                chat_id = chat_id[4:]  # Remove -100 prefix
            return f"https://t.me/c/{chat_id}/{message.id}"

        except Exception as e:
            logger.error(f"Failed to generate message link: {e}")
            return ""

    def _save_match(
        self,
        match_info: Dict,
        message_text: str,
        message_link: str,
        message: Message,
        channel_name: str,
    ):
        """Save matched message to file.

        Args:
            match_info: Product match information
            message_text: Original message text
            message_link: Link to message
            message: Telegram message object
            channel_name: Name of the channel
        """
        try:
            match_record = {
                'timestamp': datetime.now().isoformat(),
                'product_name': match_info['product_name'],
                'matched_keywords': match_info['matched_keywords'],
                'price': match_info.get('price'),
                'channel_name': channel_name,
                'message_text': message_text,
                'message_link': message_link,
                'message_id': message.id,
                'chat_id': message.chat_id,
                'date': message.date.isoformat() if message.date else None,
            }

            self.matched_messages.append(match_record)

            # Save to file
            with open(self.matches_file, 'w', encoding='utf-8') as f:
                json.dump(self.matched_messages, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved match to {self.matches_file}")

        except Exception as e:
            logger.error(f"Failed to save match: {e}", exc_info=True)

    async def check_history(self, limit: int = 100):
        """Check recent message history in channels.

        Args:
            limit: Number of recent messages to check per channel
        """
        logger.info("=" * 70)
        logger.info(f"HISTORY SCAN: Checking last {limit} messages in each channel...")
        logger.info("=" * 70)

        valid_channels = await self._validate_channels()

        # Track overall statistics
        overall_stats = {
            'messages_scanned': 0,
            'matches_found': 0,
            'messages_skipped_old': 0,
            'messages_no_text': 0,
            'messages_no_match': 0,
        }

        for channel in valid_channels:
            try:
                channel_name = channel.title if hasattr(channel, 'title') else str(channel.id)
                logger.info(f"\n📊 Scanning channel: {channel_name}")
                logger.info(f"   Requested: {limit} messages")

                # Track per-channel statistics
                channel_stats = {
                    'messages_scanned': 0,
                    'matches_found': 0,
                    'messages_skipped_old': 0,
                    'messages_no_text': 0,
                    'messages_no_match': 0,
                }

                # Collect messages first, then process in chronological order (oldest to newest)
                messages = []
                async for message in self.client.iter_messages(channel, limit=limit):
                    messages.append(message)

                # Reverse to get oldest first
                messages.reverse()

                # Process messages in chronological order
                for message in messages:
                    await self._process_message(message, stats=channel_stats)

                # Update overall stats
                for key in overall_stats:
                    overall_stats[key] += channel_stats[key]

                # Log channel statistics
                logger.info(f"   ✓ Scanned: {channel_stats['messages_scanned']} messages")
                logger.info(f"   ✓ Matches: {channel_stats['matches_found']} product match(es)")
                logger.info(f"   • Skipped (too old): {channel_stats['messages_skipped_old']}")
                logger.info(f"   • Skipped (no text): {channel_stats['messages_no_text']}")
                logger.info(f"   • No match: {channel_stats['messages_no_match']}")

            except Exception as e:
                logger.error(f"Error checking history for channel: {e}", exc_info=True)

        # Log overall statistics
        logger.info("\n" + "=" * 70)
        logger.info("📊 SCAN COMPLETE - OVERALL STATISTICS:")
        logger.info("=" * 70)
        logger.info(f"✓ Total messages scanned: {overall_stats['messages_scanned']}")
        logger.info(f"✓ Total matches found: {overall_stats['matches_found']}")
        logger.info(f"✓ Total notifications sent: {overall_stats['matches_found']}")
        logger.info(f"• Messages skipped (too old): {overall_stats['messages_skipped_old']}")
        logger.info(f"• Messages skipped (no text): {overall_stats['messages_no_text']}")
        logger.info(f"• Messages with no match: {overall_stats['messages_no_match']}")
        logger.info("=" * 70)

        if overall_stats['matches_found'] > 0:
            logger.info(f"✉️  Sent {overall_stats['matches_found']} notification(s) to Telegram")
            logger.info(f"💾 Saved {overall_stats['matches_found']} match(es) to {self.matches_file}")
        else:
            logger.info("ℹ️  No matches found in scanned messages")

        logger.info("=" * 70)
