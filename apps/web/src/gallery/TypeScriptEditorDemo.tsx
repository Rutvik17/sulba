import { Editor } from '@sulba/editor/editor';

const code = `/** The reply's text, from each event's data, as the stream gives them. */
export async function reply(events: AsyncIterable<{ data: string }>): Promise<string> {
  let text = '';
  for await (const { data } of events) text += JSON.parse(data).text;
  return text;
}
`;

/** A TypeScript solution, as a lab that runs on the learner's machine shows it. */
export default function TypeScriptEditorDemo() {
  return (
    <div className="editor-frame fit">
      <Editor defaultValue={code} label="Solution" language="typescript" readOnly />
    </div>
  );
}
