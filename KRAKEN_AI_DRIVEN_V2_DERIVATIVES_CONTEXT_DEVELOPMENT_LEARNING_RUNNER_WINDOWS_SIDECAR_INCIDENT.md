# Kraken AI-Driven V2 Context Learning Runner Windows Sidecar Incident

## Boundary

The first Windows reproduction of the uncommitted Development runner package
stopped during focused tests. No Git staging, commit or push occurred. The
Kraken archive and derivatives-context Dataset Lock were not opened; no label,
model, prediction, result directory or order was created.

## Root cause and correction

The synthetic evidence fixture used text-mode sidecar writes. Windows converted
the requested LF line ending into CRLF, while the independent reader correctly
required the canonical byte sequence recorded by the evidence protocol. The
same text-mode calls also existed in the real runner output path.

All report and prediction SHA-256 sidecars now use binary ASCII writes with one
explicit LF byte. Tests assert both successful byte verification and absence of
a CRLF suffix. Evidence validation remains strict; the reader was not relaxed.

This is an implementation-review recovery, not a consumed learning attempt.
Real Development training still requires its original separate one-shot
authorization after the corrected runner is reproduced, committed and
preflighted.
