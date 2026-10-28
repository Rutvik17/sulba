// The Worker's bindings (wrangler.jsonc), which server routes import from `cloudflare:workers`.
declare module 'cloudflare:workers' {
  export const env: {
    /** The site's files, as the platform serves them. */
    readonly ASSETS: { fetch(input: Request | URL | string): Promise<Response> };
  };
}
