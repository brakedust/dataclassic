from pathlib import Path

folder_to_search = Path(__file__).parent / "dataclassic"

import_names = set()

for f in folder_to_search.glob("**/*.py"):

    import_lines = [
        line
        for line in f.read_text().splitlines()
        if line.startswith("import ") or line.startswith("from ")
    ]

    # print(f.name)
    for line in import_lines:

        tokens = line.split(" ")
        name = tokens[1]
        if name.startswith("."):
            continue
        else:
            name = name.split(".")[0]
        # print(f"-- {name}")
        import_names.add(name)

print(import_names)
