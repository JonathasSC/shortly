
import re
from typing import Iterable


class LogSanitizerService:
    DEFAULT_PATTERNS = [
        r"Authorization:\s*Bearer\s+[A-Za-z0-9\-._~+/]+=*",
        r"Bearer\s+[A-Za-z0-9\-._~+/]+=*",
        r"password\s*=\s*['\"].+?['\"]",
        r"SECRET[_A-Z]*\s*=\s*.+",
        r"TOKEN[_A-Z]*\s*=\s*.+",
        r"api[_-]?key\s*=\s*.+",
        r"sessionid=[A-Za-z0-9]+",
        r"csrftoken=[A-Za-z0-9]+",
    ]

    def __init__(self, extra_patterns: Iterable[str] | None = None):
        patterns = list(self.DEFAULT_PATTERNS)
        if extra_patterns:
            patterns.extend(extra_patterns)

        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in patterns
        ]

    def sanitize(self, line: str) -> str:
        try:
            sanitized = line
            for pattern in self.compiled_patterns:
                sanitized = pattern.sub(self._mask, sanitized)
            return sanitized
        except Exception:
            return "[LOG SANITIZATION ERROR]"

    @staticmethod
    def _mask(match: re.Match) -> str:
        text = match.group(0)

        if len(text) <= 8:
            return "[REDACTED]"

        return text[:4] + "****" + text[-4:]

    def contains_sensitive_data(self, line: str) -> bool:
        return any(pattern.search(line) for pattern in self.compiled_patterns)
