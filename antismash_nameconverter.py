import os
import re

# Get list of folders starting with ERR
folders = [f for f in os.listdir('.') if os.path.isdir(f) and f.startswith('ERR')]
mapping_lines = []

# Compile a regex to capture node name from file name
pattern = re.compile(r'^(NODE_\S+)\.region001\.gbk$')

for folder in folders:
    folder_path = os.path.join('.', folder)
    for filename in os.listdir(folder_path):
        match = pattern.match(filename)
        if match:
            node = match.group(1)
            mapping_lines.append(f"{node}\t{folder}")

# Write the mapping file with two columns: node and file
with open("mapping.txt", "w") as f:
    f.write("node\tfile\n")
    f.write("\n".join(mapping_lines))

print("Mapping file 'mapping.txt' created.")
