import assert from "node:assert/strict";
import { test } from "node:test";
import { Window } from "happy-dom";
import { render } from "../messages.ts";

test("tst_aaaaaa Shows each message as text", () => {
  const window = new Window();
  const list = window.document.createElement("ul");
  render(list as unknown as HTMLElement, [{ role: "caller", content: "<b>Hi</b>" }]);
  assert.equal(list.children.length, 1);
  assert.equal(list.textContent, "<b>Hi</b>");
  assert.equal(list.querySelector("b"), null);
});

test("tst_bbbbbb A failing one", () => {
  assert.deepEqual({ a: 1 }, { a: 2 });
});
