interface ImportMetaEnv {
  /** Supabase's address, when a build reaches a project other than the hosted one. */
  readonly PUBLIC_SUPABASE_URL?: string;
  /** That project's publishable key. */
  readonly PUBLIC_SUPABASE_PUBLISHABLE_KEY?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
