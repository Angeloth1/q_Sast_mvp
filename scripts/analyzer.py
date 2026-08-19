import ast
import sys

import estimates


class QuantumScanner(ast.NodeVisitor):
    """Βρίσκει κλήσεις rsa.generate_private_key και εξάγει το key_size."""

    def __init__(self):
        self.flags = []

    def visit_Call(self, node):
        # ── ΦΑΣΗ ΤΑΥΤΟΠΟΙΗΣΗΣ ────────────────────────────────────────
        # "Αυτή η κλήση με αφορά;"  Ελέγχει το σχήμα rsa.generate_private_key
        #
        # ΓΝΩΣΤΟΣ ΠΕΡΙΟΡΙΣΜΟΣ: συγκρίνει το όνομα ως string. Ένα
        # `import ... as r` δεν πιάνεται, και μια άσχετη κλάση που τυχαία
        # λέγεται `rsa` δίνει false positive. Λύνεται με import
        # resolution — δεν είναι δουλειά του MVP.
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "generate_private_key"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "rsa"
        ):
            key_bits = self._extract_key_size(node)

            self.flags.append({
                "line": node.lineno,
                "algorithm": "rsa",
                "key_bits": key_bits,          # int ή None
            })

        # Συνέχισε την κατάβαση στο δέντρο — αλλιώς χάνεις φωλιασμένες κλήσεις
        self.generic_visit(node)

    def _extract_key_size(self, node):
        """Επιστρέφει int, ή None αν δεν προσδιορίζεται στατικά.

        Δύο φάσεις, χωριστά:
          Α) βρες τον ΚΟΜΒΟ του ορίσματος
          Β) αποτίμησε τον κόμβο σε αριθμό
        """
        # ── ΦΑΣΗ Α: βρες τον κόμβο ───────────────────────────────────
        value_node = None

        # Α1. Πρώτα τα keywords. Το όνομα είναι πάντα αξιόπιστο,
        #     ανεξάρτητα από τη σειρά που γράφτηκαν.
        for kw in node.keywords:
            if kw.arg == "key_size":
                value_node = kw.value
                break

        # Α2. Fallback στη θέση — ΜΟΝΟ αν δεν βρέθηκε keyword.
        #     Υπογραφή: generate_private_key(public_exponent, key_size, ...)
        #     → το key_size είναι το 2ο όρισμα, δηλαδή δείκτης 1.
        #     Ο έλεγχος len() είναι απαραίτητος: στα case_1/2/5 τα args
        #     είναι ΑΔΕΙΑ και το node.args[1] θα έσκαγε με IndexError.
        if value_node is None and len(node.args) > 1:
            value_node = node.args[1]

        # ── ΦΑΣΗ Β: αποτίμησε τον κόμβο ──────────────────────────────
        return self._get_constant_value(value_node)

    @staticmethod
    def _get_constant_value(value_node):
        """Κόμβος → int, ή None.

        Whitelist, όχι blacklist: δεκτό ΜΟΝΟ κυριολεκτικός ακέραιος.
        Οτιδήποτε άλλο (μεταβλητή, κλήση, έκφραση, string, float)
        πέφτει αυτόματα στο ασφαλές None — ακόμα και μορφές που δεν
        έχουμε προβλέψει.
        """
        if value_node is None:
            return None

        # Δύο έλεγχοι, όχι ένας: ο κόμβος μπορεί να είναι Constant αλλά
        # να κρατάει string, float ή None.
        if not isinstance(value_node, ast.Constant):
            return None

        # type() is int αντί για isinstance(): το isinstance(True, int)
        # επιστρέφει True (το bool είναι υποκλάση του int), οπότε ένα
        # key_size=True θα περνούσε ως μέγεθος κλειδιού 1.
        if type(value_node.value) is not int:
            return None

        return value_node.value


def scan_file(path):
    """Διαβάζει αρχείο, επιστρέφει λίστα από findings."""
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

        # `is None` και ΟΧΙ `if not key_bits` — το 0 θα περνούσε ως ψευδές
        if key_bits is None:
            print("    Μέγεθος κλειδιού: δεν προσδιορίστηκε στατικά")
            print("    Εκτίμηση κόστους: μη διαθέσιμη\n")
            continue

        print(f"    Μέγεθος κλειδιού: {key_bits} bits")

        # ── κλήση του estimator ──────────────────────────────────────
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
    """None → '—'. Ο πίνακας δεν πρέπει ποτέ να τυπώσει 0 για άγνωστο."""
    if value is None:
        return "—"
    return f"{value:,}"


if __name__ == "__main__":
    file_to_scan = sys.argv[1] if len(sys.argv) > 1 else "target.py"
    report(scan_file(file_to_scan), file_to_scan)