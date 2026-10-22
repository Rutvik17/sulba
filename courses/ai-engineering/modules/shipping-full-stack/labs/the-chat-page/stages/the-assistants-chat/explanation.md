Each problem passed the assistant's tests because every test followed a turn that went to plan. Each reply was plain text, came quickly, and ended with `done`, and no test closed the chat while a reply was on its way or listened to what a screen reader would hear.

What a reply holds comes from a model, and a model writes what its input leads it to. A help page or a caller's message can lead it to write markup, and `innerHTML` turns that markup into elements, scripts' event handlers included. MDN's page on `innerHTML` gives the example: an `<img src='x' onerror='alert(1)'>` whose `src` "is not a valid image URL" runs the code in its error handler. The desk's page sends a Content-Security-Policy that blocks inline handlers, and OWASP's cheat sheet still lists "Sole Reliance on Content-Security-Policy (CSP) Headers" among the approaches to avoid: the policy is a second wall, not the first.

A live region is for changes worth hearing. MDN says `aria-live="polite"` suits "Any region which receives updates that are important for the user to receive, but not so rapid as to be annoying". A reply comes in many small pieces.

Send is part of the turn's state, so it goes back with the rest in `finally`. Left in the `done` branch, every failure, from the desk's time limit to a dropped connection, left the caller with a page that couldn't send.

A flag that the loop reads is only read when the next event comes, and a desk that's searching sends nothing. Aborting the request ends it at once, and frees the desk's place for the next caller.
