# Telegram Channel Monitor

Monitor Telegram channels for specific products (buy/sell listings) and receive notifications when matches are found. Perfect for tracking marketplace channels, deal alerts, and trading groups.

## Features

- **Real-time Monitoring**: Listens for new messages in Telegram channels as they arrive
- **Multiple Channels**: Monitor several channels for the same products simultaneously
- **Channel Reference**: Each notification shows which channel the message came from
- **Age Filtering**: Only show items from the past X days (ignore old listings)
- **Flexible Matching**: Support for keywords, regex patterns, and exclude filters
- **Price Filtering**: Automatically detect and filter by price ranges
- **Telegram Notifications**: Get instant notifications in your Saved Messages
- **History Scanning**: Check past messages in channels
- **Match Logging**: Save all matches to JSON for later review
- **Multiple Products**: Monitor multiple products simultaneously
- **User Bot**: Works with channels you don't own (as long as you have access)

## How It Works

This tool uses Telegram's MTProto API (via Telethon) to authenticate as your personal user account. It can monitor any channel that you have access to, including:
- Public channels (by username)
- Private channels you've joined (by ID)
- Groups you're a member of

## Prerequisites

- Python 3.8 or higher
- A Telegram account
- API credentials from Telegram (free)

**Platform Support:**
- ✅ Linux
- ✅ Windows
- ✅ macOS

## Installation

### 1. Clone or Download

```bash
cd telegram-channel-monitor
```

### 2. Create Virtual Environment (Recommended)

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Get Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Click "API development tools"
4. Create a new application (any name/description)
5. Note your `api_id` and `api_hash`

### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
API_ID=your_api_id_here
API_HASH=your_api_hash_here
PHONE_NUMBER=+1234567890
```

### 6. Configure Products to Monitor

Edit `config.yaml` to specify:
- Channels to monitor
- Products to search for
- Keywords and price ranges
- Notification preferences

Example configuration:

```yaml
channels:
  - "https://t.me/dealsandsteals"  # Full URL format
  - "@techmarketplace"              # Username format

products:
  - name: "iPhone 15 Pro"
    keywords:
      - "iphone 15 pro"
      - "iphone15pro"
    price_range:
      min: 500
      max: 1200
    notify: true
```

## Usage

### Quick Start Scripts

**Linux/macOS:**
```bash
./run.sh                 # Real-time monitoring
./run.sh --history 100   # Check history
```

**Windows:**
```cmd
run.bat                  # Real-time monitoring
run.bat --history 100    # Check history
```

### First Time Setup

On first run, you'll need to authenticate:

**Linux/macOS:**
```bash
python3 -m src.main
```

**Windows:**
```cmd
python -m src.main
```

You'll receive a code via Telegram. Enter it to complete authentication. A session file will be saved so you won't need to authenticate again.

### Real-time Monitoring

Start monitoring for new messages:

**Linux/macOS:**
```bash
python3 -m src.main
# or use the helper script
./run.sh
```

**Windows:**
```cmd
python -m src.main
REM or use the helper script
run.bat
```

The monitor will run continuously and send notifications when matches are found.

### Check Message History

Scan recent messages in channels (useful for initial setup):

**Linux/macOS:**
```bash
python3 -m src.main --history 100
# or
./run.sh --history 100
```

**Windows:**
```cmd
python -m src.main --history 100
REM or
run.bat --history 100
```

This checks the last 100 messages in each channel and processes them in **chronological order (oldest to newest)**. Adjust the number as needed.

**Why oldest-first order?**
- See listings in the order they were posted
- Understand the timeline of available items
- Notifications arrive in chronological sequence

## Configuration Guide

### Finding Channel IDs

**For Public Channels - Multiple Formats Supported:**
You can use any of these formats:
- **Full URL**: `https://t.me/channelname` (easiest - just copy from browser!)
- **Username with @**: `@channelname`
- **Plain username**: `channelname`

