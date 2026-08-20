import ast
import sys

import estimates


class QuantumScanner(ast.NodeVisitor):
    def __init__(self):
        self.flags = []

    def visit_Call(self, node):
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "generate_private_key"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "rsa"
        ):
            key_bits = self._extract_key_size(node)

            self.flags.append({
                "line": node.lineno,
                "algorithm": "rsa", #! It's hardcoded for now, but could be extended for other algorithms  # noqa: EXE001, EXE005
                "key_bits": key_bits,
            })
        self.generic_visit(node)

    def _extract_key_size(self, node):
        value_node = None

        for kw in node.keywords:
            if kw.arg == "key_size":
                value_node = kw.value
                break

        if value_node is None and len(node.args) > 1:
            value_node = node.args[1]

        return self._get_constant_value(value_node)

    @staticmethod
    def _get_constant_value(value_node):
        if value_node is None:
            return None
        if not isinstance(value_node, ast.Constant):
            return None
        if type(value_node.value) is not int:
            return None

        return value_node.value


def scan_file(path):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=path)
    scanner = QuantumScanner()
    scanner.visit(tree)
    return scanner.flags


def report(flags, path):
    """Μετατρέπει δεδομένα σε κείμενο. ΕΔΩ ζει η διατύπωση."""
    print(f"Αρχείο: {path}")
    print("=" * 68)

    if not flags:
        print("Δεν βρέθηκε κβαντικά ευάλωτη κρυπτογραφία.")
        return

    print(f"Ευρήματα: {len(flags)}\n")

    for flag in flags:
        print(f"Γραμμή {flag['line']}: {flag['algorithm'].upper()} key generation")

        key_bits = flag["key_bits"]

        if key_bits is None:
            print("    Μέγεθος κλειδιού: δεν προσδιορίστηκε στατικά")
            print("    Εκτίμηση κόστους: μη διαθέσιμη\n")
            continue

        print(f"    Μέγεθος κλειδιού: {key_bits} bits")

        est = estimates.beauregard(key_bits)

        print(f"    Κόστος επίθεσης κατά {est.model} ({est.citation.year}):")
        print(f"        logical qubits    : {_fmt(est.logical_qubits)}")
        print(f"        Toffoli count     : {_fmt(est.toffoli_count)}")
        print(f"        measurement depth : {_fmt(est.measurement_depth)}")
        print(f"        πηγή: {est.citation.locator}")
        print(f"              {est.citation.open_access_url}")
        print()

    print("-" * 68)
    print("—  = η πηγή δεν δημοσιεύει τιμή σε συγκρίσιμη μορφή")
    print("Όλοι οι αριθμοί είναι LOGICAL qubits, όχι physical.")


def _fmt(value):
    if value is None:
        return "—"
    return f"{value:,}"


if __name__ == "__main__":
    file_to_scan = sys.argv[1] if len(sys.argv) > 1 else "target.py"
    report(scan_file(file_to_scan), file_to_scan)