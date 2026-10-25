"""
Built-in Pure Python SVG Captcha Engine.
Zero external cloud or binary dependencies. Generates dynamic mathematical and alphanumeric
challenges rendered into tamper-evident, randomized vector SVG graphics.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import hmac
import random
import secrets
from typing import Dict, Optional, Tuple
from libs.blockchain_contracts.auth_models import CaptchaChallenge


class CaptchaEngine:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)
        self._challenges: Dict[str, CaptchaChallenge] = {}

    def _hash_answer(self, answer: str) -> str:
        clean = answer.strip().lower()
        return hmac.new(self.secret_key.encode(), clean.encode(), hashlib.sha256).hexdigest()

    def generate_challenge(self) -> Tuple[str, str]:
        """
        Generates a challenge. Returns (challenge_id, svg_content).
        Rotates between mathematical arithmetic and alphanumeric string recognition.
        """
        challenge_id = secrets.token_hex(16)
        mode = random.choice(["math", "alpha"])

        if mode == "math":
            op = random.choice(["+", "-", "*"])
            if op == "+":
                a = random.randint(5, 45)
                b = random.randint(3, 35)
                answer = str(a + b)
                display_text = f"{a} + {b} = ?"
            elif op == "-":
                a = random.randint(20, 60)
                b = random.randint(3, 19)
                answer = str(a - b)
                display_text = f"{a} - {b} = ?"
            else:
                a = random.randint(3, 9)
                b = random.randint(3, 8)
                answer = str(a * b)
                display_text = f"{a} × {b} = ?"
        else:
            chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
            answer = "".join(random.choice(chars) for _ in range(5))
            display_text = " ".join(list(answer))

        expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        self._challenges[challenge_id] = CaptchaChallenge(
            challenge_id=challenge_id,
            question_text=display_text,
            answer_hash=self._hash_answer(answer),
            expires_at_utc=expires,
        )

        svg = self._render_svg(display_text)
        return challenge_id, svg

    def verify_answer(self, challenge_id: str, user_answer: str) -> bool:
        """Verifies solution and invalidates challenge to prevent replay attacks."""
        challenge = self._challenges.pop(challenge_id, None)
        if not challenge:
            return False
        if challenge.is_expired:
            return False

        expected_hash = challenge.answer_hash
        user_hash = self._hash_answer(user_answer)
        return hmac.compare_digest(expected_hash, user_hash)

    def _render_svg(self, text: str) -> str:
        """Generates dynamic SVG with noise lines and randomized character transformations."""
        width = 240
        height = 70

        # Background noise lines
        noise_lines = ""
        colors = ["#38bdf8", "#a855f7", "#10b981", "#f59e0b"]
        for _ in range(7):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            stroke = random.choice(colors)
            noise_lines += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="1.5" stroke-opacity="0.4" />'

        # Text rendering with slight randomized rotation
        char_elements = ""
        x_offset = 25
        for char in text:
            rot = random.randint(-12, 12)
            y_pos = random.randint(42, 48)
            fill_color = random.choice(["#f9fafb", "#e0f2fe", "#ede9fe", "#fef3c7"])
            char_elements += f'<text x="{x_offset}" y="{y_pos}" font-family="monospace, sans-serif" font-weight="bold" font-size="26" fill="{fill_color}" transform="rotate({rot} {x_offset} {y_pos})">{char}</text>'
            x_offset += 18 if char != " " else 10

        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="background-color: #111827; border-radius: 6px; border: 1px solid #374151; user-select: none;">
          <defs>
            <filter id="noise">
              <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" result="noise" />
              <feDisplacementMap in="SourceGraphic" in2="noise" scale="3" xChannelSelector="R" yChannelSelector="G" />
            </filter>
          </defs>
          {noise_lines}
          <g filter="url(#noise)">
            {char_elements}
          </g>
        </svg>"""
