// A file imported with `?url` arrives as the address it is served from.
declare module '*?url' {
  const url: string;
  export default url;
}
