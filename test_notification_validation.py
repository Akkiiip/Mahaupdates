import unittest
from types import SimpleNamespace

from notification_validation import clean_notification_title, is_valid_notification_title, validated_create_client
import app


class NotificationValidationTests(unittest.TestCase):
    def test_normalizes_spacing_and_unicode(self):
        self.assertEqual(clean_notification_title("  Skip\u00a0to\nmain content  "), "Skip to main content")

    def test_rejects_known_junk(self):
        for title in ("Download", "View", "Skip to main content", "What are you looking for?", "  PDF "):
            with self.subTest(title=title):
                self.assertFalse(is_valid_notification_title(title))

    def test_accepts_legitimate_notifications(self):
        for title in (
            "Recruitment Advertisement for Junior Engineer 2026",
            "Result of the departmental examination",
            "Government Circular regarding revised service rules",
        ):
            with self.subTest(title=title):
                self.assertTrue(is_valid_notification_title(title))

    def test_client_gate_skips_invalid_insert_and_allows_valid_insert(self):
        class Table:
            def __init__(self): self.inserted = []
            def insert(self, payload): self.inserted.append(payload); return self
            def execute(self): return self
        table = Table()
        class Client:
            def table(self, name): return table
        client = validated_create_client(lambda *_: Client())("url", "key")
        client.table("updates").insert({"title": "Download"}).execute()
        client.table("updates").insert({"title": " Recruitment  Notice "}).execute()
        self.assertEqual(table.inserted, [{"title": "Recruitment Notice"}])

    def test_valid_rows_are_filtered_before_pagination(self):
        rows = [{"source": "Bad", "type": "Other", "title": "Download", "first_seen": "999"} for _ in range(6)]
        rows += [{"source": "MPSC", "type": "Result", "title": f"Valid result {i}", "first_seen": f"{100 - i:03d}"} for i in range(14)]

        class Query:
            def select(self, *_args, **_kwargs): return self
            def eq(self, *_args, **_kwargs): return self
            def order(self, *_args, **_kwargs): return self
            def range(self, *_args, **_kwargs): return self
            def execute(self): return SimpleNamespace(data=rows)
        class Client:
            def table(self, _name): return Query()

        original = app.get_supabase
        try:
            app.get_supabase = lambda: Client()
            page_one, total = app.get_filtered_updates_from_db(page=1, per_page=12)
            page_two, _ = app.get_filtered_updates_from_db(page=2, per_page=12)
            app._FILTER_CACHE["expires"] = 0
            sources, types = app.get_filter_options()
        finally:
            app.get_supabase = original

        self.assertEqual((len(page_one), len(page_two), total), (12, 2, 14))
        self.assertEqual((sources, types), (["MPSC"], ["Result"]))


if __name__ == "__main__":
    unittest.main()
