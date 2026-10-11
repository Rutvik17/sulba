// A figures.py that reads a lab's data, shared by the tests in Pyodide and in CPython.
export const counted = {
  'data/votes.csv': 'choice\nyes\nno\nyes\n',
  'figures.py': [
    'import csv',
    '',
    '',
    'def figures():',
    "    with open('data/votes.csv', encoding='utf-8') as file:",
    "        votes = [row['choice'] for row in csv.DictReader(file)]",
    "    return {'yes': str(votes.count('yes')), 'share': f\"{votes.count('yes') / 3:.4f}\"}",
    '',
  ].join('\n'),
};
