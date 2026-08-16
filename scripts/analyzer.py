import ast


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
            self.flags.append(
                {
                    "line": node.lineno,
                    "message": "ΚΡΙΣΙΜΟ: Εντοπίστηκε παραγωγή κλειδιού RSA. Ευάλωτο σε αλγόριθμο Shor.",
                }
            )
        self.generic_visit(node)


fileToScan = "scripts/target.py"

with open(fileToScan, "r") as file:
    sourceCode = file.read()

tree = ast.parse(sourceCode)
scanner = QuantumScanner()
scanner.visit(tree)

if scanner.flags:
    print(f" ΠΡΟΣΟΧΗ: Βρέθηκαν {len(scanner.flags)} ευπάθειες!")
    for flag in scanner.flags:
        print(f"Γραμμή {flag['line']}: {flag['message']}")
else:
    print(" Ο κώδικας φαίνεται ασφαλής.")
