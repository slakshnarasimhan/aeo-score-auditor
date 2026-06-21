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


PROFILE_PROMPTS: Dict[str, Dict[str, List[str]]] = {
    "ecommerce": {
        "discovery": [
            "What should I know before buying {topic}?",
            "Which {topic} is best for my home?",
            "What should I look for before buying {topic}?",
        ],
        "comparison": [
            "How do different {topic} options compare?",
            "Which {topic} offers the best value?",
        ],
        "feature": [
            "What product details, pricing, and availability should I check for {topic}?",
            "Can I find reviews or proof before choosing {topic}?",
        ],
        "trust": [
            "Which {topic} brands are reliable?",
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
    ) -> Dict[str, Any]:
        brand = self._brand_name(site_url)
        topic = self._topic_from_pages(pages, brand)
        profile_type = (profile or {}).get("type") or "general"
        prompt_defs = self._generate_prompts(brand, topic, profile_type, max_prompts, pages, positioning)
        chunks = self._build_chunks(pages)

        results = [self._score_prompt(prompt, chunks, brand) for prompt in prompt_defs]
        llm_evaluation = {
            "enabled": False,
            "provider": "openai",
            "reason": "LLM evaluation was not requested",
        }

        if use_llm:
            from reporting.llm_prompt_evaluator import LLMPromptEvaluator

            llm_evaluation = LLMPromptEvaluator().evaluate_results(results)
            results = llm_evaluation.get("results", results)

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
    ) -> List[Dict[str, str]]:
        templates = PROFILE_PROMPTS.get(profile_type) or PROFILE_PROMPTS["general"]
        prompts: List[Dict[str, str]] = []
        prompts.extend(self._positioning_prompts(positioning or {}, topic))
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
                    prompts.append({
                        "prompt": question.format(brand=brand, topic=topic),
                        "intent": intent,
                    })

        seen = set()
        unique = []
        for item in prompts:
            key = item["prompt"].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique[:max_prompts]

    def _positioning_prompts(self, positioning: Dict[str, Any], topic: str) -> List[Dict[str, str]]:
        prompts: List[Dict[str, str]] = []
        locations = positioning.get("locations", [])
        value_props = positioning.get("value_props", [])
        products = positioning.get("products", []) or ([topic] if topic else [])
        city = next((loc.title() for loc in locations if loc not in {"india", "indian"}), "")
        product = products[0] if products else topic

        def add(prompt: str, intent: str, scope: str = "local"):
            normalized = self._normalize_question(prompt)
            if normalized:
                prompts.append({"prompt": normalized, "intent": intent, "market_scope": scope})

        if city and product:
            add(f"Where can I buy affordable {product} in {city}?", "transactional")
            add(f"Which {city} store offers the best price on {product}?", "transactional")
            add(f"Can I buy {product} locally in {city} for less than online marketplaces?", "comparison")
            add(f"Who offers warranty and local support for {product} in {city}?", "trust")

        if city and value_props:
            add(f"Where can I get home appliances at wholesale prices in {city}?", "transactional")
            add(f"Which appliance seller in {city} works with local dealers or wholesalers?", "trust")

        if positioning.get("market_scope") == "local":
            for prompt in prompts:
                prompt["win_likelihood"] = "realistic"

        return prompts

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
        evidence = [self._format_evidence(score, chunk) for score, chunk in scored[:3]]
        best_score = scored[0][0] if scored else 0
        coverage, answerability = self._coverage(best_score, evidence, prompt_terms)

        return {
            "prompt": prompt,
            "intent": prompt_def["intent"],
            "market_scope": prompt_def.get("market_scope", "unknown"),
            "win_likelihood": prompt_def.get("win_likelihood", "unknown"),
            "coverage": coverage,
            "answerability_score": answerability,
            "evidence": evidence,
            "gap": self._gap_message(coverage, prompt_def["intent"]),
            "recommended_fix": self._recommended_fix(coverage, prompt_def["intent"], prompt),
        }

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

    def _format_evidence(self, score: float, chunk: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "url": chunk["url"],
            "text": chunk["text"],
            "type": chunk["type"],
            "score": round(score, 1),
            "matched_terms": sorted(list(chunk["terms"]))[:12],
        }

    def _summarize(self, results: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
        counts = {"strong": 0, "partial": 0, "weak": 0, "missing": 0}
        intent_counts: Dict[str, Dict[str, int]] = {}
        for result in results:
            counts[result["coverage"]] = counts.get(result["coverage"], 0) + 1
            intent = result["intent"]
            intent_counts.setdefault(intent, {"strong": 0, "partial": 0, "weak": 0, "missing": 0})
            intent_counts[intent][result["coverage"]] += 1

        total = max(len(results), 1)
        covered = counts["strong"] + (counts["partial"] * 0.6) + (counts["weak"] * 0.25)
        return {
            "total_prompts": len(results),
            "coverage_score": round((covered / total) * 100, 1),
            "coverage_counts": counts,
            "intent_counts": intent_counts,
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

    def _gap_message(self, coverage: str, intent: str) -> str:
        if coverage == "strong":
            return "The crawled site has citeable local evidence for this prompt."
        if coverage == "partial":
            return "Related evidence exists, but the answer may be incomplete or scattered."
        if coverage == "weak":
            return "The site is topically adjacent but does not answer the prompt directly."
        return f"No strong local evidence was found for this {intent} prompt."

    def _recommended_fix(self, coverage: str, intent: str, prompt: str) -> str:
        if coverage == "strong":
            return "Keep this answer visible and citeable with clear headings or FAQ/schema."
        if intent == "comparison":
            return "Add comparison or alternatives content that explains positioning and tradeoffs."
        if intent == "trust":
            return "Add proof points such as reviews, credentials, customer examples, author info, or FAQs."
        if intent == "transactional":
            return "Make pricing, signup, purchase, contact, or availability details explicit."
        if intent == "feature":
            return "Add a feature/use-case section that directly answers this question."
        return f"Create a concise page section or FAQ that directly answers: {prompt}"
