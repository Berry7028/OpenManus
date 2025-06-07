"""
Password Generator Tool for creating secure passwords and evaluating password strength.
"""

import random
import string
import secrets
import hashlib
import re
from typing import Optional, List
import math

from app.tool.base import BaseTool, ToolResult


class PasswordGenerator(BaseTool):
    """Tool for generating secure passwords and evaluating password strength."""

    name: str = "password_generator"
    description: str = """Generate secure passwords and evaluate password strength.

    Available commands:
    - generate: Generate a secure password
    - generate_passphrase: Generate a passphrase using words
    - evaluate: Evaluate password strength
    - generate_multiple: Generate multiple passwords
    - hash_password: Hash a password using various algorithms
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["generate", "generate_passphrase", "evaluate", "generate_multiple", "hash_password"],
                "type": "string",
            },
            "length": {
                "description": "Password length (default: 12).",
                "type": "integer",
            },
            "include_uppercase": {
                "description": "Include uppercase letters (default: True).",
                "type": "boolean",
            },
            "include_lowercase": {
                "description": "Include lowercase letters (default: True).",
                "type": "boolean",
            },
            "include_numbers": {
                "description": "Include numbers (default: True).",
                "type": "boolean",
            },
            "include_symbols": {
                "description": "Include symbols (default: True).",
                "type": "boolean",
            },
            "exclude_ambiguous": {
                "description": "Exclude ambiguous characters (0, O, l, I, etc.).",
                "type": "boolean",
            },
            "password": {
                "description": "Password to evaluate or hash.",
                "type": "string",
            },
            "word_count": {
                "description": "Number of words in passphrase (default: 4).",
                "type": "integer",
            },
            "separator": {
                "description": "Separator for passphrase words (default: -).",
                "type": "string",
            },
            "count": {
                "description": "Number of passwords to generate (default: 5).",
                "type": "integer",
            },
            "hash_algorithm": {
                "description": "Hash algorithm (md5, sha1, sha256, sha512).",
                "type": "string",
            },
            "salt": {
                "description": "Salt for password hashing.",
                "type": "string",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        length: int = 12,
        include_uppercase: bool = True,
        include_lowercase: bool = True,
        include_numbers: bool = True,
        include_symbols: bool = True,
        exclude_ambiguous: bool = False,
        password: Optional[str] = None,
        word_count: int = 4,
        separator: str = "-",
        count: int = 5,
        hash_algorithm: str = "sha256",
        salt: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """Execute password generator command."""
        try:
            if command == "generate":
                return self._generate_password(length, include_uppercase, include_lowercase,
                                             include_numbers, include_symbols, exclude_ambiguous)
            elif command == "generate_passphrase":
                return self._generate_passphrase(word_count, separator)
            elif command == "evaluate":
                return self._evaluate_password(password)
            elif command == "generate_multiple":
                return self._generate_multiple_passwords(count, length, include_uppercase,
                                                       include_lowercase, include_numbers,
                                                       include_symbols, exclude_ambiguous)
            elif command == "hash_password":
                return self._hash_password(password, hash_algorithm, salt)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing password generator command '{command}': {str(e)}")

    def _generate_password(self, length: int, include_uppercase: bool, include_lowercase: bool,
                          include_numbers: bool, include_symbols: bool, exclude_ambiguous: bool) -> ToolResult:
        """Generate a secure password."""
        try:
            if length < 4:
                return ToolResult(error="Password length must be at least 4 characters")

            # Build character set
            chars = ""
            if include_lowercase:
                chars += string.ascii_lowercase
            if include_uppercase:
                chars += string.ascii_uppercase
            if include_numbers:
                chars += string.digits
            if include_symbols:
                chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

            if not chars:
                return ToolResult(error="At least one character type must be included")

            # Remove ambiguous characters if requested
            if exclude_ambiguous:
                ambiguous = "0O1lI"
                chars = "".join(c for c in chars if c not in ambiguous)

            # Generate password ensuring at least one character from each selected type
            password = []

            # Add at least one character from each selected type
            if include_lowercase:
                password.append(secrets.choice(string.ascii_lowercase))
            if include_uppercase:
                password.append(secrets.choice(string.ascii_uppercase))
            if include_numbers:
                password.append(secrets.choice(string.digits))
            if include_symbols:
                password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))

            # Fill remaining length with random characters
            for _ in range(length - len(password)):
                password.append(secrets.choice(chars))

            # Shuffle the password
            secrets.SystemRandom().shuffle(password)
            final_password = "".join(password)

            # Calculate entropy
            entropy = self._calculate_entropy(final_password, len(chars))
            strength = self._get_strength_rating(entropy)

            output = f"Generated Password: {final_password}\n"
            output += f"Length: {len(final_password)} characters\n"
            output += f"Character Set Size: {len(chars)}\n"
            output += f"Entropy: {entropy:.1f} bits\n"
            output += f"Strength: {strength}\n"
            output += f"Time to crack (brute force): {self._estimate_crack_time(entropy)}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error generating password: {str(e)}")

    def _generate_passphrase(self, word_count: int, separator: str) -> ToolResult:
        """Generate a passphrase using words."""
        try:
            # Common word list (simplified for demo)
            words = [
                "apple", "banana", "cherry", "dragon", "elephant", "forest", "guitar", "house",
                "island", "jungle", "kitten", "lemon", "mountain", "ocean", "piano", "queen",
                "river", "sunset", "tiger", "umbrella", "violet", "window", "yellow", "zebra",
                "bridge", "castle", "dream", "eagle", "flower", "garden", "happy", "ice",
                "jazz", "knight", "light", "magic", "night", "orange", "peace", "quiet",
                "rainbow", "star", "tree", "unique", "voice", "water", "extra", "young",
                "adventure", "beautiful", "creative", "delicious", "exciting", "fantastic",
                "gorgeous", "incredible", "joyful", "kindness", "lovely", "marvelous",
                "natural", "outstanding", "perfect", "wonderful", "amazing", "brilliant"
            ]

            if word_count < 2:
                return ToolResult(error="Word count must be at least 2")

            # Select random words
            selected_words = [secrets.choice(words) for _ in range(word_count)]

            # Create passphrase
            passphrase = separator.join(selected_words)

            # Calculate entropy (approximate)
            word_pool_size = len(words)
            entropy = word_count * math.log2(word_pool_size)
            strength = self._get_strength_rating(entropy)

            output = f"Generated Passphrase: {passphrase}\n"
            output += f"Word Count: {word_count}\n"
            output += f"Length: {len(passphrase)} characters\n"
            output += f"Word Pool Size: {word_pool_size}\n"
            output += f"Entropy: {entropy:.1f} bits\n"
            output += f"Strength: {strength}\n"
            output += f"Time to crack (brute force): {self._estimate_crack_time(entropy)}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error generating passphrase: {str(e)}")

    def _evaluate_password(self, password: Optional[str]) -> ToolResult:
        """Evaluate password strength."""
        try:
            if not password:
                return ToolResult(error="Password is required for evaluation")

            # Basic metrics
            length = len(password)
            has_lowercase = bool(re.search(r'[a-z]', password))
            has_uppercase = bool(re.search(r'[A-Z]', password))
            has_numbers = bool(re.search(r'\d', password))
            has_symbols = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))

            # Character set size
            charset_size = 0
            if has_lowercase:
                charset_size += 26
            if has_uppercase:
                charset_size += 26
            if has_numbers:
                charset_size += 10
            if has_symbols:
                charset_size += 32  # Approximate

            # Calculate entropy
            entropy = self._calculate_entropy(password, charset_size)

            # Check for common patterns
            patterns = self._check_patterns(password)

            # Check for common passwords (simplified)
            is_common = self._is_common_password(password)

            # Overall strength
            strength = self._get_strength_rating(entropy)
            if is_common:
                strength = "Very Weak (Common Password)"
            elif patterns:
                strength += " (Contains Patterns)"

            output = f"Password Evaluation: {password}\n"
            output += "=" * 40 + "\n"
            output += f"Length: {length} characters\n"
            output += f"Character Types:\n"
            output += f"  Lowercase: {'✓' if has_lowercase else '✗'}\n"
            output += f"  Uppercase: {'✓' if has_uppercase else '✗'}\n"
            output += f"  Numbers: {'✓' if has_numbers else '✗'}\n"
            output += f"  Symbols: {'✓' if has_symbols else '✗'}\n"
            output += f"Character Set Size: {charset_size}\n"
            output += f"Entropy: {entropy:.1f} bits\n"
            output += f"Strength: {strength}\n"
            output += f"Time to crack (brute force): {self._estimate_crack_time(entropy)}\n"

            if patterns:
                output += f"\nDetected Patterns:\n"
                for pattern in patterns:
                    output += f"  - {pattern}\n"

            if is_common:
                output += "\n⚠️  WARNING: This is a commonly used password!\n"

            # Recommendations
            recommendations = self._get_recommendations(password, has_lowercase, has_uppercase,
                                                      has_numbers, has_symbols, length, patterns)
            if recommendations:
                output += f"\nRecommendations:\n"
                for rec in recommendations:
                    output += f"  - {rec}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error evaluating password: {str(e)}")

    def _generate_multiple_passwords(self, count: int, length: int, include_uppercase: bool,
                                   include_lowercase: bool, include_numbers: bool,
                                   include_symbols: bool, exclude_ambiguous: bool) -> ToolResult:
        """Generate multiple passwords."""
        try:
            if count < 1 or count > 50:
                return ToolResult(error="Count must be between 1 and 50")

            passwords = []
            for i in range(count):
                result = self._generate_password(length, include_uppercase, include_lowercase,
                                               include_numbers, include_symbols, exclude_ambiguous)
                if result.error:
                    return result

                # Extract password from output
                password_line = result.output.split('\n')[0]
                password = password_line.split(': ')[1]
                passwords.append(password)

            output = f"Generated {count} Passwords:\n"
            output += "=" * 30 + "\n"
            for i, pwd in enumerate(passwords, 1):
                output += f"{i:2d}. {pwd}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error generating multiple passwords: {str(e)}")

    def _hash_password(self, password: Optional[str], hash_algorithm: str, salt: Optional[str]) -> ToolResult:
        """Hash a password using various algorithms."""
        try:
            if not password:
                return ToolResult(error="Password is required for hashing")

            # Prepare password for hashing
            password_bytes = password.encode('utf-8')
            if salt:
                password_bytes = salt.encode('utf-8') + password_bytes

            # Hash the password
            if hash_algorithm.lower() == "md5":
                hash_obj = hashlib.md5(password_bytes)
            elif hash_algorithm.lower() == "sha1":
                hash_obj = hashlib.sha1(password_bytes)
            elif hash_algorithm.lower() == "sha256":
                hash_obj = hashlib.sha256(password_bytes)
            elif hash_algorithm.lower() == "sha512":
                hash_obj = hashlib.sha512(password_bytes)
            else:
                return ToolResult(error=f"Unsupported hash algorithm: {hash_algorithm}")

            hash_hex = hash_obj.hexdigest()

            output = f"Password Hash:\n"
            output += f"Algorithm: {hash_algorithm.upper()}\n"
            output += f"Salt: {salt if salt else 'None'}\n"
            output += f"Hash: {hash_hex}\n"

            # Security note
            if hash_algorithm.lower() in ["md5", "sha1"]:
                output += f"\n⚠️  WARNING: {hash_algorithm.upper()} is considered cryptographically weak!\n"
                output += "Consider using SHA-256 or SHA-512 for better security.\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error hashing password: {str(e)}")

    def _calculate_entropy(self, password: str, charset_size: int) -> float:
        """Calculate password entropy."""
        if charset_size == 0:
            return 0.0
        return len(password) * math.log2(charset_size)

    def _get_strength_rating(self, entropy: float) -> str:
        """Get strength rating based on entropy."""
        if entropy < 30:
            return "Very Weak"
        elif entropy < 50:
            return "Weak"
        elif entropy < 70:
            return "Fair"
        elif entropy < 90:
            return "Strong"
        else:
            return "Very Strong"

    def _estimate_crack_time(self, entropy: float) -> str:
        """Estimate time to crack password."""
        # Assume 1 billion guesses per second
        guesses_per_second = 1e9
        total_combinations = 2 ** entropy
        average_time = total_combinations / (2 * guesses_per_second)

        if average_time < 1:
            return "Less than 1 second"
        elif average_time < 60:
            return f"{average_time:.1f} seconds"
        elif average_time < 3600:
            return f"{average_time/60:.1f} minutes"
        elif average_time < 86400:
            return f"{average_time/3600:.1f} hours"
        elif average_time < 31536000:
            return f"{average_time/86400:.1f} days"
        elif average_time < 31536000000:
            return f"{average_time/31536000:.1f} years"
        else:
            return f"{average_time/31536000000:.1f} centuries"

    def _check_patterns(self, password: str) -> List[str]:
        """Check for common patterns in password."""
        patterns = []

        # Sequential characters
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            patterns.append("Sequential letters")

        if re.search(r'(012|123|234|345|456|567|678|789)', password):
            patterns.append("Sequential numbers")

        # Repeated characters
        if re.search(r'(.)\1{2,}', password):
            patterns.append("Repeated characters")

        # Keyboard patterns
        keyboard_patterns = ['qwerty', 'asdf', 'zxcv', '1234', 'qwer', 'asdfg']
        for pattern in keyboard_patterns:
            if pattern in password.lower():
                patterns.append(f"Keyboard pattern: {pattern}")

        # Common substitutions
        if re.search(r'[4@]', password) and 'a' not in password.lower():
            patterns.append("Common substitution (a->4/@)")
        if re.search(r'[3]', password) and 'e' not in password.lower():
            patterns.append("Common substitution (e->3)")
        if re.search(r'[0]', password) and 'o' not in password.lower():
            patterns.append("Common substitution (o->0)")

        return patterns

    def _is_common_password(self, password: str) -> bool:
        """Check if password is commonly used."""
        common_passwords = [
            "password", "123456", "password123", "admin", "qwerty", "letmein",
            "welcome", "monkey", "1234567890", "abc123", "111111", "123123",
            "password1", "1234", "12345", "dragon", "master", "login"
        ]
        return password.lower() in common_passwords

    def _get_recommendations(self, password: str, has_lowercase: bool, has_uppercase: bool,
                           has_numbers: bool, has_symbols: bool, length: int, patterns: List[str]) -> List[str]:
        """Get recommendations for improving password."""
        recommendations = []

        if length < 8:
            recommendations.append("Use at least 8 characters (12+ recommended)")
        elif length < 12:
            recommendations.append("Consider using 12+ characters for better security")

        if not has_lowercase:
            recommendations.append("Include lowercase letters")
        if not has_uppercase:
            recommendations.append("Include uppercase letters")
        if not has_numbers:
            recommendations.append("Include numbers")
        if not has_symbols:
            recommendations.append("Include symbols (!@#$%^&*)")

        if patterns:
            recommendations.append("Avoid predictable patterns and sequences")

        if self._is_common_password(password):
            recommendations.append("Avoid commonly used passwords")

        if not recommendations:
            recommendations.append("Your password looks good! Consider using a password manager.")

        return recommendations
