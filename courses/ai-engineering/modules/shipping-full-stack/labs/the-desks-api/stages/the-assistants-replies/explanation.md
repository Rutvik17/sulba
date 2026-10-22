Each problem passed the assistant's tests because every test followed a conversation that went to plan. The model answered, in time, and each conversation was one message long, so no test sent a message to a conversation that wasn't there, had the model fail or hang, or came back to a conversation for a second turn.

A place at the gate is a resource like a file or a connection: whatever takes it must give it back on every path, failures included. The safe shape takes the place last, after every check that can refuse the request, and gives it back in a `finally`. A place that leaks doesn't fail one request, it fails every request after it: with one running place, a single leak leaves the desk replying to no one, and no error says why.

The agent holds the conversation: the messages the model reads, and any proposal waiting for a yes. A new agent for each message answers every message as if it were the first, so a conversation works only as long as it's one message long.

The time limit is what makes the gate's promise true. `Retry-After` tells a caller how long a running reply can have, and only `within` holds a reply to that.
