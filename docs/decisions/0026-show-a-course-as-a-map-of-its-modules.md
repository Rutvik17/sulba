# 26. Show a course as a map of its modules

- Status: accepted
- Date: 2026-10-17

## Context

A course's page listed every lab with its summary and facts. For Beginner's 8 modules and 40 labs it ran 11.5 screens on a 1280 × 900 laptop and 17.2 on a 390 × 844 phone. Its first screen showed the course's title and two labs, nothing said what the modules were, and nothing led back to where a learner left off. Each new lab added a quarter of a screen on a laptop, and the course plan has five levels. The page is prerendered and loads no framework (records 1 and 11). Progress comes from the browser and, signed in, the account (records 18 and 19). Record 17 asks each level to state the machine it needs before it begins.

## Decision

- **The next lab:** a card at the top names the learner's next lab, with Start, or with Continue and the stages done. It is the first lab started but not done; else the first not done after the last one done; else the first not done. With every lab done there is none.
- **Levels:** each level states how many modules and labs it has, their time, the machine it needs (`needs` in `course.yaml`) and, once the learner has started, the labs done.
- **Modules:** each module is a numbered row, closed at first: its title, its labs and their time, a mark per lab that fills as its stages pass, and every lab's title as a link. The title is a button inside a heading, with `aria-expanded`, a chevron and Show or Hide. Opening a module shows its labs: number, title, summary, files, stages, time and progress. Several modules can be open at once, and Show all modules opens every one. A link to a module (`/<course>/#<module>`) opens it. A closed module's labs are `hidden="until-found"`, so find in page opens the module it finds text in.
- **Without JavaScript:** every module shows open under a plain heading.
- **One page:** a course keeps one page while it fits in four screens with every module closed. Past that, each level gets its own page.

## Options

| Option | What it does well | Where it falls short |
| --- | --- | --- |
| Closed module rows that show their labs' titles (chosen) | A level in about two screens; every lab one click away; the nearest tested pattern, GOV.UK's step by step | A module's details take a click; turning a heading into a button needs JavaScript |
| Every lab in full, as before | Nothing to open | 11.5 screens on a laptop and 17.2 on a phone, growing with every lab |
| A contents list at the top, every lab in full below | Jump links to each module | The page stays 11.5 screens long; NN/g finds jump links suit pages read only in part |
| A page per level now | Short pages at any size | With one level, a page that lists one level, and a click more to every lab |
| Levels as tabs | One level in view at a time | GOV.UK: tabs are not page navigation and don't suit content read in order |
| A native `details` element per module | Works without JavaScript; find in page opens it | A heading inside `summary` loses its role for some screen readers, and a restyled marker's state is announced unreliably |

## Evidence

- Course pages on 15 learning sites, loaded signed out on 17 October 2026 at 1280 × 900 and 390 × 844: [Coursera](https://www.coursera.org/learn/machine-learning), [edX](https://www.edx.org/certificates/professional-certificate/ibm-data-science), [Udemy](https://www.udemy.com/course/100-days-of-code/), [DataCamp](https://www.datacamp.com/tracks/associate-data-scientist-in-python), [Khan Academy](https://www.khanacademy.org/math/algebra), [freeCodeCamp](https://www.freecodecamp.org/learn/responsive-web-design-v9/), [The Odin Project](https://www.theodinproject.com/paths/full-stack-javascript), [Exercism](https://exercism.org/tracks/python), [Codecademy](https://www.codecademy.com/learn/learn-python-3), [boot.dev](https://www.boot.dev/paths/backend), [Scrimba](https://scrimba.com/frontend-path-c0j), [roadmap.sh](https://roadmap.sh/ai-engineer), [Brilliant](https://brilliant.org/courses/thinking-in-python/), [Frontend Masters](https://frontendmasters.com/learn/fullstack/) and [Hack The Box Academy](https://academy.hackthebox.com/path/preview/penetration-tester).
  - Rows start closed and show counts and time on Coursera ("Week 1 • 7 hours to complete"), edX, Udemy ("7 lectures • 58min"), Codecademy, Scrimba ("Web dev basics 0/80 6.3 hrs") and freeCodeCamp ("0 of 302 steps complete").
  - One action leads back in: freeCodeCamp's Continue Learning and The Odin Project's Resume (in their published source), and edX's Resume Course and Khan Academy's Up Next (in their help pages).
  - Coursera, edX, The Odin Project, DataCamp and Frontend Masters give each level of a programme its own page.
  - Khan Academy opens everything: 19 screens on a laptop and 31 on a phone.
- GOV.UK Design System, [Accordion](https://design-system.service.gov.uk/components/accordion/): "Do not use an accordion for content that all users need to see" and "Do not put accordions within accordions"; without JavaScript all content shows; the whole heading is the button, with show and hide text.
- GOV.UK, [Step by step navigation](https://components.publishing.service.gov.uk/component-guide/step_by_step_nav): "each step should be collapsed by default so that users are not overwhelmed"; users can show or hide all steps at once.
- NN/g, [Accordions on Mobile](https://www.nngroup.com/articles/mobile-accordions/): opening the first section by default kept users from seeing the page's structure; scrolling an opened section to the top made users think a new page had loaded.
- NN/g, [Accordion Icons](https://www.nngroup.com/articles/accordion-icons/): "Use a caret icon"; the label and the icon should do the same thing.
- NN/g, [Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/): "designs that go beyond 2 disclosure levels typically have low usability".
- NN/g, [Scrolling and Attention](https://www.nngroup.com/articles/scrolling-and-attention/): "81% of the viewing time is spent in the first three screenfuls"; [Back-to-Top](https://www.nngroup.com/articles/back-to-top/): for pages "longer than 4 screens".
- W3C, [ARIA Authoring Practices: Accordion](https://www.w3.org/WAI/ARIA/apg/patterns/accordion/): each header a `button` inside a heading, with `aria-expanded` and `aria-controls`.
- MDN, [`<summary>`](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/summary): a heading inside it "will not be treated as a heading" by some browsers. MDN's compatibility data: `hidden="until-found"` works in Chrome 102, Firefox 148 and Safari 26.2.
- Scott O'Hara, [The details and summary elements, again](https://www.scottohara.me/blog/2022/09/12/details-summary.html): with the marker restyled, "VoiceOver, JAWS and NVDA all have an issue with consistently announcing the toggled state".
- Measured in Chromium on a build of the course: 2.2 screens on a laptop and 2.5 on a phone with every module closed, 3.1 and 3.9 with one open, 8.6 and 12.2 with all of them open.

## Why

The rows fold away only what a learner doesn't always need, a lab's summary and facts, and keep every lab's title on the page, so the whole level fits in the first three screens, where most attention goes. Rows that start closed with their counts are what most of the sites do, and the card at the top is the one way back in they share. A button in a heading behaves the same in every screen reader, and `hidden="until-found"` keeps find in page working, which a native `details` element gives only with less reliable announcements. The strongest case against: a learner who wants every summary has a click to make, and Show all modules makes the page long again.

## Consequences

Each level in `course.yaml` says what it needs. The page's script turns each heading into a button and closes the modules; until it runs, a style keeps the labs closed, so the page doesn't jump. If the script never runs, the labs' titles still link every lab. The next lab is worked out from passes alone, so a learner with two labs started is sent to the earlier one.

## Revisit when

The page passes four screens with every module closed, or learners need to search a course.
