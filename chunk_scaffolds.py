#!/usr/bin/env python3
import os
import argparse
from pathlib import Path
import shutil

def iter_fasta_records(fasta_path):
    """
    Stream FASTA records as (header_line_with_gt, list_of_sequence_lines, byte_size_of_record_as_written)
    """
    header = None
    seq_lines = []
    with open(fasta_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith(">"):
                if header is not None:
                    # compute size as bytes when written back
                    rec_bytes = (len(header.encode("utf-8"))
                                 + sum(len(s.encode("utf-8")) for s in seq_lines))
                    yield header, seq_lines, rec_bytes
                header = line
                seq_lines = []
            else:
                # ensure each line ends with newline
                if not line.endswith("\n"):
                    line = line + "\n"
                seq_lines.append(line)
        if header is not None:
            rec_bytes = (len(header.encode("utf-8"))
                         + sum(len(s.encode("utf-8")) for s in seq_lines))
            yield header, seq_lines, rec_bytes

def write_record(fp, header, seq_lines):
    fp.write(header)
    for s in seq_lines:
        fp.write(s)

def chunk_fasta(src_fasta: Path, base_name: str, size_limit_mb: float, overwrite: bool = True):
    """
    Split src_fasta into chunks of ~size_limit_mb without breaking records.
    Creates files base_name_1.fasta, base_name_2.fasta, ...
    Returns list of created chunk paths.
    """
    size_limit_bytes = int(size_limit_mb * 1024 * 1024)
    chunk_index = 1
    current_bytes = 0
    out_fp = None
    created = []

    def open_new_chunk():
        nonlocal out_fp, current_bytes, chunk_index
        if out_fp:
            out_fp.close()
        chunk_path = src_fasta.with_name(f"{base_name}_{chunk_index}.fasta")
        if chunk_path.exists() and overwrite:
            chunk_path.unlink()
        out_fp = open(chunk_path, "w", encoding="utf-8")
        created.append(chunk_path)
        current_bytes = 0
        chunk_index += 1
        return out_fp

    for header, seq_lines, rec_bytes in iter_fasta_records(src_fasta):
        # If no file open yet, start the first chunk
        if out_fp is None:
            out_fp = open_new_chunk()

        # If the record alone is bigger than the limit and current chunk is empty,
        # write it anyway (cannot split contigs)
        if rec_bytes > size_limit_bytes and current_bytes == 0:
            write_record(out_fp, header, seq_lines)
            current_bytes += rec_bytes
            # Start a new file for next record
            out_fp = open_new_chunk()
            continue

        # If adding this record would exceed limit and we already have content, start a new chunk
        if current_bytes > 0 and (current_bytes + rec_bytes) > size_limit_bytes:
            out_fp = open_new_chunk()

        write_record(out_fp, header, seq_lines)
        current_bytes += rec_bytes

    if out_fp:
        out_fp.close()

    # If the last chunk file ended up empty (possible if file ended exactly at boundary), clean it
    if created and created[-1].stat().st_size == 0:
        created[-1].unlink()
        created.pop()

    return created

def main():
    parser = argparse.ArgumentParser(
        description="Copy each spades/scaffolds.fasta to <folder>.fasta and split into chunks (> size limit) without breaking contigs."
    )
    parser.add_argument(
        "root",
        help="Root directory that contains the 'spades' folder (e.g., acid_nine_yi).",
    )
    parser.add_argument(
        "--spades-dir",
        default="spades",
        help="Name of the subdirectory that contains SRR folders (default: spades)",
    )
    parser.add_argument(
        "--limit-mb",
        type=float,
        default=50.0,
        help="Chunk size limit in MB (default: 50)",
    )
    parser.add_argument(
        "--skip-existing-copy",
        action="store_true",
        help="If set, skip making <folder>.fasta if it already exists.",
    )
    parser.add_argument(
        "--no-chunk",
        action="store_true",
        help="If set, do not create chunked files even if size exceeds the limit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print actions without writing files.",
    )
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve()
    spades_dir = root / args.spades_dir

    if not spades_dir.exists():
        print(f"[ERROR] {spades_dir} does not exist")
        return

    srr_dirs = sorted([p for p in spades_dir.iterdir() if p.is_dir()])
    if not srr_dirs:
        print(f"[WARN] No subdirectories found under {spades_dir}")
        return

    for srr in srr_dirs:
        folder_name = srr.name
        scaff = srr / "scaffolds.fasta"
        if not scaff.exists():
            print(f"[SKIP] {scaff} not found.")
            continue

        dest_copy = srr / f"{folder_name}.fasta"
        if dest_copy.exists() and args.skip_existing_copy:
            print(f"[SKIP] Copy exists: {dest_copy}")
        else:
            if args.dry_run:
                print(f"[DRY-RUN] Copy {scaff} -> {dest_copy}")
            else:
                # overwrite copy to make sure it's current
                shutil.copyfile(scaff, dest_copy)
                print(f"[OK] Copied {scaff.name} -> {dest_copy.name}")

        if args.no_chunk:
            continue

        # Check file size of the copy
        size_mb = (dest_copy.stat().st_size) / (1024 * 1024)
        if size_mb <= args.limit_mb:
            print(f"[OK] {dest_copy.name} size {size_mb:.2f} MB <= {args.limit_mb} MB: no chunking needed.")
            continue

        if args.dry_run:
            print(f"[DRY-RUN] Would chunk {dest_copy.name} at {args.limit_mb} MB into {folder_name}_*.fasta")
        else:
            print(f"[CHUNK] Splitting {dest_copy.name} ({size_mb:.2f} MB) into ~{args.limit_mb} MB parts...")
            created = chunk_fasta(dest_copy, folder_name, args.limit_mb, overwrite=True)
            for p in created:
                print(f"  - {p.name} ({p.stat().st_size / (1024 * 1024):.2f} MB)")
            print(f"[DONE] Created {len(created)} chunk(s) for {folder_name}")

if __name__ == "__main__":
    main()
