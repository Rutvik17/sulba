import { Editor } from '@sulba/editor/editor';

const code = `def predict_proba(X, w, b):
    """The probability of class 1 for each row of X."""
    return sigmoid(X @ w + b)
`;

/** The editor as a solution shows it: the code can be read and copied but not changed. */
export default function ReadOnlyEditorDemo() {
  return (
    <div className="editor-frame fit">
      <Editor defaultValue={code} label="Solution" readOnly />
    </div>
  );
}
