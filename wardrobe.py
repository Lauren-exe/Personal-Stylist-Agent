import csv

def load_wardrobe(filepath="my_wardrobe.csv"):
  items = []
  try:
    with open(filepath, newline='', encoding='utf-8') as f:
      reader = csv.DictReader(f)
      for row in reader:
        items.append(row)
  except FileNotFoundError:
    print(f"Wardrobe file not found: {filepath}")
  return items

if __name__ == "__main__":
  print(load_wardrobe())

