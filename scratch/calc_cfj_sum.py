amounts = [
    295.0,  # Ev 1
    250.0,  # Ev 2
    310.0,  # Ev 3
    340.0,  # Ev 4
    370.0,  # Ev 5
    380.0,  # Ev 6
    42.0,   # Ev 7
    140.0,  # Ev 8 (corrected)
    61.0,   # Ev 9 (corrected)
    193.0,  # Ev 10 (corrected)
    18.0,   # Ev 11 (corrected)
    150.0,  # Ev 12 (corrected)
    10.0,   # Ev 13
]

total = sum(amounts)
print("Total sum of general receipts:", total)
print("Transfer amount (Ev 14): 2513.0")
print("Difference:", total - 2513.0)
