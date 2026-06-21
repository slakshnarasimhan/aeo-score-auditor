"""
Lightweight positioning and USP analysis.

This is a heuristic first pass: it identifies local/value/product signals that
can shape a realistic prompt portfolio. It is deliberately separate from the
prompt gap analyzer so this layer can be replaced later.
"""
import re
from typing import Any, Dict, List, Sequence
from urllib.parse import urlparse


LOCATION_TERMS = [
    "chennai", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
    "pune", "kolkata", "coimbatore", "india", "indian",
]
VALUE_TERMS = [
    "lowest price", "low price", "best price", "affordable", "cheap",
    "discount", "wholesale", "wholesaler", "dealer", "local vendor",
    "vendor", "supplier", "direct", "savings", "offer",
]
SERVICE_TERMS = [
    "delivery", "installation", "warranty", "support", "service",
    "local", "near me", "store", "contact", "dealer",
]
PRODUCT_TERMS = [
    "BLDC ceiling fan", "ceiling fan", "water heater", "geyser",
    "mixer grinder", "air cooler", "exhaust fan", "household appliance",
    "home appliance",
]


class PositioningAnalyzer:
    """Infer the realistic wedge a site may be able to win for."""

    def analyze(
        self,
        pages: Sequence[Dict[str, Any]],
        site_url: str,
        profile: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        brand = self._brand_name(site_url)
        combined = self._combined_text(pages)
        combined_l = combined.lower()
        locations = self._find_terms(combined_l, LOCATION_TERMS)
        value_props = self._find_terms(combined_l, VALUE_TERMS)
        service_props = self._find_terms(combined_l, SERVICE_TERMS)
        products = self._find_terms(combined_l, PRODUCT_TERMS)

        market_scope = self._market_scope(locations, combined_l)
        wedge = self._wedge(brand, products, locations, value_props, market_scope, profile)
        usp_claims = self._usp_claims(products, locations, value_props, service_props)
        constraints = self._constraints(market_scope, locations)
        evidence = self._evidence(pages, locations + value_props + service_props + products)
        strength = self._evidence_strength(usp_claims, evidence)

        return {
            "brand": brand,
            "business_type": self._business_type(profile),
            "market_scope": market_scope,
            "locations": locations,
            "products": products,
            "value_props": value_props,
            "service_props": service_props,
            "usp_claims": usp_claims,
            "likely_wedge": wedge,
            "constraints": constraints,
            "evidence_strength": strength,
            "evidence": evidence[:8],
            "recommended_proof": self._recommended_proof(locations, value_props, service_props),
        }

    def _combined_text(self, pages: Sequence[Dict[str, Any]]) -> str:
        parts: List[str] = []
        for page in pages[:40]:
            evidence = page.get("prompt_evidence") or {}
            parts.extend([
                page.get("url", ""),
                evidence.get("title", ""),
                evidence.get("meta_description", ""),
                " ".join(evidence.get("headings", [])[:12]),
                " ".join(evidence.get("paragraphs", [])[:6]),
            ])
        return " ".join(str(part) for part in parts if part)

    def _find_terms(self, text_l: str, terms: List[str]) -> List[str]:
        found = []
        for term in terms:
            if term.lower() in text_l:
                found.append(term)
        return found

    def _business_type(self, profile: Dict[str, Any] | None) -> str:
        profile_type = (profile or {}).get("type", "general")
        if profile_type == "ecommerce":
            return "local/online product retailer"
        if profile_type == "local_business":
            return "local service business"
        return profile_type.replace("_", " ")

    def _market_scope(self, locations: List[str], text_l: str) -> str:
        city_terms = [loc for loc in locations if loc not in {"india", "indian"}]
        if city_terms:
            return "local"
        if "india" in locations or "indian" in locations or ".in" in text_l:
            return "national"
        return "unknown"

    def _wedge(
        self,
        brand: str,
        products: List[str],
        locations: List[str],
        value_props: List[str],
        market_scope: str,
        profile: Dict[str, Any] | None,
    ) -> str:
        product = products[0] if products else "products/services"
        city = next((loc.title() for loc in locations if loc not in {"india", "indian"}), "")
        value = value_props[0] if value_props else ""
        if market_scope == "local" and value:
            return f"{city}-focused {product} provider positioned around {value}."
        if market_scope == "local":
            return f"{city}-focused {product} provider."
        if value:
            return f"{brand} appears positioned around {value} for {product}."
        return f"{brand} appears positioned around {product}."

    def _usp_claims(
        self,
        products: List[str],
        locations: List[str],
        value_props: List[str],
        service_props: List[str],
    ) -> List[str]:
        claims = []
        if locations:
            city = next((loc.title() for loc in locations if loc not in {"india", "indian"}), None)
            if city:
                claims.append(f"Local relevance in {city}")
        if value_props:
            claims.append(f"Price/value positioning: {', '.join(value_props[:3])}")
        if products:
            claims.append(f"Product/category focus: {', '.join(products[:4])}")
        if service_props:
            claims.append(f"Service proof needed around: {', '.join(service_props[:3])}")
        return claims

    def _constraints(self, market_scope: str, locations: List[str]) -> List[str]:
        constraints = []
        if market_scope == "local":
            city = next((loc.title() for loc in locations if loc not in {"india", "indian"}), "local market")
            constraints.append(f"Prioritize {city} and nearby commercial-intent prompts over national prompts.")
            constraints.append("Avoid broad marketplace prompts unless the site proves distribution capacity.")
        elif market_scope == "unknown":
            constraints.append("Market scope is not explicit enough; clarify location/service area or delivery coverage.")
        return constraints

    def _evidence(self, pages: Sequence[Dict[str, Any]], terms: List[str]) -> List[Dict[str, str]]:
        snippets = []
        seen = set()
        for page in pages[:40]:
            evidence = page.get("prompt_evidence") or {}
            url = page.get("url") or evidence.get("url") or ""
            candidates = [
                evidence.get("title", ""),
                evidence.get("meta_description", ""),
                *evidence.get("headings", [])[:8],
                *evidence.get("paragraphs", [])[:6],
            ]
            for text in candidates:
                text_s = self._clean(text)
                text_l = text_s.lower()
                if not text_s or (url, text_s[:80]) in seen:
                    continue
                if any(term.lower() in text_l for term in terms):
                    seen.add((url, text_s[:80]))
                    snippets.append({"url": url, "text": text_s[:260]})
                    break
        return snippets

    def _evidence_strength(self, usp_claims: List[str], evidence: List[Dict[str, str]]) -> str:
        if len(evidence) >= 5 and len(usp_claims) >= 3:
            return "strong"
        if len(evidence) >= 2 and usp_claims:
            return "partial"
        if usp_claims:
            return "weak"
        return "missing"

    def _recommended_proof(
        self,
        locations: List[str],
        value_props: List[str],
        service_props: List[str],
    ) -> List[str]:
        proof = []
        if not locations:
            proof.append("State service area, delivery coverage, and local address/contact clearly.")
        if not value_props:
            proof.append("Explain price advantage with MRP/offer comparisons, sourcing model, or supplier relationships.")
        if not service_props or "warranty" not in service_props:
            proof.append("Add warranty, installation, delivery, and after-sales support details.")
        proof.append("Create FAQ answers for local buyers comparing local dealers, marketplaces, price, warranty, and availability.")
        return proof

    def _brand_name(self, site_url: str) -> str:
        parsed = urlparse(site_url)
        host = parsed.netloc or parsed.path
        host = host.replace("www.", "").split("/")[0]
        name = host.split(".")[0].replace("-", " ").replace("_", " ") if host else "this website"
        return " ".join(part.capitalize() for part in name.split())

    def _clean(self, text: Any) -> str:
        return re.sub(r"\s+", " ", str(text or "")).strip()
