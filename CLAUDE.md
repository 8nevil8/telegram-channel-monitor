# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Telegram channel monitoring bot that watches Telegram channels for product listings based on configurable keywords, price ranges, and filters. It uses Telethon (MTProto API) to act as a user bot and sends notifications to Telegram when matches are found.

## Development Commands

### Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Real-time monitoring
python3 -m src.main

# Check message history (scan last N messages)
python3 -m src.main --history 100

# Helper scripts available
./run.sh                 # Linux/macOS
./run.sh --history 100
run.bat                  # Windows
```

### Testing
There is no formal test suite. The README mentions `test_matcher.py` but this file doesn't exist in the current codebase.

### Configuration
- `config.yaml` - Main configuration file (products, channels, matching rules)
- `.env` - Environment variables (API credentials)
- Logs stored in `~/.tgmonitor/` (cross-platform home directory)

## Architecture

### Core Components

**src/main.py** - Entry point
- Loads configuration from `config.yaml` and environment variables from `.env`
- Sets up logging to both file (`~/.tgmonitor/monitor.log`) and stdout
- Initializes Telethon client with user credentials (API_ID, API_HASH, PHONE_NUMBER)
- Creates ChannelMonitor and delegates to either real-time monitoring or history scanning based on CLI args
- Handles graceful shutdown on KeyboardInterrupt

**src/monitor.py** - Channel monitoring orchestrator
- `ChannelMonitor` class manages the monitoring lifecycle
- Normalizes channel identifiers from various formats (URLs, usernames, numeric IDs)
- Validates channels on startup by resolving entities via Telethon
- Implements age filtering (`max_age_days`) to skip old messages
- For real-time mode: registers event handler for `events.NewMessage` and runs until disconnected
- For history mode: fetches messages via `iter_messages()`, reverses to chronological order (oldest first), processes each
- Delegates product matching to `ProductMatcher` and notifications to `Notifier`
- Saves matches to JSON file at `~/.tgmonitor/matches.json`
- Tracks statistics (messages scanned, matches found, skipped messages) during history scans

**src/matcher.py** - Product matching engine
- `ProductMatcher` class handles all matching logic
- Normalizes text by converting Cyrillic look-alike characters to Latin (anti-spam measure)
- Matches keywords with optional regex support and whole-word matching
- Implements exclude keywords to filter out unwanted messages (e.g., "куплю", "case")
- Extracts prices using configurable patterns from `config.yaml` with sophisticated parsing
- Price parsing handles multiple formats: space-separated thousands, commas, dots, various currency symbols
- Price extraction uses pattern priority: tries patterns in order, first match wins
- Detects currency (€, $) from matched text context
- Validates price ranges when configured for products

**src/notifier.py** - Notification handler
- `Notifier` class sends notifications to Telegram
- Formats notifications with emojis, product name, channel name, posted datetime, keywords, price, message preview
- Sends to user's Saved Messages by default (chat_id: "me") or configured chat
- Truncates long messages to 500 characters
- Includes message link with markdown formatting
- Currency display adapts to symbol (€ after price, $ before price)

### Data Flow

1. **Message Receipt**: Telethon receives message from monitored channel (real-time or history)
2. **Age Filtering**: Monitor checks if message is within `max_age_days` threshold
3. **Text Extraction**: Monitor extracts message text
4. **Normalization**: Matcher normalizes text (Cyrillic → Latin conversion)
5. **Keyword Matching**: Matcher checks if any product's keywords match
6. **Exclude Filtering**: Matcher checks if exclude keywords present (early exit if match)
7. **Price Extraction**: Matcher attempts to extract price using configured patterns
8. **Price Validation**: Matcher validates price is within configured range
9. **Match Recording**: Monitor saves match to JSON file
10. **Notification**: Notifier formats and sends notification to Telegram

### Configuration Architecture

**config.yaml structure:**
- `channels[]` - List of channel identifiers (supports URLs, @usernames, numeric IDs)
- `products[]` - Each product has: name, keywords, exclude_keywords, price_range (min/max), notify flag
- `notifications` - Telegram settings (enabled, chat_id), include_link, include_keywords
- `monitoring` - check_interval, max_age_days, save_matches, file paths, log_level
- `matching` - case_sensitive, whole_word, regex_enabled flags
- `price_patterns[]` - Ordered list of price detection patterns (uses {price} placeholder)
- `price_number_format` - Regex and separators for number parsing

**Price Pattern Priority:**
The price extraction system tries patterns in sequence. Most specific patterns come first to avoid ambiguity:
1. Currency + space-separated (e.g., "€ 1 500")
2. Space-separated + currency with digit limits (e.g., "1 500€" but not "13 450€")
3. End-of-description prices (e.g., "...description 450€")
4. Simple standalone (e.g., "450€")
5. Named currencies (e.g., "450 EUR")
6. Context-based (e.g., "цена: 450")
7. Plain numbers as fallback (with min_value threshold)

### Session Management

- Telethon stores session in `telegram_monitor.session` file (or custom via SESSION_NAME env var)
- First run requires phone authentication with code from Telegram
- Subsequent runs reuse session automatically
- Session file location is in project root by default

## Important Patterns

### Channel ID Normalization
The monitor accepts multiple channel identifier formats and normalizes them:
- Full URLs: `https://t.me/channel` → `channel`
- @ prefix: `@channel` → `channel`
- Numeric IDs: `-1001234567890` → `-1001234567890` (int)
- Plain usernames: `channel` → `channel`

