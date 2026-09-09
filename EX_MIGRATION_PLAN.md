# Reva Android v1.6 — 3.0 EX Chinese migration

Goal: keep the v1.5 Android shell/input architecture and replace only the bundled Korean Final body with the latest verified 3.0 EX Chinese build.

Acceptance gates:

1. Verify source identity and size against a public 3.0 EX release page.
2. Confirm SWF header/declared length and compute SHA-256.
3. Launch under bundled Ruffle using the existing local HTTPS origin.
4. Preserve v1.5 pointer ownership, logical input state, DOM-key backend, and input black-box logging unchanged unless EX compatibility requires a targeted adaptation.
5. Verify Chinese title/menu text is actually present/visible before calling the migration complete.
6. Re-run Android 35 input regression and multi-touch stress tests.
7. Build a separate v1.6 APK; do not overwrite the last-known-good v1.5 artifact.

Source note: MHHF currently lists 雷巴的冒险 3.0 EX 汉化版 (game 4711), authored/recommended by 晓之车, and describes the latest update as 2026-03-21. The migration workflow should discover and validate the exact playable SWF rather than assuming the old Korean Final body is equivalent.
