Each problem passed the assistant's tests because the tests scripted a model that does what's asked of it: one call at a time, with arguments its tool takes, to a tool it was offered, and an answer after one round. The checks scripted replies a real model can give, and a customer can steer.

The model decides when it's done calling tools, so the code decides how long to wait for it: after `ROUNDS` requests, the customer gets `SORRY`.

A reply can call several tools at once, written together before any result came back, and each call needs its result, in a `tool` message of its own, under its call's id.

A tool's error is a result too. The model chose the arguments, so it's the one to read what was wrong with them, and try again or tell the customer.

A tool call is text the model wrote after reading the customer's message, so the code runs only the tools it offered. Every tool the assistant can reach is one a customer can try to make it run.
