With a story {% $fig.story %} tokens long, writing the next token as a full pass reads every token again, {% $fig.uncached %} multiply-adds. With the cache, it reads only the new token, {% $fig.cached %}, {% $fig.ratio %} times fewer, and the gap grows with the story.

The cache only grows. Each token keeps a key and a value of {% $fig.kv_heads %} heads, {% $fig.dim %} wide, in each of the {% $fig.layers %} blocks: {% $fig.token_bytes %} bytes in float32. SmolLM2's whole context of {% $fig.context %} tokens would take {% $fig.context_bytes %} bytes, and with a key and value head for each of its {% $fig.heads %} query heads, {% $fig.full_bytes %}. Grouped-query attention saves memory mostly here.

The cache keeps keys rotated. A key's angle depends only on its own position, which doesn't change as the story grows, so it's turned once, when it's made, and every later token reads it as it is.

After the app's opening line, "{% $fig.opening %}", SmolLM2 wrote {% $fig.written %} tokens: "{% $fig.continuation %}"
