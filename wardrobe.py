import my_wardrobe.csv

def load_wardrobe(filepath="my_wardrobe.csv"):
  items = []
  with open(filepath, newline="") as f:
    reader=csv.DictReader(f)
    for row in reader:
      items.append(row)
  return items

