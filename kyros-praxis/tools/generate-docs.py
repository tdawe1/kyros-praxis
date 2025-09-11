#!/usr/bin/env python3
import subprocess


def generate_docs():
    # Build MkDocs site from READMEs and runbooks
    subprocess.run(["mkdocs", "build", "--config-file", "mkdocs.yml"], check=True)
    print("Docs generated in site/ directory.")


if __name__ == "__main__":
    generate_docs()
