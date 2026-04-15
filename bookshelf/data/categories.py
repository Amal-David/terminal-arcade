"""Genre and mood definitions for the bookshelf."""

GENRES = {
    "motivation": {
        "label": "Motivation",
        "icon": "★",
        "description": "Self-help, personal growth, and life philosophy",
    },
    "startup": {
        "label": "Startup",
        "icon": "◆",
        "description": "Business, entrepreneurship, and innovation",
    },
    "romance": {
        "label": "Romance",
        "icon": "♥",
        "description": "Love stories, relationships, and the heart",
    },
    "fiction": {
        "label": "Fiction",
        "icon": "✦",
        "description": "Literary fiction, classics, sci-fi, fantasy, and thrillers",
    },
    "science": {
        "label": "Science",
        "icon": "◎",
        "description": "Physics, biology, technology, and the natural world",
    },
    "philosophy": {
        "label": "Philosophy",
        "icon": "◇",
        "description": "Ancient wisdom, existentialism, ethics, and the examined life",
    },
    "psychology": {
        "label": "Psychology",
        "icon": "◈",
        "description": "The mind, behavior, decision-making, and human nature",
    },
    "history": {
        "label": "History",
        "icon": "▣",
        "description": "World events, civilizations, wars, and the story of humanity",
    },
}

GENRE_ORDER = ["all", "motivation", "startup", "romance", "fiction", "science", "philosophy", "psychology", "history"]

MOODS = [
    "hustle mode",
    "rainy afternoon",
    "cozy night",
    "fresh start",
    "beach read",
    "commute listen",
    "Sunday morning",
    "late night reflection",
    "morning ritual",
    "gym session",
    "career pivot",
    "existential crisis",
    "butterflies",
    "ugly cry",
    "slow burn",
    "summer vibes",
    "winter blanket",
    "road trip",
    "heartbreak recovery",
    "boardroom energy",
    "founder mode",
    "scaling up",
    "side project vibes",
    "productivity",
    "daily grind",
    "self-discovery",
]

# Context-matching tags for quotes (used by the agent skill)
CONTEXT_TAGS = [
    "perseverance",
    "ambition",
    "love",
    "heartbreak",
    "courage",
    "wisdom",
    "humor",
    "creativity",
    "leadership",
    "failure",
    "success",
    "change",
    "growth",
    "fear",
    "discipline",
    "focus",
    "relationships",
    "money",
    "time",
    "death",
    "happiness",
    "solitude",
    "friendship",
    "self-discovery",
    "resilience",
    "patience",
    "innovation",
    "risk",
    "simplicity",
    "authenticity",
    "vulnerability",
]

# Mapping from coding context keywords to quote tags
# Used by the ambient quote system to pick relevant quotes
CONTEXT_MAP = {
    # Debugging / fixing bugs
    "error": ["perseverance", "resilience", "patience"],
    "bug": ["perseverance", "resilience", "patience"],
    "fix": ["perseverance", "growth", "resilience"],
    "debug": ["patience", "perseverance", "focus"],
    "fail": ["failure", "resilience", "courage"],
    "broken": ["perseverance", "resilience", "change"],
    # Building / creating
    "create": ["creativity", "ambition", "innovation"],
    "build": ["ambition", "creativity", "growth"],
    "new": ["change", "innovation", "courage"],
    "feature": ["creativity", "ambition", "innovation"],
    "design": ["creativity", "simplicity", "innovation"],
    # Testing
    "test": ["discipline", "focus", "perseverance"],
    "pass": ["success", "growth", "happiness"],
    "assert": ["discipline", "focus", "courage"],
    # Shipping / deploying
    "deploy": ["courage", "risk", "ambition"],
    "ship": ["ambition", "courage", "success"],
    "release": ["courage", "success", "growth"],
    "push": ["ambition", "courage", "risk"],
    "merge": ["relationships", "growth", "change"],
    # Refactoring
    "refactor": ["simplicity", "growth", "change"],
    "clean": ["simplicity", "discipline", "focus"],
    "optimize": ["focus", "discipline", "growth"],
    # Collaboration
    "review": ["wisdom", "growth", "relationships"],
    "comment": ["relationships", "wisdom", "patience"],
    "team": ["leadership", "relationships", "friendship"],
    # Late night coding
    "midnight": ["solitude", "perseverance", "focus"],
    "tired": ["resilience", "perseverance", "patience"],
    # Success moments
    "done": ["success", "happiness", "growth"],
    "complete": ["success", "happiness", "ambition"],
    "works": ["success", "happiness", "perseverance"],
}
