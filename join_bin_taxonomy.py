import pandas as pd
import re, sys

bgc2contig = pd.read_csv("maps/bgc_to_contig.tsv", sep="\t")
ctg2bin     = pd.read_csv("maps/contig_to_bin.tsv", sep="\t", names=["contig_id","bin_id"])

tax = pd.read_csv("gtdbtk_out/gtdbtk.bac120.summary.tsv", sep="\t")
# keep only user_genome and classification
tax = tax[["user_genome","classification"]].rename(columns={"user_genome":"bin_id"})

def rank(classif, r):
    m = re.search(rf"{r}__([^;]+)", str(classif))
    return m.group(1) if m else None

tax["phylum"]  = tax["classification"].apply(lambda x: rank(x,"p"))
tax["genus"]   = tax["classification"].apply(lambda x: rank(x,"g"))
tax["species"] = tax["classification"].apply(lambda x: rank(x,"s"))

# join contig -> bin
m = bgc2contig.merge(ctg2bin, on="contig_id", how="left")
# join bin -> taxonomy
m = m.merge(tax, on="bin_id", how="left")

m.to_csv("maps/bgc_to_bin_tax.tsv", sep="\t", index=False)
print("Wrote maps/bgc_to_bin_tax.tsv with columns: ", list(m.columns))
