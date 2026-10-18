The assistant's tests checked each part once. The reader read the validation digits well in both tests that read them: none of the problems changes the weights of a run that never stops, and a run picked up wrongly still trains, only to other weights. The checkpoint had all the keys. And a second run went on from the first, which was all the test asked: not from where, nor whether it ended where a run that never stopped would.

---

A run is picked up right when it can't be told from one that never stopped: the same weights and running estimates, the same momentum, the same next order, the same count of epochs. The assistant's checkpoints held all four, but its `resume` put back only the reader, and the count it saved was one short. The fourth problem let validation change the reader it was meant to judge.
