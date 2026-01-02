from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, CropModel, FarmerInfoModel, WarehouseModel, FarmerToWarehouseModel, CultivationCostCalculator, AboutPageContent

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'role', 'district', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Make district initially required=False in form logic because it depends on role, 
        # but we validate it in clean()
        self.fields['district'].required = False

        # Check if a Government user already exists
        if User.objects.filter(role='govt').exists():
            # If exists, remove 'govt' from choices so no one else can see/select it
            current_choices = list(self.fields['role'].choices)
            self.fields['role'].choices = [c for c in current_choices if c[0] != 'govt']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        district = cleaned_data.get('district')

        if role == 'govt':
            # Double check in backend validation
            if User.objects.filter(role='govt').exists():
                self.add_error('role', 'A Government account already exists. Only one is allowed.')
        
        if role == 'admin':
            if not district:
                self.add_error('district', 'District is required for Admin role.')
            else:
                if User.objects.filter(role='admin', district=district).exists():
                    self.add_error('district', f'An admin already exists for {district}.')
        
        return cleaned_data

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
        fields = ['crop', 'farmer', 'warehouse', 'quantity_kg', 'farmer_selling_cost', 'transport_cost', 'warehouse_cost']
        widgets = {
            'crop': forms.Select(attrs={'class': 'form-control'}),
            'farmer': forms.Select(attrs={'class': 'form-control'}),
            'warehouse': forms.Select(attrs={'class': 'form-control'}),
            'quantity_kg': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Total Quantity in KG'}),
            'farmer_selling_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'transport_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'warehouse_cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CultivationCostForm(forms.ModelForm):
    class Meta:
        model = CultivationCostCalculator
        fields = ['farmer', 'crop', 'cultivation_area', 'seed_cost', 'fertilizer_cost', 'pesticide_cost', 'labor_cost', 'irrigation_cost', 'extra_cost']
        widgets = {
            'farmer': forms.Select(attrs={'class': 'form-control'}),
            'crop': forms.Select(attrs={'class': 'form-control'}),
            'cultivation_area': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Area in Acres'}),
            'seed_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'fertilizer_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'pesticide_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'labor_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'irrigation_cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'extra_cost': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'district']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class AboutPageContentForm(forms.ModelForm):
    class Meta:
        model = AboutPageContent
        fields = ['hero_image', 'mission_image']
        widgets = {
            'hero_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'mission_image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }