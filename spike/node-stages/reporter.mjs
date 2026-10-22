export default async function* reporter(source) {
  for await (const event of source) {
    if (event.type === "test:pass" || event.type === "test:fail") {
      const { name, nesting, details } = event.data;
      const error = details.error;
      yield JSON.stringify({ type: event.type, name, nesting, message: error?.cause?.message ?? error?.message, expected: error?.cause?.expected, actual: error?.cause?.actual }) + "\n";
    }
  }
}
