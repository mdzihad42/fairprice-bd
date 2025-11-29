from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, CropModel, FarmerInfoModel, WarehouseModel, FarmerToWarehouseModel, CultivationCostCalculator

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'role', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class CropForm(forms.ModelForm):
    class Meta:
        model = CropModel
        fields = ['name', 'image']   # FIXED
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter crop name'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            })
        }


class FarmerForm(forms.ModelForm):
    class Meta:
        model = FarmerInfoModel
        fields = ['name', 'phone', 'nid', 'location']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'nid': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class WarehouseForm(forms.ModelForm):
    class Meta:
        model = WarehouseModel
        fields = ['shop_name', 'licence_number', 'owner_nid', 'owner_phone', 'location']
        widgets = {
            'shop_name': forms.TextInput(attrs={'class': 'form-control'}),
            'licence_number': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_nid': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class FarmerToWarehouseForm(forms.ModelForm):
    class Meta:
        model = FarmerToWarehouseModel
        fields = ['crop', 'farmer', 'warehouse', 'farmer_selling_cost', 'transport_cost', 'warehouse_cost']
        widgets = {
            'crop': forms.Select(attrs={'class': 'form-control'}),
            'farmer': forms.Select(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'farmer_selling_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'transport_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'warehouse_cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CultivationCostForm(forms.ModelForm):
    class Meta:
        model = CultivationCostCalculator
        fields = ['farmer', 'crop', 'cultivation_area', 'seed_cost', 'extra_cost']
        widgets = {
            'farmer': forms.Select(attrs={'class': 'form-control'}),
            'crop': forms.Select(attrs={'class': 'form-control'}),
            'cultivation_area': forms.NumberInput(attrs={'class': 'form-control'}),
            'seed_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'extra_cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }