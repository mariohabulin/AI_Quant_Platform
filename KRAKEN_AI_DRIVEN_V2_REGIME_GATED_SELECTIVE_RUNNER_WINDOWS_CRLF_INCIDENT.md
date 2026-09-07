# Kraken AI-Driven V2 Regime-Gated Selective Runner Windows CRLF Incident

## Boundary and observed failure

Commit `7c68bfe` was transferred exactly to Windows and its focused suite stopped
before push. The static review rejected `runner_protocol` because the newly
introduced Markdown protocol had been checked out with CRLF bytes while its
frozen SHA-256 represented LF bytes. The later `runner_component` tamper case
then encountered the same earlier protocol mismatch.

## Impact

The failure occurred during static implementation review. No real Development
archive or derivatives-context value was opened, no label or model was created,
and no economic result or remote commit was produced. Calibration, Evaluation,
Candidate v2, PAPER, cloud and live execution remained closed.

## Bounded correction

The correction adds explicit `text eol=lf` attributes only for the five new
runner protocol/source/test files, binds `.gitattributes` into the static source
registry and changes the protocol and runner blobs so Windows checks them out
again under the new policy. Hash comparison remains byte-exact; no outcome,
feature, fold, learner, threshold, gate, fit budget or authorization field is
changed.
