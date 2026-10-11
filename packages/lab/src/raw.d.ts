// A file imported with `?raw` arrives as its text.
declare module '*?raw' {
  const text: string;
  export default text;
}
