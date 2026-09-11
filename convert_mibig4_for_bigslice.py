## Had to convert Mibig-gbk download
## bigslice incompatibility
## this is the code
from pathlib import Path
from Bio import SeqIO
from Bio.SeqFeature import SeqFeature, FeatureLocation
import sys

if len(sys.argv) != 3:
    print("Usage: python convert_mibig4_for_bigslice.py INPUT_DIR OUTPUT_DIR")
    sys.exit(1)

indir = Path(sys.argv[1])
outdir = Path(sys.argv[2])
outdir.mkdir(parents=True, exist_ok=True)

converted = 0
failed = 0

for src in sorted(indir.rglob("BGC*.gbk")):

    try:
        records = list(SeqIO.parse(str(src), "genbank"))

        if not records:
            print("EMPTY:", src)
            failed += 1
            continue

        for record in records:

            # ------------------------------------------------
            # Add antiSMASH metadata that BiG-SLiCE recognizes
            # ------------------------------------------------
            structured = record.annotations.setdefault(
                "structured_comment", {}
            )

            antismash = structured.setdefault(
                "antiSMASH-Data", {}
            )

            antismash["Version"] = "7.0.0"

            # Required when writing GenBank
            record.annotations.setdefault("molecule_type", "DNA")

            # ------------------------------------------------
            # Add MiBIG subregion covering the whole BGC
            # ------------------------------------------------
            already_mibig = any(
                f.type == "subregion"
                and f.qualifiers.get("aStool", [""])[0] == "mibig"
                for f in record.features
            )

            if not already_mibig:

                feature = SeqFeature(
                    FeatureLocation(0, len(record.seq)),
                    type="subregion",
                    qualifiers={
                        "aStool": ["mibig"],
                        "label": ["unknown"]
                    }
                )

                record.features.insert(0, feature)

        dest = outdir / src.name

        SeqIO.write(records, str(dest), "genbank")

        converted += 1

    except Exception as e:
        print(f"FAILED: {src}: {e}")
        failed += 1

print()
print("Converted:", converted)
print("Failed:", failed)
print("Output:", outdir)

## Adding to bigslice path
## docker1 run --rm \
##  -v /workdir/cb846/bgc_data:/data \
##  biohpc_cb846/bigslice-v3 \
## python3 /data/convert_mibig4_for_bigslice.py \
##  /data/bigslice_input/gbk_file/mibig4/mibig_gbk_4.0 \
##  /data/bigslice_input/gbk_file/mibig4_bigslice
