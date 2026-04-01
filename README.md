antismash_nameconverter -> Spades/Fasta files have Contig name. In antismash the gbk files get named as contigName_region. This script help creates a name mapper. Thus I have contigName_region and file name.


chunk_scaffolds.py -> Chunks scaffolds.fasta after renaming it to the original name of the folder
For PRISM

To run:
```
python3 chunk_scaffolds.py iss_3mm/results/ --spades-dir spades --limit-mb 50
```

After running metabat2, antismash and gtdb:


This will create a mapping to contig names
```
# run in your project root
mkdir -p maps
> maps/contig_to_bin.tsv

for fa in bins/*.fa; do
  bin=$(basename "${fa%.fa}")   # e.g., ERR12711387_bin.4
  awk -v BIN="$bin" '
    /^>/ {
      # take the token after ">"
      id=$1; sub(/^>/,"",id);
      print id "\t" BIN
    }
  ' "$fa" >> maps/contig_to_bin.tsv
done

# sanity check
head maps/contig_to_bin.tsv
# contig_id<TAB>bin_id

```

This will create a mapping to antismash
```
find /path/to/your/antismash_outputs -type f -name "*.gbk" | sort > maps/gbk_paths.txt
```



Then run the following
```
python extract_bgc_contig_from_gbk.py maps/gbk_paths.txt maps/bgc_to_contig.tsv
python join_bin_taxonomy.py
```


Bigslice: Convert .db into individual .csv 
```
mkdir -p csv

for t in $(sqlite3 result/data.db "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"); do
  echo "Exporting $t..."
  sqlite3 -header -csv result/data.db "SELECT * FROM \"$t\";" > "csv/${t}.csv"
done

```


To convert gtdbtk -> taxa for antismash the gtdbtk, go to krumsiek lab server and run 
```
python make_bigslice_taxonomy2.py tara
```

Also, to arrange the bins, ie sample name + taxa 
```
python organize_bgcs_by_bin.py antarctica_thompson
```
Both are run from bgc_data
