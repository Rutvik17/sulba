`search` ranks only what `readable` gives, so a document the person may not read never takes one of their `k` places, and its words never decide what they see. Taking the `k` best of every document and dropping the ones they may not read would give fewer than `k`, or none, to someone whose best matches are for others.

A document is for the groups it names and for no one else, so one that names none is for no one. That makes a mistake in the store fail closed: a document whose groups were never set stays unread, where a rule that read "no groups" as "everyone" would show it to all.

Access checked in the search is only as good as the groups it's given. The next stage takes them from the sign-in, where the office's own directory says who belongs where.
