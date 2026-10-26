import { Editor } from '@sulba/editor/editor';

const code = `// Wait blocks until the bucket has a token or ctx is done.
func (l *Limiter) Wait(ctx context.Context) error {
	for {
		wait, ok := l.take(time.Now())
		if ok {
			return nil
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(wait):
		}
	}
}
`;

/** A Go solution, as a lab that runs on the learner's machine shows it. */
export default function GoEditorDemo() {
  return (
    <div className="editor-frame fit">
      <Editor defaultValue={code} label="Solution" language="go" readOnly />
    </div>
  );
}
