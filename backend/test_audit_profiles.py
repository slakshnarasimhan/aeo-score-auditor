import unittest

from scoring.audit_profiles import infer_audit_profile
from reporting.recommendation_generator import RecommendationGenerator


class AuditProfileTests(unittest.TestCase):
    def test_auto_detects_saas_app_from_software_schema_and_language(self):
        page_data = {
            "url": "https://www.maadhyamik.com/lexifyd",
            "title": "Lexifyd language learning app",
            "meta_description": "An app that makes language learning easier",
            "main_content": (
                "Lexifyd is an app for language learning with features, lessons, "
                "supported languages, iOS, Android, free trial, subscription pricing, "
                "privacy and support."
            ),
            "schema_types": ["SoftwareApplication"],
            "content_type": {"type": "transactional"},
        }

        profile = infer_audit_profile(page_data, "auto")

        self.assertEqual(profile["type"], "saas_app")
        self.assertEqual(profile["label"], "SaaS / App")
        self.assertIn("app_name", profile["extraction_goals"])
        self.assertIn("SoftwareApplication", profile["recommended_schema"])

    def test_manual_override_wins_over_detection(self):
        page_data = {
            "url": "https://example.com/product/widget",
            "title": "Widget product",
            "main_content": "Buy now. Add to cart. In stock. Shipping and returns.",
            "schema_types": ["Product"],
            "content_type": {"type": "transactional"},
        }

        profile = infer_audit_profile(page_data, "publisher")

        self.assertEqual(profile["type"], "publisher")
        self.assertEqual(profile["confidence"], "manual")
        self.assertIn("direct_answer", profile["extraction_goals"])

    def test_recommendations_skip_low_applicability_categories(self):
        result = {
            "audit_profile": {
                "type": "saas_app",
                "description": "Optimized for app identity and capability extraction.",
            },
            "breakdown": {
                "structured_data": {
                    "score": 2,
                    "max": 10,
                    "percentage": 20,
                    "applicability": "high",
                    "applicability_reason": "Schema exposes app identity.",
                },
                "citationability": {
                    "score": 1,
                    "max": 10,
                    "percentage": 10,
                    "applicability": "low",
                    "applicability_reason": "Dense citations are less relevant for app pages.",
                },
            },
        }

        recommendations = RecommendationGenerator().generate_extraction_recommendations(result)
        categories = [rec["category"] for rec in recommendations]

        self.assertIn("structured_data", categories)
        self.assertNotIn("citationability", categories)
        self.assertEqual(recommendations[0]["title"], "Improve app extraction")


if __name__ == "__main__":
    unittest.main()

