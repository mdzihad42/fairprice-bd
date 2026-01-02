from django.contrib import admin
from fairpriceApp.models import *
admin.site.register([User,CropModel, FarmerInfoModel,WarehouseModel,FarmerToWarehouseModel,CultivationCostCalculator,PriceHistory])
# Register your models here.
