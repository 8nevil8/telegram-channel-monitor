"""Product matching logic for Telegram messages."""

import re
import logging
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Mapping of Cyrillic characters that look like Latin characters
# Used to normalize mixed Cyrillic/Latin text for better matching
CYRILLIC_TO_LATIN = {
    # Uppercase
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M',
    'Н': 'H', 'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T',
    'Х': 'X', 'У': 'Y', 'І': 'I',
    # Lowercase
    'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c',
    'у': 'y', 'х': 'x', 'і': 'i',
}


class ProductMatcher:
    """Matches products in messages based on keywords and filters."""

    def __init__(self, config: Dict):
        """Initialize the product matcher.

        Args:
            config: Configuration dictionary with matching settings
        """
        self.config = config
        self.products = config.get('products', [])
        self.matching_config = config.get('matching', {})
        self.case_sensitive = self.matching_config.get('case_sensitive', False)
        self.whole_word = self.matching_config.get('whole_word', False)
        self.regex_enabled = self.matching_config.get('regex_enabled', True)

        # Load price extraction configuration
        self.price_patterns = config.get('price_patterns', [])
        self.price_number_format = config.get('price_number_format', {})

        # Set default price number regex if not configured
        if not self.price_number_format.get('regex'):
            self.price_number_format['regex'] = r'(\d{1,4}(?:[,\s]\d{3})*(?:[.,]\d{1,2})?)'

        logger.debug(f"Loaded {len(self.price_patterns)} price patterns from config")

    def _normalize_text(self, text: str) -> str:
        """Normalize text by replacing Cyrillic look-alike characters with Latin.

        This helps catch spam/scam messages that use mixed Cyrillic/Latin characters
        to avoid detection (e.g., "iРhоnе" instead of "iphone").

        Args:
            text: Text to normalize

        Returns:
            Normalized text with Cyrillic look-alikes replaced by Latin
        """
        result = []
        for char in text:
            result.append(CYRILLIC_TO_LATIN.get(char, char))
        return ''.join(result)

    def match_message(self, message_text: str) -> List[Dict]:
        """Check if message matches any products.

        Args:
            message_text: The message text to check

        Returns:
            List of matched products with match details
        """
        if not message_text:
            return []

        matched_products = []

        for product in self.products:
            match_info = self._match_product(message_text, product)
            if match_info:
                matched_products.append(match_info)

        return matched_products

    def _match_product(self, message_text: str, product: Dict) -> Optional[Dict]:
        """Check if message matches a specific product.

        Args:
            message_text: The message text
            product: Product configuration

        Returns:
            Match information if matched, None otherwise
        """
        # Normalize Cyrillic look-alikes to Latin before matching
        normalized_text = self._normalize_text(message_text)
        text = normalized_text if self.case_sensitive else normalized_text.lower()

        # Check keywords
        matched_keywords = []
        for keyword in product.get('keywords', []):
            if self._match_keyword(text, keyword):
                matched_keywords.append(keyword)

        if not matched_keywords:
            return None

        # Check exclude keywords
        exclude_keywords = product.get('exclude_keywords') or []
        for exclude_keyword in exclude_keywords:
            if self._match_keyword(text, exclude_keyword):
                logger.debug(f"Message excluded due to keyword: {exclude_keyword}")
                return None

        # Check price range if specified
        price_match = None
        currency = None
        price_range = product.get('price_range')
        if price_range:
            price_info = self._extract_price(message_text)
            if price_info:
                price_match = price_info['value']
                currency = price_info['currency']
                min_price = price_range.get('min', 0)
                max_price = price_range.get('max', float('inf'))
                if not (min_price <= price_match <= max_price):
                    logger.debug(
                        f"Price {price_match} outside range {min_price}-{max_price}"
                    )
                    return None

        # Match found
        return {
            'product_name': product.get('name', 'Unknown'),
            'matched_keywords': matched_keywords,
            'price': price_match,
            'currency': currency,
            'notify': product.get('notify', True),
        }

    def _match_keyword(self, text: str, keyword: str) -> bool:
        """Check if keyword matches in text.

        Args:
            text: Text to search (already normalized and case-normalized)
            keyword: Keyword to find

        Returns:
            True if keyword matches
        """
        # Normalize keyword to handle Cyrillic look-alikes
        keyword_normalized = self._normalize_text(keyword)
        keyword_normalized = keyword_normalized if self.case_sensitive else keyword_normalized.lower()

        if self.regex_enabled:
            try:
                # Try as regex pattern
                if self.whole_word:
                    pattern = r'\b' + keyword_normalized + r'\b'
                else:
                    pattern = keyword_normalized

                return bool(re.search(pattern, text))
            except re.error:
                # If regex fails, fall back to simple string matching
                logger.warning(f"Invalid regex pattern: {keyword}")

        # Simple string matching
        if self.whole_word:
            # Match whole words only
            pattern = r'\b' + re.escape(keyword_normalized) + r'\b'
            return bool(re.search(pattern, text))
        else:
            return keyword_normalized in text

    def _extract_price(self, text: str) -> Optional[Dict]:
        """Extract price and currency from message text using configurable patterns.

        Uses price patterns from config.yaml to detect prices in various formats.

        Args:
            text: Message text

        Returns:
            Dict with 'value' (float) and 'currency' (str), or None
        """
        # If no patterns configured, return None
        if not self.price_patterns:
            logger.warning("No price patterns configured")
            return None

        # Get price number regex from config
        price_number_regex = self.price_number_format.get('regex', r'(\d{1,4}(?:[,\s]\d{3})*(?:[.,]\d{1,2})?)')

        # Try each pattern in order (first match wins)
        for pattern_config in self.price_patterns:
            pattern_template = pattern_config.get('pattern')
            if not pattern_template:
                continue

            # Replace {price} placeholder with the actual price number regex
            pattern = pattern_template.replace('{price}', price_number_regex)

            try:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Extract the price number from the first capturing group
                    price_str = match.group(1)

                    # Parse the price string to float
                    price = self._parse_price_string(price_str)

                    if price is not None:
                        # Check minimum value if specified in pattern
                        min_value = pattern_config.get('min_value', 0)
                        if price >= min_value:
                            # Detect currency from the matched text
                            currency = self._detect_currency(match.group(0))

                            logger.debug(
                                f"Price {price} {currency} extracted using pattern: {pattern_config.get('description', 'unknown')}"
                            )
                            return {'value': price, 'currency': currency}
                        else:
                            logger.debug(
                                f"Price {price} below min_value {min_value}, trying next pattern"
                            )
                            continue

            except (IndexError, ValueError, re.error) as e:
                logger.debug(f"Pattern '{pattern}' failed: {e}")
                continue

        logger.debug("No price found in message")
        return None

    def _detect_currency(self, matched_text: str) -> str:
        """Detect currency symbol from matched price text.

        Args:
            matched_text: The full matched price string

        Returns:
            Currency symbol (€, $, or empty string)
        """
        # Check for euro
        if '€' in matched_text or 'EUR' in matched_text.upper() or 'евро' in matched_text.lower():
            return '€'

        # Check for dollar
        if '$' in matched_text or 'USD' in matched_text.upper() or 'dollar' in matched_text.lower() or 'доллар' in matched_text.lower():
            return '$'

        # Default to empty if no currency detected
        return ''

    def _parse_price_string(self, price_str: str) -> Optional[float]:
        """Parse a price string to float, handling various separators.

        Args:
            price_str: Price string (e.g., "1,234.56", "1234,56", "1 234.56")

        Returns:
            Price as float or None if parsing fails
        """
        try:
            cleaned = price_str.strip()

            # Detect decimal separator by looking for the last dot or comma
            # If there are 1-2 digits after the last separator, it's a decimal
            last_dot_pos = cleaned.rfind('.')
            last_comma_pos = cleaned.rfind(',')

            decimal_sep = None
            decimal_pos = -1

            # Check which comes last and has 1-2 digits after it
            if last_dot_pos > last_comma_pos:
                after_dot = cleaned[last_dot_pos + 1:]
                if 1 <= len(after_dot) <= 2 and after_dot.isdigit():
                    decimal_sep = '.'
                    decimal_pos = last_dot_pos
            elif last_comma_pos > last_dot_pos:
                after_comma = cleaned[last_comma_pos + 1:]
                if 1 <= len(after_comma) <= 2 and after_comma.isdigit():
                    decimal_sep = ','
                    decimal_pos = last_comma_pos

            # Split into integer and decimal parts
            if decimal_sep and decimal_pos > 0:
                int_part = cleaned[:decimal_pos]
                dec_part = cleaned[decimal_pos + 1:]

                # Remove all separators from integer part
                int_part = int_part.replace(',', '').replace('.', '').replace(' ', '').replace('\u00a0', '')

                # Combine
                cleaned = int_part + '.' + dec_part
            else:
                # No decimal part, just remove all separators
                cleaned = cleaned.replace(',', '').replace('.', '').replace(' ', '').replace('\u00a0', '')

            return float(cleaned)

        except (ValueError, AttributeError) as e:
            logger.debug(f"Failed to parse price string '{price_str}': {e}")
            return None
