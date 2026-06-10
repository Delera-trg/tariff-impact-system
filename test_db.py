import sys
sys.path.insert(0, '.')
from modules.database import DatabaseManager

db = DatabaseManager()
detail = db.get_industry_detail(hs_code='0101.10')

print('HS Code:', detail['hs_code'])
print('Base Price:', detail['base_price'])
print('Tariff Rate:', detail.get('current_tariff_rate', 0))
