# q-SAST

[![License: PolyForm Noncommercial 1.0.0](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-blue)](LICENSE)

Static analysis for Python source that finds quantum-vulnerable
cryptography and **quantifies the cost of breaking it** — using published
quantum resource-estimation models, with every number traceable to its
source.

## The gap this fills

Cryptographic Bill of Materials (CBOM) tooling is a mature space. IBM
CBOMkit, `csnp/cryptoscan`, and several commercial products all answer the
same question well: *is there quantum-vulnerable cryptography in this
codebase, yes or no?*

For asymmetric cryptography that answer is always yes, and it does not
change with key size, algorithm, or context. It carries almost no
information.

q-SAST answers a different question: **given a specific key size at a
specific call site, what would it actually cost a fault-tolerant quantum
computer to break it — according to which published model, from which year,
under which assumptions?**

## Traceability, not correctness

q-SAST does not claim its numbers are right. It claims you can check where
each one came from.

Every estimate carries a structured citation pointing at the *location* of
the figure inside the paper — section, table, equation — not merely at the
paper. Verification is therefore a two-minute task: open the PDF, go to the
stated location, confirm the number. No code reading required.

This is a deliberate constraint. A platform that guarantees correctness
needs a permanent maintainer. A platform that guarantees traceability does
not.

## Example

```
$ python scripts/analyzer.py scripts/target.py

Line 16: RSA key generation
    Key size: 2048 bits
    Attack cost per Beauregard 2003:
        logical qubits    : 4,099
        Toffoli count     : —
        measurement depth : —
        source: abstract (2n+3, gate count, depth)
                https://arxiv.org/abs/quant-ph/0205095

Line 49: RSA key generation
    Key size: not statically determined
    Cost estimate: unavailable
```

## Architecture

```
source ──ast.parse──► tree ──scanner──► findings ──report──► output
                                            │
                                       estimates
```

Three responsibilities, deliberately separated:

| module | job | knows nothing about |
|---|---|---|
| `analyzer.py` | detect calls, extract parameters | cost models, severity, wording |
| `estimates.py` | encode published models | files, ASTs, findings |
| `report()` | turn data into text | how anything was found or computed |

The scanner emits **data** — `{line, algorithm, key_bits}` — never prose.
All judgement and phrasing lives in the reporting layer.

### Planned: one file per model — NOT YET IMPLEMENTED

The structure above is the current state, not the target. `estimates.py`
currently holds both the data structures and the single model, which does
not scale and does not satisfy the contribution rule below.

The intended layout:

```
models/
  schema.py           # Citation, Estimate — data structures only
  beauregard_2003.py  # one paper, one file
  gidney_ekera_2019.py
```

Two properties this is designed for:

- **No contributor touches shared code.** Adding a model means adding one
  file named `<author>_<year>.py`. Models are discovered by scanning the
  directory — there is no registry list to edit, so no shared file is a
  merge point.
- **No model imports another.** A faulty contribution costs one table row,
  not the project.

A validator will enforce structure on every file in `models/`: required
fields populated, `locator` non-empty, `doi` or `open_access_url` present,
`provenance_class` from the permitted set, all three cost axes explicitly
declared, and a verification test that reproduces a published figure. It
will also warn — not reject — when a paper already present under the same
algorithm family is added again, since the same paper can legitimately
yield several models (a published Pareto frontier, for instance) and
independent reimplementation of an existing model is desirable.

Style is checked separately with `ruff`. Note that a linter checks syntax
and style, not structural contract — the two are different jobs and need
different tools.

Tracked as issues. Until this lands, treat the module layout as unstable.

### Why `estimates.py` must not import `ast`

Two structural reasons:

1. **Standalone research use.** Comparing RSA-3072 against P-256 at equal
   classical security is a valid query with no source code involved. If
   estimators consumed findings, that use case would be impossible.
2. **Differential validation.** Cross-checking against independent
   implementations — Qualtran (Google) and the Azure Quantum Resource
   Estimator (Microsoft) — requires passing `(algorithm, parameter)`, not
   an internal finding object. The separation is a precondition for the
   validation strategy, not tidiness.

## Core contract: `None` is not `0`

`None` appears in three places and means the same thing everywhere —
**unknown**:

| field | meaning of `None` |
|---|---|
| `key_bits` | not statically determinable (e.g. a variable) |
| `toffoli_count` | the paper does not publish this figure |
| `measurement_depth` | given asymptotically only; not computable |

It renders as `—`, never as zero. Beauregard's circuit certainly contains
Toffoli gates; the paper simply does not count them. Reporting `0` would be
a false claim, and would sort that model to the top of any cost ranking.

Consequence for contributors: test with `is None`, never `if not value` —
`0` is falsy and the two cases would silently merge.

## Model policy

> **Never replace, only add. Never rank, only list.**

A new model does not supersede an older one. Two reasons:

- No contribution loses its value because a later one arrived.
- The **trajectory of estimates over time** is itself among the most
  interesting results — 20M physical qubits for RSA-2048 in 2019, under 1M
  in 2025, sub-100k claimed for qLDPC codes in 2026. That trajectory
  disappears if newer numbers overwrite older ones.

Publication year is a **column**, not a branch or a directory.

What is immutable is the **claim**, not the code. Fixing a mis-transcribed
formula is required. Changing which paper a model represents is not.

## Contributing

