# 45. Run a machine lab's Java stages with a JDK and JUnit the runner pins

- Status: accepted
- Date: 2026-10-26

## Context

Intermediate's optional Java module teaches Java to a programmer who knows Python, for the forward-deployed roles whose customers run Java: classes, records and interfaces, generics, collections and streams, exceptions, the JVM, JUnit, and a REST service. Its labs rebuild the help desk's API from Shipping full stack in Java. Java doesn't run in the browser's Pyodide, so its stages run on the learner's machine (decision record 28), on Windows, macOS and Linux each on x86-64 and Arm, with nothing for the learner to install but uv. A service needs JSON, which Java's standard library doesn't read or write, and its tests need a test framework. A run's results have to come back as a Python run's do: one per test, with its id, and the line of the learner's code where it failed.

## Decision

- **JDK:** Liberica JDK Lite 25.0.5.0.2+5, BellSoft's build of OpenJDK 25 with its modules compressed, from the archives BellSoft publishes for each of the six systems on its GitHub releases. `sulba_runner.py` pins each by its size and sha256 and fetches it into `sulba` in the learner's cache folder the first time a Java run needs it, as it fetches Go (decision record 43).
- **Libraries:** JUnit's console launcher 6.1.3, a single jar with JUnit Jupiter and the JUnit Platform, and Jackson 3.2.4 for JSON, its databind and core jars with Jackson's annotations 2.22, which it uses. The runner pins each jar by its sha256 and fetches it from Maven Central into the same folder. A run's classes see Jackson and the JDK, and its tests see JUnit too. A lab adds no other library.
- **Files:** a Java file is named for its class, as `Ticket.java`, and has no `package` declaration, so the learner's classes, the lab's given classes and the tests share Java's unnamed package, and a lab's download stays one flat folder an IDE opens as it is. A test file is `<Name>Test.java`, and a test class's name is the lab's own: two stages' tests, or a stage's tests and its checks, never share one, since each run puts them on one class path.
- **Tests:** a test is a JUnit Jupiter `@Test` method whose `@DisplayName` starts with its id, as `@DisplayName("tst_... Refuses a blank id")`. The runner compiles the learner's and the lab's classes with `javac`, then the tests, and runs them with the console launcher, which writes its legacy XML report. Each test's result comes from its entry there, found by its display name, with a failure's message, the expected and actual values of an `assertEquals`, and for an exception, the deepest line of the learner's own files in its stack.
- **Builds:** `javac`'s first error, with its file and line, is the run's problem, and the tests don't run. A class that doesn't compile with the tests, such as a starter without a method they call, is a problem too.
- **Settings:** a run leaves out `JAVA_TOOL_OPTIONS`, `JDK_JAVA_OPTIONS`, `_JAVA_OPTIONS` and `CLASSPATH` from its environment, so the learner's own Java settings don't change it, and reads Java's output as UTF-8.
- **Where:** only a lab that runs on the learner's machine.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Liberica JDK Lite, pinned and fetched by the runner (chosen) | OpenJDK 25.0.5, TCK-verified, on all six systems, at 80 to 83 MB each | One vendor's build, from GitHub releases; the pins move by hand |
| Azul Zulu, pinned and fetched by the runner | 25.0.5, TCK-verified, on all six systems | 227 to 232 MB to fetch on each |
| Eclipse Temurin | The Eclipse Foundation's build, widely used | No build of 25 for Windows on Arm, and Windows on x86-64 a release behind |
| Microsoft's build of OpenJDK | Builds for all six systems | 215 to 225 MB each, and macOS a release behind |
| A JDK the learner installs | Nothing to fetch | Each learner has their own version, and one more install before the first stage |
| Gradle, with the libraries it resolves | The build tool many Java teams use, with locked dependencies | A daemon and a distribution of its own to fetch, and seconds of start-up on every run, for a lab's few classes and four jars |
| A package for the learner's classes, as `package desk;`, in a flat folder | The way Java services name their classes | An IDE reports every file whose package doesn't match its folder |

## Evidence

