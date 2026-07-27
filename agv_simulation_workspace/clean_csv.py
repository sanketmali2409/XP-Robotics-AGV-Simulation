import sys
import re

def clean_csv(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # The CSV columns end with Kd, which is "0.200"
    # Find all occurrences of "0.200" followed immediately by a digit (the timestamp)
    # and insert a newline between them.
    # The timestamp looks like "1147.803" or "54.675" or similar.
    # Pattern: 0.200 followed by digits.
    # Be careful not to replace "0.200" that is already at the end of a line.
    
    # We can match `0.200` followed by a number (no comma in between)
    cleaned_content = re.sub(r'(0\.200)(\d+\.\d+)', r'\1\n\2', content)

    # Also, we might have cases like "000,1.200,0.000,0.200" which are partial lines.
    # Let's filter out lines that don't have exactly 10 columns.
    lines = cleaned_content.split('\n')
    valid_lines = []
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        cols = line.split(',')
        if len(cols) == 10:
            valid_lines.append(line)
        else:
            print(f"Removing malformed line {i}: {line}")

    with open(filepath, 'w') as f:
        f.write('\n'.join(valid_lines) + '\n')
    
    print(f"Cleaned {filepath}. Total valid lines: {len(valid_lines)}")

if __name__ == "__main__":
    clean_csv(sys.argv[1])
