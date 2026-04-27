"""
Agentic recommendation loop powered by Claude.

Flow:
  1. User describes what they want in natural language.
  2. Claude calls `score_songs` tool to get scored candidates.
  3. Claude calls `get_genre_knowledge` tool to retrieve RAG context.
  4. Claude writes a conversational explanation of its picks.
  5. User can give feedback; Claude refines in a follow-up turn.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv

try:
    from src.recommender import load_songs, score_song
except ModuleNotFoundError:
    from recommender import load_songs, score_song

load_dotenv()
logging.basicConfig(
    filename="agent.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"
DATA_PATH = Path(__file__).parent.parent / "data" / "songs.csv"

GENRE_TO_FILE = {
    "pop": "pop.md",
    "indie pop": "pop.md",
    "lofi": "lofi.md",
    "rock": "rock.md",
    "metal": "rock.md",
    "ambient": "ambient.md",
    "hip-hop": "hiphop.md",
    "r&b": "hiphop.md",
    "folk": "folk.md",
    "country": "folk.md",
    "jazz": "folk.md",
    "synthwave": "pop.md",
    "edm": "edm.md",
    "classical": "ambient.md",
}

SYSTEM_PROMPT = """You are VibeFinder, a friendly music recommendation assistant. \
Your personality is warm, enthusiastic, and concise — like a friend who knows a lot about music.

You have two tools available:
- score_songs: call this with a user preference dict to get a ranked list of songs from the catalog.
- get_genre_knowledge: call this with a genre name to get background knowledge that helps you explain picks.

IMPORTANT — mood must be one of these exact values from the catalog:
happy, chill, intense, relaxed, focused, moody, confident, melancholy
Map the user's words to the closest catalog mood before calling score_songs.
Examples: "energetic" → "intense", "sad" → "melancholy", "peaceful" → "chill", "pumped up" → "intense"

Rules:
1. Always call score_songs first before making any recommendations.
2. After scoring, call get_genre_knowledge for the user's preferred genre to enrich your explanation.
3. Present exactly the top 3 recommendations by default (top 5 if the user asks for more).
4. For each song, give ONE sentence explaining why it fits — mention the specific signals (genre match, energy, mood).
5. Never make up songs that aren't in the tool results.
6. If the user gives feedback like "too intense" or "something more chill", call score_songs again \
   with adjusted preferences and explain what you changed.
7. Keep responses under 200 words unless the user asks for more detail.

Few-shot style examples:
Q: "I want something chill to study to"
A: "Here are 3 picks to keep you in the zone:
   1. **Library Rain** — perfect lofi match: low energy (0.35), chill mood, and high acousticness makes it ideal background noise.
   2. **Midnight Coding** — same lofi DNA, slightly more energy (0.42) if you need a gentle beat to stay awake.
   3. **Focus Flow** — labeled 'focused' rather than 'chill' but the numbers are nearly identical, great for deep work."

Q: "Give me something to hype me up"
A: "Turning the dial to 11:
   1. **Drop It Hard** — EDM at 0.95 energy, 140 BPM, built for maximum intensity.
   2. **Broken Glass** — metal, 0.96 energy — the most aggressive track in the catalog.
   3. **Gym Hero** — pop/intense at 0.93, more melodic than the others but still a serious energy boost."
"""

TOOLS = [
    {
        "name": "score_songs",
        "description": (
            "Score all songs in the catalog against user preferences and return the top-k results. "
            "Returns a list of dicts with keys: title, artist, genre, mood, energy, score, explanation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {"type": "string", "description": "User's preferred genre"},
                "mood": {"type": "string", "description": "User's preferred mood"},
                "energy": {"type": "number", "description": "Target energy level 0.0–1.0"},
                "likes_acoustic": {"type": "boolean", "description": "Whether user prefers acoustic sounds"},
                "k": {"type": "integer", "description": "Number of results to return (default 5)"},
            },
            "required": ["genre", "mood", "energy"],
        },
    },
    {
        "name": "get_genre_knowledge",
        "description": "Retrieve background knowledge about a genre to inform recommendation explanations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {"type": "string", "description": "Genre name to look up"},
            },
            "required": ["genre"],
        },
    },
]


def _run_score_songs(prefs: dict) -> list[dict]:
    """Execute score_songs tool call against the real catalog."""
    songs = load_songs(str(DATA_PATH))
    k = prefs.pop("k", 5)
    results = []
    for song in songs:
        score, explanation = score_song(prefs, song)
        results.append({
            "title": song["title"],
            "artist": song["artist"],
            "genre": song["genre"],
            "mood": song["mood"],
            "energy": song["energy"],
            "score": round(score, 2),
            "explanation": explanation,
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:k]


def _run_get_genre_knowledge(genre: str) -> str:
    """Retrieve RAG document for a genre."""
    filename = GENRE_TO_FILE.get(genre.lower())
    if not filename:
        return f"No specific knowledge available for '{genre}'. Use general music intuition."
    path = KNOWLEDGE_DIR / filename
    if not path.exists():
        return f"Knowledge file {filename} not found."
    return path.read_text(encoding="utf-8")


def _dispatch_tool(tool_name: str, tool_input: dict) -> str:
    """Route a tool call to the correct function and return JSON string result."""
    logger.info("Tool call: %s | input: %s", tool_name, tool_input)
    if tool_name == "score_songs":
        result = _run_score_songs(tool_input)
        return json.dumps(result)
    if tool_name == "get_genre_knowledge":
        result = _run_get_genre_knowledge(tool_input["genre"])
        return result
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


class MusicAgent:
    """
    Stateful agentic conversation loop.
    Maintains message history so the user can give follow-up feedback.
    """

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and add your key."
            )
        self.client = anthropic.Anthropic(api_key=api_key)
        self.history: list[dict] = []
        self.steps: list[dict] = []  # visible reasoning steps for UI

    def chat(self, user_message: str) -> str:
        """
        Send a user message, run the agentic tool loop, return final text response.
        Also populates self.steps with intermediate reasoning for display.
        """
        self.steps = []
        self.history.append({"role": "user", "content": user_message})
        logger.info("User: %s", user_message)

        while True:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.history,
            )
            logger.info("Claude stop_reason: %s", response.stop_reason)

            # Collect any text blocks for streaming display
            text_parts = [b.text for b in response.content if b.type == "text"]

            if response.stop_reason == "end_turn":
                final_text = "\n".join(text_parts)
                self.history.append({"role": "assistant", "content": response.content})
                logger.info("Assistant: %s", final_text[:200])
                return final_text

            if response.stop_reason == "tool_use":
                # Record assistant message with tool_use blocks
                self.history.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    step = {"tool": block.name, "input": block.input}
                    result_str = _dispatch_tool(block.name, dict(block.input))

                    # Parse for display
                    try:
                        step["output"] = json.loads(result_str)
                    except json.JSONDecodeError:
                        step["output"] = result_str[:300]

                    self.steps.append(step)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

                self.history.append({"role": "user", "content": tool_results})
                continue

            # Unexpected stop reason — return whatever text we have
            logger.warning("Unexpected stop_reason: %s", response.stop_reason)
            return "\n".join(text_parts) or "Something went wrong. Please try again."

    def reset(self) -> None:
        """Clear conversation history for a new session."""
        self.history = []
        self.steps = []
        logger.info("Session reset")
