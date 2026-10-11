import { Segment, SegmentedChoice } from '@sulba/ui/segmented';

/** Segmented choices in a React island: two options, then three with one unavailable. */
export default function SegmentedDemo() {
  return (
    <>
      <SegmentedChoice aria-label="Where tests run" defaultValue="browser">
        <Segment value="browser">Browser</Segment>
        <Segment value="machine">Your machine</Segment>
      </SegmentedChoice>
      <SegmentedChoice aria-label="Layout" defaultValue="split">
        <Segment value="editor">Editor</Segment>
        <Segment value="split">Split</Segment>
        <Segment value="output" isDisabled>
          Output
        </Segment>
      </SegmentedChoice>
    </>
  );
}
