"""
Prompt gap analysis for local answerability simulation.

Given crawled site content, this module generates realistic buyer prompts and
checks whether the local page evidence can answer them.
"""
import re
from typing import Any, Dict, List, Sequence, Tuple
from urllib.parse import urlparse


STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "best", "by", "can", "do",
    "does", "for", "from", "how", "i", "in", "is", "it", "me", "my", "of",
    "on", "or", "should", "that", "the", "this", "to", "use", "what",
    "when", "where", "which", "who", "why", "with", "would",
}

JOURNEY_STAGES = [
    "problem_recognition",
    "solution_discovery",
    "use_case_fit",
    "provider_comparison",
    "branded_validation",
    "implementation",
]

JOURNEY_STAGE_LABELS = {
    "problem_recognition": "Problem Recognition",
    "solution_discovery": "Solution Discovery",
    "use_case_fit": "Use-Case Fit",
    "provider_comparison": "Provider Comparison",
    "branded_validation": "Branded Validation",
    "implementation": "Implementation & Procurement",
}

JOURNEY_WEIGHTS = {
    "problem_recognition": 1.0,
    "solution_discovery": 1.0,
    "use_case_fit": 0.9,
    "provider_comparison": 0.8,
    "branded_validation": 0.6,
    "implementation": 0.4,
}


PROFILE_PROMPTS: Dict[str, Dict[str, List[str]]] = {
    "ecommerce": {
        "discovery": [
            "What should I know before buying {topic}?",
            "Which {topic} options are best for my home?",
            "What should I look for before buying {topic}?",
        ],
        "comparison": [
            "How do different {topic} options compare?",
            "Which {topic} options offer the best value?",
        ],
        "feature": [
            "What product details, pricing, and availability should I check for {topic}?",
            "Can I find reviews or proof before choosing {topic}?",
        ],
        "trust": [
            "Which {topic} brands or sellers are reliable?",
            "What warranty or support should I expect for {topic}?",
        ],
        "transactional": [
            "Where can I buy {topic} online?",
            "What is the price range for {topic}?",
        ],
    },
    "saas_app": {
        "discovery": [
            "What is the best app for {topic}?",
            "What software helps with {topic}?",
            "What tools should I use to manage {topic}?",
        ],
        "comparison": [
            "How does {brand} compare with other {topic} tools?",
            "What are alternatives to {brand}?",
        ],
        "feature": [
            "What features does {brand} offer?",
            "Can {brand} help users manage {topic}?",
            "Does {brand} support reminders, tracking, or reporting?",
        ],
        "trust": [
            "Is {brand} reliable?",
            "Who is {brand} built for?",
            "Does {brand} show customer proof or case studies?",
        ],
        "transactional": [
            "How much does {brand} cost?",
            "Where can I sign up for {brand}?",
        ],
    },
    "publisher": {
        "discovery": [
            "What should I know about {topic}?",
            "Where can I find a clear guide to {topic}?",
        ],
        "feature": [
            "Does {brand} answer common questions about {topic}?",
            "Does {brand} provide examples, data, or expert guidance?",
        ],
        "trust": [
            "Is {brand} a trustworthy source on {topic}?",
            "Who writes or reviews content on {brand}?",
        ],
    },
    "local_business": {
        "discovery": [
            "Who provides {topic} near me?",
            "What is the best local option for {topic}?",
        ],
        "feature": [
            "What services does {brand} provide?",
            "Does {brand} explain service areas, pricing, and availability?",
        ],
        "trust": [
            "Is {brand} a reliable local business?",
            "Does {brand} show reviews, credentials, or proof?",
        ],
        "transactional": [
            "How do I contact {brand}?",
            "How do I book or request a quote from {brand}?",
        ],
    },
    "documentation": {
        "discovery": [
            "How do I get started with {topic}?",
            "Where can I find documentation for {topic}?",
        ],
        "feature": [
            "Does {brand} explain how to configure {topic}?",
            "Does {brand} provide examples and troubleshooting steps?",
        ],
        "trust": [
            "Is {brand} documentation complete and current?",
        ],
    },
    "general": {
        "discovery": [
            "What is {brand}?",
            "What does {brand} help people do?",
            "What is the best solution for {topic}?",
        ],
        "comparison": [
            "How does {brand} compare with similar options?",
            "What are alternatives to {brand}?",
        ],
        "feature": [
            "What features or services does {brand} offer?",
            "Can {brand} help with {topic}?",
        ],
        "trust": [
            "Is {brand} trustworthy?",
            "Who is {brand} for?",
        ],
        "transactional": [
            "How do I get started with {brand}?",
            "How much does {brand} cost?",
        ],
    },
}


