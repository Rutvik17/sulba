// A lab's download (decision record 25): its files in one zip, made in the browser and saved from a
// blob URL, so the learner's code goes nowhere but their own machine.
import { strToU8, zipSync } from 'fflate';

/** The files, each by its path, in a zip that holds them inside one folder. */
export function zipped(
  folder: string,
  files: Readonly<Record<string, string>>,
): Uint8Array<ArrayBuffer> {
  const inside = Object.entries(files).map(([path, text]) => [`${folder}/${path}`, strToU8(text)]);
  // A copy, so the bytes are typed as the plain buffer a Blob takes.
  return new Uint8Array(zipSync(Object.fromEntries(inside)));
}

/** Has the browser download the bytes as a file with the name given. */
export function save(name: string, bytes: Uint8Array<ArrayBuffer>): void {
  const url = URL.createObjectURL(new Blob([bytes], { type: 'application/zip' }));
  const link = document.createElement('a');
  link.href = url;
  link.download = name;
  link.click();
  // The download reads the blob after the click returns, so its URL is released later.
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
