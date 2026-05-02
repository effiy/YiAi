Invoke the `wework-bot` skill to send a WeChat Work bot message.

Arguments: `$ARGUMENTS`

Execution requirements:
- When the user's intent is to send a group notification, must execute `send-message.js` for real sending; do not stop at a draft.
- Long copy should use `--content-file`; short copy may use `--content`. Body must align with `message-contract`.
- When linked with `generate-document` / `implement-code`: run `import-docs` first, then `wework-bot`.
- Completion notification `☁️ Document sync` must reference real `import-docs` statistics; do not write placeholder numbers.
- Do not leak `API_X_TOKEN` or webhook plaintext.
