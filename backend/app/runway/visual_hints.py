from typing import Optional

GAME_VISUAL_HINTS: dict[str, str] = {
    "fruit_slots": "abstract fruit-colored reel symbols, soft gold particles, cinematic motion, premium dark backdrop, no text, no logos",
    "neon_spins": "neon-lit abstract spinning discs, electric cyan and magenta light trails, futuristic dark backdrop, no text, no logos",
    "weekend_accas": "abstract matchday energy, flowing green lines and stadium-light geometry, no teams, no crowds, no text, no logos",
    "classic_roulette": "elegant roulette-inspired circular motion, red and black geometric arcs, soft reflections, no text, no logos",
    "starter_reels": "warm abstract reel shapes, gentle amber glow, soft particle rise, dark minimal backdrop, no text, no logos",
    "daily_rooms": "abstract interior ambient glow, soft gradient warm light, minimalist architectural geometry, no text, no logos",
    "high_limit_tables": "deep emerald felt-inspired abstract planes, gold filament lines, moody cinematic lighting, no text, no logos",
    "blackjack_tables": "abstract card-shaped silhouettes in emerald and gold, soft spotlight diffusion, dark backdrop, no text, no logos",
    "card_tables": "abstract playing-card suit symbols floating, subtle blue-felt texture lines, cinematic depth, no text, no logos",
    "wheel_games": "abstract concentric spinning rings, warm amber and crimson gradients, smooth rotational motion, no text, no logos",
    "jackpot_style_reels": "radiant golden burst patterns, shimmering abstract coin-shaped particles, premium dark setting, no text, no logos",
    "sports_matchday": "abstract athletic energy, flowing emerald and white streaks, stadium-light geometric beams, no text, no logos",
    "live_tables": "abstract broadcast-style ambient light, deep blue and gold shifting gradients, cinematic depth, no text, no logos",
    "arcade_instant": "vivid abstract pixel-burst patterns, rapid color flashes, digital grid underlay, no text, no logos",
    "scratch_cards": "abstract metallic shimmer layer, soft silver and copper particle drift, textured dark backdrop, no text, no logos",
    "lottery_draw": "abstract numbered sphere silhouettes in soft motion, gentle gold dust, deep navy backdrop, no text, no logos",
    "crash_style": "ascending abstract curve line, hot orange-to-red gradient trail, dark cosmic backdrop, no text, no logos",
    "poker_tables": "abstract deep green oval planes, soft spotlight halo, subtle chip-stack geometry, dark cinematic backdrop, no text, no logos",
}

CATEGORY_VISUAL_HINTS: dict[str, str] = {
    "slots": "abstract spinning reel shapes, colorful soft-edged symbols, ambient light trail, dark backdrop, no text, no logos",
    "live_casino": "abstract broadcast-lit interior, deep blue and gold ambient glow, cinematic depth, no text, no logos",
    "roulette": "elegant circular motion, red and black geometric arcs, soft reflections, no text, no logos",
    "blackjack": "abstract card silhouettes, emerald and gold tones, soft spotlight, dark backdrop, no text, no logos",
    "sportsbook": "abstract athletic energy, flowing emerald streaks, stadium-light geometry, no text, no logos",
    "football": "abstract pitch-inspired green geometry, flowing white line motion, stadium-light ambiance, no text, no logos",
    "bingo": "abstract numbered sphere grid, soft pastel color clusters, gentle dot-pattern overlay, no text, no logos",
    "table_games": "abstract green felt-inspired planes, warm amber light diffusion, cinematic shadows, no text, no logos",
    "cards": "abstract card-suit symbols floating, subtle blue-felt texture, cinematic depth, no text, no logos",
    "instant_games": "vivid abstract color burst, rapid digital flash patterns, dark minimal backdrop, no text, no logos",
    "poker": "abstract deep green oval planes, chip-stack geometry, soft spotlight halo, no text, no logos",
    "lottery": "abstract sphere silhouettes in soft orbit, gold dust particles, deep navy backdrop, no text, no logos",
}

DEFAULT_VISUAL_HINT: str = "abstract premium motion-graphics, soft golden particle flow, cinematic dark backdrop, no text, no logos"


def get_visual_hint(game_label: Optional[str], game_category: Optional[str] = None) -> str:
    if game_label and game_label in GAME_VISUAL_HINTS:
        return GAME_VISUAL_HINTS[game_label]
    if game_category and game_category in CATEGORY_VISUAL_HINTS:
        return CATEGORY_VISUAL_HINTS[game_category]
    return DEFAULT_VISUAL_HINT