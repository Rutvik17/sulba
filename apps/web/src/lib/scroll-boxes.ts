// A table or a formula on its own lines in a lab's prose sits in a box marked `data-scroll`
// (packages/content's prose.ts), which scrolls sideways when it is wider than the text. While it
// does, the box takes keyboard focus, so it can be scrolled with the arrow keys.

/** Keeps each box in `root` focusable while it scrolls, until the returned function is called. */
export function keyboardScrollBoxes(root: ParentNode): () => void {
  const boxes = [...root.querySelectorAll<HTMLElement>('[data-scroll]')];
  const update = () => {
    for (const box of boxes) {
      if (box.scrollWidth > box.clientWidth) box.tabIndex = 0;
      else box.removeAttribute('tabindex');
    }
  };
  // The box resizes with the page, and what it holds changes width as its fonts load.
  const watcher = new ResizeObserver(update);
  for (const box of boxes) {
    watcher.observe(box);
    if (box.firstElementChild) watcher.observe(box.firstElementChild);
  }
  return () => watcher.disconnect();
}
