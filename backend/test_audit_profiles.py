import unittest

from scoring.audit_profiles import infer_audit_profile
from reporting.positioning_analyzer import PositioningAnalyzer
from reporting.prompt_gap_analyzer import PromptGapAnalyzer
from reporting.recommendation_generator import RecommendationGenerator
from reporting.site_context import load_site_context
from reporting.domain_intelligence import (
    merge_intelligence_into_site_context,
    prioritize_urls_with_intelligence,
)


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

    def test_positioning_defaults_to_global_without_supplemental_context(self):
        pages = [
            {
                "url": "https://www.satsure.co/contact",
                "prompt_evidence": {
                    "title": "SatSure - Satellite intelligence for enterprises",
                    "meta_description": "Decision intelligence for agriculture, infrastructure, and BFSI teams.",
                    "headings": ["Global satellite intelligence platform", "Our offices"],
                    "paragraphs": [
                        "SatSure works with banks, insurers, and governments across multiple markets.",
                        "Registered office: Chennai, India. Enterprise teams can contact us for partnerships.",
                    ],
                },
            }
        ]

        analysis = PositioningAnalyzer().analyze(
            pages,
            "https://www.satsure.co",
            {"type": "general"},
        )

        self.assertNotEqual(analysis["market_scope"], "local")
        self.assertEqual(analysis["market_scope"], "global")
        self.assertNotIn("chennai", analysis["locations"])
        self.assertNotIn("Chennai-focused", analysis["likely_wedge"])
        self.assertFalse(
            any("local buyers" in proof for proof in analysis["recommended_proof"])
        )

    def test_global_markets_are_not_labeled_as_local_relevance(self):
        analysis = PositioningAnalyzer().analyze(
            [],
            "https://satsure.co",
            {"type": "general"},
            {
                "market_scope": "global",
                "locations": ["India", "United States", "United Kingdom"],
                "offers": ["Earth observation analytics"],
            },
        )

        self.assertIn(
            "Markets served: India, United States, United Kingdom",
            analysis["usp_claims"],
        )
        self.assertFalse(
            any("Local relevance" in claim for claim in analysis["usp_claims"])
        )

    def test_positioning_uses_supplemental_context_for_local_scope(self):
        pages = [
            {
                "url": "https://betterhomeapp.example",
                "prompt_evidence": {
                    "title": "BetterHomeApp - Home appliances in Chennai",
                    "meta_description": "Affordable home appliances with delivery in Chennai.",
                    "headings": ["Wholesale prices for Chennai buyers"],
                    "paragraphs": [
                        "Buy ceiling fan and water heater products from a local dealer in Chennai.",
                        "We provide delivery in Chennai, warranty support, and installation.",
                    ],
                },
            }
        ]

        analysis = PositioningAnalyzer().analyze(
            pages,
            "https://betterhomeapp.example",
            {"type": "ecommerce"},
            {
                "market_scope": "local",
                "locations": ["chennai"],
                "products": ["home appliance"],
                "value_props": ["wholesale"],
            },
        )

        self.assertEqual(analysis["market_scope"], "local")
        self.assertIn("chennai", analysis["locations"])
        self.assertIn("Chennai-focused", analysis["likely_wedge"])

    def test_site_context_loads_from_domains_folder_and_maps_offers(self):
        context = load_site_context("https://betterhomeapp.com")
        analysis = PositioningAnalyzer().analyze(
            [],
            "https://betterhomeapp.com",
            {"type": "ecommerce"},
            context,
        )

        self.assertEqual(analysis["market_scope"], "local")
        self.assertIn("Chennai", analysis["locations"])
        self.assertIn("home appliances", analysis["products"])
        self.assertIn("/domains/site_context/betterhomeapp.com.json", analysis["context_source"])

    def test_ecommerce_prompt_generation_uses_offers_not_brand_as_product(self):
        context = load_site_context("https://betterhomeapp.com")
        pages = [
            {
                "url": "https://betterhomeapp.com",
                "prompt_evidence": {
                    "title": "BetterHome - Home appliances in Chennai",
                    "meta_description": "Buy home appliances, ceiling fans, and water heaters.",
                    "headings": ["Home appliances at wholesale prices"],
                    "paragraphs": ["BetterHome sells appliances with local warranty support."],
                },
            }
        ]
        positioning = PositioningAnalyzer().analyze(
            pages,
            "https://betterhomeapp.com",
            {"type": "ecommerce"},
            context,
        )

        analysis = PromptGapAnalyzer().analyze(
            pages,
            "https://betterhomeapp.com",
            {"type": "ecommerce"},
            positioning=positioning,
            site_context=context,
        )
        prompts = [item["prompt"] for item in analysis["prompts"]]

        self.assertNotIn("Which BetterHome offers the best value?", prompts)
        self.assertNotIn("What should I check before buying BetterHome?", prompts)
        self.assertNotIn("What is the price range for BetterHome?", prompts)
        self.assertIn("What should I know before buying home appliances?", prompts)
        self.assertIn("Which home appliances options offer the best value?", prompts)

    def test_global_space_tech_does_not_receive_appliance_local_prompts(self):
        context = {
            "brand": "SatSure",
            "entity_type": "company",
            "business_type": "Earth Observation data and analytics",
            "market_scope": "global",
            "locations": ["India", "United States"],
            "offers": [
                "Crop yield forecasting",
                "Claims validation",
                "Earth observation data licensing",
            ],
        }
        pages = [{
            "url": "https://satsure.co",
            "prompt_evidence": {
                "title": "Earth intelligence and geospatial analytics",
                "headings": ["Satellite intelligence for global enterprises"],
                "paragraphs": [
                    "SatSure offers direct access to Earth observation analytics and local risk insights."
                ],
            },
        }]
        positioning = PositioningAnalyzer().analyze(
            pages,
            "https://satsure.co",
            {"type": "ecommerce"},
            context,
        )

        analysis = PromptGapAnalyzer().analyze(
            pages,
            "https://satsure.co",
            {"type": "ecommerce"},
            positioning=positioning,
            site_context=context,
        )
        prompts = [item["prompt"].lower() for item in analysis["prompts"]]

        self.assertFalse(any("home appliance" in prompt for prompt in prompts))
        self.assertFalse(any("appliance seller" in prompt for prompt in prompts))
        self.assertFalse(
            any(item.get("market_scope") == "local" for item in analysis["prompts"])
        )

    def test_deep_strategy_is_not_padded_with_generic_templates(self):
        strategy = {
            "problem_aware_questions": [
                "How can satellite data reduce crop insurance loss ratios?",
                "What makes manual agricultural claim validation unreliable?",
                "How can utilities detect vegetation risk remotely?",
            ],
            "solution_aware_questions": [
                "How accurate are crop yield forecasting models?",
                "Can Earth observation data integrate with underwriting systems?",
                "How frequently is satellite risk data updated?",
            ],
            "comparison_questions": [
                "How do Earth observation providers compare on resolution?",
                "What differentiates geospatial risk platforms?",
                "Should we license satellite data or buy analytics?",
            ],
            "trust_questions": [
                "What customer outcomes prove the models work?",
                "How are model accuracy claims validated?",
                "Which compliance standards does the platform support?",
            ],
        }
        analysis = PromptGapAnalyzer().analyze(
            [],
            "https://satsure.co",
            {"type": "ecommerce"},
            site_context={
                "brand": "SatSure",
                "offers": ["Earth observation analytics"],
                "question_strategy": strategy,
            },
        )

        self.assertEqual(len(analysis["prompts"]), 12)
        self.assertTrue(
            all(item.get("source") == "question_strategy" for item in analysis["prompts"])
        )

    def test_question_journey_orders_unbranded_demand_before_brand_and_implementation(self):
        strategy = {
            "problem_recognition_questions": [
                "How can I monitor crop health across thousands of farms?"
            ],
            "solution_discovery_questions": [
                "Which satellite analytics platforms support crop monitoring?"
            ],
            "use_case_fit_questions": [
                "Can satellite data validate agricultural damage claims?"
            ],
            "provider_comparison_questions": [
                "Should I buy imagery or use an integrated analytics platform?"
            ],
            "branded_validation_questions": [
                "How accurate are SatSure crop yield models?"
            ],
            "implementation_questions": [
                "How long does SatSure integration take?"
            ],
        }
        pages = [{
            "url": "https://satsure.co",
            "prompt_evidence": {
                "title": "Satellite crop monitoring and Earth observation analytics",
                "headings": ["Crop health monitoring", "Agricultural claims validation"],
                "paragraphs": [
                    "SatSure provides satellite analytics for crop monitoring and agricultural risk."
                ],
            },
        }]

        analysis = PromptGapAnalyzer().analyze(
            pages,
            "https://satsure.co",
            {"type": "general"},
            site_context={
                "brand": "SatSure",
                "offers": ["Earth observation analytics"],
                "question_strategy": strategy,
            },
        )

        self.assertEqual(
            [item["journey_stage"] for item in analysis["prompts"]],
            [
                "problem_recognition",
                "solution_discovery",
                "use_case_fit",
                "provider_comparison",
                "branded_validation",
                "implementation",
            ],
        )
        self.assertEqual(analysis["prompts"][0]["audience_scope"], "unbranded")
        self.assertEqual(analysis["prompts"][-1]["audience_scope"], "branded")
        self.assertIn("eligibility_score", analysis["prompts"][0])
        self.assertIn("answer_completeness_score", analysis["prompts"][0])
        self.assertIn("eligibility_score", analysis["summary"])

    def test_question_strategy_prompts_are_used_before_generated_templates(self):
        intelligence = {
            "brand_guess": "Aprisio",
            "business": {
                "entity_type": "coaching_community",
                "category": "midlife coaching/community",
                "core_offers": ["midlife coaching community"],
                "primary_audience": ["women in midlife"],
                "market_scope": "global",
            },
            "question_strategy": {
                "problem_aware_questions": [
                    "How do I know if I am going through a midlife transition?",
                    "What helps when career and identity feel misaligned in midlife?",
                ],
                "solution_aware_questions": [
                    "What does a midlife coaching community include?"
                ],
                "comparison_questions": [
                    "How is midlife coaching different from therapy?",
                    "Aprisio vs private coaching: what is different?",
                ],
                "trust_questions": [
                    "Who runs Aprisio?"
                ],
                "conversion_questions": [
                    "How do I join Aprisio?"
                ],
                "questions_to_avoid": ["marketing slogans as questions"],
            },
        }
        context = merge_intelligence_into_site_context({}, intelligence)
        analysis = PromptGapAnalyzer().analyze(
            [],
            "https://aprisio.com",
            {"type": "general"},
            max_prompts=5,
            site_context=context,
        )

        prompts = analysis["prompts"]
        self.assertEqual(
            prompts[0]["prompt"],
            "How do I know if I am going through a midlife transition?",
        )
        self.assertEqual(prompts[0]["source"], "question_strategy")
        self.assertIn("How is midlife coaching different from therapy?", [p["prompt"] for p in prompts])

    def test_content_derived_prompt_filter_rejects_cta_and_chart_fragments(self):
        pages = [{
            "url": "https://moative.com/guild",
            "prompt_evidence": {
                "title": "Moative Guild - AI operating partner",
                "meta_description": "Co-own AI products with operators in insurance and healthcare workflows.",
                "headings": [
                    "Where this sits in the $84B pool",
                    "Sound like your industry?",
                    "Which vehicle fits?",
                    "How can bordereaux analytics improve MGA portfolio pricing?",
                ],
                "questions": [
                    {"question": "When do I get paid?", "answer": "Quarterly distributions."},
                    {
                        "question": "Become a founding Guild member Ask for the Charter Frequently asked questions Do I need any technical skills?",
                        "answer": "No.",
                    },
                    {
                        "question": "What portfolio optimization opportunities does bordereaux analytics reveal?",
                        "answer": "It surfaces class-level margins and geographic performance trends.",
                    },
                ],
                "paragraphs": [
                    "Moative builds AI operating partnerships for insurance, healthcare, legal, and energy workflows."
                ],
            },
        }]

        analysis = PromptGapAnalyzer().analyze(
            pages,
            "https://moative.com",
            {"type": "general"},
            max_prompts=12,
            site_context={
                "brand": "Moative",
                "offers": ["AI operating partner", "bordereaux analytics"],
                "business_type": "equity-based AI joint ventures",
            },
        )
        prompts = [item["prompt"] for item in analysis["prompts"]]

        self.assertNotIn("Where this sits in the $84B pool?", prompts)
        self.assertNotIn("Sound like your industry?", prompts)
        self.assertNotIn("Which vehicle fits?", prompts)
        self.assertNotIn("When do I get paid?", prompts)
        self.assertFalse(any("Become a founding Guild member" in prompt for prompt in prompts))
        self.assertIn(
            "What portfolio optimization opportunities does bordereaux analytics reveal?",
            prompts,
        )
        relevant = next(
            item for item in analysis["prompts"]
            if item["prompt"] == "What portfolio optimization opportunities does bordereaux analytics reveal?"
        )
        self.assertEqual(relevant["source"], "content_question")

    def test_geo_eligibility_questions_use_section_evidence_across_pages(self):
        prompt = "Does Climate Collective support founders outside of India, and which countries are eligible?"
        pages = [
            {
                "url": "https://climatecollective.net/about/",
                "prompt_evidence": {
                    "title": "About-Us - ClimateCollective",
                    "headings": [
                        "Today Climate Collective is a dynamic team of 50+ driven individuals, who daily build platforms that support climate tech entrepreneurs in the early perilous stages of the startup journey."
                    ],
                    "paragraphs": [
                        "The program grows to 4 more states and Sri Lanka in 2018.",
                        "Climate Collective builds follow-on accelerators and pre-accelerators and boards over 470+ cleantech startups of India and South Asia.",
                    ],
                },
            },
            {
                "url": "https://climatecollective.net/sup-challenge/",
                "prompt_evidence": {
                    "title": "SUP Challenge - ClimateCollective",
                    "headings": [
                        "Eligibility",
                        "Startups who are based and operating in India",
                        "Startups who can pilot their solutions in Goa",
                    ],
                    "paragraphs": [
                        "The Single-Use Plastic Challenge is an international acceleration program.",
                        "Eight Entrepreneur Support Organizations were selected to run The SUP Challenges with F&B partners in five countries, i.e. India, Philippines, Thailand, Vietnam, and Indonesia. Climate Collective Foundation is implementing partner in Goa, India.",
                    ],
                },
            },
            {
                "url": "https://climatecollective.net/act4green-ii/",
                "prompt_evidence": {
                    "title": "Act4Green II",
                    "paragraphs": [
                        "The program will support 12 promising AI or Big Data focused startups from India and UK working on climate tech solutions.",
                        "Climate Collective Foundation and partners strengthen the Indian and UK climate tech start-up ecosystems.",
                    ],
                },
            },
            {
                "url": "https://climatecollective.net/impactmetrics/case-studies/",
                "prompt_evidence": {
                    "title": "Case Studies - ClimateCollective",
                    "paragraphs": [
                        "New Energy Nexus is a network of accelerators and funds supporting clean energy entrepreneurship. They have supported startups in Philippines, Indonesia, Vietnam, California, and India.",
                    ],
                },
            },
        ]

        analysis = PromptGapAnalyzer().analyze(
            pages,
            "https://climatecollective.net",
            {"type": "general"},
            max_prompts=1,
            site_context={
                "brand": "Climate Collective",
                "question_strategy": {
                    "branded_validation_questions": [prompt],
                },
            },
        )

        result = analysis["prompts"][0]
        evidence_urls = [item["url"] for item in result["evidence"]]

        self.assertEqual(result["coverage"], "partial")
        self.assertIn("https://climatecollective.net/sup-challenge/", evidence_urls)
        self.assertIn("https://climatecollective.net/about/", evidence_urls)
        self.assertIn("https://climatecollective.net/act4green-ii/", evidence_urls)
        self.assertNotIn("https://climatecollective.net/impactmetrics/case-studies/", evidence_urls)

    def test_sparse_domain_intelligence_does_not_inject_generic_questions(self):
        intelligence = {
            "brand_guess": "Saavigen",
            "confidence": "low",
            "business": {
                "entity_type": "unknown",
                "category": "unknown",
                "core_offers": [],
                "primary_audience": [],
                "market_scope": "unknown",
            },
            "question_strategy": {
                "problem_aware_questions": [],
                "solution_aware_questions": [],
                "comparison_questions": [],
                "trust_questions": [
                    "What is Saavigen?",
                    "Who is Saavigen for?",
                    "Is Saavigen trustworthy?",
                ],
                "conversion_questions": ["How do I get started with Saavigen?"],
                "support_or_post_purchase_questions": [],
                "questions_to_avoid": ["marketing slogans as questions"],
            },
        }

        context = merge_intelligence_into_site_context({}, intelligence)

        self.assertNotIn("question_strategy", context)
        self.assertNotEqual(context.get("business_type"), "unknown")
        self.assertNotEqual(context.get("market_scope"), "unknown")

    def test_domain_intelligence_prioritizes_high_value_urls(self):
        intelligence = {
            "website_structure_hypothesis": {
                "likely_important_sections": [
                    {
                        "crawler_priority": "high",
                        "url_patterns_to_look_for": ["/services", "/about"],
                    }
                ],
                "crawl_strategy": {
                    "start_pages": ["/"],
                    "must_include_patterns": ["/services", "/pricing"],
                    "avoid_patterns": ["/privacy"],
                },
            }
        }
        urls = [
            "https://example.com/privacy",
            "https://example.com/blog/post",
            "https://example.com/services",
            "https://example.com/",
            "https://example.com/pricing",
        ]

        ordered = prioritize_urls_with_intelligence(urls, intelligence, max_pages=3)

        self.assertEqual(ordered[0], "https://example.com/")
        self.assertIn("https://example.com/services", ordered)
        self.assertNotIn("https://example.com/privacy", ordered)


if __name__ == "__main__":
    unittest.main()
