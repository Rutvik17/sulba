Before the shop picks a provider's model, it wants to know what a month of its customers' questions would cost. Providers charge by the million tokens, at a price for each kind of token: the prompt's tokens read fresh, read from the provider's cache of prompts it has seen, or written to that cache, and the reply's tokens. `PRICES` in `costs.py` holds the published prices of two of OpenAI's models and two of Anthropic's on {% $fig.priced %}.

Each provider reports a request's tokens its own way:

- OpenAI's chat completions report `prompt_tokens`, which include the `cached_tokens` and `cache_write_tokens` in `prompt_tokens_details`. Either may be missing, and so may the details.
- Anthropic's messages report `input_tokens`, which leave out `cache_read_input_tokens` and `cache_creation_input_tokens`. Either may be missing or `null`.

Some models charge more for long prompts: a request whose prompt has more tokens than its price's `above`, counting those read from and written to the cache, pays the prices of its `long` for every token. Each request is priced on its own.

In `costs.py`, write:

- `openai_tokens(usage)` and `anthropic_tokens(usage)`, the tokens of each provider's `usage` as `Tokens`;
- `cost(tokens, price)`, what a request costs in dollars, exactly, as a `Decimal`;
- `month(requests, price)`, what a list of requests' `Tokens` costs.

```
openai_tokens(usage) -> Tokens
anthropic_tokens(usage) -> Tokens
cost(tokens, price) -> Decimal
month(requests, price) -> Decimal
```
