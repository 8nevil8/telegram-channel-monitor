"""Main entry point for Telegram Channel Monitor."""

import asyncio
import logging
import sys
from pathlib import Path
import yaml
from dotenv import load_dotenv
import os
from telethon import TelegramClient

from .monitor import ChannelMonitor

# Load environment variables
load_dotenv()


def setup_logging(config: dict):
    """Setup logging configuration.

    Args:
        config: Configuration dictionary
    """
    monitoring_config = config.get('monitoring', {})
    log_level = monitoring_config.get('log_level', 'INFO')
    log_file = monitoring_config.get('log_file', 'logs/monitor.log')

    # Ensure logs directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_config(config_path: str = 'config.yaml') -> dict:
    """Load configuration from YAML file.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        logging.error(f"Error parsing configuration file: {e}")
        sys.exit(1)


def validate_env_variables():
    """Validate required environment variables."""
    required_vars = ['API_ID', 'API_HASH', 'PHONE_NUMBER']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logging.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logging.error("Please copy .env.example to .env and fill in your credentials")
        sys.exit(1)


async def main():
    """Main application entry point."""
    # Load configuration
    config = load_config()

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)

    logger.info("=" * 50)
    logger.info("Telegram Channel Monitor")
    logger.info("=" * 50)

    # Validate environment variables
    validate_env_variables()

    # Get Telegram credentials from environment
    api_id = int(os.getenv('API_ID'))
    api_hash = os.getenv('API_HASH')
    phone_number = os.getenv('PHONE_NUMBER')
    session_name = os.getenv('SESSION_NAME', 'telegram_monitor')

    # Create Telegram client
    logger.info("Initializing Telegram client...")
    client = TelegramClient(session_name, api_id, api_hash)

    try:
        # Connect to Telegram
        await client.start(phone=phone_number)

        logger.info("Successfully connected to Telegram")

        # Get user info
        me = await client.get_me()
        logger.info(f"Logged in as: {me.first_name} (@{me.username})")

        # Create and start monitor
        monitor = ChannelMonitor(client, config)

        # Parse command line arguments
        if len(sys.argv) > 1 and sys.argv[1] == '--history':
            # Check history mode
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 100
            await monitor.check_history(limit=limit)
        else:
            # Real-time monitoring mode
            await monitor.start()

    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if client.is_connected():
            await client.disconnect()
        logger.info("Disconnected from Telegram")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
