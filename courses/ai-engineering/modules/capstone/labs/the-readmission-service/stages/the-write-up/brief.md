The hospital network's leaders will decide on the service from one page. Write it in `report.py`:

```
write_up(table, trained, probabilities) -> the write-up, in Markdown
```

`table` holds the stays, `trained` is what `train` gave for them, and `probabilities` is each stay's out-of-fold probability, from `out_of_fold(table, make_chosen)`. Work out every number in the write-up from these, so a model trained again gets a write-up of its own. It has these sections, as Markdown headings, in this order:

| Heading | What it gives |
| --- | --- |
| `# The readmission service` | A title |
| `## What it answers` | The number of stays it learned from, with commas between thousands, and the share of them readmitted, as a percentage to one decimal |
| `## How well it ranks` | The mean AUC over the folds `cross_validated` uses and its standard error, each to three decimals, written as mean ± error |
| `## How far its probabilities hold` | The readmissions its probabilities add up to and those that came back, as whole numbers with commas, and for the tenth of stays it rates highest, their mean probability and the share readmitted, as percentages to one decimal |
| `## The calls` | The threshold to three decimals, `SHARE` as a whole percentage, and the recall and precision there, as percentages to one decimal |
| `## What it doesn't know` | The limits of what it learned from, in a few sentences |

The tests work out each number again and look for it in its section.
