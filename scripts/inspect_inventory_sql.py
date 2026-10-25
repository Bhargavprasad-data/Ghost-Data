with open("dataset/evidence/databases/customer_data_inventory_20260916.sql", "r", encoding="utf-8") as f:
    lines = [f.readline() for _ in range(50)]
print("".join(lines[:45]))
