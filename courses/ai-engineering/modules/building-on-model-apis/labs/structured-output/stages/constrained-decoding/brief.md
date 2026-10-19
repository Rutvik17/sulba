A request can ask the model's server to hold the reply to a schema, and the server does it while the model writes. At each step the model scores every token of its vocabulary, and before one is chosen, the server takes out every token that can't lead to a reply the schema allows, and the end of the reply until it's whole. This stage builds that.

A reply here is an object with every property of the schema, in the schema's order, written with no spaces or line breaks outside its strings:

```json
{"name":"Ana Silva","bike":"city","service":"brakes","day":"Monday","bikes":1,"collect":true}
```

Its properties' schemas use these keywords, as the tests' booking schema does:

- `enum`, a list of strings;
- `"type": "string"`, with `minLength` and `maxLength`, its strings holding no `"`, no `\` and no character below a space;
- `"type": "integer"`, with `minimum` and `maximum`, neither negative, written with no leading zero;
- `"type": "boolean"`, `true` or `false`.

In `constrain.py`, write:

- `allowed(text, schema)`: whether `text` can go on to be a whole reply, or is one. `""` can, and so can `{"name":"An`, but `{"name": ` can't.
- `complete(text, schema)`: whether `text` is a whole reply.
- `mask(text, vocabulary, schema)`: for each token in `vocabulary`, whether it can come next. `END`, the model's end of its reply, can come once `text` is whole, and any other token when `text` with it still can go on to a whole reply.
- `generate(scores, vocabulary, schema, max_tokens)`: the reply the model writes. `scores(text)` gives the model's score for each token of the vocabulary after `text`. At each step, add the token the mask allows that the model scores highest, the first of them in the vocabulary on a tie. Return the text and `"stop"` when that token is `END`, or `"length"` when `max_tokens` tokens have been written.

The tests compare your functions with a regular expression for the replies the booking schema allows, matched with the `regex` package, which can tell whether a text can go on to match.

```
allowed(text, schema) -> bool
complete(text, schema) -> bool
mask(text, vocabulary, schema) -> list[bool]
generate(scores, vocabulary, schema, max_tokens) -> (text, finish_reason)
```
