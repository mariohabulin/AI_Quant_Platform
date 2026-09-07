# US Equity Point-in-Time Result Review Windows CRLF Incident

## Scope

The first Windows reproduction of commit
`b041a231528e48fa21b4437b551a8afac1870e70` verified both downloaded package
hashes, fast-forwarded from `6a185e6d0dd9a7e31513f951a234601cfb9b06fa`
and verified all three immutable evidence hashes.

The focused suite then stopped with `38 passed, 1 failed`. Push was not
executed. Market values, labels, model training, paid data, real orders and live
execution remained closed.

## Failure

The failing test created temporary SHA-256 sidecars through
`Path.write_text`. Windows text-mode newline translation changed the intended
terminal LF byte into CRLF. The production feasibility writer already emits
canonical ASCII sidecars through `write_bytes`, and the downloaded evidence
package retained the correct hashes.

The external result reader correctly rejected the byte-different temporary
sidecar. The failure was therefore in the cross-platform test fixture, not in
the audit result or evidence package.

## Recovery boundary

The fixture must write sidecars as explicit ASCII bytes with a terminal LF. A
regression test must emulate Windows text-mode translation and prove that the
fixture no longer depends on it. The production reader remains strict; no
CRLF normalization or weakened hash acceptance is allowed.

Recovery requires the expanded 41-test focused suite, the complete 2,199-test
suite, static source binding and the unchanged external evidence review to
pass on Windows before any separate push authorization.
