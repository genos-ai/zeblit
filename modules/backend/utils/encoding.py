"""
Message encoding utilities for the backend.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-16): Initial backend encoding utilities.
"""

import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MessageDecoder:
    """Centralized message decoding for backend processing."""
    
    @classmethod
    def is_encoded(cls, message: str) -> bool:
        """
        Check if a message is base64 encoded.
        
        Args:
            message: Message to check
            
        Returns:
            True if message appears to be base64 encoded
        """
        return message.startswith('b64:')
    
    @classmethod
    def decode_message(cls, encoded_message: str) -> str:
        """
        Decode a base64 encoded message.
        
        Args:
            encoded_message: Base64 encoded message (with or without prefix)
            
        Returns:
            Original decoded message
            
        Raises:
            ValueError: If decoding fails
        """
        try:
            # Remove prefix if present
            if encoded_message.startswith('b64:'):
                encoded_str = encoded_message[4:]
            else:
                encoded_str = encoded_message
            
            # Decode from base64
            decoded_bytes = base64.b64decode(encoded_str)
            return decoded_bytes.decode('utf-8')
            
        except Exception as e:
            raise ValueError(f"Failed to decode message: {str(e)}")
    
    @classmethod
    def safe_decode(cls, message: str) -> str:
        """
        Safely decode a message, returning original if not encoded.
        
        Args:
            message: Potentially encoded message
            
        Returns:
            Decoded message or original if not encoded
        """
        if cls.is_encoded(message):
            try:
                decoded = cls.decode_message(message)
                logger.debug(f"Decoded message: {decoded[:100]}{'...' if len(decoded) > 100 else ''}")
                return decoded
            except ValueError as e:
                logger.warning(f"Failed to decode message, using original: {e}")
                return message
        else:
            return message
    
    @classmethod
    def format_for_logging(cls, message: str, max_length: Optional[int] = 200) -> str:
        """
        Format a message for logging (decode if needed, truncate if long).
        
        Args:
            message: Message to format
            max_length: Maximum length before truncation
            
        Returns:
            Human-readable formatted message for logs
        """
        # Decode if encoded
        decoded = cls.safe_decode(message)
        
        # Truncate if needed
        if max_length and len(decoded) > max_length:
            return decoded[:max_length-3] + "..."
        
        return decoded


# Convenience function
def decode_chat_message(message: str) -> str:
    """Convenience function to decode chat messages consistently."""
    return MessageDecoder.safe_decode(message)
