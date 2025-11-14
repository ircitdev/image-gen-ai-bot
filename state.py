from collections import defaultdict

user_state = defaultdict(lambda: {
    "prompt": "",
    "images": [],
    "format": None,
    "shot": None,
    "angle": None,
    "style": None,
    "lighting": None,
    "quality": None
})
