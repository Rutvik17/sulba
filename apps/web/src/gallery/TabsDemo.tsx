import { Tab, TabList, TabPanel, Tabs } from '@sulba/ui/tabs';

const tabs = [
  { id: 'brief', name: 'Brief', text: 'Write sigmoid(z) and make its tests pass.' },
  { id: 'hints', name: 'Hints', text: 'Start from the formula: 1 / (1 + e^-z).' },
  {
    id: 'explanation',
    name: 'Explanation',
    text: 'Sigmoid maps any number to one between 0 and 1.',
  },
  { id: 'tests', name: 'Tests', text: 'Five tests check it, large negative inputs included.' },
] as const;

/** Tabs in a React island, the way a session shows them, with Solution not yet open. */
export default function TabsDemo() {
  return (
    <Tabs defaultSelectedKey="brief">
      <TabList aria-label="Session">
        {tabs.map(({ id, name }) => (
          <Tab key={id} id={id}>
            {name}
          </Tab>
        ))}
        <Tab id="solution" isDisabled>
          Solution
        </Tab>
      </TabList>
      {tabs.map(({ id, text }) => (
        <TabPanel key={id} id={id}>
          {text}
        </TabPanel>
      ))}
    </Tabs>
  );
}
