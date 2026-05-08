from app.runway.visual_hints import get_visual_hint

SYSTEM_PROMPT = """\
You are a CRM Reactivation Agent for an online subscription/deposit-based service.
Your task: for a given dormant player, generate a personalized reactivation script.

Principles:
- Warm tone, like a familiar account manager, not aggressive sales
- Script 30-45 seconds voiceover = 70-110 words
- Use player's name, last favorite activity, and offered value
- Final CTA must be single and unambiguous

Prohibited:
- Urgency more than once in the script
- Guaranteeing wins or money-back
- Words: guaranteed, you will definitely win, don't miss your chance, last chance
- Real operator/provider names, real game titles, real faces, logos
- Gambling slang

Output ONLY valid JSON. No markdown fences. No explanation outside JSON.\
"""

# Terms that disqualify LLM output and trigger fallback.
FORBIDDEN_TEXT_TERMS: tuple[str, ...] = (
    "guaranteed",
    "you will definitely win",
    "don't miss",
    "last chance",
    "certain to win",
    "winners guaranteed",
)

SCENE_TYPE_ORDER: tuple[str, ...] = ("intro", "personalized_hook", "offer", "cta")


def build_user_prompt(
    first_name: str,
    country: str,
    currency: str,
    cohort: str,
    offer: str,
    game_label: str | None,
    game_category: str | None,
) -> str:
    visual_hint = get_visual_hint(game_label, game_category)
    return f"""\
Generate a reactivation script for this player.

Player: {first_name}, {country}, {currency}
Favourite activity: {game_category or "casino"} / {game_label or "general"}
Cohort: {cohort}
Offer: {offer}
Visual hint (use for visual_brief fields): {visual_hint}

Return exactly this JSON structure — no extra keys, no markdown:
{{
  "scenes": [
    {{"id": 1, "type": "intro",              "text": "...", "visual_brief": "..."}},
    {{"id": 2, "type": "personalized_hook",  "text": "...", "visual_brief": "..."}},
    {{"id": 3, "type": "offer",              "text": "...", "visual_brief": "..."}},
    {{"id": 4, "type": "cta",               "text": "...", "visual_brief": "..."}}
  ],
  "full_voiceover_text": "complete voiceover 70-110 words",
  "estimated_duration_sec": 38,
  "tone": "warm",
  "cta_text": "single CTA phrase"
}}

Constraints:
- Use {first_name} by name in the intro scene text.
- Reference {game_category or "their favourite activity"} naturally.
- Embed the offer "{offer}" in scene 3.
- visual_brief: abstract motion-graphics description, no text, no logos, no faces, no real brands.
- Voiceover 70-110 words total.
- No forbidden terms: {", ".join(FORBIDDEN_TEXT_TERMS)}\
"""
