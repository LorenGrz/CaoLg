import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import caolg_lib as L  # noqa: E402


class TestCaolg(unittest.TestCase):
    def test_transcript_dir_encoding(self):
        d = L.transcript_dir("/tmp/claude-1000/-home-loren/x.y/repo-wt/smoke")
        self.assertEqual(d.name, "-tmp-claude-1000--home-loren-x-y-repo-wt-smoke")

    def test_last_usage_sums_context_tokens(self):
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            f.write(json.dumps({"message": {"model": "claude-opus-5-5", "usage": {
                "input_tokens": 1, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 10,
                "output_tokens": 999}}}) + "\n")
            f.write('{"type": "summary"}\n')
        self.assertEqual(L.last_usage(f.name), ("claude-opus-5-5", 111))

    def test_last_usage_missing_file(self):
        self.assertEqual(L.last_usage("/no/existe.jsonl"), (None, None))

    def test_load_colors_merges_theme_and_defaults(self):
        with tempfile.NamedTemporaryFile("w", suffix=".toml", delete=False) as f:
            f.write('accent = "#123456"\nmode = "dark"\n')
        c = L.load_colors(f.name)
        self.assertEqual(c["accent"], "#123456")
        self.assertEqual(c["green"], L.DEFAULT_COLORS["green"])
        self.assertNotIn("mode", c)

    def test_load_colors_without_file(self):
        self.assertEqual(L.load_colors("/no/existe.toml"), L.DEFAULT_COLORS)

    def test_build_bar(self):
        colors = L.DEFAULT_COLORS
        session = {"terminals": [
            {"id": "a", "provider": "claude_code", "agent_profile": "supervisor", "status": "idle"},
            {"id": "b", "provider": "antigravity_cli", "agent_profile": "gemini-dev",
             "description": "front", "status": "processing"},
        ]}
        usage = {"providers": [{"agent": "claude", "tokens": 25_880_496, "cost_usd": 13.65},
                               {"agent": "codex", "tokens": 0, "cost_usd": 0.0}]}
        bar = L.build_bar(session, 42, usage, colors)
        self.assertIn("front · agy●", bar)
        self.assertIn("Opus ctx 42%", bar)
        self.assertIn("claude 25.9M $13.65", bar)
        self.assertIn("codex 0", bar)
        self.assertNotIn("supervisor", bar)

    def test_build_bar_empty(self):
        bar = L.build_bar({"terminals": []}, None, None, L.DEFAULT_COLORS)
        self.assertIn("(sin workers)", bar)
        self.assertIn("Opus ctx n/d", bar)

    def test_status_icons(self):
        session = {"terminals": [
            {"id": "a", "provider": "claude_code"},
            {"id": "b", "provider": "codex", "description": "back", "status": "waiting_user_answer"},
            {"id": "c", "provider": "copilot_cli", "description": "rev", "status": "unknown"},
        ]}
        bar = L.build_bar(session, 5, None, L.DEFAULT_COLORS)
        self.assertIn("back · codex⚠", bar)
        self.assertIn("rev · copilot◌", bar)

    def test_ctx_color_relative_to_clear_threshold(self):
        c = L.DEFAULT_COLORS
        bar = lambda pct: L.build_bar({"terminals": []}, pct, None, c, clear_at=40)  # noqa: E731
        self.assertIn(f"#[fg={c['green']}]Opus ctx 10%", bar(10))
        self.assertIn(f"#[fg={c['yellow']}]Opus ctx 30%", bar(30))
        self.assertIn(f"#[fg={c['red']}]Opus ctx 40%", bar(40))

    def test_bar_marks_providers_without_login(self):
        usage = {"providers": [{"agent": "codex", "tokens": 0, "cost_usd": 0.0, "logged_in": False},
                               {"agent": "claude", "tokens": 10, "cost_usd": 0.0, "logged_in": True}]}
        bar = L.build_bar({"terminals": []}, None, usage, L.DEFAULT_COLORS)
        self.assertIn("codex#[nostrikethrough] sin login", bar)
        self.assertIn("claude 10", bar)

    def test_claude_costs_for_path_sums_by_model_only_for_that_cwd(self):
        cwd = "/home/loren/projects/web-wt/demo"
        enc = L.transcript_dir(cwd).name
        data = {"sessions": [
            {"projectPath": enc, "modelBreakdowns": [{"modelName": "claude-opus-5-5", "cost": 1.0},
                                                     {"modelName": "claude-sonnet-5-5", "cost": 0.25}]},
            {"projectPath": enc, "modelBreakdowns": [{"modelName": "claude-opus-5-5", "cost": 0.5}]},
            {"projectPath": "-otra-carpeta", "modelBreakdowns": [{"modelName": "claude-opus-5-5", "cost": 9}]},
        ]}
        self.assertEqual(L.claude_costs_for_path(data, cwd), {"opus": 1.5, "sonnet": 0.25})
        self.assertEqual(L.claude_costs_for_path(None, cwd), {})

    def test_cost_since(self):
        data = {"sessions": [{"lastActivity": "2026-11-05T18:00:00Z", "totalCost": 0.1},
                             {"lastActivity": "2026-11-05T10:00:00Z", "totalCost": 5},
                             {"lastActivity": "2026-11-05T19:00:00Z", "costUSD": 0.2}]}
        self.assertAlmostEqual(L.cost_since(data, "2026-11-05T17:00:00"), 0.3)

    def test_session_cost_text_marks_approx(self):
        txt = L.session_cost_text({"opus": (1.234, True), "agy": (0.06, False), "codex": (0.0, False)},
                                  L.DEFAULT_COLORS)
        self.assertIn("sesión $1.29", txt)
        self.assertIn("opus1.23 · agy≈0.06", txt)
        self.assertNotIn("codex", txt)

    def test_opus_context_ignores_transcripts_before_clear(self):
        import os
        import time
        with tempfile.TemporaryDirectory() as home:
            old_home = os.environ.get("HOME")
            os.environ["HOME"] = home
            try:
                L_home = L.transcript_dir("/x/y")  # usa Path.home() en cada llamada
                L_home.mkdir(parents=True)
                f = L_home / "a.jsonl"
                f.write_text(json.dumps({"message": {"model": "claude-opus-5-5", "usage": {"input_tokens": 500}}}))
                past = time.time() - 100
                os.utime(f, (past, past))
                self.assertEqual(L.opus_context_tokens("/x/y"), 500)
                self.assertEqual(L.opus_context_tokens("/x/y", since=time.time() - 10), 0)
            finally:
                if old_home is not None:
                    os.environ["HOME"] = old_home

    def test_pane_label(self):
        self.assertEqual(L.pane_label({"id": "a"}, "a"), "Opus · líder")
        self.assertEqual(L.pane_label({"id": "b", "provider": "codex", "agent_profile": "codex-dev"}, "a"),
                         "codex-dev · codex")


if __name__ == "__main__":
    unittest.main()
