llama.cpp's server works this way. A request's schema becomes a grammar, and before each token is chosen, every token the grammar rejects gets a score of minus infinity, and the end of the reply too until the grammar is complete. Checking every token of the vocabulary at every step takes time in proportion to the vocabulary's size, which is why libraries such as Outlines work out in advance, for each point a reply can reach, which tokens can follow it.

The tests showed what that guarantees and what it doesn't:

- Every reply that stopped was a reply the schema allows, even when the model wanted to start with "Sure!" or to write a bike the shop doesn't list. Where its choice was masked, it wrote the best token the mask left, which needn't mean what it meant: a model that would have answered that an email asks for no booking can only write a booking. A schema needs a way to say no, such as a field that can be `null`.
- A reply that reached `max_tokens` stopped partway, the start of a valid reply but not valid JSON. A long string, or a model that keeps writing within one, can run a reply to its limit.
- The keys come in the schema's order, as OpenAI's guide says its structured outputs do, so a property the model should fill in after another goes after it in the schema.

So the check from the earlier stage stays: a reply held to a schema can still be cut off.