**For Private Channels:**
1. Forward a message from the channel to [@userinfobot](https://t.me/userinfobot)
2. It will show you the channel ID (e.g., `-1001234567890`)
3. Use this numeric ID in your config

**Pro Tip:** Just copy the channel link from Telegram or your browser and paste it directly! The monitor will automatically parse it.

### Monitoring Multiple Channels

You can monitor **multiple channels for the same products**! Simply list all channels in your config using any supported format:

```yaml
channels:
  - "https://t.me/marketplace1"  # Full URL
  - "@marketplace2"              # Username with @
  - "dealsgroup"                 # Plain username
  - -1001234567890               # Private channel numeric ID
```

**Benefits:**
- All products are matched across **all channels** automatically
- Each notification shows which channel the message came from
- Perfect for monitoring multiple marketplaces for the same items
- The `channel_name` is also saved in the match log (`logs/matches.json`)

**Example use case:**
If you're looking for an iPhone 15 Pro, you can monitor 5 different marketplace channels simultaneously. When found in any channel, you'll get a notification showing which marketplace it's from!

### Keyword Matching

**Simple Keywords:**
```yaml
keywords:
  - "macbook pro"
  - "ps5"
```

**Regex Patterns:**
```yaml
keywords:
  - "rtx.*4090"  # Matches "rtx 4090", "rtx4090", etc.
  - "iphone (14|15) pro"  # Matches iPhone 14 Pro or 15 Pro
```

**Exclude Keywords:**
```yaml
exclude_keywords:
  - "broken"
  - "parts only"
  - "case"  # Excludes phone case listings
```

### Price Detection

The tool automatically detects prices in various formats:
- `$1,234.56`
- `1234 USD`
- `€1.234,56`
- `1234` (plain numbers)

Set price ranges to filter:
```yaml
price_range:
  min: 500    # Minimum price
  max: 2000   # Maximum price
```

### Age Filtering

Filter out old listings by only processing messages from the past X days. Perfect for marketplace channels where old posts are no longer relevant.

Configure in `config.yaml`:
```yaml
monitoring:
  max_age_days: 7  # Only process messages from past 7 days
```

**How it works:**
- Messages older than the specified number of days are automatically skipped
- Applies to both real-time monitoring and history checks
- Set to `0` or `null` to disable age filtering (process all messages)

**Example use cases:**
- `max_age_days: 1` - Only show items posted today or yesterday
- `max_age_days: 7` - Only show items from the past week
- `max_age_days: 30` - Only show items from the past month
- `max_age_days: 0` - Show all items regardless of age

**Benefits:**
- Avoid notifications for outdated/sold items
- Reduce noise from old posts when scanning history
- Focus on fresh listings only

The monitor logs will show when age filtering is enabled: `"Age filtering enabled: only messages from past 7 days will be processed"`

## Testing

The project includes a comprehensive test suite to verify price extraction and product matching logic. This is especially useful when:
- Adding new price patterns to `config.yaml`
- Testing keyword matching with your specific use cases
- Debugging why certain messages aren't matching

### Running Tests

**Run all tests:**
```bash
python test_matcher.py
```

**Show detailed output for each test:**
```bash
python test_matcher.py --verbose
```

**Show debug logs (see pattern matching details):**
```bash
python test_matcher.py --debug
```

### Test Output Example

```
================================================================================
                               MATCHER TEST SUITE
================================================================================
Configuration loaded:
  • Products: 5
  • Price patterns: 17
  • Case sensitive: False
  • Regex enabled: True

Total test cases: 25

================================================================================
                      COMPREHENSIVE MESSAGE MATCHING TESTS
================================================================================

✅ PASS # 1: iPhone 13 with euro price in range (450 < 700)
✅ PASS # 2: iPhone with Russian keyword айфон and евро currency
✅ PASS # 3: iPhone ABOVE max price (850 > 700) - should NOT match
❌ FAIL # 5: iPhone case with exclude keyword - should NOT match
       Msg: Продаю iPhone 13 case Новый, в упаковке Цена: 25€
       Expected: No match | Got: iPhone

Summary
--------------------------------------------------------------------------------
Total tests:  25
Passed:       17
Failed:       8
Success rate: 68%

Failed Cases
--------------------------------------------------------------------------------

❌ 1. iPhone case with exclude keyword - should NOT match

Original Message:
Продаю iPhone 13 case
Новый, в упаковке
Цена: 25€

Matching Criteria:
iPhone (keywords: ['iphone'], exclude: ['case'])

Expected: No match
Got:      iPhone

What was matched:
  • iPhone: keywords=['iphone'], price=25.0 €
```

### Adding Your Own Test Cases

You can easily add test cases by editing `test_matcher.py`. Add to the `test_cases` list:

```python
test_cases = [
    {
        'message': """iPhone 13 128gb Green
Батарейка 80%
Полный комплект: с коробкой и даже оригинальным проводом + 2 чехла
Цена: 450 €""",
        'expected_matches': ['iPhone'],  # or [] for no match
        'description': 'iPhone 13 with euro price in range (450 < 700)',
        'matching_criteria': {
            'iPhone': {
                'keywords': ['iphone', 'айфон'],
                'price_range': {'max': 700},
                'exclude_keywords': ['куплю', 'case'],
            }
        }
    },
    {
        'message': """Куплю iPhone 13 в хорошем состоянии
Цена до 500 евро""",
        'expected_matches': [],  # Should NOT match
        'description': 'iPhone with exclude keyword "куплю" (buying)',
        'matching_criteria': {
            'iPhone': {
                'keywords': ['iphone'],
                'exclude_keywords': ['куплю'],
            }
        }
    },
    # Add your own test cases here!
]
```

**Test Format:**
- `message`: Full original message text (as it appears in Telegram)
- `expected_matches`: List of product names that should match, or `[]` for no match
- `description`: Brief description of what this tests
- `matching_criteria`: Shows the matching rules being tested (for documentation)

### Understanding Test Results

- ✅ **Green PASS**: The test matched expectations
- ❌ **Red FAIL**: The test didn't match expectations
- **Failed Cases section**: Shows details of what went wrong

**Common reasons for failures:**
- **Ambiguous numbers**: "iPhone 13 450€" could be interpreted as 13,450 or just 450
- **Model numbers**: "iPhone 13" has the number 13, which some patterns might catch
- **Exclude keywords not working**: Check your `config.yaml` exclude_keywords configuration

### Testing Your Configuration

Before running the monitor, it's a good idea to test your configuration:

1. **Add test cases** that match messages you expect to see in your channels
2. **Run the test suite** to verify your price patterns work correctly
3. **Adjust price_patterns in config.yaml** if tests fail
4. **Re-run tests** until you get the expected results

This iterative approach helps ensure your monitor will catch the right messages without false positives.

## Project Structure

```
telegram-channel-monitor/
├── src/
│   ├── __init__.py       # Package initialization
│   ├── main.py           # Entry point and CLI
│   ├── monitor.py        # Channel monitoring logic
│   ├── matcher.py        # Product matching engine
│   └── notifier.py       # Notification handler
├── config.yaml           # Configuration file (copy from config.example.yaml)
├── config.example.yaml   # Configuration template
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Environment template
├── run.sh                # Linux/macOS startup script
├── run.bat               # Windows startup script
├── test_matcher.py       # Comprehensive test suite
├── requirements.txt      # Python dependencies
└── README.md             # This file

# Logs stored in user's home directory (cross-platform)
~/.tgmonitor/
├── monitor.log           # Application logs
└── matches.json          # Saved matches
```

**Note:** Logs and match data are stored in `~/.tgmonitor/` directory in your home folder. This works on all platforms (Linux, macOS, Windows).

## Notification Example

When a product is found, you'll receive a message like:

```
🔔 Found: Mac Mini

📢 Channel: @buyandselllt
🕒 Posted: 2025-12-27 13:25:20
🔑 Keywords: Mac mini M4
💰 Price: 600.00€

📝 Message:
Продам Mac mini M4 (2024) — мощный и компактный компьютер для работы и творчества.
Конфигурация: 16 ГБ ОЗУ / 256 ГБ SSD — быстрый, тихий и энергоэффективный.
Состояние отличное, полностью готов к использованию.

🔹 Без коробки
🔹 Привезён из США

💶 Цена: 600 €

🔗 View Original Message
```

**Features shown:**
- **Channel name** helps you identify which marketplace the listing came from
- **Posted datetime** shows when the message was originally posted
- **Currency detection** automatically shows € for euros or $ for dollars
- **Matched keywords** show why this message was selected
- **Price display** shows the detected price with correct currency
- Perfect for monitoring multiple channels for the same products!

## Tips and Best Practices

1. **Start with History Check**: Run `--history 50` first to test your keywords
2. **Be Specific**: Use multiple keywords to reduce false positives
3. **Use Exclude Keywords**: Filter out unwanted listings (cases, broken items, etc.)
4. **Set Age Filter**: Use `max_age_days` to ignore old listings (recommended: 7 days for marketplaces)
5. **Test Price Detection**: Check `logs/matches.json` to see if prices are detected correctly
6. **Monitor Logs**: Watch `logs/monitor.log` for any issues
7. **Adjust Regex**: Enable/disable regex in config if you don't need it

## Troubleshooting

### "Failed to access channel"
- Make sure you're a member of the channel (join it in Telegram first)
- For private channels, verify the numeric ID is correct
- Check that the channel username is spelled correctly

### "No matches found"
- Test your keywords with `--history` mode first
- Check `logs/monitor.log` for matching attempts
- Try broader keywords or disable `whole_word` matching

### "Authentication failed"
- Verify your `API_ID`, `API_HASH`, and `PHONE_NUMBER` in `.env`
- Delete the session file and authenticate again
- Make sure you're entering the correct code from Telegram

### Price not detected
- Check the message format in `logs/matches.json`
- The price extractor supports common formats, but some may be missed
- Consider making price_range optional for that product

## Legal and Ethical Considerations

- **Telegram ToS**: This tool uses official Telegram APIs in a way that complies with their Terms of Service
- **User Bot Limits**: Telegram may rate-limit user accounts. Don't spam or abuse the API
- **Privacy**: You can only access channels you're already a member of
- **Responsibility**: Use this tool responsibly and respect channel rules
- **No Spam**: Don't use this to spam or harass users

## Advanced Usage

### Running as a Service

**Linux (systemd):**

Create `/etc/systemd/system/telegram-monitor.service`:

```ini
[Unit]
Description=Telegram Channel Monitor
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/telegram-channel-monitor
ExecStart=/usr/bin/python3 -m src.main
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable telegram-monitor
sudo systemctl start telegram-monitor
```

**macOS (launchd):**

Create `~/Library/LaunchAgents/com.telegram.monitor.plist` and use `launchctl load`.

### Running in Docker

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.main"]
```

Build and run:
```bash
docker build -t telegram-monitor .
docker run -v $(pwd)/config.yaml:/app/config.yaml \
           -v $(pwd)/.env:/app/.env \
           -v $(pwd)/logs:/app/logs \
           telegram-monitor
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is provided as-is for personal use. Respect Telegram's Terms of Service and use responsibly.

## Acknowledgments

- Built with [Telethon](https://github.com/LonamiWebs/Telethon) - Telegram client library
- Inspired by the need to monitor marketplace channels for deals

---

**Happy Monitoring!** 🔔
