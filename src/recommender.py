import csv
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class Song:
    """Represents a song and its audio/genre attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """Represents a user's taste preferences for recommendations."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool


def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file and return a list of dicts with typed values."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    print(f"Loaded songs: {len(songs)}")
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, str]:
    """
    Score a single song against user preferences and return (score, explanation).

    Scoring recipe:
      +2.0  genre match
      +1.0  mood match
      +1.0  energy similarity  (1 - |song_energy - target_energy|)
      +0.5  acousticness bonus when user likes_acoustic and song acousticness > 0.6
      +0.5  valence bonus when song valence > 0.7 (bright / positive feel)
    """
    score = 0.0
    reasons = []

    if song["genre"].lower() == user_prefs.get("genre", "").lower():
        score += 2.0
        reasons.append("genre match (+2.0)")

    if song["mood"].lower() == user_prefs.get("mood", "").lower():
        score += 1.0
        reasons.append("mood match (+1.0)")

    target_energy = user_prefs.get("energy", 0.5)
    energy_sim = 1.0 - abs(song["energy"] - target_energy)
    score += energy_sim
    reasons.append(f"energy similarity (+{energy_sim:.2f})")

    if user_prefs.get("likes_acoustic", False) and song["acousticness"] > 0.6:
        score += 0.5
        reasons.append("acoustic match (+0.5)")

    if song["valence"] > 0.7:
        score += 0.5
        reasons.append("positive vibe (+0.5)")

    explanation = ", ".join(reasons)
    return score, explanation


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score all songs against user preferences and return the top-k sorted by score."""
    scored = []
    for song in songs:
        score, explanation = score_song(user_prefs, song)
        scored.append((song, score, explanation))

    scored = sorted(scored, key=lambda x: x[1], reverse=True)
    return scored[:k]


def _score_song_oop(user: UserProfile, song: Song) -> Tuple[float, str]:
    """OOP variant of score_song used by the Recommender class."""
    score = 0.0
    reasons = []

    if song.genre.lower() == user.favorite_genre.lower():
        score += 2.0
        reasons.append("genre match (+2.0)")

    if song.mood.lower() == user.favorite_mood.lower():
        score += 1.0
        reasons.append("mood match (+1.0)")

    energy_sim = 1.0 - abs(song.energy - user.target_energy)
    score += energy_sim
    reasons.append(f"energy similarity (+{energy_sim:.2f})")

    if user.likes_acoustic and song.acousticness > 0.6:
        score += 0.5
        reasons.append("acoustic match (+0.5)")

    if song.valence > 0.7:
        score += 0.5
        reasons.append("positive vibe (+0.5)")

    return score, ", ".join(reasons)


class Recommender:
    """OOP implementation of the recommendation logic."""

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs ranked by score for the given user profile."""
        scored = sorted(
            self.songs,
            key=lambda song: _score_song_oop(user, song)[0],
            reverse=True,
        )
        return scored[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why this song was recommended."""
        _, explanation = _score_song_oop(user, song)
        return explanation
