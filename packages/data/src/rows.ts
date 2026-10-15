// Reads every row a query gives, however many requests that takes.

/** The most rows the Data API returns for one request, as Supabase sets it by default. */
const page = 1000;

/** Every row `query` gives, asked for a page at a time: it asks for the rows `from` to `to`. */
export async function readAll<Row>(
  query: (from: number, to: number) => PromiseLike<{ data: Row[] | null; error: Error | null }>,
): Promise<Row[]> {
  const rows: Row[] = [];
  for (;;) {
    const { data, error } = await query(rows.length, rows.length + page - 1);
    if (error) throw error;
    rows.push(...(data ?? []));
    if ((data?.length ?? 0) < page) return rows;
  }
}
