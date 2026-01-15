import ast, os

RULES = [
    ("core", {"bridge","lens","inquiry","observations"}),
    ("observations", {"bridge","lens"}),
]

def parse_imports(path: str):
    try:
        src = open(path, "r", encoding="utf-8").read()
    except UnicodeDecodeError:
        return []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []

    imports = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                imports.append(a.name)
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                imports.append(n.module)
    return imports

violations = []
for root, banned in RULES:
    for d, _, files in os.walk(root):
        for f in files:
            if not f.endswith('.py'):
                continue
            p = os.path.join(d, f)
            for imp in parse_imports(p):
                top = imp.split('.', 1)[0]
                if top in banned:
                    violations.append(f"{p} -> {imp}")

print(f"ARCH_IMPORT_VIOLATIONS {len(violations)}")
for v in violations:
    print(v)
