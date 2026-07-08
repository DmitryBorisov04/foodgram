import json

with open('ingredients.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

result = []
for i, item in enumerate(data, 1):
    result.append({
        "model": "recipes.ingredient",
        "pk": i,
        "fields": {
            "name": item["name"],
            "measurement_unit": item["measurement_unit"]
        }
    })

with open('ingredients.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f"Конвертировано {len(result)} ингредиентов")
