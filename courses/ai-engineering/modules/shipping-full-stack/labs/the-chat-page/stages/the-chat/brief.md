The page's chat shows a conversation, sends the caller's message from its form, and puts the reply on the page as it comes. The page has these parts, which the chat is given:

```html
<div id="log" role="log" aria-live="polite" aria-labelledby="chat-title"></div>
<form id="ask">
  <label for="content">Message</label>
  <textarea id="content" name="content" maxlength="2000"></textarea>
  <button id="send" type="submit">Send</button>
</form>
<p id="status" role="status" aria-live="polite"></p>
```

In `chat.ts`, write `Chat`:

- `new Chat(desk, conversation, elements)` shows each message of the conversation in the log, as `<div class="message" data-role="caller">` or `data-role="desk"`, holding `<p class="who">`, with `You` or `The desk`, and `<p class="text">`, with the message. A message is text, never markup. Make the elements with the log's own `ownerDocument`, so the chat works in any document, the tests' among them.
- Sending the form sends what's in the box, and the browser doesn't send the form itself.
- `send(content)` sends the message, without the spaces at its ends. A blank message isn't sent, and nor is one sent while a reply is coming. The caller's message and an empty reply join the log at once, the box empties, and the status clears. While the reply comes, Send is off and the log has `aria-busy="true"`; after it, Send is on and `aria-busy` is `false`. Each piece of text adds to the reply, and `done`'s content replaces it with the whole reply.
- A turn that doesn't end in a reply leaves the page as it was: its two messages leave the log, the message goes back in the box if the box is empty, and the status says why. That's an `error` event's title, the message of an `ApiError` the desk answered with, or `The message couldn't be sent.` for anything else.
- `close()` stops the reply that's coming, if any, and the chat takes no more messages, as when the caller opens another conversation. A reply it stops shows no problem.

```ts
new Chat(desk: Desk, conversation: Conversation, elements: ChatElements)
chat.send(content: string): Promise<void>
chat.close(): void
```

The tests build the page in happy-dom, a DOM that runs in Node, and stand in for the desk.
