import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "FairPriceTracker.settings")
django.setup()

from fairpriceApp.models import *

def populate():
    print("Populating database...")

    # Create Superuser if not exists
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superuser 'admin' created (password: admin123)")

    # Create Agent
    agent, created = User.objects.get_or_create(username='agent1', defaults={'email': 'agent1@example.com', 'role': 'agent', 'is_approved': True, 'district': 'ঢাকা'})
    if created:
        agent.set_password('agent123')
        agent.save()
        print("Agent 'agent1' created (password: agent123)")
    else:
        agent = User.objects.get(username='agent1')

    # Create Crops
    crops_list = ['Rice', 'Potato', 'Wheat', 'Onion', 'Lentil', 'Jute']
    created_crops = []
    for crop_name in crops_list:
        crop, created = CropModel.objects.get_or_create(name=crop_name, defaults={'created_by': agent, 'is_approved': True})
        created_crops.append(crop)
    print(f"{len(created_crops)} crops created/verified.")

    # Create Farmers
    farmers = []
    for i in range(5):
        farmer, created = FarmerInfoModel.objects.get_or_create(
            nid=f'1234567890{i}',
            defaults={
                'name': f'Farmer {i+1}',
                'phone': f'0170000000{i}',
                'location': 'Village, District',
                'created_by': agent
            }
        )
        farmers.append(farmer)
    print(f"{len(farmers)} farmers created/verified.")

    # Create Warehouses
    warehouses = []
    for i in range(3):
        warehouse, created = WarehouseModel.objects.get_or_create(
            licence_number=f'LIC-{i}',
            defaults={
                'shop_name': f'Warehouse {i+1}',
                'owner_nid': f'9876543210{i}',
                'owner_phone': f'0180000000{i}',
                'location': 'Market, District',
                'created_by': agent,
                'is_approved': True
            }
        )
        warehouses.append(warehouse)
    print(f"{len(warehouses)} warehouses created/verified.")

    # Create Transactions
    for i in range(20):
        farmer = random.choice(farmers)
        warehouse = random.choice(warehouses)
        crop = random.choice(created_crops)
        
        # Random costs
        farmer_cost = random.randint(20, 100)
        transport = random.randint(2, 10)
        warehouse_c = random.randint(1, 5)
        
        FarmerToWarehouseModel.objects.create(
            crop=crop,
            farmer=farmer,
            warehouse=warehouse,
            farmer_selling_cost=farmer_cost,
            transport_cost=transport,
            warehouse_cost=warehouse_c,
            created_by=agent
        )
    print("20 transactions created.")

if __name__ == '__main__':
    populate()
