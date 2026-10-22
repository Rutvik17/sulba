This stage's agent held the same conversations, with the same seeds, with a budget of 8,192 tokens. The server refused a request for its size in {% $fig.memory_refused %} of its runs, against {% $fig.whole_refused %} of the last lab's agent's. Its largest request had a median of {% $fig.memory_largest %} tokens and was at most {% $fig.memory_most %}, against a median of {% $fig.whole_largest %} and at most {% $fig.whole_most %}. The memory cleared old results {% $fig.cleared %} times and summarised {% $fig.summaries %} times.

| Parts | The last lab's agent | With a memory | This less the last | Its {% $fig.confidence %} interval |
| --- | --- | --- | --- | --- |
| Questions | {% $fig.question_whole %} | {% $fig.question_memory %} | {% $fig.question_difference %} | {% $fig.question_interval %} |
| Callbacks | {% $fig.callback_whole %} | {% $fig.callback_memory %} | {% $fig.callback_difference %} | {% $fig.callback_interval %} |
| All | {% $fig.all_whole %} | {% $fig.all_memory %} | {% $fig.all_difference %} | {% $fig.all_interval %} |

Each share is of a conversation's parts that were done, a part the run never reached counting as not done, and the difference is worked out conversation by conversation, with an interval that counts each conversation once. Callbacks gained: the second comes last, after ten questions, where the last lab's agent's runs had often ended, and each needs the part of the day the caller named at the start. Questions did about as well either way.

The memory costs time. Over the parts each run reached, a part took {% $fig.memory_seconds %} seconds on average, against {% $fig.whole_seconds %}. Some of it is the summaries, a request each. More is the server's cache. llama.cpp's server keeps the state it computed for the last prompt, and with `cache_prompt`, on by default, "the common prefix does not have to be re-processed, only the suffix that differs between the requests." A request that only adds to the conversation keeps its whole prefix. One that clears a result or puts a summary in place of turns changes the conversation near its start, and the server works out the rest again. {% $fig.whole_cached %} of the last agent's tokens of prompt came from the cache, against {% $fig.memory_cached %} of this one's.

Notes outlast summaries. A note is the model's own record of one fact, kept word for word, where a summary rewords many turns at once and can drop a detail. Anthropic's guide warns that "overly aggressive compaction can result in the loss of subtle but critical context whose importance only becomes apparent later."
