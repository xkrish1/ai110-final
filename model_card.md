# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

VibeFinder is designed to suggest 3–5 songs from a small catalog based on a user's stated genre preference, mood, and energy level. It is built for classroom exploration of how content-based recommenders work—not for deployment to real users. It should not be used to make decisions about licensing, artist promotion, or real listener data.

---

## 3. How the Model Works

When you tell VibeFinder your favorite genre, the mood you're in, and how high-energy you want the music to feel, it goes through every song in the catalog and gives each one a score. A song earns the most points for matching your genre (the strongest signal of musical identity), a smaller bonus for matching your mood, and a sliding score based on how close its energy level is to yours—close energy earns almost a full point, distant energy earns almost nothing. There are two small bonus points available: one if you prefer acoustic sounds and the song is mostly acoustic, and one if the song has a bright and positive musical feel. Once every song has a score, the list is sorted from highest to lowest and the top five are returned with a plain-English note explaining exactly which rules fired.

---

## 4. Data

The catalog contains **20 songs** stored in `data/songs.csv`. Genres represented include: pop, lofi, rock, ambient, jazz, synthwave, indie pop, EDM, country, hip-hop, classical, metal, folk, and R&B. Moods include: happy, chill, intense, relaxed, focused, moody, confident, and melancholy. The dataset was expanded from 10 to 20 songs to improve genre diversity. It still skews toward English-language Western genres; styles like afrobeats, K-pop, bossa nova, and Bollywood are entirely absent. Every song has equal weight regardless of real-world popularity.

---

## 5. Strengths

- For users who know exactly what genre and mood they want, the top result almost always feels correct. The "Chill Lofi" profile consistently surfaced the two quietest lofi tracks with near-perfect scores.
- The explanation system is fully transparent—every point is traced back to a specific rule, so users (and developers) can immediately see why a song ranked where it did.
- The energy similarity calculation avoids the trap of just rewarding "more energy is better." A user who wants low energy (0.3) correctly gets low-energy songs at the top.

---

## 6. Limitations and Bias

- **Genre string matching is brittle.** "indie pop" and "pop" score zero for a genre match even though they are close in practice. A user searching for pop music misses Rooftop Lights entirely unless they exactly type "indie pop."
- **The valence bonus favors happy music unconditionally.** Every profile gets a small push toward songs with valence > 0.7, even the "Late Night R&B / moody" profile. This is a mild but consistent bias toward positivity.
- **Catalog imbalance creates a filter bubble.** Pop songs make up 3 out of 20 entries. Genres with only one representative (metal, country, classical) will never produce a diverse top-5 list for users who prefer those styles.
- **No personalization over time.** The system treats every session as if the user has no history. Real recommenders improve as they accumulate behavioral signals; this one stays static.

---

## 7. Evaluation

Five distinct user profiles were tested:

| Profile | Top Song | Score | Intuition check |
|---|---|---|---|
| High-Energy Pop | Sunrise City | 4.47 | Correct — pop, happy, energy 0.82 ≈ target 0.85 |
| Chill Lofi | Library Rain | 4.47 | Correct — lofi, chill, acoustic, energy 0.35 ≈ 0.38 |
| Deep Intense Rock | Storm Runner | 3.99 | Correct — rock, intense, energy 0.91 ≈ 0.92 |
| Late Night R&B | Late Night FM | 3.99 | Correct — only R&B song in catalog |
| Acoustic Folk | Campfire Song | 4.99 | Correct — folk, relaxed, acoustic, positive |

**Surprising result:** The Late Night R&B profile's top song scored 3.99 but its second-place song (Night Drive Loop, synthwave/moody) scored only 1.85—a huge gap. This is because there is only one R&B song. Real systems would surface more genre variety; VibeFinder falls back to energy/mood proximity for slots 2–5, which works but feels thin.

**Weight experiment:** Doubling energy weight and halving genre weight caused Gym Hero to overtake Sunrise City for the pop profile. The moral: small weight changes cascade quickly with a 20-song catalog.

---

## 8. Future Work

1. **Fuzzy genre matching** — map related genres (indie pop → pop, synthwave → electronic) so users don't miss near-miss songs.
2. **Diversity injection** — after scoring, enforce that the top-5 list cannot contain more than two songs from the same genre, improving variety.
3. **Behavioral feedback loop** — let the user mark recommendations as "liked" or "skipped" and adjust weights dynamically, moving toward a hybrid collaborative + content model.

---

## 9. AI Collaboration

**How AI was used during this project:**
AI (Claude) was used throughout — for designing the agentic loop architecture, writing the tool-use scaffolding in `agent.py`, drafting the RAG knowledge documents, and building the eval harness. It also served as a real-time debugging partner when the `.env` key wasn't loading and when Streamlit import paths conflicted between `run src/app.py` and direct execution.

**One instance where AI gave a helpful suggestion:**
When building the eval harness, Claude suggested separating `confidence_score()` into its own function rather than inlining it in the print loop. That made the metric reusable across test cases and easier to average at the end — a clean structural improvement that I wouldn't have thought to do immediately.

**One instance where AI's suggestion was flawed:**
Claude initially generated the `score_songs` tool schema with `"energy": {"type": "string"}` instead of `"type": "number"}`. This would have silently broken the scoring math — Python would have received a string like `"0.85"` and the subtraction `abs(song["energy"] - target_energy)` would have thrown a TypeError at runtime. Always verify tool schema types manually; the AI does not automatically catch type mismatches between the schema and the actual function logic.

---

## 10. Personal Reflection

Building this recommender made the "black box" feeling of Spotify Discover Weekly feel much more concrete. Even a 5-rule scoring function on 20 songs produces results that genuinely feel personalized — which explains why real platforms with millions of signals and thousands of features feel almost magical. The most surprising moment was discovering how much the valence bonus subtly shaped every profile toward brighter songs; I had added it as a small aesthetic touch but it ended up acting like an invisible thumb on the scale. That's a real lesson: every design choice in a scoring function is an implicit value judgment about what "good music" means, and those judgments compound. Human oversight still matters because no scoring formula can capture the context of why someone wants a particular song at a particular moment — that's still a domain only the listener understands.
