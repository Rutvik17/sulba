// Vite turns a CSS Module into an object of the class names it scoped.
declare module '*.module.css' {
  const classes: Readonly<Record<string, string>>;
  export default classes;
}
