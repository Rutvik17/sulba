// The kinds of bug a Catch stage's drafts start from. Each can leave code that looks right and
// passes the tests it was written with, then fails in use: six of the patterns Tambon et al. found
// in code that language models wrote, and four kinds of leakage Kapoor and Narayanan found in
// machine-learning code.
//
// Tambon et al., "Bugs in Large Language Models Generated Code: An Empirical Study" (2024),
// https://arxiv.org/abs/2403.08937
// Kapoor and Narayanan, "Leakage and the Reproducibility Crisis in Machine-Learning-Based
// Science", Patterns 4 (2023), https://doi.org/10.1016/j.patter.2023.100804

export interface Fault {
  readonly id: string;
  readonly description: string;
}

export const faults: readonly Fault[] = [
  {
    id: 'misinterpretation',
    description:
      'The code does something close to what was asked, but not it: the wrong class or column, the wrong denominator, the wrong order or unit.',
  },
  {
    id: 'missing-corner-case',
    description:
      'The code is right except for inputs it overlooks: one sample, an empty batch, ties, zeros, missing or extreme values.',
  },
  {
    id: 'non-prompted-consideration',
    description:
      'The code adds something nobody asked for that changes the result: it sorts, drops, fills, clips, rounds or reweights.',
  },
  {
    id: 'prompt-biased',
    description:
      'The code works for the examples it was written against, such as its own tests, and not for other inputs.',
  },
  {
    id: 'silly-mistake',
    description:
      'A small slip that is easy to miss: a redundant or inverted condition, an unnecessary cast, the wrong variable.',
  },
  {
    id: 'wrong-input-type',
    description:
      'A correct call given the wrong kind of input: a list for an array, integers for floats, a row for a column.',
  },
  {
    id: 'preprocessing-leakage',
    description:
      'Preprocessing learns from data it should not see: scaling, imputing or resampling fitted on test or serving data.',
  },
  {
    id: 'feature-selection-leakage',
    description:
      'Features or settings are chosen with the test set, so its scores flatter the model.',
  },
  {
    id: 'duplicate-leakage',
    description:
      'The same rows reach both training and evaluation, so the evaluation measures memory.',
  },
  {
    id: 'temporal-leakage',
    description: 'The model learns from data recorded after the moment it predicts.',
  },
];
