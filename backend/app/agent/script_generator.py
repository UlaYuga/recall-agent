from app.agent.offers import select_offer


def generate_script(player_name: str, cohort: str) -> dict[str, str]:
    offer = select_offer(cohort)
    return {
        "script": f"Hi {player_name}, we made a short personal update for you. {offer}.",
        "cta": "See what's new",
        "visual_prompt": "abstract premium motion graphics, warm welcome-back tone, no text, no logos",
    }

