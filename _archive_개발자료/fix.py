import sys

with open('_시스템_코어/receipt_parser.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('if "입금" in filename:', 'if "입금" in filename or "COMMISSION USD" in raw_text.upper():')

with open('_시스템_코어/receipt_parser.py', 'w', encoding='utf-8') as f:
    f.write(text)
