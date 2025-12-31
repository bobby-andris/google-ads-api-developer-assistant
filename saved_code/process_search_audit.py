import csv

def main():
    input_path = 'saved_csv/search_keyword_efficiency_audit.csv'
    data = []
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['cost'] = float(row['cost'])
            row['roas'] = float(row['roas'])
            data.append(row)

    # 1. Top 5 'Heroes' (Highest ROAS with >$25 spend)
    # We look for outliers that are actually scalable
    heroes = [r for r in data if r['cost'] > 25]
    heroes.sort(key=lambda x: x['roas'], reverse=True)
    
    # 2. Top 5 'Bleeders' (Highest Cost with <1.0 ROAS)
    # This is the immediate waste we can reclaim
    bleeders = [r for r in data if r['roas'] < 1.0]
    bleeders.sort(key=lambda x: x['cost'], reverse=True)

    print('--- TOP 10 SEARCH HEROES (SCALABLE AD GROUPS) ---')
    for r in heroes[:10]:
        print(f"Keyword: {r['keyword']} | ROAS: {r['roas']} | Match: {r['match_type']} | Campaign: {r['campaign']}")

    print('\n--- TOP 10 SEARCH BLEEDERS (IMMEDIATE WASTE) ---')
    for r in bleeders[:10]:
        print(f"Keyword: {r['keyword']} | Cost: ${r['cost']} | ROAS: {r['roas']} | Match: {r['match_type']}")

if __name__ == "__main__":
    main()