One paper → one model → one file. No contact with core code.

> **Not yet mechanically enforced.** The `models/` layout and its validator
> are not implemented (see Architecture). The rules below are the contract
> the structure is being built around, and they apply to contributions now
> — they are just checked by hand until the validator lands.

Every model ships with a test that **reproduces a figure printed in the
paper itself**, with a citation pointing at that figure's location.

This is not bureaucracy. If a test asserts against a number you produced by
running your own formula, it is circular and proves nothing — a
mis-transcribed formula passes it silently. The anchor must be a value
printed in the source.

### Provenance classes

Every estimate declares one, and it appears in the output:

| class | requirement |
|---|---|
| `peer-reviewed` | published paper + test reproducing a published figure |
| `unverified` | paper gives asymptotics only; no anchor point exists |
| `original` | our own derivation, committed alongside the code |

The classification follows from available evidence rather than anyone's
judgement: a paper with no concrete published figure yields `unverified`
automatically.

`original` exists because a rule of "always cite a paper" would forbid the
best possible outcome — a contributor producing a *new* estimate rather
than implementing someone else's. It carries the same documentation burden;
the evidence is a thesis or technical note instead of a publication. It is
labelled so nobody confuses an industrial lab's estimate with a student's.

### Review is a label, not a gate

Contributions are not blocked on review. A model that passes CI merges and
is marked `unreviewed`; that label shows in the output. An unreviewed model
sitting for six months poisons nothing — it reads as unreviewed.

This makes verification asynchronous and delegable. A contributor who has
moved on blocks nobody, because verification needs the PDF, not them.

## Coverage

| | supported |
|---|---|
| Languages | Python |
| Detection | RSA private key generation |
| Argument forms | keyword, positional, mixed, reordered |
| Models | Beauregard 2003 |
| Axes | logical qubits (Toffoli count and depth: `—`) |
| Cost level | logical only |
| Model plugin structure | not implemented — see Architecture |
| Contribution validator | not implemented |

## Known limitations

Stated explicitly, because each is a well-defined piece of work rather than
an oversight.

- **Detection matches identifiers as strings.** `import ... as r` is
  missed; an unrelated class named `rsa` yields a false positive.
- **Key sizes are read only as integer literals.** Variables and
  expressions yield `None`. Deliberate: naive assignment tracking produces
  *confidently wrong* answers when a name is reassigned, which is worse
  than declining to answer.
- **All estimates are logical, not physical.** The gap is orders of
  magnitude and depends on hardware assumptions.
- **Estimates are per run.** Shor's algorithm is probabilistic and may
  require repetitions.

## Non-goals

- **Not an operational decision tool for asymmetric cryptography.** The
  practical answer is always "migrate", whether the figure is 1,730 or
  6,190 logical qubits. The value here is educational and research-facing.
  (This changes for symmetric primitives — see open topics.)
- **Not a forecast.** It reports cost under stated assumptions, not when
  capable hardware will exist.
- **Not competing with CBOM tools on breadth.** They inventory; this
  quantifies.
- **Not a ranking.** Models are listed, never ordered by credibility.

## Open research topics

Each is thesis-sized, phrased as a question, with a starting point.

1. **Elliptic curves.** How many logical qubits and Toffoli gates does
   Shor's algorithm need for the discrete log on P-256, and how does that
   compare to RSA at equivalent classical security? A different circuit
   family — nothing transfers from the existing models.
   *Start: Roetteler et al., ASIACRYPT 2017.*

2. **Physical cost model.** Translating logical to physical qubits through
   surface-code overhead. A simple model yields ~7.7M for RSA-2048 against
   a published 20M; the difference is magic state factories. Can it be
   closed?
   *Start: Gidney & Ekerå 2019, physical costs; Fowler et al. 2012.*

3. **Symmetric primitives and hashes under Grover.** Only a quadratic
   speedup, so this is the one area where quantification yields genuinely
   different answers — "AES-128: marginal, AES-256: fine". Here the
   framework acquires decision value.

4. **Hierarchical circuit visualisation.** The full circuit (~2.6×10⁹
   Toffoli) cannot be drawn, but its decomposition can: modular
   exponentiation → controlled multiplication → modular addition → adder →
   gates, with multiplicities at each level, so the total is derived rather
   than asserted.
   *Start: Beauregard 2003, circuit construction sections.*

5. **Differential validation in CI.** Automatic comparison against Qualtran
   and the Azure Quantum Resource Estimator, catching transcription errors
   without a human reviewer.

6. **Static name resolution.** Two current failure modes — aliased imports
   and non-literal key sizes — are the same problem. What is the safe
   subset that can be resolved without producing confidently wrong answers?

## License

**PolyForm Noncommercial 1.0.0** — see `LICENSE`.

Source-available, not open source in the OSI sense. Reading, studying,
auditing, modifying, and contributing are all permitted. Use by educational
institutions, public research organisations, and government bodies is
explicitly permitted regardless of funding source. Commercial use is not.

Any copy or derived work must carry the `Required Notice:` lines from
`LICENSE`. The license obliges those lines to travel with the software; it
does not itself impose a citation requirement, which is why the citation
file below exists alongside it.

For academic citation, see `CITATION.cff` (GitHub renders a "Cite this
repository" button from it).

The license is a legal instrument; the citation file is an academic
convention. They cover different things and both apply.
