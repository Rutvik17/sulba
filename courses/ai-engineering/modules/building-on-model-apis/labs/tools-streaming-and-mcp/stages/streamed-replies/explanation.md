A stream changes when the customer sees the reply, not what the reply is: the pieces put together are the same message a whole reply would have been. Until the chunk with `finish_reason` arrives, the reply isn't finished, and a stream that ends without one was cut off on the way.

A tool call streams as text does, its arguments in pieces of JSON that don't parse until the last has come, so the code reads a call's arguments only once the reply has finished. Each call has an `index`, and only the first piece of each carries its `id` and name, which is why the pieces are kept by index.

Server-sent events are part of the WHATWG's HTML standard, with rules that matter here: a line ends at CR LF, LF or CR, a value loses one space after its colon, a line starting with a colon is a comment, which a server can send to keep a quiet connection open, and an event left unfinished when the stream ends is dropped. httpx's `iter_lines` splits text as Python's `str.splitlines` does, at characters such as U+2028 too, which can appear in a model's text, so it can cut one chunk of JSON in two. The openai package splits the bytes, at CR and LF only.

With `stream_options` asking for it, OpenAI's API sends the tokens used "before the `data: [DONE]` message", in a chunk whose `choices` "will always be an empty array".
