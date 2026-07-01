# Logging and data handling

The POC writes local JSONL session logs under:

```text
logs/sessions/
```

JSONL means one JSON object per line. It is useful for replay because each event can be read in order.

## Current log contents

Logs may include:

- timestamp
- session ID
- scenario ID
- sequence number
- event type
- inbound trainee action message
- validation result
- state snapshot

## Current privacy rule

Do not put real personal, medical, patient, trainee, or operational data into this POC.

The demo uses stubbed data only.

## Git rule

Session logs should usually not be committed.

The repo keeps `logs/sessions/` ignored so local demo runs do not accidentally become repo history.

## Future questions

Before this becomes anything beyond local demo work, I need answers for:

- What data is allowed in logs?
- How long should logs be kept?
- Who can read logs?
- How are logs deleted?
- Should logs be anonymized?
- Should review summaries hide raw event details?
- How do I handle real trainee names, if they ever appear?

## Simple rule for now

Use fake IDs. Keep logs local. Do not store real emergency, patient, or trainee data.

