# 29. Fetch a machine lab's large files from their publishers, pinned by size and sha256

- Status: accepted
- Date: 2026-10-18

## Context

Intermediate's PyTorch module needs files too large for the site to serve. Its convolutional networks lab trains on Fashion-MNIST, whose training images are 26,421,880 bytes, over the 25 MiB a Cloudflare static asset may be. Its transfer learning lab uses EuroSAT's RGB tiles, 94,658,721 bytes, and DINOv2's ViT-S/14 weights, 88,283,115 bytes. A lab's datasets have been CSV text that the site serves and each run reads as text. These labs run on the learner's machine, from their download (record 28), and Sulba runs no server for their code. The bill stays at $0, the site never links to its repository, and every number a learner reads comes from code CI runs on the files the learner gets.

## Decision

- **Listed and pinned:** `fetch` in a machine lab's `lab.yaml` lists each source of files, with the credit its licence asks for, as data or as a model's weights. It lists each file with the HTTPS address its publisher serves it from, its size and its sha256. A lab that runs in the browser fetches nothing.
- **The learner's runner:** before a run, `sulba.py` checks each file in the download's `data/` against its size and sha256. It fetches each one that is missing or doesn't match from its publisher, into a file beside it, which a fetch cut short goes on from with a range request. It moves the file into place once it matches, and refuses one that doesn't. A run has each file at `data/<file>`, linked into the run's folder: a hard link where the system allows one, a copy where it doesn't. Of `data/`, a run reads as text only the lab's own datasets.
- **The checks:** the content check, the build and `pnpm check:machine` keep each file under its sha256 in `node_modules/.cache/sulba-fetched`. They fetch it the first time and check it against its sha256 once in each process, and the content check fails when a run changes one. CI keeps the folder in a cache named for the sha256s the labs pin, which changes only when a file does. The Machine labs jobs save it, since only they fetch every file, and the checks and content jobs start from it. Each machine job puts the files it has kept into the download, so the runner fetches from a publisher only a file new to that system. The deploy job keeps no cache, so it fetches every file again.
- **The page:** a lab's page credits each source, and says how much the first run downloads and from which hosts. The Privacy Policy says the runner downloads the files and that each publisher receives the learner's IP address.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Fetch each file from its publisher, pinned by size and sha256 (chosen) | Costs nothing; each file stays where its publisher and its licence put it; the sha256 makes every copy the one CI checked | The learner's first run needs each publisher to be up; each publisher learns the learner's IP address; a file its publisher moves breaks the lab until it is pinned again |
| Copies on sulba.dev, split into parts under 25 MiB | One host, the one the learner already uses | Cloudflare's terms send large files on its CDN to its paid services, short of Enterprise; every deploy uploads them; the site would redistribute each file, under each licence's conditions |
| Copies on the Hugging Face Hub | Free, fast, with range requests | The copies there aren't the publishers' bytes; hosting Sulba's own copies is the "excessive or irrelevant data" its content policy names; an account to keep |
| torchvision's downloaders | No code of Sulba's | Fashion-MNIST over plain HTTP, checked by md5; a different EuroSAT zip, from Hugging Face; one more package in each lab's lock |
| Cloudflare R2 | 10 GB free, with free egress | An R2 subscription goes through a checkout flow; `r2.dev` addresses are rate-limited and meant for development; the site would redistribute the files |
| GitHub Releases of the repository | Free, and takes large files | The site never links to its repository |

## Evidence

