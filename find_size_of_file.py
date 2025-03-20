import os
import re
import csv

# Directory containing the FASTQ files (current directory in this example)
directory = '.'

# Dictionary to store sizes keyed by sample name and read type
# Example: { "BC-0332771064_S133": {"R1": size, "R2": size} }
sample_dict = {}

# Regular expression to capture the sample name and read number
# This pattern assumes files are named like: <sample>_Lxxx_R[1|2]_001.fastq.gz
pattern = re.compile(r'^(.*?)_L\d+_R([12])_001\.fastq\.gz$')

# Loop over all files in the directory
for filename in os.listdir(directory):
    if filename.endswith('.fastq.gz'):
        match = pattern.match(filename)
        if match:
            sample_name = match.group(1)  # e.g., "BC-0332771064_S133"
            read_type = match.group(2)    # "1" or "2"
            filepath = os.path.join(directory, filename)
            # Get the file size in bytes
            size = os.path.getsize(filepath)
            if sample_name not in sample_dict:
                sample_dict[sample_name] = {'R1': None, 'R2': None}
            sample_dict[sample_name][f'R{read_type}'] = size

# Write out the mapping file as a tab-separated values (TSV) file
with open('mapping_file.tsv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter='\t')
    # Write header
    writer.writerow(['sample_name', 'R1_size', 'R2_size'])
    # Write each sample's sizes (if a file is missing, output NA)
    for sample, sizes in sample_dict.items():
        writer.writerow([
            sample,
            sizes['R1'] if sizes['R1'] is not None else 'NA',
            sizes['R2'] if sizes['R2'] is not None else 'NA'
        ])

print("Mapping file 'mapping_file.tsv' has been created.")
