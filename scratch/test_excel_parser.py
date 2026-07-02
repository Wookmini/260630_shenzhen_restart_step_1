import re

def parse_cell(text):
    if not text:
        return {}
    
    # Find all occurrences of "N페이지:"
    parts = re.split(r'(\d+)페이지:', text)
    if len(parts) < 3:
        # If it doesn't match the pattern, check if there is a single page without "1페이지:"
        # but actually all our rows have "1페이지:"
        return {}
        
    pages = {}
    # parts looks like: ['', '1', ' content...', '2', ' content...']
    for idx in range(1, len(parts), 2):
        page_num = int(parts[idx])
        content = parts[idx+1].strip()
        
        # Remove trailing spaces or separator
        # Content usually has "내역 / 금액위안"
        # We can split by '/'
        amount = None
        desc = content
        if '/' in content:
            # Split from the right side in case desc has '/'
            desc_part, amt_part = content.rsplit('/', 1)
            desc = desc_part.strip()
            # Clean amount part
            amt_clean = amt_part.replace('위안', '').replace('원', '').replace(',', '').strip()
            try:
                amount = float(amt_clean)
            except ValueError:
                amount = None
        pages[page_num] = {'desc': desc, 'amount': amount}
    return pages

# Test cases
test_1 = "1페이지: 톨비 (通行费 - 6장 합산) / 68.00위안   2페이지: 톨비 (通行费 - 6장 합산) / 100.00위안"
test_2 = "1페이지: 장량 정산금 (张亮报销款) 계좌 이체 수수료 / 3.60위안"
print("Test 1:", parse_cell(test_1))
print("Test 2:", parse_cell(test_2))
