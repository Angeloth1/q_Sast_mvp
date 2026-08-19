from dataclasses import dataclass


@dataclass(frozen=True)
class Citation:
    authors: str
    year: int
    title: str
    venue: str
    locator: str                      # where in the paper to find the relevant information
    doi: str | None = None
    open_access_url: str | None = None


@dataclass(frozen=True)
class Estimate:
    model: str
    citation: Citation
    provenance_class: str             # peer-reviewed | unverified | original
    logical_qubits: int | None        
    toffoli_count: int | None
    measurement_depth: int | None
    note: str = ""


BEAUREGARD_2003 = Citation(
    authors="S. Beauregard",
    year=2003,
    title="Circuit for Shor's algorithm using 2n+3 qubits",
    venue="Quantum Information and Computation 3(2):175-185",
    locator="abstract (2n+3, gates, depth)· conclusion (ανάλυση qubits)",
    doi="10.5555/2011517.2011525",
    open_access_url="https://arxiv.org/abs/quant-ph/0205095",
)


def beauregard(n: int) -> Estimate:
    """
    Beauregard 2003 — family: factorization.
    n = number of bits of the modulus to be factored.
    """
    return Estimate(
        model="Beauregard 2003",
        citation=BEAUREGARD_2003,
        provenance_class="peer-reviewed",
        logical_qubits=2 * n + 3,
        toffoli_count=None,
        measurement_depth=None,
        note=(
            "Qubit analysis: n (value) + n (auxiliary register) "
            "+ 1 ancilla + 1 overflow + 1 control. "
            "Toffoli count: not published· the paper gives total "
            "elementary gates O(n^3 lg n), which is another metric. "
            "Depth: only given asymptotically, O(n^3) — not computable. "
            "Estimate per execution· Shor is probabilistic."
        ),
    )