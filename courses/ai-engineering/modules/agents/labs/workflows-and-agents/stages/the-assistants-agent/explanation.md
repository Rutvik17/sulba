Each problem passed the assistant's tests because each test stopped short of it. The scripted model in the tests stopped calling tools by itself, its arguments were always JSON, it answered whatever the messages held, and each test was one turn long.

A real server reads the messages as the API defines them, and a `tool` message must follow the assistant message whose `tool_calls` it answers; llama.cpp's server, like a provider's, refuses a result whose call it can't find. A model that keeps calling tools is a failure the agent has to end itself, since each request costs the caller time. And the model writes its arguments as text, so text that stops halfway, or isn't JSON at all, is a mistake of the model's to report back to it, not a reason to drop the caller's turn.

A conversation lives only in what the agent sends. The API keeps nothing, so an agent that starts each turn afresh hears "Yes, please book it." with no offer before it, and the yes means nothing.
