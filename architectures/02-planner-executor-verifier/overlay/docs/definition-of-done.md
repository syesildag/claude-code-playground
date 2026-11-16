# Definition of Done (applies to every ticket)

- [ ] Every acceptance criterion in the ticket is met, and each one is covered by a test that would fail without
      the change.
- [ ] `python3 -m unittest` passes, with no new failures and no existing test edited to pass.
- [ ] No hard-coded status or priority names outside `taskboard/models.py`.
- [ ] User-supplied text written to HTML is escaped. File writes can't corrupt existing data.
- [ ] Error messages go to stderr as `error: <message>`, with exit code 1 and no traceback.
- [ ] Nothing outside the ticket's scope was changed.
