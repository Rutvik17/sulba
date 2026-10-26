Streaming changes what a student sees, not what the desk decides. Every rule of `answer` still holds, applied once the reply is whole: a citation can come in its last piece, and a reply that says it doesn't know can say so after an answer. So the desk shows the pieces as they come and lets the verdict replace them.

A reply stopped by the token limit can end mid-sentence, after a citation, so its pages can't vouch for what it says, and it goes to staff too. Of the {% $fig.replies %} recorded replies, {% $fig.cut %} stopped at the limit.

A failure before the reply starts, an error status, a dropped connection or no reply in time, raises from `client.stream` or `raise_for_status` as it would from `client.post`, and the generator ends with the verdict to staff.
