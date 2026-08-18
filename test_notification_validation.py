import unittest

from notification_validation import clean_notification_title, is_valid_notification_title, validated_create_client


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


if __name__ == "__main__":
    unittest.main()
