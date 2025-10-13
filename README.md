antismash_nameconverter -> Spades/Fasta files have Contig name. In antismash the gbk files get named as contigName_region. This script help creates a name mapper. Thus I have contigName_region and file name.


chunk_scaffolds.py -> Chunks scaffolds.fasta after renaming it to the original name of the folder
For PRISM

To run:
```
python3 chunk_scaffolds.py iss_3mm/results/ --spades-dir spades --limit-mb 50
```
