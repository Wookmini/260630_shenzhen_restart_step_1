known = [
    268.49, # p1
    77.10,  # p2
    198.43, # p3
    28.80,  # p4
    # p5 (x)
    594.30, # p6
    597.40, # p7
    # p8 (y)
    100.00, # p9
    103.80, # p10
    350.00, # p11
    200.00, # p12
    80.00,  # p13
    80.00,  # p14
    80.00,  # p15
    260.00  # p16
]

target = 3489.39
sum_known = sum(known)
diff = target - sum_known
print(f"Sum of known pages: {sum_known:.2f}")
print(f"Remaining (p5 + p8): {diff:.2f}")
