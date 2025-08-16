"""
Message encoding utilities for safe command-line transmission.

*Version: 1.0.0*
*Author: Zeblit Development Team*

## Changelog
- 1.0.0 (2025-01-16): Initial encoding utilities for special character handling.
"""

import base64
import re
from typing import Optional, Tuple


class MessageEncoder:
    """Centralized message encoding/decoding for safe CLI transmission."""
    
    # Characters that cause issues in bash
    PROBLEMATIC_CHARS = {'!', '$', '`', '\\', '"', "'", '&', '|', ';', '(', ')', '<', '>'}
    
    @classmethod
    def needs_encoding(cls, message: str) -> bool:
        """
        Check if a message contains characters that need base64 encoding.
        
        Args:
            message: Message to check
            
        Returns:
            True if encoding is needed
        """
        return any(char in cls.PROBLEMATIC_CHARS for char in message)
    
    @classmethod
    def encode_message(cls, message: str) -> str:
        """
        Encode a message to base64 for safe transmission.
        
        Args:
            message: Original message
            
        Returns:
            Base64 encoded message with prefix
        """
        encoded_bytes = base64.b64encode(message.encode('utf-8'))
        encoded_str = encoded_bytes.decode('ascii')
        return f"b64:{encoded_str}"
    
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
    def always_encode(cls, message: str) -> str:
        """
        Always encode a message for consistent handling.
        
        Args:
            message: Original message
            
        Returns:
            Base64 encoded message with prefix
        """
        return cls.encode_message(message)
    
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
                return cls.decode_message(message)
            except ValueError:
                # If decoding fails, return original
                return message
        else:
            return message
    
    @classmethod
    def format_for_display(cls, message: str, max_length: Optional[int] = None) -> str:
        """
        Format a message for human-readable display (decode if needed, truncate if long).
        
        Args:
            message: Message to format
            max_length: Maximum length before truncation
            
        Returns:
            Human-readable formatted message
        """
        # Decode if encoded
        decoded = cls.safe_decode(message)
        
        # Truncate if needed
        if max_length and len(decoded) > max_length:
            return decoded[:max_length-3] + "..."
        
        return decoded


# Convenience functions for common operations
def encode_message(message: str) -> str:
    """Always encode a message for consistent handling."""
    return MessageEncoder.always_encode(message)


def decode_message(encoded_message: str) -> str:
    """Decode a base64 encoded message."""
    return MessageEncoder.decode_message(encoded_message)


def decode_for_display(message: str, max_length: Optional[int] = None) -> str:
    """Convenience wrapper for format_for_display."""
    return MessageEncoder.format_for_display(message, max_length)
