"""
Evaluation harness for VibeFinder.

Runs a fixed set of test profiles through the scoring engine and checks that
the top result matches expectations. Prints a pass/fail summary with confidence scores.

Run with:
    python -m tests.eval_harness
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.recommender import load_songs, score_song, recommend_songs

DATA_PATH = "data/songs.csv"

# Each case: (label, user_prefs, expected_top_genre, expected_top_mood)
TEST_CASES = [
    (
        "Happy pop fan",
        {"genre": "pop", "mood": "happy", "energy": 0.85, "likes_acoustic": False},
        "pop", "happy",
    ),
    (
        "Chill lofi studier",
        {"genre": "lofi", "mood": "chill", "energy": 0.38, "likes_acoustic": True},
        "lofi", "chill",
    ),
    (
        "Intense rock listener",
        {"genre": "rock", "mood": "intense", "energy": 0.92, "likes_acoustic": False},
        "rock", "intense",
    ),
    (
        "Acoustic folk fan",
        {"genre": "folk", "mood": "relaxed", "energy": 0.30, "likes_acoustic": True},
        "folk", "relaxed",
    ),
    (
        "Late night R&B",
        {"genre": "r&b", "mood": "moody", "energy": 0.60, "likes_acoustic": False},
        "r&b", "moody",
    ),
    (
        "EDM/intense (edge case — small catalog)",
        {"genre": "edm", "mood": "intense", "energy": 0.95, "likes_acoustic": False},
        "edm", "intense",
    ),
]


def confidence_score(top_song: dict, user_prefs: dict) -> float:
    """
    Simple 0–1 confidence score based on how cleanly the top result matches.
    Full confidence = genre match + mood match + energy within 0.1.
    """
    points = 0.0
    if top_song["genre"].lower() == user_prefs["genre"].lower():
        points += 1.0
    if top_song["mood"].lower() == user_prefs["mood"].lower():
        points += 1.0
    if abs(top_song["energy"] - user_prefs["energy"]) <= 0.1:
        points += 1.0
    return round(points / 3.0, 2)


def run_harness() -> None:
    songs = load_songs(DATA_PATH)
    passed = 0
    total = len(TEST_CASES)

    print("\n" + "=" * 60)
    print("  VibeFinder Evaluation Harness")
    print("=" * 60)

    for label, prefs, exp_genre, exp_mood in TEST_CASES:
        results = recommend_songs(prefs, songs, k=5)
        top_song, top_score, top_explanation = results[0]

        genre_ok = top_song["genre"].lower() == exp_genre.lower()
        mood_ok = top_song["mood"].lower() == exp_mood.lower()
        conf = confidence_score(top_song, prefs)

        status = "PASS" if (genre_ok and mood_ok) else "FAIL"
        if status == "PASS":
            passed += 1

        print(f"\n[{status}] {label}")
        print(f"  Top result : {top_song['title']} by {top_song['artist']}")
        print(f"  Genre      : {top_song['genre']} (expected {exp_genre}) {'✓' if genre_ok else '✗'}")
        print(f"  Mood       : {top_song['mood']} (expected {exp_mood}) {'✓' if mood_ok else '✗'}")
        print(f"  Score      : {top_score:.2f}  |  Confidence: {conf:.2f}")
        print(f"  Reasons    : {top_explanation}")

    print("\n" + "=" * 60)
    print(f"  Results: {passed}/{total} passed")
    print(f"  Average confidence: {sum(confidence_score(recommend_songs(p, songs, k=1)[0][0], p) for _, p, *_ in TEST_CASES) / total:.2f}")
    print("=" * 60 + "\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    run_harness()
