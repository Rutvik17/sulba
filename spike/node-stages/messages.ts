export interface Message {
  role: "caller" | "desk";
  content: string;
}

export function render(list: HTMLElement, messages: readonly Message[]): void {
  list.replaceChildren(
    ...messages.map((message) => {
      const item = list.ownerDocument.createElement("li");
      item.className = message.role;
      item.textContent = message.content;
      return item;
    }),
  );
}
