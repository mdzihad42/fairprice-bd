from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator


# -------------------------
# CUSTOM USER
# -------------------------
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('agent', 'Agent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='agent')
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.role})"


# -------------------------
# CROP MODEL (IMAGE ADDED)
# -------------------------
class CropModel(models.Model):
    name = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to="crop_images/", null=True, blank=True)  # NEW FIELD
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'agent'}, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Crop"
        verbose_name_plural = "Crops"


class PriceHistory(models.Model):
    crop = models.ForeignKey(CropModel, on_delete=models.CASCADE, related_name='price_histories')
    year = models.PositiveIntegerField()
    price = models.FloatField()

    class Meta:
        unique_together = ('crop', 'year')
        ordering = ['year']

    def __str__(self):
        return f"{self.crop.name} - {self.year}"
# -------------------------
# FARMER INFO
# -------------------------
class FarmerInfoModel(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    nid = models.CharField(max_length=20, unique=True)
    location = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'agent'})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Farmer"
        verbose_name_plural = "Farmers"


# -------------------------
# WAREHOUSE
# -------------------------
class WarehouseModel(models.Model):
    shop_name = models.CharField(max_length=100)
    licence_number = models.CharField(max_length=50, unique=True)
    owner_nid = models.CharField(max_length=20)
    owner_phone = models.CharField(max_length=15)
    location = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'agent'})
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.shop_name

    class Meta:
        verbose_name = "Warehouse"
        verbose_name_plural = "Warehouses"


# -------------------------
# FARMER → WAREHOUSE PRICE FLOW
# -------------------------
class FarmerToWarehouseModel(models.Model):
    crop = models.ForeignKey(CropModel, on_delete=models.CASCADE)
    farmer = models.ForeignKey(FarmerInfoModel, on_delete=models.CASCADE)
    warehouse = models.ForeignKey(WarehouseModel, on_delete=models.CASCADE)

    farmer_selling_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    transport_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    warehouse_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'agent'})
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_cost = self.farmer_selling_cost + self.transport_cost + self.warehouse_cost
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.farmer} -> {self.warehouse} ({self.crop})"

    class Meta:
        verbose_name = "Farmer to Warehouse Transaction"
        verbose_name_plural = "Farmer to Warehouse Transactions"


# -------------------------
# CULTIVATION COST
# -------------------------
class CultivationCostCalculator(models.Model):
    farmer = models.ForeignKey(FarmerInfoModel, on_delete=models.CASCADE)
    crop = models.ForeignKey(CropModel, on_delete=models.CASCADE)

    cultivation_area = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    seed_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    extra_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'agent'})
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.total_cost = self.seed_cost + self.extra_cost
        super().save(*args, **kwargs)

    @property
    def cost_per_acre(self):
        if self.cultivation_area > 0:
            return self.total_cost / self.cultivation_area
        return 0

    def __str__(self):
        return f"{self.farmer} - {self.crop} Cultivation"

    class Meta:
        verbose_name = "Cultivation Cost"
        verbose_name_plural = "Cultivation Costs"