- BellSoft's API, `api.bell-sw.com/v1/liberica/releases` for version 25 and bundle `jdk-lite`, read on 26 October 2026: 25.0.5.0.2+5 for Windows, macOS and Linux on x86 and ARM, 64-bit, each TCK-verified, at 80,303,853 to 83,098,331 bytes, from `github.com/bell-sw/Liberica/releases/download/25.0.5.0.2+5/`. Its [release notes](https://docs.bell-sw.com/liberica-jdk/25.0.5.0.2b5/general/release-notes/): "an unscheduled patch release for vulnerability fixes in Liberica JDK 25.0.5.0.2."
- BellSoft, [Choosing Liberica JDK flavor](https://docs.bell-sw.com/liberica-jdk/25.0.5.0.2b5/how-to/choosing-flavor/): Lite "is a full-fledged, Java SE-compliant runtime but much smaller than any standard Java distribution. We didn't remove any components to trim down its size; instead, we introduced multiple enhancements, such as better compression for modules."
- Azul's metadata API for Zulu 25.0.5 (25.38.107): builds for the six systems, 226,556,000 to 232,039,000 bytes. Adoptium's API for Temurin 25: no build for Windows on aarch64, and 25.0.4.1 for Windows on x64 against 25.0.5 elsewhere. Microsoft's `aka.ms/download-jdk` links for 25: 25.0.5.0.2 for Linux and Windows, 25.0.4.1 for macOS, 215,867,316 to 224,665,284 bytes.
- [JDK 25](https://openjdk.org/projects/jdk/25/): "General Availability on 16 September 2025." [JEP 400](https://openjdk.org/jeps/400): "Specify UTF-8 as the default charset of the standard Java APIs." [JEP 444](https://openjdk.org/jeps/444): "Introduce virtual threads to the Java Platform."
- JUnit, [Console Launcher](https://docs.junit.org/6.1.3/running-tests/console-launcher.html): "An executable Fat JAR (junit-platform-console-standalone-6.1.3.jar) that contains the contents of all of its dependencies is published in the Maven Central repository", "typically invoked directly from the command line or a shell script without a build script", and "status code 1 is returned if any containers or tests failed." [JUnit Platform Reporting](https://docs.junit.org/6.1.3/advanced-topics/junit-platform-reporting.html): "The LegacyXmlReportGeneratingListener is used by the Console Launcher as well."
- Maven Central's metadata for `tools.jackson.core:jackson-databind`: 3.2.4 is the latest release, and its parent `jackson-base` 3.2.4 sets `jackson.version.annotations` to 2.22.
- Spring Boot, [JSON](https://docs.spring.io/spring-boot/reference/features/json.html): "Jackson 3 is the preferred and default library."
- [The Java Language Specification, Java SE 25, chapter 7](https://docs.oracle.com/javase/specs/jls/se25/html/jls-7.html): "A compilation unit that has no package declaration is part of an unnamed package", and "Unnamed packages are provided by the Java SE Platform principally for convenience when developing small or temporary applications or when just beginning development."
- A spike ran Liberica JDK Lite 25.0.5.0.2+5 from its archive on GitHub's Windows, macOS and Linux runners on x86-64 and Arm, from a folder whose name had accented letters, and each run took 6 to 16 seconds, the JDK's and the jars' downloads included. On each, `javac` compiled a project using Jackson and `jdk.httpserver`, the console launcher exited with 1 for a run with failures, and its XML report gave every test's result under its display name: a test of an HTTP server on virtual threads answering JSON in UTF-8, ten thousand virtual threads, a fake clock passed to the code, an `assertEquals` failure with its expected and actual values, and an exception with the line of the code under test in its stack. A file that didn't compile gave its file, line and message as `javac`'s first error.

## Why

The runner already fetches and pins what pip can't install, Node.js and Go among them, so a JDK joins them with the same checks and the same cache folder, and the learner still installs only uv. Liberica Lite is the only build of 25.0.5 for all six systems at under 100 MB, about a third of the size of the others, and it's a whole JDK, `javac` and `jdk.httpserver` included. JUnit's launcher runs the tests a Java team would write, without a build tool, and Jackson 3 is the JSON library Spring Boot defaults to. The unnamed package keeps a lab's files flat, like every other lab's. The strongest case against: Java services always name their packages, and teams build with Gradle or Maven, which the labs leave out.

## Consequences

A learner's first Java run fetches about 80 MB from github.com and 5.7 MB from repo1.maven.org, and later runs, in any lab, use the copies in the cache folder. A run compiles before it tests, which adds a second or two to the JVM's start. A lab's tests reach what its classes make public or leave package-private, since they share the unnamed package. The content check refuses a Java test class that two of a lab's test files define. The lab's page says what the first run downloads and from where, and the Privacy Policy names github.com and repo1.maven.org. The page shows a Java stage's solution in the editor, which doesn't read Java, until the editor gains Java.

## Revisit when

Java 25 leaves BellSoft's support, a lab needs a library past JUnit and Jackson, or a lab is worth building with Gradle.
