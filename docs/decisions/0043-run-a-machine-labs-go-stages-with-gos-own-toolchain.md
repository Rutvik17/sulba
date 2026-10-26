# 43. Run a machine lab's Go stages with Go's own toolchain, pinned by the runner

- Status: accepted
- Date: 2026-10-26

## Context

Intermediate's optional Go module teaches Go to a programmer who knows Python: types, slices and maps, interfaces, errors as values, goroutines, channels and context, the standard library's HTTP server, and tests and benchmarks. Its labs build an LLM gateway in front of the course's model API, with routing, rate limits, retries and caching. Go doesn't run in the browser's Pyodide, so its stages run on the learner's machine (decision record 28), on the six systems machine labs run on, Windows, macOS and Linux each on x86-64 and Arm, with nothing for the learner to install but uv. A rate limit, a retry's backoff or a timeout has to be tested without waiting for real time to pass, and a run's results have to come back as a Python run's do: one per test, with its id, and the line of the learner's code where it failed.

## Decision

- **Toolchain:** Go 1.27.3, the archive go.dev publishes for each of the six systems, from dl.google.com, where go.dev's links lead. `sulba_runner.py` pins each by its size and sha256 and fetches it into `sulba` in the learner's cache folder the first time a Go run needs it, as it fetches Node.js (decision record 39). A run sets `GOTOOLCHAIN=local`, so a `go.mod` never fetches another toolchain; `GOPROXY=off`, so it fetches no module; `GOENV=off`, so the learner's own `go env -w` settings don't change it; `CGO_ENABLED=0`, so it needs no C compiler; and `GOCACHE` and `GOPATH` in the cache folder, so later runs reuse what earlier ones compiled.
- **Packages:** the standard library alone. A Go lab's project has a `go.mod` that names its module, under `example/`, and its Go version, and every run has it beside the learner's files.
- **Tests:** a test file is `<name>_test.go`. Each folder of test files, `tests/`, `tests/checks/` and the folders a later stage's runs put earlier stages' tests in, is a package of its own, which imports the learner's package from the module, as `example/ledger`. A test is a subtest whose name starts with its id, as in `t.Run("tst_... Waits for a token", ...)`. The runner runs `go test -json` on those packages and takes each subtest's result from its `pass` or `fail` event, and a failure's message from its first line of `t.Errorf` or `t.Fatalf`.
- **Builds:** `go vet` checks every package of the run first, and builds them as it does. Its first error, the compiler's or vet's, is the run's problem, and the tests don't run: `go test` vets only the packages it tests, and the learner's package is one the tests import.
- **Panics:** a panic ends its package's test binary. The test that panicked is an error, with the panic's message and the first line of the learner's code in its stack, and each test after it in the package is an error that says it didn't run.
- **Time:** a test of a rate limit, a retry or a timeout runs in a `testing/synctest` bubble, whose clock moves only when every goroutine in it is blocked, so a second's wait takes no time and comes out the same on every system.
- **Where:** only a lab that runs on the learner's machine.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Go's own archives, pinned and fetched by the runner (chosen) | The current release, a security release, from the Go project, on all six systems; checked by size and sha256, as the runner's other fetches are | 67 to 79 MB to fetch once on each system; the pins move by hand |
| go-bin from PyPI, in the lab's project | uv installs and locks it with the project's Python packages, on all six systems | A repackaging of Go by one person, not the Go project's |
| Go the learner installs | Nothing to fetch | Each learner has their own version, and one more install before the first stage |
| Tests in the learner's package, beside their files | Tests can reach what the package doesn't export | A test file of one stage can't sit in the same folder as another stage's under the same name, and tests see what the learner never meant to share |
| Modules through proxy.golang.org, such as testify | Familiar assertions, and libraries a gateway might use | A fetch on each lab's first run, and modules to pin and review, for what the standard library does |
| Real time in tests, with short waits | No fake clock to explain | Slow tests, and results that change with a busy machine |

## Evidence

