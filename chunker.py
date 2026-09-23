import os
import math

with open('/tmp/sp_subs.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

chunk_size = 100
num_chunks = math.ceil(len(lines) / chunk_size)

for i in range(num_chunks):
    start = i * chunk_size
    end = min((i + 1) * chunk_size, len(lines))
    chunk_lines = lines[start:end]
    with open(f'/tmp/sp_subs_chunk_{i}.txt', 'w', encoding='utf-8') as f:
        f.writelines(chunk_lines)

print(f"Created {num_chunks} chunks.")
