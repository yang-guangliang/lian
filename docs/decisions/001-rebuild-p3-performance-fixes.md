# ADR-001: Rebuild P3 performance fixes from verified invariants

## Status

Accepted

## Date

2026-08-02

## Context

The `gxm9` branch made large P3 memory and runtime improvements, but its 27
commits are not 27 independent changes. The history starts with a 1,478-line
source checkpoint, repeatedly adds and removes mutable caches, and ends with an
864-line experimental checkpoint. Several later commits exist solely to repair
invalidation, aliasing, definition, or container-compatibility problems caused
by earlier optimizations.

The delivery branch is `gxm11`, based on `origin/master`. It must retain full
P3 entry-point, call-target, path, state, and context coverage. Passing the two
large C cases is not sufficient if decoded workspace semantics change.

## Decision

Do not merge or transplant the `gxm9` snapshots. Rebuild only independently
measured mechanisms on `gxm11`, one invariant and one commit at a time.

The implementation must follow these boundaries:

1. Compact summaries are immutable data. Runtime `State` and `Symbol` objects
   remain ordinary runtime objects; they are not replaced by lazy subclasses.
2. Do not disguise shared storage as a mutable `set`. Shared references use an
   explicit immutable representation, and a caller materializes a mutable
   value only at a documented write boundary.
3. Resolver and fusion caches are scoped by an explicit, immutable analysis
   snapshot. A frame-global dictionary or `id(mutable_set)` is not a validity
   proof.
4. Cache values are immutable. Reusing a mutable state graph across rounds or
   call sites is forbidden.
5. Streaming and representation-only changes are implemented before semantic
   graph reuse because they have smaller correctness surfaces.
6. Every optimization requires a before/after profile and decoded-workspace
   equivalence evidence. If equivalence cannot be proved, the optimization is
   rejected even when it is faster.

## gxm9 commit audit

| Commit | Disposition | Reason |
| --- | --- | --- |
| `f1fb281` | Decompose only | Mixed correctness fixes, serialization, graph deduplication, caches, and summary behavior in one checkpoint. |
| `dcb3735` | Reject implementation; retain concept | Copy-on-write mutable-set wrappers leaked a new container protocol throughout runtime code. |
| `67fc0d3` | Reimplement | Cached `CallPath` cycle metadata and direct trie path view are local and behavior-preserving. |
| `8600451` | Reimplement after baseline | Partition refinement has a measured 67.8s to 32.0s improvement and an identical mapping digest. |
| `251f543` | Redesign | Cache is keyed by `id()` of a mutable definition set and relies on implicit frame reset. |
| `f973cea` | Redesign and measure | Decoded mappings are reused as mutable dataclass objects; immutable cached records are safer. |
| `0426a01` | Do not transplant | First of several resolver identity-memo revisions; validity was incomplete. |
| `ba1c8a2` | Do not transplant | Repairs stale nested identity entries introduced by the preceding resolver cache. |
| `7f88d61` | Reimplement | Affine append mapping avoids a deterministic allocation without changing index lookup semantics. |
| `48607e5` | Redesign | Adds another mutable resolver cache with snapshot validity carried by convention. |
| `6efb7d1` | Already rebuilt | Covered by `a11b7dc` and stronger unresolved-index validation in `gxm11`. |
| `4857df9` | Do not transplant | Extends resolver-cache lifetime across roots; the original patch even contains duplicate initialization. |
| `345f801` | Reject with wrapper design | Micro-optimizes the rejected mapped mutable-set abstraction. |
| `ad71e93` | Redesign | Useful reachability memo idea, but it belongs in one explicit resolver snapshot index. |
| `a3049ed` | Split | Missing-index guard is already rebuilt; byte-bounded Arrow streaming is a low-risk candidate. |
| `30d199a` | Reimplement | Incremental JSON encoding avoids large temporary lists and preserves decoded values. |
| `6c93a26` | Reimplement with bounds checks | Bitmap/deque reachability removes large frontier sets without changing the closure. |
| `d3fe540` | Reject | Reused mutable fusion states before proving that their complete contents and definitions were stable. |
| `d767a2b` | Already rebuilt | Reimplemented and differentially verified by `ce6b82d`. |
| `df02ae6` | Reject implementation | Shares resolved tangping results through a mutable-set facade. |
| `67f0c1c` | Evidence only | Narrows the preceding cache after discovering stale cross-traversal values; does not remove its protocol risk. |
| `a687b98` | Reject implementation; retain concept | Lazy `State`/`Symbol` subclasses created pervasive data-structure compatibility risk. |
| `d2cfad5` | Evidence only | Repairs missing definition side effects in the first fusion cache. |
| `1f2d432` | Evidence only | Explicitly removes the unsafe mutable fusion cache. |
| `5ec7dda` | Redesign and measure | Full-content validation is useful, but reusable mutable fusion nodes remain the wrong cache value. |
| `527b901` | Reimplement | Reusing immutable SFG node/edge metadata inside one loop is local and low risk. |
| `af05642` | Reject snapshot; mine tests | Adds another large family of compact mutable containers, view caches, and unrelated incremental fixes. |

## Required implementation order

1. Correctness fixes extracted from `f1fb281`, each with a failing regression.
2. Baseline profiles for `CVE-2026-40527` and `CVE-2026-52860`.
3. Streaming, hashing, call-path, affine-index, and reachability improvements.
4. One explicit resolver snapshot index for repeated reachability and newest-state
   lookup; no layered memo patches.
5. Immutable callee-summary graph plus caller-local overlays, only if the first
   four steps do not meet the resource target.

## Consequences

This approach initially lands fewer optimizations than `gxm9`, but each retained
change has an independently reviewable correctness and performance argument.
Some large memory savings from lazy runtime subclasses are intentionally not
carried over; they may be recovered later behind an explicit summary/runtime
boundary instead of expanding the accepted container protocols of all P3 code.