- Go's [downloads in JSON](https://go.dev/dl/?mode=json) list go1.27.3 as stable, with each archive's size and sha256, and `https://go.dev/dl/go1.27.3.linux-amd64.tar.gz` answers with a redirect to `https://dl.google.com/go/go1.27.3.linux-amd64.tar.gz`. [Release history](https://go.dev/doc/devel/release): "go1.27.3 (released 2026-10-19) includes security fixes to the crypto/x509 package", and "Each major Go release is supported until there are two newer major releases."
- [Go toolchains](https://go.dev/doc/toolchain): "When GOTOOLCHAIN is set to local, the go command always runs the bundled Go toolchain."
- [Go modules reference](https://go.dev/ref/mod): GOPROXY's "off: disallows downloading modules from any source"; "Since Go 1.16, the go command acts as if -mod=readonly were set"; and "The paths example and test are reserved for users: they will not be used in the standard library and are suitable for use in self-contained modules".
- [The go command](https://pkg.go.dev/cmd/go): "As part of building a test binary, go test runs go vet on the package and its test source files to identify significant problems. If go vet finds any problems, go test reports those and does not run the test binary. Only a high-confidence subset of the default go vet checks are used."
- [test2json](https://pkg.go.dev/cmd/test2json): the events' fields, the actions `run`, `pass`, `fail`, `output` and `skip`, and `OutputType` "error - an error produced by Error(f) or Fatal(f)". [Go 1.24's release notes](https://go.dev/doc/go1.24): "go test -json now reports build output and failures in JSON, interleaved with test result JSON."
- [testing/synctest](https://pkg.go.dev/testing/synctest), added in Go 1.25: "Within a bubble, the time package uses a fake clock. Each bubble has its own clock. The initial time is midnight UTC 2000-01-01. Time in a bubble only advances when every goroutine in the bubble is durably blocked."
- [Go telemetry](https://go.dev/doc/telemetry): "By default, telemetry data is kept only on the local computer, but users may opt in to uploading an approved subset of telemetry data to telemetry.go.dev."
- PyPI's JSON for [go-bin](https://pypi.org/project/go-bin/): 1.27.3, "Prebuilt golang binary", from github.com/jmelahman/go-bin, with wheels for macOS on x86-64 and arm64, manylinux on x86-64 and aarch64, `win_amd64` and `win_arm64`.
- A spike ran Go 1.27.3 from its archive on GitHub's Windows, macOS and Linux runners on x86-64 and Arm, from a folder whose name had accented letters, and each run took 15 to 55 seconds, Go's download included. On each, `go test -json` gave the same result for every subtest, named for its id, a subtest's fake second in `synctest.Test` took no time, a failure's `t.Errorf` line came as `error` output, a panic's message and stack came as output of the test that ran it, and a package that didn't build, or that vet refused, came as `build-output` events.

## Why

The runner already fetches and pins what pip can't install, Node.js and llama.cpp's server among them, so Go joins them with the same checks and the same cache folder, and the learner still installs only uv. Go's own archives are the current security release on every system, from the project that makes them. The standard library has what a gateway needs, an HTTP server and client, contexts and a fake clock for tests, so a run fetches nothing past Go itself. Tests in packages of their own test what the learner's package exports, as its users would. The strongest case against: the runner carries a third language's toolchain, whose pins move by hand.

## Consequences

A learner's first Go run fetches 67 to 79 MB from dl.google.com, and later runs, in any lab, use the copy in the cache folder. Go keeps counts of its own use in the learner's config folder, and uploads none unless they turn that on. A lab's tests reach only what its package exports, and a starter returns a zero value or an error rather than panicking, since a panic stops the tests after it. A run vets and builds before it tests, which adds a second or two. The lab's page says what the first run downloads and from where, and the Privacy Policy names dl.google.com. The page shows a Go stage's solution in the editor, which doesn't read Go, until the editor gains Go.

## Revisit when

Go 1.27 leaves support, a lab needs a module from outside the standard library, or the browser can run Go's tests.
