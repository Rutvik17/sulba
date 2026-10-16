The assistant's tests checked that the probabilities add up to 1, that top-k keeps no more than `$k$` tokens, that only kept tokens are drawn, that two runs give the same labels, and that the labels are Yes or No. None compared the probabilities with the ones generation draws from, counted how often each token comes up, or compared one pair's draw with another's.

---

Each problem left labels that pass for the model's answers and aren't. A sampler is checked the way generation would be: its probabilities against generation's, its draws by counting them, and its pairs by drawing them independently of each other.
