"""CLI smoke tests."""

from __future__ import annotations

import contextlib
import io
import unittest

from ataxia.cli import _interactive_welcome, main


class TestCLI(unittest.TestCase):
    def test_profiles_command(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["profiles"])
        self.assertEqual(code, 0)
        for key in ("healthy", "learned_helplessness", "perseveration", "sensory_neglect"):
            self.assertIn(key, buffer.getvalue())

    def test_demo_command_offline(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["demo", "--profile", "perseveration", "--seeds", "1"])
        self.assertEqual(code, 0)
        self.assertIn("Induction Report", buffer.getvalue())
        self.assertIn("Emulation, not diagnosis", buffer.getvalue())

    def test_tour_lists_all(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["tour", "--seeds", "1"])
        self.assertEqual(code, 0)
        self.assertIn("Tour", buffer.getvalue())

    def test_bare_invocation_without_tty_prints_hint(self) -> None:
        from unittest.mock import patch

        class _FakeStdin:
            def isatty(self) -> bool:
                return False

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), patch("sys.stdin", _FakeStdin()):
            code = main([])
        self.assertEqual(code, 0)
        self.assertIn("ataxia tour", buffer.getvalue())

    def test_interactive_menu_runs_profile(self) -> None:
        def fake_input(answer: str):
            return lambda _prompt: answer

        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = _interactive_welcome(input_fn=fake_input("1"))
        self.assertEqual(code, 0)
        self.assertIn("Induction Report", buffer.getvalue())

    def test_interactive_quit(self) -> None:
        def fake_input(answer: str):
            return lambda _prompt: answer

        self.assertEqual(_interactive_welcome(input_fn=fake_input("q")), 0)


if __name__ == "__main__":
    unittest.main()
