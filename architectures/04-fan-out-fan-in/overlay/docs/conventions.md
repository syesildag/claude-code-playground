# Code conventions

1. Every public function and method has type hints on all parameters and its return value.
2. Status names are only referenced through `STATUSES` (never as string literals outside `models.py`).
3. Modules import only what they use.
4. Errors shown to users go to stderr as `error: <message>`, never as a traceback.
5. Comments explain *why*, not *what*.
