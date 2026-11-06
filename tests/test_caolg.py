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

    def test_bar_marks_providers_without_login(self):
        usage = {"providers": [{"agent": "codex", "tokens": 0, "cost_usd": 0.0, "logged_in": False},
                               {"agent": "claude", "tokens": 10, "cost_usd": 0.0, "logged_in": True}]}
        bar = L.build_bar(usage, L.DEFAULT_COLORS)
        self.assertIn("codex#[nostrikethrough] sin login", bar)
        self.assertIn("claude 10", bar)

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

    def test_build_bar_only_today_usage(self):
        usage = {"providers": [{"agent": "claude", "tokens": 25_880_496, "cost_usd": 13.65},
                               {"agent": "antigravity", "tokens": 76_700, "cost_usd": 0.0}]}
        bar = L.build_bar(usage, L.DEFAULT_COLORS)
        self.assertIn("hoy: claude 25.9M $13.65 · agy 76.7k", bar)
        for gone in ("agentes", "ctx", "sesión"):
            self.assertNotIn(gone, bar)
        self.assertIn("usage n/d", L.build_bar(None, L.DEFAULT_COLORS))

    def test_display_model(self):
        self.assertEqual(L.display_model({"model": "opus", "provider": "claude_code"}), "Opus 5.5")
        self.assertEqual(L.display_model({"model": "claude-sonnet-5-5"}), "Sonnet 5.5")
        self.assertEqual(L.display_model({"model": None, "provider": "codex"}), "codex")

    def test_pane_label(self):
        self.assertEqual(L.pane_label({"id": "a", "model": "opus"}, "a"), "Opus 5.5 · líder")
        self.assertEqual(L.pane_label({"id": "b", "provider": "claude_code", "model": "sonnet",
                                       "description": "front"}, "a"), "Sonnet 5.5 · front")
        self.assertEqual(L.pane_label({"id": "c", "provider": "codex", "agent_profile": "codex-dev"}, "a"),
                         "codex · codex-dev")

    def test_pane_label_role_override(self):
        term = {"id": "b", "provider": "codex", "description": "front"}
        self.assertEqual(L.pane_label(term, "a", "reviewer"), "codex · reviewer")
        self.assertEqual(L.pane_label(term, "a", None), "codex · front")

    def test_tab_keys(self):
        self.assertEqual([L.tab_key(i) for i in range(10)], ["2", "3", "4", "5", "6", "7", "8", "9", "0", ""])
        self.assertEqual([L.key_to_pos(k) for k in "1234567890"], [None, 0, 1, 2, 3, 4, 5, 6, 7, 8])

    def test_assign_tabs_appends_new_ones(self):
        tabs = [{"id": "%1", "tab": 3}, {"id": "%2", "tab": None}, {"id": "%3", "tab": None}]
        self.assertEqual(L.assign_tabs(tabs), {"%2": 4, "%3": 5})
        self.assertEqual(L.assign_tabs([{"id": "%9", "tab": None}]), {"%9": 1})

    def test_pick_visible_prefers_newest(self):
        self.assertIsNone(L.pick_visible([]))
        c = [{"id": "%1", "tab": 1}, {"id": "%2", "tab": 2}]
        self.assertEqual(L.pick_visible(c), "%2")  # worker nuevo de Opus: aparece aunque mirabas otra

    def test_owner_marks_window_mark_belongs_to_leader_only(self):
        # Opus (%10) tiene la marca de ventana; %12 es una terminal suelta en la misma ventana: no hereda.
        rows = [{"id": "%12", "win": "@1", "own": "", "inherited": "sup"},
                {"id": "%10", "win": "@1", "own": "", "inherited": "sup"},
                {"id": "%13", "win": "@1", "own": "w1", "inherited": "sup"},
                {"id": "%20", "win": "@2", "own": "", "inherited": "w2"},
                {"id": "%21", "win": "@3", "own": "", "inherited": ""}]
        self.assertEqual(L.owner_marks(rows, "%10"), {"%10": "sup", "%13": "w1", "%20": "w2"})

    def test_owner_marks_without_leader_uses_first_pane(self):
        rows = [{"id": "%1", "win": "@1", "own": "", "inherited": "sup"},
                {"id": "%2", "win": "@1", "own": "", "inherited": "sup"}]
        self.assertEqual(L.owner_marks(rows), {"%1": "sup"})

    def test_tab_colors_rotate_and_follow_theme(self):
        keys = [L.tab_color_key(n) for n in range(1, 9)]
        self.assertEqual(len(set(keys[:7])), 7)  # 7 tabs seguidas, 7 colores distintos
        self.assertEqual(keys[7], keys[0])
        self.assertNotIn("accent", keys)  # reservado para Opus
        colors = dict(L.DEFAULT_COLORS)
        self.assertEqual(L.tab_color("green", colors), colors["green"])
        self.assertEqual(L.tab_color("#123456", colors), "#123456")
        self.assertEqual(L.tab_color("", colors), colors["muted"])

    def test_tab_strip_highlights_visible(self):
        tabs = [{"id": "%1", "label": "front · agy", "color": "#00f"}, {"id": "%2", "label": "zsh", "color": None}]
        s = L.tab_strip(tabs, "%2", L.DEFAULT_COLORS)
        self.assertIn("#[fg=#00f] 2 front · agy ", s)
        self.assertIn(f"bg={L.DEFAULT_COLORS['muted']},bold] 3 zsh ", s)


if __name__ == "__main__":
    unittest.main()
