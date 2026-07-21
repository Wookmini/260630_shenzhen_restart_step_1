import re

with open(r'c:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\_발표자료\V2\presentation.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the bounds of Slide 3
s3_start = content.find('<div class="slide" id="s3">')
s4_start = content.find('<div class="slide" id="s4">')
s5_start = content.find('<div class="slide" id="s5">')
s6_start = content.find('<div class="slide" id="s6">')

s3_content = content[s3_start:s4_start]
s5_content = content[s5_start:s6_start]

# Extract the grid2 blocks
def get_grid2(slide_content):
    g_start = slide_content.find('<div class="grid2"')
    # Find matching closing div for grid2
    idx = g_start
    depth = 0
    while idx < len(slide_content):
        if slide_content[idx:idx+4] == '<div':
            depth += 1
        elif slide_content[idx:idx+5] == '</div':
            depth -= 1
            if depth == 0:
                return slide_content[g_start:idx+6]
        idx += 1
    return None

s3_grid2 = get_grid2(s3_content)
s5_grid2 = get_grid2(s5_content)

# Swap them in the slides
new_s3_content = s3_content.replace(s3_grid2, s5_grid2)
new_s5_content = s5_content.replace(s5_grid2, s3_grid2)

# Replace back into the main content
content = content[:s3_start] + new_s3_content + content[s4_start:s5_start] + new_s5_content + content[s6_start:]

with open(r'c:\Users\20000177\Desktop\Wooktigravity\260630_shenzhen_restart_step_1\_발표자료\V2\presentation.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Swap successful")
