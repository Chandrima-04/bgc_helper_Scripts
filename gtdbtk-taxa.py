#!/usr/bin/env python

import sys
from pathlib import Path
import pandas as pd


def extract_rank(classif: str, prefix: str) -> str:
    """
    Extract a GTDB rank from a classification string, e.g.
    'd__Bacteria;p__Actinomycetota;...;s__Cutibacterium acnes'
    prefix: 'd','p','c','o','f','g','s'
    """
    if not isinstance(classif, str):
        return ""
    for part in classif.split(";"):
        part = part.strip()
        if part.startswith(prefix + "__"):
            return part.split("__", 1)[1]
    return ""


def main():
    if len(sys.argv) != 2:
        print("Usage: python make_taxonomy_from_gtdbtk_bins.py <dataset_name>", file=sys.stderr)
        print("Example: python make_taxonomy_from_gtdbtk_bins.py iss_3dmm", file=sys.stderr)
        sys.exit(1)

    dataset = sys.argv[1].rstrip("/")
    base = Path(".").resolve()

    ds_dir = base / dataset
    gtdb_dir = ds_dir / "gtdbtk_out"

    if not gtdb_dir.exists():
        print(f"[ERROR] GTDB-Tk output folder not found: {gtdb_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] Dataset: {dataset}")
    print(f"[INFO] Using GTDB-Tk folder: {gtdb_dir}")

    dfs = []
    for fname in ["gtdbtk.bac120.summary.tsv", "gtdbtk.ar53.summary.tsv"]:
        f = gtdb_dir / fname
        if f.exists():
            dfs.append(pd.read_csv(f, sep="\t"))

    if not dfs:
        print("[ERROR] No GTDB-Tk summary files found.", file=sys.stderr)
        sys.exit(1)

    tax = pd.concat(dfs, ignore_index=True)

    rows = []

    for _, row in tax.iterrows():
        user_genome = str(row["user_genome"])  # e.g. acid_nine_yi_bin.001
        classif = row.get("classification", "")

        kingdom = extract_rank(classif, "d")  # domain/kingdom
        # BiG-SLiCE schema: Kingdom, Class, Order, Family, Genus, Species
        class_name = extract_rank(classif, "c")
        order = extract_rank(classif, "o")
        family = extract_rank(classif, "f")
        genus = extract_rank(classif, "g")
        species = extract_rank(classif, "s")

        organism = species if species else user_genome
        genome_folder = f"{user_genome}/"  # must match bin folder name under gbk_file/<dataset>/

        rows.append(
            [genome_folder, kingdom, class_name, order, family, genus, species, organism]
        )

    # Optionally add an 'unbinned/' pseudo-genome if such folder exists
    gbk_dataset_dir = base / "bigslice_input" / "gbk_file" / dataset
    unbinned_dir = gbk_dataset_dir / "unbinned"
    if unbinned_dir.exists():
        rows.append(["unbinned/", "Unbinned", "", "", "", "", "", "Unbinned"])

    out_dir = base / "bigslice_input" / "taxonomy"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{dataset}.tsv"

    cols = ["Genome", "Kingdom", "Class", "Order", "Family", "Genus", "Species", "Organism"]

    with out_path.open("w") as out:
        out.write("#" + "\t".join(cols) + "\n")
        for r in rows:
            out.write("\t".join(r) + "\n")

    print(f"[INFO] Wrote taxonomy file: {out_path}")


if __name__ == "__main__":
    main()
