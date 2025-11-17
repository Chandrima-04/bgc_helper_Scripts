import sys, os, re
from pathlib import Path

def contig_from_filename(p: Path):
    # e.g., NODE_43_length_57262_cov_215.912616.region001.gbk -> NODE_43_length_57262_cov_215.912616
    m = re.match(r"(.+?)\.region\d+\.gbk$", p.name)
    return m.group(1) if m else None

def contigs_from_scaffolds_gbk(path: Path):
    # yields (bgc_name, contig_id) for multi-record GBKs (e.g., scaffolds.gbk)
    # antiSMASH typically writes separate BGC records with "LOCUS <contigId> ..." lines
    out = []
    with open(path, "r", errors="ignore") as fh:
        contig = None
        bgc_idx = 0
        for line in fh:
            if line.startswith("LOCUS"):
                # LOCUS <contig> ...
                toks = line.split()
                if len(toks) >= 2:
                    contig = toks[1]
                    bgc_idx += 1
                    out.append((f"{path.parent.name}:{path.name}:record{bgc_idx}", contig))
    return out

def main(listfile, outfile):
    with open(listfile) as f:
        paths = [Path(l.strip()) for l in f if l.strip()]
    rows = []
    for p in paths:
        if not p.exists():
            continue
        name_guess = contig_from_filename(p)
        if name_guess:
            rows.append((p.stem, name_guess))  # bgc_name (without .gbk), contig_id
        elif p.name == "scaffolds.gbk":
            rows.extend(contigs_from_scaffolds_gbk(p))
        else:
            # fallback: try LOCUS of first record
            contig=None
            with open(p, "r", errors="ignore") as fh:
                for line in fh:
                    if line.startswith("LOCUS"):
                        toks = line.split()
                        if len(toks) >= 2: contig = toks[1]
                        break
            if contig:
                rows.append((p.stem, contig))
            else:
                rows.append((p.stem, None))
    with open(outfile, "w") as out:
        out.write("bgc_name\tcontig_id\tgbk_path\n")
        for bgc, contig in rows:
            out.write(f"{bgc}\t{contig or ''}\t{p.as_posix()}\n")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python extract_bgc_contig_from_gbk.py <gbk_list.txt> <out_tsv>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
