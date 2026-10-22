Notes that outlast a conversation are the caller's data, kept by the desk. So the desk owes the caller what any store of their data does: their own notes and no one else's, and a way to have them removed.

A caller's id is their input, not a file name. Built into a path as it is, `../a` opens another caller's notes, and enough `..` writes outside the folder. A hash of the id gives each caller one file inside it, whatever the id holds.

Each note goes into every request of every conversation the caller has from then on, so the notebook has a size. A cap on the notes, and on each note's length, keeps what they cost in tokens bounded, and the error tells the model what to do instead. Writing the notes to a file beside the caller's, then moving it into place, means a conversation that stops while the notes are written leaves the caller's file as it was.