- Cloudflare's [Workers limits](https://developers.cloudflare.com/workers/platform/limits/) give "Individual Static Asset file size" as 25 MiB on both the Free and the Paid plan, which is 26,214,400 bytes. Its [service-specific terms](https://www.cloudflare.com/service-specific-terms-application-services/): "Unless you are an Enterprise customer, Cloudflare offers specific Paid Services (e.g., the Developer Platform, Images, and Stream) that you must use in order to serve video and other large files via the CDN."
- Fashion-MNIST's [README](https://github.com/zalandoresearch/fashion-mnist) links each file over HTTP from an S3 website endpoint, with its md5, and its licence is MIT. AWS's [website endpoints](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteEndpoints.html) page: "Amazon S3 website endpoints do not support HTTPS or access points." The same bucket's REST endpoint, `fashion-mnist.s3.eu-central-1.amazonaws.com`, serves each file over HTTPS byte for byte, measured: the training images at 26,421,880 bytes, with the README's md5.
- EuroSAT's [Zenodo record](https://zenodo.org/records/7711810), which its [README](https://github.com/phelber/EuroSAT) names as its host, lists `EuroSAT_RGB.zip` at 94,658,721 bytes under the MIT licence. A copy fetched from it had that size and Zenodo's md5, and a range request was answered 206. Zenodo's [terms](https://about.zenodo.org/terms/): "Access to Zenodo’s content is open to all, for non-military purposes only." Its [developer docs](https://developers.zenodo.org/#rate-limiting) allow guests 60 requests a minute.
- DINOv2's [README](https://github.com/facebookresearch/dinov2): "DINOv2 code and model weights are released under the Apache License 2.0", with ViT-S/14's backbone at `dl.fbaipublicfiles.com/dinov2/dinov2_vits14/dinov2_vits14_pretrain.pth`. A copy fetched from it was 88,283,115 bytes.
- On the Hugging Face Hub, [facebook/dinov2-small](https://huggingface.co/facebook/dinov2-small)'s `model.safetensors` is 88,249,960 bytes and [timm's](https://huggingface.co/timm/vit_small_patch14_dinov2.lvd142m) is 88,240,510 bytes: converted copies, not Meta's file. Its [content policy](https://huggingface.co/content-policy) lists "Hosting excessive or irrelevant data in repositories" under abuse of its services.
- torchvision's [`datasets/mnist.py`](https://github.com/pytorch/vision/blob/268ddfce8e7938226c4ec8ed23fc7b9c46b97316/torchvision/datasets/mnist.py) sets `mirrors = ["http://fashion-mnist.s3-website.eu-central-1.amazonaws.com/"]` and checks each file's md5. Its [`datasets/eurosat.py`](https://github.com/pytorch/vision/blob/268ddfce8e7938226c4ec8ed23fc7b9c46b97316/torchvision/datasets/eurosat.py) fetches `torchgeo/eurosat`'s `EuroSAT.zip` from Hugging Face, which is 94,280,567 bytes, not Zenodo's file.
- Cloudflare's [R2 guide](https://developers.cloudflare.com/r2/get-started/): "You need a Cloudflare account with an R2 subscription. ... Complete the checkout flow to add an R2 subscription to your account." Its [public buckets](https://developers.cloudflare.com/r2/buckets/public-buckets/) page: "Public access through `r2.dev` subdomains is rate-limited and should only be used for development purposes."
- GitHub's [dependency caching](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching) reference: a repository's caches are limited to 10 GB by default, entries "not accessed in over 7 days" are removed, and "Cache contents are not signed or verified".
- [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-14): "Range requests are an OPTIONAL feature of HTTP", and "A server MAY ignore the Range header field."
- Python's [http.client](https://docs.python.org/3/library/http.client.html): "Changed in version 3.4.3: This class now performs all the necessary certificate and hostname checks by default." Its [ssl](https://docs.python.org/3/library/ssl.html) module's `load_default_certs`: "On Windows it loads CA certs from the CA and ROOT system stores." On Linux, the CPython 3.14.6 uv installs reads `/etc/ssl/cert.pem` and `/etc/ssl/certs`, as `ssl.get_default_verify_paths()` shows.
- Python's [os](https://docs.python.org/3/library/os.html) module: `os.replace` "will be an atomic operation (this is a POSIX requirement)" and "may fail if src and dst are on different filesystems", so a fetch writes beside its file; `os.link` has "Availability: Unix, Windows".

## Why

Each file is free to fetch from the publisher that hosts it, under a licence that allows it, so fetching costs nothing and Sulba redistributes nothing. A size and sha256 pin each file, so the learner's machine, CI and the deploy work from the same bytes whatever the publisher's server does. A fetch that doesn't match is refused, and one cut short goes on where it stopped. The strongest case against: a host Sulba controls, such as R2 or the site itself, would keep a lab working if a publisher moved a file. Cloudflare's terms, the size of each deploy and R2's checkout weigh against it, and a pin fails loudly the moment a publisher changes a file.

## Consequences

A learner's first run must reach each publisher, and each publisher receives their IP address. Every run checks each file's sha256 first, which reads the whole file. A deploy fetches every file again, so a publisher that is down holds up deploys until it is back; CI's other jobs don't depend on it while their cache holds the file. A publisher that moves or changes a file breaks its lab until its `lab.yaml` pins the file again, and the next deploy finds it. On Windows and macOS, the runner's fetch of a file runs in CI only while that system's cache lacks it.

## Revisit when

A publisher removes or changes a file a lab fetches, limits its fetches, or stops serving it over HTTPS; or a lab needs a file no publisher serves.
