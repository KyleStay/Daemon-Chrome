# Background 1.0.2 candidate

The production package follows the existing 1.0.1 manifest and current store listing. Build with `python3 scripts/package.py`; run package contracts with `python3 -m unittest discover -s tests -v`.

Use `python3 scripts/package.py --mode dev` for a separately labeled 1.0.2.1 unpacked candidate at `dist/dev`. Keep its absolute directory unchanged to retain the path-derived Chrome ID. Moving it changes that ID. A higher version cannot replace a different extension ID.

Use `python3 scripts/package.py --mode replacement --public-key-file /path/to/existing-public-key.txt` for explicit same-ID replacement preparation. The tool accepts only a public key deriving to the existing store ID `mfcallgpgnojmoaffommnnbfojdghfck`, otherwise it writes no replacement output. Never provide a private signing key. Loading a same-ID build is a replacement workflow and requires a reload of affected contexts; it is not simultaneous execution of two IDs. The reviewed public store CRX and its signature-verified key are retained in release evidence; no browser installation was changed.

This extension has only the browser's `background` permission. It has no worker, content scripts, timers, observers, commands, or page UI to elect or tear down. Separate current or old instances independently request the same process-level browser behavior. They do not supersede each other. The process can remain in background while either extension requests it; removing one does not revoke the other's request. This is a source-level expectation, pending disposable-browser validation. Never add management permission or page messaging for this product.

The supplied permission-free Chrome for Testing runner is the validation route. Test both load orders, closing/reopening windows, browser restart, and removal in a disposable profile. Runtime testing here was blocked by `/bin/ps` EPERM during owner-identity preflight before allocating a profile or starting Chrome. Do not bypass that boundary or use the user's profile. Chrome is the intended target; Firefox/Safari are unsupported and other Chromium browsers are unverified. No numeric browser floor is asserted without platform testing.

Upload only the production ZIP to the existing listing after release checks. The replacement and dev ZIPs are local testing artifacts. No upload or store approval happened during preparation.
