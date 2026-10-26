A law firm of {% $fig.staff %} people keeps {% $fig.documents %} documents in a file store, a wiki and its system of matters. Who may read each document comes from groups in the firm's directory: a matter's documents are for the people on that matter. The firm wants an assistant that answers each person's questions from the documents they may read, and never from the others.

Design how the documents are indexed, how access is enforced, and how both stay current. Take these as given:

- a document splits into about {% $fig.per_document %} passages;
- each passage's embedding is {% $fig.dimensions %} numbers of {% $fig.number_bytes %} bytes;
- about {% $fig.changes %} documents change on a working day;
- staff ask about {% $fig.questions %} questions a day.
