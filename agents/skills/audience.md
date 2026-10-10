---
name: audience
description: Use when deciding what a docs page should mention. The readers are developers who use NFFT3 in their software, not people who modify the library. Says what to keep, what to move and what to leave out. Triggers - "audience", "who reads this", "build page", "developer option", "internal file".
---

# Audience of the NFFT3 site

The first reader is a developer who builds NFFT3 and calls it from their own
software. This reader does not change the library. Write for this reader.
People who work on NFFT3 itself are a second audience. They get their own
section, `doc/development/`.

## Test for every fact

Ask: does a user who builds and uses the library need this to do the task?

- Yes: write it, in the main text.
- Only a library developer needs it: put it under `doc/development/`, or link
  there in one sentence. Do not put it in a user page.
- Nobody needs it: leave it out.

## Build files and generated files

Do not name a file that the build creates or reads unless the user must open
or edit it. Describe the effect, not the mechanism.

Leave out of user pages:

- Names of internal makefiles, `configure.ac`, m4 files and generated logs.
- Names of test programs and test result files. Say what the command does
  and how a failure looks on the terminal.

Keep in user pages: options that change what the user gets (modules,
precision, window, threads, interfaces, install prefix, location of FFTW),
the commands `configure`, `make`, `make check`, `make install`, and the names
of the installed libraries and headers.

## Check against the real build

Before you describe a build step, trace what a normal build does: unpack the
archive, `./configure`, `make`, optional `make check`, `make install`. Compare
your text with it. A step that this sequence does not run does not belong in
the main flow. State a default only when a user can see its effect.

## Options tables

Document every option that the project defines, for example every `configure`
option. Do not select a subset. Order the options by relevance. Put the
options that every user needs first. Put the other options in later sections
and say when they are relevant, for example "Use these options if you measure
the speed of the library". Do not describe how to use them beyond their
effect. Link to `doc/development/` for the procedure.