This normalization happens in `ChannelMonitor._normalize_channel_id()` before entity resolution.

### Cyrillic-Latin Normalization
To catch spam messages that use mixed scripts (e.g., "iРhоnе"), the matcher normalizes Cyrillic look-alikes to Latin equivalents. This happens before keyword matching. The mapping is in `CYRILLIC_TO_LATIN` dict in matcher.py.

### Age Filtering Logic
Age filtering compares message datetime with `now - max_age_days`:
- If `max_age_days` is 0 or null → no filtering
- Message datetime must be timezone-aware (converts to UTC if needed)
- Applies to both real-time monitoring and history scans

### Multiple Matches per Message
A single message can match multiple products. Each match:
- Gets logged separately
- Sends a separate notification
- Is saved to matches.json individually
- Has a 0.5s delay between notifications to avoid rate limiting

## Common Modifications

### Adding New Keywords
Edit `config.yaml` → `products[].keywords[]`. Supports plain strings or regex patterns if `matching.regex_enabled: true`.

### Adjusting Price Patterns
Add new pattern to `config.yaml` → `price_patterns[]`. Place more specific patterns earlier in the list. Use `{price}` placeholder for the number part.

### Changing Notification Format
Modify `Notifier._send_telegram_notification()` in src/notifier.py. The notification is built as a list of parts joined with newlines.

### Supporting New Currency
Add currency detection logic to `ProductMatcher._detect_currency()` and update price patterns in config.yaml.

### Modifying Logging
Logging configuration is in `src/main.py:setup_logging()`. Logs go to both file and stdout. Log level set in config.yaml.

## Environment Variables

Required in `.env`:
- `API_ID` - Telegram API ID (get from https://my.telegram.org/apps)
- `API_HASH` - Telegram API hash
- `PHONE_NUMBER` - User's phone number with country code

Optional:
- `SESSION_NAME` - Custom session file name (default: "telegram_monitor")

## File Paths

All log and data files use `os.path.expanduser()` to support `~` in paths for cross-platform compatibility. Default locations:
- Logs: `~/.tgmonitor/monitor.log`
- Matches: `~/.tgmonitor/matches.json`
- Session: `./telegram_monitor.session` (project root)

## Notes

- This is a user bot, not a bot account. It runs with user's credentials and can access any channel the user has joined.
- Rate limiting: Telethon handles most rate limiting internally, but the monitor adds 0.5s delays between multiple notifications.
- History scanning reverses message order to process chronologically (oldest → newest) so notifications arrive in time sequence.
- The monitor saves ALL matches to matches.json cumulatively (appends to list).
- Telethon event handlers are async and run continuously via `run_until_disconnected()`.
