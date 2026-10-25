"""Regression guard: Galaxy is not C; ?: causes the 3-race startup error."""
from __future__ import annotations
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "Payload" / "APRogue.galaxy").read_text(encoding="utf-8")

def live_tokens(src: str) -> str:
    out = list(src)
    state = "code"
    i = 0
    while i < len(out):
        ch = src[i]
        nxt = src[i + 1] if i + 1 < len(src) else ""
        if state == "code":
            if ch == '"': state = "string"; out[i] = " "
            elif ch == "/" and nxt == "/": state = "line"; out[i] = out[i + 1] = " "; i += 1
            elif ch == "/" and nxt == "*": state = "block"; out[i] = out[i + 1] = " "; i += 1
        elif state == "string":
            if ch == "\\" and nxt: out[i] = out[i + 1] = " "; i += 1
            elif ch == '"': state = "code"; out[i] = " "
            elif ch != "\n": out[i] = " "
        elif state == "line":
            if ch == "\n": state = "code"
            else: out[i] = " "
        elif state == "block":
            if ch == "*" and nxt == "/": state = "code"; out[i] = out[i + 1] = " "; i += 1
            elif ch != "\n": out[i] = " "
        i += 1
    assert state not in ("string", "block"), "Unterminated Galaxy literal"
    return "".join(out)

class GalaxyCompileGuard(unittest.TestCase):
    def test_no_unsupported_ternary_operator(self):
        live = live_tokens(SOURCE)
        for line, value in enumerate(live.splitlines(), 1):
            self.assertNotIn("?", value, f"Galaxy ternary operator near line {line}")

    def test_dev1_dev2_bad_expression_is_rejected(self):
        broken = SOURCE.replace("if (initialTimer) {",
                                "if (initialTimer ? true : false) {", 1)
        self.assertNotEqual(SOURCE, broken)
        self.assertIn("?", live_tokens(broken))

    def test_fast_delivery_zero_cooldown_uses_if_else(self):
        start = SOURCE.index("void APRG_ClampMercenaryCooldownField(")
        end = SOURCE.index("\n}\n", start)
        body = SOURCE[start:end]
        self.assertIn("if (initialTimer) {", body)
        self.assertIn('field, player, "0");', body)
        self.assertIn('field, player, "1");', body)

if __name__ == "__main__":
    unittest.main()
