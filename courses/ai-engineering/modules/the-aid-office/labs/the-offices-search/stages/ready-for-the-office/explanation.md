The solution needs a closeness of {% $fig.limit %}, the threshold your `threshold` gives on the office's validation questions to keep {% $fig.keep %} of them, and weighs meaning at {% $fig.weight %} against words. By the recorded vectors, that threshold keeps {% $fig.kept_test %} of the office's test questions and turns away {% $fig.declined_test %} of the others'.

It embeds the question once, with a timeout of {% $fig.timeout %} seconds, and uses the one vector for both the closeness and the search. Any `httpx.HTTPError` sends it to the words alone: a student is better served by the pages the words find than by an error. With no vector, there's no closeness to turn a question away by, so while the model is down, every question gets the pages its words find.

The full build goes on from here: answers from the served model that cite these pages, the student's own aid record, for the student signed in, and an eval suite that gates each change.
