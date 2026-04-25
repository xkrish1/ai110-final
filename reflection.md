# Reflection: Profile Comparisons

## High-Energy Pop vs. Deep Intense Rock

Both profiles target high energy (0.85 vs 0.92) but diverge completely at genre. The pop profile's top 3 are all pop or indie-pop with happy/intense moods and valence above 0.77. The rock profile's top result is the only rock song—Storm Runner—and then falls through to non-rock high-energy songs like Gym Hero and Drop It Hard. This makes sense: energy alone doesn't define a genre's "feel," and the genre weight correctly separates them at the top while energy similarity handles the rest of the list.

## Chill Lofi vs. Acoustic Folk

Both profiles want low energy and acoustic sounds, but they land in completely different corners. The lofi profile rewards genre-specific tracks (Library Rain, Midnight Coding) which are electronic-adjacent and studio-produced, even though they score high on acousticness. The folk profile picks up Campfire Song with a near-perfect score because it matches genre, mood, energy, acousticness, AND valence simultaneously. The key insight: two "quiet" profiles can point to very different music depending on which genre tag the user supplies. A real system using collaborative filtering would surface even finer distinctions—e.g., the difference between lo-fi hip-hop listeners and Appalachian folk listeners is obvious in behavioral data but invisible to a pure string-match genre check.

## Late Night R&B vs. High-Energy Pop

These profiles share nothing. The R&B profile wants moody, mid-energy (0.60) songs; the pop profile wants happy, high-energy (0.85) songs. Predictably, their top-5 lists have zero overlap. The R&B profile's list drops steeply after the first song because the catalog has only one R&B entry, and the fallback (energy + mood similarity) pulls in Night Drive Loop (synthwave/moody) and then a cluster of high-valence pop songs that happen to have mid-range energy—not a great fit. This exposes the catalog imbalance problem more clearly than any other pair.

## EDM vs. Acoustic Folk (edge case)

I tested an adversarial profile: EDM, intense, energy 0.95, likes_acoustic=False. The top 3 were Drop It Hard (EDM, 0.95), Broken Glass (metal, 0.96), and Gym Hero (pop, 0.93). EDM gets the genre match; metal and pop sneak in purely on energy proximity. The acoustic folk list has zero overlap. This confirms the system correctly separates "high-energy electronic" from "low-energy acoustic"—but also shows that once you leave the genre match, the fallback is just "nearest energy," which might feel random to a real user.
