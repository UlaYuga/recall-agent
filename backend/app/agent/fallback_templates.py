FALLBACK_TEMPLATES: dict[str, dict] = {
    "casual_dormant": {
        "tone": "Warm, light, welcoming, and low-pressure.",
        "estimated_duration_sec": 38,
        "cta_text": "{cta}",
        "scenes": [
            {
                "id": 1,
                "type": "intro",
                "text": "Hi {first_name}, here is a short personal update made with your recent activity in mind.",
                "visual_brief": "abstract motion graphics inspired by {favorite_game_visual_hint}, soft glow, calm movement, no text, brand-free",
            },
            {
                "id": 2,
                "type": "personalized_hook",
                "text": "We remembered the style and pace you seemed to enjoy in your favorite area, so this message keeps things simple and familiar.",
                "visual_brief": "layered abstract shapes echoing {favorite_game_visual_hint}, smooth transitions, premium atmosphere, no text, brand-free",
            },
            {
                "id": 3,
                "type": "offer",
                "text": "There is a tailored offer waiting for you: {offer_value}, prepared as a gentle welcome back when you feel ready to take a look.",
                "visual_brief": "refined abstract highlights and rhythmic motion around {favorite_game_visual_hint}, clean composition, no text, brand-free",
            },
            {
                "id": 4,
                "type": "cta",
                "text": "When you are ready, {cta}.",
                "visual_brief": "focused abstract close with warm light and subtle motion, no text, brand-free",
            },
        ],
        "full_voiceover_text": (
            "Hi {first_name}, here is a short personal update made with your recent activity in mind. "
            "We remembered the style and pace you seemed to enjoy in your favorite area, with details shaped by {favorite_game_visual_hint}. "
            "To make your return feel straightforward, we prepared a tailored offer for you: {offer_value}. "
            "This is simply a warm welcome back and a clear reason to take another look when it suits you. "
            "When you are ready, {cta}."
        ),
    },
    "high_value_dormant": {
        "tone": "Polished, respectful, and premium without pressure.",
        "estimated_duration_sec": 40,
        "cta_text": "{cta}",
        "scenes": [
            {
                "id": 1,
                "type": "intro",
                "text": "Hello {first_name}, this is a short personal update prepared with care around your recent activity.",
                "visual_brief": "premium abstract motion inspired by {favorite_game_visual_hint}, elegant contrast, measured pacing, no text, brand-free",
            },
            {
                "id": 2,
                "type": "personalized_hook",
                "text": "Your preferred rhythm and style stood out, so we built this message to feel considered, calm, and relevant to your favorite area.",
                "visual_brief": "sleek abstract layers reflecting {favorite_game_visual_hint}, restrained shimmer, no text, brand-free",
            },
            {
                "id": 3,
                "type": "offer",
                "text": "We have set aside a tailored offer for you, including {offer_value}, designed to make your next session feel easy to review.",
                "visual_brief": "structured abstract composition with subtle highlights and motion linked to {favorite_game_visual_hint}, no text, brand-free",
            },
            {
                "id": 4,
                "type": "cta",
                "text": "When the timing feels right, {cta}.",
                "visual_brief": "clean abstract finish with steady motion and soft premium lighting, no text, brand-free",
            },
        ],
        "full_voiceover_text": (
            "Hello {first_name}, this is a short personal update prepared with care around your recent activity. "
            "Your preferred rhythm and style stood out, and the look of {favorite_game_visual_hint} reflects the atmosphere you seemed to enjoy most. "
            "To welcome you back in a clear and thoughtful way, we set aside a tailored offer that includes {offer_value}. "
            "Everything about this message is meant to stay simple, relevant, and easy to review on your terms. "
            "When the timing feels right, {cta}."
        ),
    },
    "post_event": {
        "tone": "Timely, upbeat, and smoothly transitional.",
        "estimated_duration_sec": 39,
        "cta_text": "{cta}",
        "scenes": [
            {
                "id": 1,
                "type": "intro",
                "text": "Hi {first_name}, after your recent activity, we wanted to share a short personal update while everything still feels familiar.",
                "visual_brief": "dynamic abstract motion based on {favorite_game_visual_hint}, bright accents, fluid transitions, no text, brand-free",
            },
            {
                "id": 2,
                "type": "personalized_hook",
                "text": "The energy of your favorite area gave us a clear sense of what you respond to, so we kept this message direct and relevant.",
                "visual_brief": "energetic abstract pulses and shapes linked to {favorite_game_visual_hint}, balanced composition, no text, brand-free",
            },
            {
                "id": 3,
                "type": "offer",
                "text": "As a follow-up, we prepared a tailored offer for you: {offer_value}, ready to review whenever you want a closer look.",
                "visual_brief": "abstract momentum lines and soft luminous accents around {favorite_game_visual_hint}, no text, brand-free",
            },
            {
                "id": 4,
                "type": "cta",
                "text": "If you want to continue from there, {cta}.",
                "visual_brief": "confident abstract end frame with smooth settling motion, no text, brand-free",
            },
        ],
        "full_voiceover_text": (
            "Hi {first_name}, after your recent activity, we wanted to share a short personal update while everything still feels familiar. "
            "The energy and flow you seemed to enjoy most, reflected here through {favorite_game_visual_hint}, helped shape a message that stays direct and relevant. "
            "As a simple follow-up, we prepared a tailored offer for you: {offer_value}. "
            "It is meant to give you a clear next step without pressure, just a useful reason to revisit when you feel ready. "
            "If you want to continue from there, {cta}."
        ),
    },
    "first_deposit_no_return": {
        "tone": "Reassuring, clear, and easygoing for early re-engagement.",
        "estimated_duration_sec": 41,
        "cta_text": "{cta}",
        "scenes": [
            {
                "id": 1,
                "type": "intro",
                "text": "Hi {first_name}, we put together a short personal update because your recent activity suggested there may be more you would enjoy exploring.",
                "visual_brief": "welcoming abstract motion built from {favorite_game_visual_hint}, gentle light, steady movement, no text, brand-free",
            },
            {
                "id": 2,
                "type": "personalized_hook",
                "text": "You already showed interest in a certain style, so we kept this message focused on the part of the experience that felt most natural for you.",
                "visual_brief": "abstract pathways and layered motion echoing {favorite_game_visual_hint}, clean framing, no text, brand-free",
            },
            {
                "id": 3,
                "type": "offer",
                "text": "To make the next step easier, we prepared a tailored offer with {offer_value}, ready for you to review at your own pace.",
                "visual_brief": "abstract highlights and measured movement centered on {favorite_game_visual_hint}, no text, brand-free",
            },
            {
                "id": 4,
                "type": "cta",
                "text": "Whenever it suits you, {cta}.",
                "visual_brief": "calm abstract closing motion with a clear focal point, no text, brand-free",
            },
        ],
        "full_voiceover_text": (
            "Hi {first_name}, we put together a short personal update because your recent activity suggested there may be more you would enjoy exploring. "
            "You already showed interest in a certain style, and the feel of {favorite_game_visual_hint} matches the area that seemed most natural for you. "
            "To make the next step easier, we prepared a tailored offer with {offer_value}. "
            "The idea is to keep your return simple, comfortable, and fully on your timing, with one clear next action when you want it. "
            "Whenever it suits you, {cta}."
        ),
    },
    "vip_at_risk": {
        "tone": "Attentive, elevated, and relationship-focused.",
        "estimated_duration_sec": 40,
        "cta_text": "{cta}",
        "scenes": [
            {
                "id": 1,
                "type": "intro",
                "text": "Hello {first_name}, this is a short personal update shaped around your recent activity and the standards you usually expect.",
                "visual_brief": "elevated abstract motion influenced by {favorite_game_visual_hint}, rich texture, controlled pacing, no text, brand-free",
            },
            {
                "id": 2,
                "type": "personalized_hook",
                "text": "We paid attention to the atmosphere and style you favor most, so this message stays selective, calm, and personal.",
                "visual_brief": "luxury abstract gradients and structured motion inspired by {favorite_game_visual_hint}, no text, brand-free",
            },
            {
                "id": 3,
                "type": "offer",
                "text": "A tailored offer has been prepared for you, including {offer_value}, to make it easier to reconnect on terms that feel worthwhile.",
                "visual_brief": "polished abstract highlights with deliberate motion around {favorite_game_visual_hint}, no text, brand-free",
            },
            {
                "id": 4,
                "type": "cta",
                "text": "When you would like to check the details, {cta}.",
                "visual_brief": "premium abstract resolution with warm depth and minimal motion, no text, brand-free",
            },
        ],
        "full_voiceover_text": (
            "Hello {first_name}, this is a short personal update shaped around your recent activity and the standards you usually expect. "
            "We paid attention to the atmosphere and style you favor most, and {favorite_game_visual_hint} reflects that familiar direction in a clean, understated way. "
            "To support a smooth return, a tailored offer has been prepared for you, including {offer_value}. "
            "The message is intentionally simple and respectful, with one clear next step whenever the timing feels appropriate for you. "
            "When you would like to check the details, {cta}."
        ),
    },
    "lapsed_loyal": {
        "tone": "Appreciative, familiar, and steady.",
        "estimated_duration_sec": 39,
        "cta_text": "{cta}",
        "scenes": [
            {
                "id": 1,
                "type": "intro",
                "text": "Hi {first_name}, we wanted to share a short personal update for you because your recent activity still gives us a clear sense of your preferences.",
                "visual_brief": "familiar abstract motion drawn from {favorite_game_visual_hint}, warm tones, smooth pacing, no text, brand-free",
            },
            {
                "id": 2,
                "type": "personalized_hook",
                "text": "You spent time in a favorite area with a recognizable style, so we kept this message warm, direct, and easy to follow.",
                "visual_brief": "soft abstract loops and layered forms related to {favorite_game_visual_hint}, balanced motion, no text, brand-free",
            },
            {
                "id": 3,
                "type": "offer",
                "text": "As a welcome back gesture, we prepared a tailored offer for you: {offer_value}, ready whenever you want to review it.",
                "visual_brief": "abstract glow and repeating motion motifs around {favorite_game_visual_hint}, tidy composition, no text, brand-free",
            },
            {
                "id": 4,
                "type": "cta",
                "text": "When you feel ready to reconnect, {cta}.",
                "visual_brief": "settled abstract close with warm light and gentle motion, no text, brand-free",
            },
        ],
        "full_voiceover_text": (
            "Hi {first_name}, we wanted to share a short personal update for you because your recent activity still gives us a clear sense of your preferences. "
            "You spent time in a favorite area with a recognizable style, and {favorite_game_visual_hint} helps echo that familiar mood. "
            "As a welcome back gesture, we prepared a tailored offer for you: {offer_value}. "
            "The goal is to make reconnecting feel simple and considered, with a message that respects your pace and keeps the next step clear. "
            "When you feel ready to reconnect, {cta}."
        ),
    },
}
