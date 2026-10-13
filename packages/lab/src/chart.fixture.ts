// A chart.py that draws with the learner's code and a lab's data, shared by the tests in Pyodide
// and in CPython.
import type { ChartRequest } from './protocol.ts';

export const shares: ChartRequest = {
  files: {
    'data/votes.csv': 'choice\nyes\nno\nyes\n',
    'tally.py': 'def share(votes, choice):\n    return votes.count(choice) / len(votes)\n',
    'chart.py': [
      'import csv',
      '',
      'import numpy as np',
      '',
      'from tally import share',
      '',
      '',
      'def chart(votes):',
      "    with open('data/votes.csv', encoding='utf-8') as file:",
      "        cast = [row['choice'] for row in csv.DictReader(file)][:votes]",
      "    yes = share(cast, 'yes')",
      '    return {',
      "        'x': {'min': 0, 'max': 1, 'step': 1, 'label': 'votes'},",
      "        'y': {'min': 0, 'max': 1, 'step': 0.5, 'label': 'share'},",
      "        'lines': [",
      "            {'style': 'main', 'label': 'Yes', 'x': np.array([0.0, 1.0]), 'y': (0.0, yes)},",
      '        ],',
      "        'points': [{'x': 1, 'y': np.float64(yes)}],",
      "        'readouts': [{'label': f'share of {votes}', 'value': f'{yes:.4f}'}],",
      "        'description': f'The share of yes votes in the first {votes}',",
      '    }',
      '',
    ].join('\n'),
  },
  values: { votes: 3 },
  packages: ['numpy'],
};
