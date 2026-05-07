def select_offer(cohort: str) -> str:
    offers = {
        "high_value_dormant": "Personal welcome-back gift",
        "long_dormant": "New features preview",
        "warm_dormant": "Friendly check-in",
    }
    return offers.get(cohort, "No offer")

