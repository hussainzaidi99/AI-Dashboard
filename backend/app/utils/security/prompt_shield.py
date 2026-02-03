"""
PromptShield - Security utility for AI Data Assistant
Detects and mitigates prompt injection attempts.
"""
#backend/app/utils/security/prompt_shield.py

import re
import base64
import logging
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class PromptShield:
    """Security guardrails for LLM inputs"""
    
    # Common Patterns for Prompt Injection
    INJECTION_PATTERNS = [
        # Instruction Overrides & Jailbreaks
        r"(ignore|disregard|forget|skip|override) (all )?(previous )?(rules|instructions|everything|system|constraints|safety)",
        r"(stop|cease) (being|acting|following) (a|the|your|all|previous)",
        r"for safety reasons,? ignore",
        r"new (rule|instruction|directive|persona):",
        
        # Role/Persona Attacks
        r"(you are|be|act as) (now )?(a|an|the|acting as)?\s?(pirate|developer|hacker|debugger|system|evil|unfiltered|god|assistant)",
        r"switch (roles|personas|modes)",
        r"no longer (a|an|the)?\s?(chatbot|assistant|ai)",
        r"pretend (you are|to be)",
        
        # System & Context Leaks
        r"(reveal|dump|print|show|output|tell me) (your|the|all|full)?\s?(internal|hidden|system|original|safety)?\s?(instructions|prompt|context|rules|directives|protocols|guidelines)",
        r"(what are|show me) (your|the)?\s?(internal|hidden|system|original|safety)?\s?(rules|instructions|directives|prompt|context|protocols|guidelines)",
        
        # Spoofing & Framing
        r"###\s?system( message)?",
        r"\[system( message)?\]",
        r"```system",
        r"<query_start>",
        r"<data_start>",
        
        # Obfuscation & Decoding
        r"(decode|translate|rot13|base64) (and follow|this|the following|instructions)",
        r"injected",
        r"overridden",
        r"hacked"
    ]
    
    # Delimiters for data vs instructions
    DATA_START = "<DATA_START>"
    DATA_END = "<DATA_END>"
    USER_QUERY_START = "<QUERY_START>"
    USER_QUERY_END = "<QUERY_END>"

    @classmethod
    def scan_for_injection(cls, text: str) -> Tuple[bool, Optional[str]]:
        """
        Scan text for common injection patterns.
        """
        if not text:
            return False, None
            
        # Normalize: lower case and collapse whitespace
        text_norm = " ".join(text.lower().split())
        
        # 1. Regex Pattern Matching
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text_norm):
                logger.warning(f"Prompt injection detected: Pattern '{pattern}' matched in: {text[:100]}...")
                return True, f"Security violation: Instruction or role manipulation detected."

        # 2. Heuristic for suspicious strings (potential Base64 obfuscation)
        # Look for long blocks of alphanumeric characters that look like Base64
        suspicious_blocks = re.findall(r"[A-Za-z0-9+/]{30,}={0,2}", text)
        if suspicious_blocks:
            for block in suspicious_blocks:
                try:
                    decoded = base64.b64decode(block).decode('utf-8', errors='ignore').lower()
                    if any(p in decoded for p in ["ignore", "instructions", "rules", "system", "prompt"]):
                        logger.warning(f"Obfuscated prompt injection detected in Base64 block.")
                        return True, "Obfuscated instruction override attempt detected."
                except:
                    continue

        return False, None

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """Sanitize user input before sending to LLM"""
        # Remove any attempts to use our internal delimiters
        sanitized = text.replace(cls.DATA_START, "").replace(cls.DATA_END, "")
        sanitized = sanitized.replace(cls.USER_QUERY_START, "").replace(cls.USER_QUERY_END, "")
        return sanitized

    @classmethod
    def wrap_data_context(cls, context: str) -> str:
        """Wrap untrusted data context with structural delimiters"""
        return f"{cls.DATA_START}\n{context}\n{cls.DATA_END}"

    @classmethod
    def wrap_user_query(cls, query: str) -> str:
        """Wrap user query with structural delimiters"""
        return f"{cls.USER_QUERY_START}\n{query}\n{cls.USER_QUERY_END}"
