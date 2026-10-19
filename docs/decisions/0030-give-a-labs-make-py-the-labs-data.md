# 30. Give a lab's make.py the lab's data, fetched files included

- Status: accepted
- Date: 2026-10-19

## Context

A lab that builds what a library does checks the learner's code against the library's results, which its `references/make.py` records (record 27). A lab that runs on the learner's machine can fetch files too large for the site to serve, which the checks keep under their sha256 in `node_modules/.cache/sulba-fetched` (record 29). The GPT-2 weights lab of Intermediate's Transformers module ports GPT-2 small from the weights on the Hugging Face Hub, a `model.safetensors` of 548,105,171 bytes that the lab fetches, and its tests compare the learner's model with what Hugging Face's own library makes of the same weights. Until now, `pnpm check:references` has given make.py only the folder to write into, so a make.py couldn't read a file its lab fetches.

## Decision

- **The data:** `pnpm check:references` runs `uv run make.py <folder> <data>`. `<data>` holds the lab's data as a run has it in `data/`: its datasets, and a copy of each file it fetches, each by its name.
- **The files:** each copy comes from the checks' folder of fetched files, through the fetcher the other checks use, which fetches a file the folder lacks and checks each against its sha256. A file that can't be fetched is a problem with the lab's `lab.yaml`, and its make.py doesn't run.
- **Copies:** each is a copy-on-write clone where the file system makes one, and a full copy where it doesn't, so a make.py that writes to a file it reads can't change the file kept.
- **CI:** the References job restores the fetched files' cache, as the checks and content jobs do, and doesn't save it.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| The check gives make.py the lab's data, from the checks' fetched files (chosen) | One fetcher and one cache, each file checked against the sha256 `lab.yaml` pins; make.py stays a script that reads files | To record by hand, the author passes a folder holding the files, such as a lab's download's `data/` |
| make.py fetches each file itself | Runs with no folder given | A second fetcher to write and keep; each run of the check fetches every file again, unless CI keeps a second cache |
| make.py downloads with `huggingface_hub` at the pinned revision | The Hub's own downloader, with its own cache | Only for files on the Hub; a second cache for CI to keep, beside the checks' own |
| Recordings made on the author's machine, never again in CI | Nothing to build | Nothing would show the recordings still hold, which is what record 27's check is for |

## Evidence

- Node's [fs](https://nodejs.org/docs/latest-v24.x/api/fs.html#fspromisescopyfilesrc-dest-mode) documentation, for the version in `.node-version`: with `fs.constants.COPYFILE_FICLONE`, "The copy operation will attempt to create a copy-on-write reflink. If the platform does not support copy-on-write, then a fallback copy mechanism is used." Without a mode, "dest is overwritten if it already exists."
- `huggingface_hub`'s [download guide](https://huggingface.co/docs/huggingface_hub/guides/download): `hf_hub_download()` "downloads the remote file, caches it on disk (in a version-aware way), and returns its local file path", "it is important to not modify the file to avoid having a corrupted cache", and its `revision` parameter downloads a file "from a specific branch, a PR, a tag or a commit hash".
- GitHub's [dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) reference: "By default, the limit is 10 GB per repository"; past it, GitHub evicts caches "in order of last access date"; and "Increasing the limit beyond the default 10 GB will incur additional costs, if that storage is used."
- The Hugging Face Hub's listing of [openai-community/gpt2](https://huggingface.co/openai-community/gpt2/tree/607a30d783dfa663caf39e06633721c8d4cfcd7e) at revision `607a30d` gives `model.safetensors` as 548,105,171 bytes, and a copy fetched from it was that size.

## Why

A make.py reads the same bytes the learner's runs and the content check read, checked against the same pin, through the one fetcher that already does it. Restoring the cache the Machine labs jobs save adds nothing to the repository's 10 GB, so the bill stays at $0. A copy keeps the kept file safe from a make.py that writes, and a clone makes it as quick as a link where the file system allows. The strongest case against: an author who records by hand must gather the files first, where a make.py that fetched its own would need nothing.

## Consequences

The References job restores the fetched files' cache, which holds every file the labs pin, and fetches from its publisher any file new since the cache was saved. Where the file system can't clone, each run of the check writes a full copy of each file a lab with references fetches. A make.py that reads data takes the folder as its second argument; one that reads none ignores it.

## Revisit when

A make.py needs a file that no lab fetches, or the fetched files' cache nears GitHub's 10 GB.
