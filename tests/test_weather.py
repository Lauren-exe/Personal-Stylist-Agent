import unittest
from types import SimpleNamespace

from weather import normalize_location_input, suggest_location_correction


class NormalizeLocationInputTests(unittest.TestCase):
    def test_preserves_clean_location(self):
        self.assertEqual(normalize_location_input("Sammamish, WA"), "Sammamish, WA")

    def test_corrects_common_typos(self):
        self.assertEqual(normalize_location_input("berkely, ca"), "Berkeley, CA")
        self.assertEqual(normalize_location_input("seatlle, wa"), "Seattle, WA")
        self.assertEqual(normalize_location_input("sammamish, wa"), "Sammamish, Washington")
        self.assertEqual(normalize_location_input("boise, id"), "Boise, Idaho")
        self.assertEqual(normalize_location_input("sealtte, wa"), "Seattle, WA")
        self.assertEqual(normalize_location_input("snafransico, ca"), "San Francisco, CA")
        self.assertEqual(normalize_location_input("sanfransisco, ca"), "San Francisco, CA")
        self.assertEqual(normalize_location_input("potland orgon"), "Portland Oregon")
        self.assertEqual(normalize_location_input("portland, oregon"), "Portland, Oregon")
        self.assertEqual(normalize_location_input("austin, texas"), "Austin, Texas")
        self.assertEqual(normalize_location_input("portland, or"), "Portland, Oregon")
        self.assertEqual(normalize_location_input("seattle, wa"), "Seattle, Washington")
        self.assertEqual(normalize_location_input("londn, uk"), "London, United Kingdom")
        self.assertEqual(normalize_location_input("parsi, france"), "Parsi, France")

    def test_returns_none_for_unhelpful_input(self):
        self.assertIsNone(normalize_location_input("????????"))

    def test_suggests_a_cleaner_location_with_ai_client(self):
        class StubClient:
            class _Chat:
                class _Completions:
                    def create(self, model, messages, temperature=0.0):
                        return SimpleNamespace(
                            choices=[SimpleNamespace(message=SimpleNamespace(content="Seattle, Washington"))]
                        )

                completions = _Completions()

            chat = _Chat()

        self.assertEqual(suggest_location_correction("seatlle wa", StubClient()), "Seattle, Washington")


if __name__ == "__main__":
    unittest.main()
