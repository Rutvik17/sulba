## What it must do

Answer staff's questions from the hospital's policies, with every part running on the hospital's servers, at the busiest moment it expects, and stay current without any connection out.

## What runs where

Both servers run the same things: a model server with the model, an embedding model, the index of the policy documents, and the app staff sign in to with the hospital's own sign-in. Requests go to either server through the hospital's load balancer. Nothing calls out: no telemetry, no updates fetched, no hosted model.

## Memory

The model's {% $fig.params %} billion weights at {% $fig.weight_bits %} bits take about {% $fig.weights_gb %} on each GPU. Every token a conversation holds keeps a key and a value for each of {% $fig.kv_heads %} heads of {% $fig.head_dim %} numbers, in each of {% $fig.layers %} layers, at {% $fig.cache_bytes %} bytes each: {% $fig.kv_token %} bytes a token. A conversation of {% $fig.context %} tokens needs {% $fig.kv_user %}, and {% $fig.peak %} at once need {% $fig.kv_peak %}.

The two GPUs hold {% $fig.total_gb %}. After the weights, and {% $fig.reserve_gb %} on each for the server's own work, {% $fig.free_gb %} is left for the cache: {% $fig.fit_full %} conversations at {% $fig.context %} tokens, fewer than {% $fig.peak %}. Shortening the context to {% $fig.short_context %} tokens, by sending fewer passages, makes room for {% $fig.fit_short %}. Keeping the cache in half the bytes a number would double what fits, if the hospital's test set shows answers don't suffer.

## Choosing the model

Open-weight models that fit these GPUs are scored on a test set of the hospital's own questions, written with its staff, each with the policy that answers it. The hospital sets the bar. The smallest model that clears it is chosen, since a smaller model leaves more memory for conversations.

## When it's full

A request that would take the servers past what they hold waits, with a message saying so, rather than slowing every conversation. The dashboard shows how often that happens, which tells the hospital when to add a server.

## Updates

New model and software versions come as signed packages, which the hospital's IT checks and installs on one server at a time, so the assistant stays up. The documents are indexed from the hospital's own stores whenever they change, all inside the network.

## Logs

Usage and quality logs stay on the hospital's servers, and its staff decide what's kept and for how long.

## The follow-up questions

- **A model twice the size:** twice the memory for the weights, {% $fig.double_weights_gb %} on each GPU, and a larger cache a token, which leaves room for far fewer conversations at once. It's worth it only if the test set shows answers the smaller model gets wrong, and then the hospital needs more GPUs or shorter conversations.
- **A policy is updated:** the indexer reads the hospital's document store, inside the network, and indexes the new version within minutes. Nothing comes from outside.
- **Good enough:** the hospital's own test set, scored by its staff, with the bar they set, run on every new version before it's installed.
