"""
Command line runner for the Music Recommender Simulation.

Run with:
    python -m src.main
"""

try:
    from src.recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs


def print_recommendations(label: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    """Print the top-k recommendations for a given user profile."""
    print(f"\n{'='*55}")
    print(f"  Profile: {label}")
    print(f"  Prefs:   genre={user_prefs['genre']}, mood={user_prefs['mood']}, energy={user_prefs['energy']}")
    print(f"{'='*55}")
    results = recommend_songs(user_prefs, songs, k=k)
    for rank, (song, score, explanation) in enumerate(results, start=1):
        print(f"  {rank}. {song['title']} by {song['artist']}")
        print(f"     Score: {score:.2f}  |  {explanation}")
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")

    profiles = [
        ("High-Energy Pop", {"genre": "pop",     "mood": "happy",    "energy": 0.85, "likes_acoustic": False}),
        ("Chill Lofi",      {"genre": "lofi",    "mood": "chill",    "energy": 0.38, "likes_acoustic": True}),
        ("Deep Intense Rock",{"genre": "rock",   "mood": "intense",  "energy": 0.92, "likes_acoustic": False}),
        ("Late Night R&B",  {"genre": "r&b",     "mood": "moody",    "energy": 0.60, "likes_acoustic": False}),
        ("Acoustic Folk",   {"genre": "folk",    "mood": "relaxed",  "energy": 0.30, "likes_acoustic": True}),
    ]

    for label, prefs in profiles:
        print_recommendations(label, prefs, songs)


if __name__ == "__main__":
    main()
