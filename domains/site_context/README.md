# Site Context

Add optional per-site JSON files here when the crawler cannot infer business
positioning safely.

File name:

```text
domains/site_context/example.com.json
```

Example:

```json
{
  "brand": "BetterHomeApp",
  "business_type": "local appliance retailer",
  "entity_type": "ecommerce_store",
  "market_scope": "local",
  "locations": ["Chennai"],
  "products": ["home appliances", "ceiling fans", "water heaters"],
  "value_props": ["wholesale pricing", "local warranty support"],
  "service_props": ["delivery", "installation", "warranty"],
  "prompt_subject": "products sold on BetterHomeApp",
  "avoid_prompts_about": ["BetterHomeApp subscription cost", "BetterHomeApp price range"],
  "constraints": [
    "Prioritize Chennai buyer prompts over national marketplace prompts."
  ]
}
```

If no JSON is provided, positioning defaults to `global`.
