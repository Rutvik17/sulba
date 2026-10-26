Before you started, the office asked an assistant for the desk's answers and records. The assistant wrote `desk_answers.py`: `student_record`, a student's record read as `ROLE`; `pages_cited`, the pages a reply cites; and `office_answer`, the answer from the office's pages with the pages it cites, or `STAFF` and no pages. Its three tests all pass.

Review it as if the office were about to use it: fix every problem you can find, and keep what it does right. Four hidden checks test it the way the office's desk will call it, on the office's passages and records, with one connection kept open from one question to the next. A run shows how many pass. You see which ones when you finish the review.

What the code must do:

- pass a question the search turns away to staff without asking the model;
- name the page of each passage a reply cites;
- read only the record of the student it's given;
- leave the connection as it found it.