class PromptGapAnalyzer:
    """Generate prompts and test local site evidence for answerability."""

    def analyze(
        self,
        pages: Sequence[Dict[str, Any]],
        site_url: str,
        profile: Dict[str, Any] | None = None,
        max_prompts: int = 24,
        use_llm: bool = False,
        positioning: Dict[str, Any] | None = None,
        site_context: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        site_context = site_context or {}
        brand = str(site_context.get("brand") or self._brand_name(site_url))
        topic = self._prompt_topic(pages, brand, site_context, positioning or {})
        profile_type = (profile or {}).get("type") or "general"
        prompt_defs = self._generate_prompts(
            brand,
            topic,
            profile_type,
            max_prompts,
            pages,
            positioning,
            site_context,
        )
        chunks = self._build_chunks(pages)

        results = [self._score_prompt(prompt, chunks, brand) for prompt in prompt_defs]
        llm_evaluation = {
            "enabled": False,
            "provider": "openai",
            "reason": "LLM evaluation was not requested",
        }

        if use_llm:
            from reporting.llm_prompt_evaluator import LLMPromptEvaluator

            llm_evaluation = LLMPromptEvaluator(
                model=site_context.get("_answerability_model")
            ).evaluate_results(results)
            results = llm_evaluation.get("results", results)

        for result in results:
            result["answer_completeness_score"] = result.get(
                "answerability_score",
                result.get("answer_completeness_score", 0),
            )
            result["opportunity_score"] = self._opportunity_score(
                result.get("journey_stage", "solution_discovery"),
                result.get("eligibility_score", 0),
                result["answer_completeness_score"],
            )
        results = self._rank_results(results)
        summary = self._summarize(results)

        return {
            "brand": brand,
            "topic": topic,
            "profile": profile_type,
            "evaluation_mode": "llm" if llm_evaluation.get("enabled") else "deterministic",
            "llm_evaluation": {k: v for k, v in llm_evaluation.items() if k != "results"},
            "summary": summary,
            "prompts": results,
        }

    def _generate_prompts(
        self,
        brand: str,
        topic: str,
        profile_type: str,
        max_prompts: int,
        pages: Sequence[Dict[str, Any]] | None = None,
        positioning: Dict[str, Any] | None = None,
        site_context: Dict[str, Any] | None = None,
    ) -> List[Dict[str, str]]:
        site_context = site_context or {}
        templates = PROFILE_PROMPTS.get(profile_type) or PROFILE_PROMPTS["general"]
        prompts: List[Dict[str, str]] = []
        strategy_prompts = self._strategy_prompts(site_context)
        strategy = site_context.get("question_strategy")
        has_journey_strategy = isinstance(strategy, dict) and any(
            strategy.get(key)
            for key in [
                "problem_recognition_questions",
                "solution_discovery_questions",
                "use_case_fit_questions",
                "provider_comparison_questions",
                "branded_validation_questions",
                "implementation_questions",
            ]
        )
        if has_journey_strategy or len(strategy_prompts) >= 12:
            return self._filter_context_prompts(
                self._deduplicate_prompts(strategy_prompts),
                brand,
                site_context,
            )[:max_prompts]

        prompts.extend(strategy_prompts)
        prompts.extend(
            self._positioning_prompts(positioning or {}, topic, profile_type)
        )
        prompts.extend(self._content_derived_prompts(pages or [], brand, profile_type))

        for intent, questions in templates.items():
            for question in questions:
                prompts.append({
                    "prompt": question.format(brand=brand, topic=topic),
                    "intent": intent,
                })

        if profile_type != "general":
            for intent, questions in PROFILE_PROMPTS["general"].items():
                for question in questions[:1]:
                    if self._skip_general_brand_template(profile_type, question):
                        continue
                    prompts.append({
                        "prompt": question.format(brand=brand, topic=topic),
                        "intent": intent,
                    })

        unique = self._deduplicate_prompts(prompts)
        return self._filter_context_prompts(unique, brand, site_context)[:max_prompts]

    def _deduplicate_prompts(
        self,
        prompts: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        seen = set()
        unique = []
        for item in prompts:
            key = item["prompt"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    def _strategy_prompts(self, site_context: Dict[str, Any]) -> List[Dict[str, str]]:
        strategy = site_context.get("question_strategy")
        if not isinstance(strategy, dict):
            return []

        stage_map = {
            "problem_recognition_questions": ("problem_recognition", "discovery"),
            "solution_discovery_questions": ("solution_discovery", "discovery"),
            "use_case_fit_questions": ("use_case_fit", "feature"),
            "provider_comparison_questions": ("provider_comparison", "comparison"),
            "branded_validation_questions": ("branded_validation", "trust"),
            "implementation_questions": ("implementation", "transactional"),
        }
        legacy_map = {
            "problem_aware_questions": ("problem_recognition", "discovery"),
            "solution_aware_questions": ("solution_discovery", "feature"),
            "comparison_questions": ("provider_comparison", "comparison"),
            "trust_questions": ("branded_validation", "trust"),
            "conversion_questions": ("implementation", "transactional"),
            "support_or_post_purchase_questions": ("implementation", "support"),
        }
        active_map = stage_map if any(strategy.get(key) for key in stage_map) else legacy_map
        prompts: List[Dict[str, str]] = []
        for key, (stage, intent) in active_map.items():
            questions = self._strategy_question_list(strategy.get(key))
            for rank, question in enumerate(questions):
                normalized = self._normalize_question(question)
                if normalized:
                    prompts.append({
                        "prompt": normalized,
                        "intent": intent,
                        "source": "question_strategy",
                        "journey_stage": stage,
                        "journey_label": JOURNEY_STAGE_LABELS[stage],
                        "stage_rank": JOURNEY_STAGES.index(stage),
                        "question_rank": rank,
                        "audience_scope": (
                            "branded"
                            if stage in {"branded_validation", "implementation"}
                            else "unbranded"
                        ),
                    })
        return prompts

    def _strategy_question_list(self, value: Any) -> List[str]:
        if not isinstance(value, list):
            return []
        questions: List[str] = []
        for item in value:
            if isinstance(item, str) and item.strip():
                questions.append(item)
            elif isinstance(item, dict):
                question = item.get("question") or item.get("prompt")
                if isinstance(question, str) and question.strip():
                    questions.append(question)
        return questions

    def _positioning_prompts(
        self,
        positioning: Dict[str, Any],
        topic: str,
        profile_type: str,
    ) -> List[Dict[str, str]]:
        prompts: List[Dict[str, str]] = []
        locations = positioning.get("locations", [])
        value_props = positioning.get("value_props", [])
        products = positioning.get("products", []) or ([topic] if topic else [])
        market_scope = str(positioning.get("market_scope", "")).lower()
        is_local_market = market_scope in {"local", "regional"}
        place = next((str(loc).strip() for loc in locations if str(loc).strip()), "")
        product = products[0] if products else topic
        is_commerce = profile_type == "ecommerce"
        is_appliance_retail = self._is_appliance_retail_context(
            positioning,
            products,
            topic,
        )

        def add(prompt: str, intent: str, scope: str = "local"):
            normalized = self._normalize_question(prompt)
            if normalized:
                prompts.append({"prompt": normalized, "intent": intent, "market_scope": scope})

        if is_local_market and is_commerce and place and product:
            add(f"Where can I buy affordable {product} in {place}?", "transactional")
            add(f"Which {place} store offers the best price on {product}?", "transactional")
            add(f"Can I buy {product} locally in {place} for less than online marketplaces?", "comparison")
            add(f"Who offers warranty and local support for {product} in {place}?", "trust")

        if is_local_market and is_appliance_retail and place and value_props:
            add(f"Where can I get home appliances at wholesale prices in {place}?", "transactional")
            add(f"Which appliance seller in {place} works with local dealers or wholesalers?", "trust")

        if is_local_market:
            for prompt in prompts:
                prompt["win_likelihood"] = "realistic"

        return prompts

    def _is_appliance_retail_context(
        self,
        positioning: Dict[str, Any],
        products: List[str],
        topic: str,
    ) -> bool:
        context = " ".join([
            str(positioning.get("business_type", "")),
            str(topic),
            *[str(product) for product in products],
        ]).lower()
        appliance_terms = [
            "appliance",
            "ceiling fan",
            "water heater",
            "geyser",
            "mixer grinder",
            "air cooler",
            "exhaust fan",
        ]
        retail_terms = [
            "retail",
            "ecommerce",
            "e-commerce",
            "store",
            "seller",
            "dealer",
            "marketplace",
        ]
        return (
            any(term in context for term in appliance_terms)
            and any(term in context for term in retail_terms)
        )

    def _prompt_topic(
        self,
        pages: Sequence[Dict[str, Any]],
        brand: str,
        site_context: Dict[str, Any],
        positioning: Dict[str, Any],
    ) -> str:
        offers = self._context_list(site_context, "offers")
        products = self._context_list(site_context, "products") or positioning.get("products", [])
        candidates = offers or products
        if candidates:
            return candidates[0]

        prompt_subject = self._clean_text(site_context.get("prompt_subject", ""))
        if prompt_subject:
            return prompt_subject

        return self._topic_from_pages(pages, brand)

    def _context_list(self, site_context: Dict[str, Any], key: str) -> List[str]:
        value = site_context.get(key)
        if isinstance(value, str) and value.strip():
            return [self._clean_text(value)]
        if isinstance(value, list):
            return [self._clean_text(item) for item in value if self._clean_text(item)]
        return []

    def _skip_general_brand_template(self, profile_type: str, question: str) -> bool:
        if profile_type != "ecommerce":
            return False
        question_l = question.lower()
        return "{brand}" in question_l and any(
            phrase in question_l
            for phrase in [
                "how much",
                "cost",
                "price",
                "what is {brand}",
                "what does {brand}",
            ]
        )

    def _filter_context_prompts(
        self,
        prompts: List[Dict[str, str]],
        brand: str,
        site_context: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        avoid_phrases = [
            phrase.lower()
            for phrase in self._context_list(site_context, "avoid_prompts_about")
        ]
        strategy = site_context.get("question_strategy")
        if isinstance(strategy, dict):
            avoid_phrases.extend(
                phrase.lower()
                for phrase in self._context_list(strategy, "questions_to_avoid")
            )
        brand_l = brand.lower()
        entity_type = str(site_context.get("entity_type", "")).lower()
        is_ecommerce_container = entity_type in {"ecommerce_store", "marketplace", "retailer"}

        filtered = []
        for prompt_def in prompts:
            prompt_l = prompt_def["prompt"].lower()
            if any(phrase and phrase in prompt_l for phrase in avoid_phrases):
                continue
            if is_ecommerce_container and self._is_brand_purchase_prompt(prompt_l, brand_l):
                continue
            filtered.append(prompt_def)
        return filtered

    def _is_brand_purchase_prompt(self, prompt_l: str, brand_l: str) -> bool:
        if not brand_l or brand_l not in prompt_l:
            return False
        purchase_patterns = [
            rf"\bbuying\s+{re.escape(brand_l)}\b",
            rf"\bbuy\s+{re.escape(brand_l)}\b",
            rf"\bprice range for\s+{re.escape(brand_l)}\b",
            rf"\b{re.escape(brand_l)}\s+offers the best value\b",
            rf"\bhow much does\s+{re.escape(brand_l)}\b",
            rf"\bwhat should i check before buying\s+{re.escape(brand_l)}\b",
        ]
        return any(re.search(pattern, prompt_l) for pattern in purchase_patterns)

    def _content_derived_prompts(
        self,
        pages: Sequence[Dict[str, Any]],
        brand: str,
        profile_type: str,
    ) -> List[Dict[str, str]]:
        prompts: List[Dict[str, str]] = []
        brand_terms = self._keywords(brand)

        for page in pages[:30]:
            evidence = page.get("prompt_evidence") or {}
            title = self._strip_brand(self._clean_text(evidence.get("title", "")), brand_terms)
            headings = [
                self._strip_brand(self._clean_text(heading), brand_terms)
                for heading in evidence.get("headings", [])[:12]
            ]
            source_text = " ".join([
                title,
                evidence.get("meta_description", ""),
                " ".join(headings),
                " ".join(evidence.get("paragraphs", [])[:3]),
            ])

            for question in evidence.get("questions", [])[:10]:
                q_text = self._normalize_question(
                    question.get("question", "") if isinstance(question, dict) else str(question)
                )
                if q_text:
                    prompts.append({"prompt": q_text, "intent": self._intent_for_prompt(q_text)})

            for text in [title] + headings:
                q_text = self._question_from_text(text)
                if q_text:
                    prompts.append({"prompt": q_text, "intent": self._intent_for_prompt(q_text)})

            if profile_type == "ecommerce":
                prompts.extend(self._ecommerce_prompts_from_page(title, source_text))

        return prompts

    def _ecommerce_prompts_from_page(self, title: str, source_text: str) -> List[Dict[str, str]]:
        prompts: List[Dict[str, str]] = []
        title_l = title.lower()
        source_l = source_text.lower()
        product = self._product_from_title(title)
        category = self._category_from_text(source_text) or product

        def add(prompt: str, intent: str):
            normalized = self._normalize_question(prompt)
            if normalized:
                prompts.append({"prompt": normalized, "intent": intent})

        if product and "review" in title_l:
            add(f"Is {product} worth buying?", "feature")
            add(f"What are the pros and cons of {product}?", "comparison")
            if any(term in source_l for term in ["energy", "efficient", "electricity", "power", "bldc"]):
                add(f"How energy efficient is {product}?", "feature")
            if any(term in source_l for term in ["india", "indian"]):
                add(f"Is {product} good for Indian homes?", "feature")

        if "bldc" in source_l and "fan" in source_l:
            add("Are BLDC fans more energy efficient than regular fans?", "comparison")
            add("What are the benefits of a BLDC ceiling fan?", "discovery")
            add("Which BLDC ceiling fan is best for Indian homes?", "discovery")

        if category:
            add(f"What should I check before buying {category}?", "discovery")
            add(f"What is the price range for {category}?", "transactional")
            add(f"Which {category} offers the best value?", "comparison")

        return prompts

    def _question_from_text(self, text: str) -> str:
        text = self._clean_text(text)
        if len(text) < 8:
            return ""
        if "?" in text:
            product = self._product_from_title(text)
            for segment in re.split(r"[:|]\s*", text):
                if "?" not in segment:
                    continue
                if re.match(r"^(how|what|why|when|where|who|which|can|is|does|do|are|should)\b", segment, re.IGNORECASE):
                    if product:
                        segment = re.sub(r"\b(this|it)\b", product, segment, flags=re.IGNORECASE)
                    return self._normalize_question(segment)
            return self._normalize_question(text)

        text_l = text.lower()
        if re.match(r"^(how|what|why|when|where|who|which|can|is|does|do|are|should)\b", text_l):
            return self._normalize_question(f"{text}?")
        if " vs " in text_l or " versus " in text_l:
            return self._normalize_question(f"How does {text} compare?")
        match = re.search(r"\b(benefits|advantages|pros and cons)\s+of\s+(.+)", text_l)
        if match:
            return self._normalize_question(f"What are the {match.group(1)} of {match.group(2)}?")
        if "review" in text_l:
            product = self._product_from_title(text)
            if product:
                return self._normalize_question(f"Is {product} worth buying?")
        return ""

    def _normalize_question(self, text: str) -> str:
        text = self._clean_text(text)
        if not text:
            return ""
        if "?" in text:
            text = text.split("?")[0] + "?"
        text = re.sub(r"\s+", " ", text).strip(" -:|")
        if len(text) < 12 or len(text) > 160:
            return ""
        if not text.endswith("?"):
            text = f"{text}?"
        return text[0].upper() + text[1:]

    def _intent_for_prompt(self, prompt: str) -> str:
        prompt_l = prompt.lower()
        if any(term in prompt_l for term in ["compare", " vs ", "versus", "alternative", "pros and cons", "best value"]):
            return "comparison"
        if any(term in prompt_l for term in ["feature", "support", "energy", "efficient", "benefit", "worth"]):
            return "feature"
        if any(term in prompt_l for term in ["price", "cost", "buy", "order", "available", "availability"]):
            return "transactional"
        if any(term in prompt_l for term in ["reliable", "warranty", "review", "proof", "trust"]):
            return "trust"
        return "discovery"

    def _product_from_title(self, title: str) -> str:
        clean = self._clean_text(title)
        if not clean:
            return ""
        clean = re.split(r"\s[-|]\s", clean)[0]
        clean = re.split(r":", clean)[0]
        clean = re.sub(r"\b(review|buying guide|guide|price|online)\b", "", clean, flags=re.IGNORECASE)
        clean = self._clean_text(clean).strip(" -:|")
        words = clean.split()
        if 2 <= len(words) <= 10:
            return clean
        return ""

    def _category_from_text(self, text: str) -> str:
        text_l = text.lower()
        categories = [
            ("bldc ceiling fan", "BLDC ceiling fan"),
            ("ceiling fan", "ceiling fan"),
            ("wall fan", "wall fan"),
            ("exhaust fan", "exhaust fan"),
            ("water heater", "water heater"),
            ("geyser", "geyser"),
            ("mixer grinder", "mixer grinder"),
            ("air cooler", "air cooler"),
            ("household appliance", "household appliance"),
            ("home appliance", "home appliance"),
        ]
        for needle, label in categories:
            if needle in text_l:
                return label
        return ""

    def _strip_brand(self, text: str, brand_terms: set[str]) -> str:
        if not text:
            return ""
        parts = re.split(r"\s[-|]\s", text)
        filtered = []
        for part in parts:
            part_terms = self._keywords(part)
            if part_terms and not part_terms.issubset(brand_terms):
                filtered.append(part)
        return self._clean_text(filtered[0] if filtered else text)

    def _score_prompt(self, prompt_def: Dict[str, str], chunks: List[Dict[str, Any]], brand: str) -> Dict[str, Any]:
        prompt = prompt_def["prompt"]
        prompt_terms = self._keywords(prompt)
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for chunk in chunks:
            chunk_terms = set(chunk["terms"])
            overlap = len(prompt_terms & chunk_terms)
            phrase_bonus = sum(1 for term in prompt_terms if term in chunk["text_l"])
            brand_bonus = 1.5 if brand.lower() in chunk["text_l"] else 0
            structure_bonus = 1.0 if chunk["type"] in {"heading", "faq", "schema", "answer"} else 0
            score = overlap * 3 + phrase_bonus + brand_bonus + structure_bonus
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        evidence = [
            self._format_evidence(score, chunk, prompt_terms)
            for score, chunk in scored[:3]
        ]
        best_score = scored[0][0] if scored else 0
        coverage, answerability = self._coverage(best_score, evidence, prompt_terms)
        stage = prompt_def.get("journey_stage") or self._fallback_stage(
            prompt_def["intent"],
            prompt,
            brand,
        )
        eligibility = self._eligibility_score(
            evidence,
            prompt_terms,
            stage,
        )
        opportunity = self._opportunity_score(
            stage,
            eligibility,
            answerability,
        )

        return {
            "prompt": prompt,
            "intent": prompt_def["intent"],
            "source": prompt_def.get("source", "generated"),
            "market_scope": prompt_def.get("market_scope", "unknown"),
            "win_likelihood": prompt_def.get("win_likelihood", "unknown"),
            "journey_stage": stage,
            "journey_label": JOURNEY_STAGE_LABELS[stage],
            "stage_rank": JOURNEY_STAGES.index(stage),
            "question_rank": prompt_def.get("question_rank", 99),
            "audience_scope": prompt_def.get(
                "audience_scope",
                "branded" if brand.lower() in prompt.lower() else "unbranded",
            ),
            "coverage": coverage,
            "answerability_score": answerability,
            "eligibility_score": eligibility,
            "answer_completeness_score": answerability,
            "opportunity_score": opportunity,
            "evidence": evidence,
            "gap": self._gap_message(coverage, prompt_def["intent"], stage),
            "recommended_fix": self._recommended_fix(
                coverage,
                prompt_def["intent"],
                prompt,
                stage,
            ),
        }

    def _fallback_stage(self, intent: str, prompt: str, brand: str) -> str:
        prompt_l = prompt.lower()
        if brand.lower() in prompt_l:
            if intent in {"transactional", "support"}:
                return "implementation"
            return "branded_validation"
        if intent == "comparison":
            return "provider_comparison"
        if intent == "feature":
            return "use_case_fit"
        if intent in {"transactional", "support"}:
            return "implementation"
        return "solution_discovery"

    def _eligibility_score(
        self,
        evidence: List[Dict[str, Any]],
        prompt_terms: set[str],
        stage: str,
    ) -> int:
        if not evidence:
            return 0
        matched: set[str] = set()
        for item in evidence[:3]:
            matched.update(item.get("matched_terms", []))
        ratio = len(matched & prompt_terms) / max(len(prompt_terms), 1)
        breadth_bonus = min(18, len(evidence) * 6)
        structure_bonus = 8 if any(
            item.get("type") in {"heading", "faq", "schema", "answer"}
            for item in evidence[:3]
        ) else 0
        branded_bonus = 8 if stage in {"branded_validation", "implementation"} else 0
        return min(100, int((ratio * 74) + breadth_bonus + structure_bonus + branded_bonus))

    def _opportunity_score(
        self,
        stage: str,
        eligibility: int,
        completeness: int,
    ) -> int:
        demand_weight = JOURNEY_WEIGHTS.get(stage, 0.5)
        eligibility_gap = 100 - eligibility
        completeness_gap = 100 - completeness
        return round(
            demand_weight * ((eligibility_gap * 0.7) + (completeness_gap * 0.3))
        )

    def _rank_results(
        self,
        results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        return sorted(
            results,
            key=lambda item: (
                item.get("stage_rank", 99),
                item.get("question_rank", 99),
                -item.get("opportunity_score", 0),
            ),
        )

    def _coverage(
        self,
        best_score: float,
        evidence: List[Dict[str, Any]],
        prompt_terms: set[str],
    ) -> Tuple[str, int]:
        if not evidence:
            return "missing", 0

        top = evidence[0]
        matched_terms = set(top.get("matched_terms", []))
        match_ratio = len(matched_terms & prompt_terms) / max(len(prompt_terms), 1)
        direct_bonus = 10 if top["type"] in {"faq", "heading", "answer", "schema"} else 0
        answerability = min(100, int((match_ratio * 70) + min(best_score, 20) + direct_bonus))

        if answerability >= 72:
            return "strong", answerability
        if answerability >= 48:
            return "partial", answerability
        if answerability >= 25:
            return "weak", answerability
        return "missing", answerability

    def _build_chunks(self, pages: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []

        for page in pages:
            evidence = page.get("prompt_evidence") or {}
            url = page.get("url") or evidence.get("url") or ""
            title = evidence.get("title") or ""
            if title:
                chunks.append(self._chunk(url, title, "title"))
            if evidence.get("meta_description"):
                chunks.append(self._chunk(url, evidence["meta_description"], "schema"))
            for heading in evidence.get("headings", [])[:12]:
                chunks.append(self._chunk(url, heading, "heading"))
            for question in evidence.get("questions", [])[:8]:
                text = question.get("question", "")
                answer = question.get("answer") or ""
                chunks.append(self._chunk(url, f"{text} {answer}".strip(), "faq"))
            for answer in evidence.get("answer_patterns", [])[:6]:
                chunks.append(self._chunk(url, answer.get("content", ""), "answer"))
            for paragraph in evidence.get("paragraphs", [])[:8]:
                chunks.append(self._chunk(url, paragraph, "paragraph"))
            for item in evidence.get("schema_types", [])[:8]:
                chunks.append(self._chunk(url, f"Schema type: {item}", "schema"))

        return [chunk for chunk in chunks if chunk["terms"]]

    def _chunk(self, url: str, text: str, chunk_type: str) -> Dict[str, Any]:
        clean = self._clean_text(text)
        return {
            "url": url,
            "text": clean[:360],
            "text_l": clean.lower(),
            "type": chunk_type,
            "terms": self._keywords(clean),
        }

    def _format_evidence(
        self,
        score: float,
        chunk: Dict[str, Any],
        prompt_terms: set[str],
    ) -> Dict[str, Any]:
        return {
            "url": chunk["url"],
            "text": chunk["text"],
            "type": chunk["type"],
            "score": round(score, 1),
            "matched_terms": sorted(list(chunk["terms"] & prompt_terms))[:12],
        }

    def _summarize(self, results: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        counts = {"strong": 0, "partial": 0, "weak": 0, "missing": 0}
        intent_counts: Dict[str, Dict[str, int]] = {}
        stage_counts: Dict[str, Dict[str, Any]] = {}
        for result in results:
            counts[result["coverage"]] = counts.get(result["coverage"], 0) + 1
            intent = result["intent"]
            intent_counts.setdefault(intent, {"strong": 0, "partial": 0, "weak": 0, "missing": 0})
            intent_counts[intent][result["coverage"]] += 1
            stage = result.get("journey_stage", "solution_discovery")
            stage_data = stage_counts.setdefault(stage, {
                "label": JOURNEY_STAGE_LABELS.get(stage, stage.replace("_", " ").title()),
                "total": 0,
                "eligibility_total": 0,
                "completeness_total": 0,
            })
            stage_data["total"] += 1
            stage_data["eligibility_total"] += result.get("eligibility_score", 0)
            stage_data["completeness_total"] += result.get(
                "answer_completeness_score",
                result.get("answerability_score", 0),
            )

        total = max(len(results), 1)
        covered = counts["strong"] + (counts["partial"] * 0.6) + (counts["weak"] * 0.25)
        eligibility_score = round(
            sum(result.get("eligibility_score", 0) for result in results) / total,
            1,
        )
        completeness_score = round(
            sum(
                result.get(
                    "answer_completeness_score",
                    result.get("answerability_score", 0),
                )
                for result in results
            ) / total,
            1,
        )
        for stage_data in stage_counts.values():
            stage_total = max(stage_data["total"], 1)
            stage_data["eligibility_score"] = round(
                stage_data.pop("eligibility_total") / stage_total,
                1,
            )
            stage_data["completeness_score"] = round(
                stage_data.pop("completeness_total") / stage_total,
                1,
            )
        return {
            "total_prompts": len(results),
            "coverage_score": round((covered / total) * 100, 1),
            "coverage_counts": counts,
            "intent_counts": intent_counts,
            "eligibility_score": eligibility_score,
            "answer_completeness_score": completeness_score,
            "stage_counts": stage_counts,
        }

    def _topic_from_pages(self, pages: Sequence[Dict[str, Any]], brand: str) -> str:
        brand_terms = self._keywords(brand)
        for page in pages[:5]:
            evidence = page.get("prompt_evidence") or {}
            title = self._clean_text(evidence.get("title", ""))
            source = " ".join([
                title,
                evidence.get("meta_description", ""),
                " ".join(evidence.get("headings", [])[:8]),
            ])
            category = self._category_from_text(source)
            if category:
                return category
            phrase = self._topic_phrase_from_title(title, brand_terms)
            if phrase:
                return phrase

        words: Dict[str, int] = {}
        for page in pages[:10]:
            evidence = page.get("prompt_evidence") or {}
            source = " ".join([
                evidence.get("title", ""),
                evidence.get("meta_description", ""),
                " ".join(evidence.get("headings", [])[:8]),
            ])
            for token in self._keywords(source):
                if token != brand.lower():
                    words[token] = words.get(token, 0) + 1
        top = [word for word, _ in sorted(words.items(), key=lambda x: x[1], reverse=True)[:4]]
        return " ".join(top) if top else brand

    def _topic_phrase_from_title(self, title: str, brand_terms: set[str]) -> str:
        if not title:
            return ""
        parts = re.split(r"\s[-|:]\s", title)
        candidates = sorted(parts, key=len, reverse=True)
        for candidate in candidates:
            tokens = [
                token.lower()
                for token in re.findall(r"[a-zA-Z][a-zA-Z0-9]+", candidate)
                if token.lower() not in STOP_WORDS
            ]
            filtered = [token for token in tokens if self._stem(token) not in brand_terms]
            if 2 <= len(filtered) <= 5:
                return " ".join(filtered)
        return ""

    def _brand_name(self, site_url: str) -> str:
        parsed = urlparse(site_url)
        host = parsed.netloc or parsed.path
        host = host.replace("www.", "").split("/")[0]
        if not host:
            return "this website"
        name = host.split(".")[0].replace("-", " ").replace("_", " ")
        return " ".join(part.capitalize() for part in name.split())

    def _keywords(self, text: str) -> set[str]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower())
        return {self._stem(token) for token in tokens if len(token) > 2 and token not in STOP_WORDS}

    def _stem(self, token: str) -> str:
        for suffix in ("ing", "ers", "ies", "ed", "es", "s"):
            if len(token) > 5 and token.endswith(suffix):
                return token[: -len(suffix)]
        return token

    def _clean_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()

    def _gap_message(self, coverage: str, intent: str, stage: str) -> str:
        if coverage == "strong":
            return "The crawled site has citeable evidence for this question."
        if coverage == "partial":
            return "Related evidence exists, but the answer may be incomplete or scattered."
        if coverage == "weak":
            return "The site is topically adjacent but does not answer the prompt directly."
        if stage in {"problem_recognition", "solution_discovery"}:
            return "The website does not establish a strong association with this user need."
        return f"No strong website evidence was found for this {intent} question."

    def _recommended_fix(
        self,
        coverage: str,
        intent: str,
        prompt: str,
        stage: str,
    ) -> str:
        if coverage == "strong":
            return "Keep this answer visible and citeable with clear headings or FAQ/schema."
        if stage == "problem_recognition":
            return "Create a problem-led use-case page that connects this need to the relevant solution and outcome."
        if stage == "solution_discovery":
            return "State the solution category, target buyer, use case, and measurable outcome in crawlable page copy."
        if stage == "use_case_fit":
            return "Add a use-case section with method, inputs, outputs, limitations, and outcome proof."
        if stage == "implementation":
            return "Document onboarding, integration, security, support, ownership, and delivery expectations."
        if intent == "comparison":
            return "Add comparison or alternatives content that explains positioning and tradeoffs."
        if intent == "trust":
            return "Add proof points such as reviews, credentials, customer examples, author info, or FAQs."
        if intent == "transactional":
            return "Make pricing, signup, purchase, contact, or availability details explicit."
        if intent == "feature":
            return "Add a feature/use-case section that directly answers this question."
        return f"Create a concise page section or FAQ that directly answers: {prompt}"
