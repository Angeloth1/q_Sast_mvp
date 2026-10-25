import ast
import sys

import estimates


class QuantumScanner(ast.NodeVisitor):
    def __init__(self, constants=None):
        self.flags = []
        # Ονόματα μεταβλητών με γνωστή ακέραια τιμή, π.χ. {"KEY_SIZE": 2048}.
        # Τα συμπληρώνει η collect_int_constants πριν ξεκινήσει το scan.
        self.constants = constants or {}

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

    def _get_constant_value(self, value_node):
        # Μεταβλητή (π.χ. key_size=KEY_SIZE): ψάχνω αν ξέρουμε την τιμή της.
        if isinstance(value_node, ast.Name):
            return self.constants.get(value_node.id)

        return _int_literal(value_node)


def _int_literal(node):
    """Ο ακέραιος, αν το node είναι γραμμένος αριθμός (π.χ. 2048). Αλλιώς None."""
    if not isinstance(node, ast.Constant):
        return None
    # type(...) is int και όχι isinstance: το True είναι κι αυτό int στην Python.
    if type(node.value) is not int:
        return None
    return node.value


def collect_int_constants(tree):
    """
    Βρίσκει μεταβλητές που παίρνουν τιμή ΜΙΑ φορά σε όλο το αρχείο,
    και η τιμή αυτή είναι γραμμένος ακέραιος, π.χ. KEY_SIZE = 2048.

    Αν ένα όνομα παίρνει τιμή πάνω από μία φορά, δεν το κρατάμε:
    στατικά δεν ξέρουμε ποια τιμή ισχύει τη στιγμή της κλήσης.
    """
    assignment_count = {}   # όνομα → πόσες φορές παίρνει τιμή
    int_values = {}         # όνομα → ακέραια τιμή (μόνο από απλό "X = 2048")

    for node in ast.walk(tree):
        # Κάθε μορφή ανάθεσης: X = ..., X += ..., for X in ..., a, X = ...
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            assignment_count[node.id] = assignment_count.get(node.id, 0) + 1
        # Παράμετροι συνάρτησης: def f(X): η τιμή έρχεται από τον καλούντα.
        elif isinstance(node, ast.arg):
            assignment_count[node.arg] = assignment_count.get(node.arg, 0) + 1

        # Η μόνη μορφή που μας δίνει τιμή: X = 2048 ή X: int = 2048
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target, value = node.targets[0], node.value
        elif isinstance(node, ast.AnnAssign):
            target, value = node.target, node.value
        else:
            continue

        number = _int_literal(value)
        if isinstance(target, ast.Name) and number is not None:
            int_values[target.id] = number

    return {
        name: number
        for name, number in int_values.items()
        if assignment_count.get(name) == 1
    }


def scan_file(path):
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source, filename=path)
    scanner = QuantumScanner(constants=collect_int_constants(tree))
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