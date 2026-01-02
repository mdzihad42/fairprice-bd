from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login,logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Q
from django.contrib import messages
from django.http import HttpResponseForbidden
from .models import *
from .forms import *
from django.db.models import Q
import difflib
from django.shortcuts import render, get_object_or_404
def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_agent(user):
    return user.is_authenticated and user.role == 'agent'

def is_approved_agent(user):
    return user.is_authenticated and user.role == 'agent' and user.is_approved


def public_dashboard(request):
    crops = CropModel.objects.all()
    search_query = request.GET.get('search', '').strip()

    if search_query:
        crops = crops.filter(name__icontains=search_query)

    crop_data = []
    for crop in crops:
        transactions = FarmerToWarehouseModel.objects.filter(crop=crop)
        avg_price = transactions.aggregate(Avg('total_cost'))['total_cost__avg']

        crop_data.append({
            'crop': crop,
            'avg_price': avg_price if avg_price else 0,
            'transaction_count': transactions.count()
        })

    # Statistics
    total_farmers = FarmerInfoModel.objects.count()
    total_transactions = FarmerToWarehouseModel.objects.count()
    
    # Recent Updates (Ticker)
    recent_updates = FarmerToWarehouseModel.objects.select_related('crop', 'warehouse').order_by('-created_at')[:10]

    # Sorting logic
    sort_option = request.GET.get('sort', '')
    if sort_option == 'price_low':
        crop_data.sort(key=lambda x: x['avg_price'])
    elif sort_option == 'price_high':
        crop_data.sort(key=lambda x: x['avg_price'], reverse=True)

    return render(request, 'public_dashboard.html', {
        'crop_data': crop_data,
        'search_query': search_query,
        'total_farmers': total_farmers,
        'total_transactions': total_transactions,
        'recent_updates': recent_updates
    })



def crop_details(request, crop_id):
    crop = get_object_or_404(CropModel, id=crop_id)
    
    # Farmers
    farmers_transactions = FarmerToWarehouseModel.objects.filter(crop=crop)
    farmers = set(transaction.farmer for transaction in farmers_transactions)
    
    # Warehouses
    warehouses_transactions = FarmerToWarehouseModel.objects.filter(crop=crop)
    warehouses = set(transaction.warehouse for transaction in warehouses_transactions)
    
    # Cultivation costs
    cultivation_costs = CultivationCostCalculator.objects.filter(crop=crop)
    
    # Price history for this crop
    price_history = PriceHistory.objects.filter(crop=crop).order_by('year')

    context = {
        'crop': crop,
        'farmers': farmers,
        'warehouses': warehouses,
        'cultivation_costs': cultivation_costs,
        'price_history': price_history,
    }
    return render(request, 'crop_details.html', context)



def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if user.role == 'admin':
                user.is_approved = True  
            user.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_system(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Hardcoded credentials for system access
        if username == 'system' and password == 'agro123':
            request.session['system_access'] = True
            messages.success(request, 'System access granted! You can now login or register.')
            return redirect('public_dashboard')
        else:
            messages.error(request, 'Invalid system credentials.')
            
    return render(request, 'login_system.html')

def logout_system(request):
    if 'system_access' in request.session:
        del request.session['system_access']
        messages.info(request, "System access locked.")
    return redirect('public_dashboard')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'registration/login.html')

def user_logout(request):
    logout(request)
    return redirect('public_dashboard')

@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('govt_dashboard')
    elif request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'agent':
        return redirect('agent_dashboard')
    else:
        return redirect('public_dashboard')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def govt_dashboard(request):
    admins = User.objects.filter(role='admin')
    agents = User.objects.filter(role='agent')
    
    # Recent activities (All transactions globally)
    recent_activities = FarmerToWarehouseModel.objects.select_related('created_by', 'crop', 'warehouse').order_by('-created_at')[:20]
    
    return render(request, 'govt_dashboard.html', {
        'admins': admins, 
        'agents': agents,
        'recent_activities': recent_activities
    })

@login_required
def delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, id=user_id)
    
    # Superuser can delete anyone except other superusers/govt
    if request.user.is_superuser:
        if user_to_delete.is_superuser or user_to_delete.role == 'govt':
            messages.error(request, "Cannot delete government/superuser accounts.")
        else:
            user_to_delete.delete()
            messages.success(request, "User deleted successfully.")
        return redirect('govt_dashboard')
    
    # District Admin can delete Agents in their district
    elif request.user.role == 'admin':
        if user_to_delete.role == 'agent' and user_to_delete.district == request.user.district:
            user_to_delete.delete()
            messages.success(request, "Agent deleted successfully.")
            return redirect('admin_dashboard')
        else:
            messages.error(request, "You do not have permission to delete this user.")
            return redirect('admin_dashboard')
            
    else:
        messages.error(request, "Permission denied.")
        return redirect('dashboard')

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Filter by district if the admin has one
    if request.user.district:
        pending_agents = User.objects.filter(role='agent', is_approved=False, district=request.user.district)
        active_agents = User.objects.filter(role='agent', is_approved=True, district=request.user.district)
        
        pending_warehouses = WarehouseModel.objects.filter(is_approved=False, location__icontains=request.user.district)
        
        # Recent activities (Filtered by Agents in Admin's District)
        recent_activities = FarmerToWarehouseModel.objects.filter(
            created_by__district=request.user.district
        ).select_related('created_by', 'crop', 'warehouse').order_by('-created_at')[:20]
    else:
        pending_agents = User.objects.filter(role='agent', is_approved=False)
        active_agents = User.objects.filter(role='agent', is_approved=True)

        pending_warehouses = WarehouseModel.objects.filter(is_approved=False)
        recent_activities = FarmerToWarehouseModel.objects.select_related('created_by', 'crop', 'warehouse').order_by('-created_at')[:20]
    
    context = {
        'pending_agents': pending_agents,
        'active_agents': active_agents,
        'pending_warehouses': pending_warehouses,
        'recent_activities': recent_activities
    }

    
    return render(request, 'admin_dashboard.html', context)

@login_required
@user_passes_test(is_agent)
def agent_dashboard(request):
    if not request.user.is_approved:
        return render(request, 'pending_approval.html')
    
    farmers = FarmerInfoModel.objects.filter(created_by=request.user)
    warehouses = WarehouseModel.objects.filter(created_by=request.user)
    transactions = FarmerToWarehouseModel.objects.filter(created_by=request.user)
    cultivation_costs = CultivationCostCalculator.objects.filter(created_by=request.user)
    crops = CropModel.objects.all()
    user_crops_count = CropModel.objects.filter(created_by=request.user).count()
    
    context = {
        'farmers': farmers,
        'warehouses': warehouses,
        'transactions': transactions,
        'cultivation_costs': cultivation_costs,
        'crops': crops,
        'user_crops_count': user_crops_count,
    }
    return render(request, 'agent_dashboard.html', context)

from django.contrib import messages

@login_required
@user_passes_test(is_approved_agent)
def crop_list(request):
    crops = CropModel.objects.all()
    active_crops = crops.filter(is_approved=True).count()
    user_crops = crops.filter(created_by=request.user).count()
    
    context = {
        'crops': crops,
        'active_crops': active_crops,
        'user_crops': user_crops,
    }
    return render(request, 'agent/crop_list.html', context)

@login_required
@user_passes_test(is_approved_agent)
def add_crop(request):
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES)   
        if form.is_valid():
            crop = form.save(commit=False)
            crop.created_by = request.user
            crop.save()
            messages.success(request, f'Crop "{crop.name}" added successfully!')
            return redirect('crop_list')
    else:
        form = CropForm()
    return render(request, 'agent/crop_form.html', {'form': form, 'title': 'Add Crop'})


@login_required
@user_passes_test(is_approved_agent)
def edit_crop(request, crop_id):
    crop = get_object_or_404(CropModel, id=crop_id)
    if request.method == 'POST':
        form = CropForm(request.POST, request.FILES, instance=crop) 
        if form.is_valid():
            form.save()
            messages.success(request, f'Crop "{crop.name}" updated successfully!')
            return redirect('crop_list')
    else:
        form = CropForm(instance=crop)
    return render(request, 'agent/crop_form.html', {'form': form, 'title': 'Edit Crop'})


@login_required
@user_passes_test(is_approved_agent)
def delete_crop(request, crop_id):
    crop = get_object_or_404(CropModel, id=crop_id)
    if request.method == 'POST':
        crop_name = crop.name
        crop.delete()
        messages.success(request, f'Crop "{crop_name}" deleted successfully!')
        return redirect('crop_list')
    return render(request, 'agent/confirm_delete.html', {'object': crop, 'type': 'Crop'})


@login_required
@user_passes_test(is_approved_agent)
def farmer_list(request):
    farmers = FarmerInfoModel.objects.filter(created_by=request.user)
    return render(request, 'agent/farmer_list.html', {'farmers': farmers})

@login_required
@user_passes_test(is_approved_agent)
def add_farmer(request):
    if request.method == 'POST':
        form = FarmerForm(request.POST)
        if form.is_valid():
            farmer = form.save(commit=False)
            farmer.created_by = request.user
            farmer.save()
            messages.success(request, 'Farmer added successfully!')
            return redirect('farmer_list')
    else:
        form = FarmerForm()
    return render(request, 'agent/farmer_form.html', {'form': form, 'title': 'Add Farmer'})

@login_required
@user_passes_test(is_approved_agent)
def edit_farmer(request, farmer_id):
    farmer = get_object_or_404(FarmerInfoModel, id=farmer_id, created_by=request.user)
    if request.method == 'POST':
        form = FarmerForm(request.POST, instance=farmer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farmer updated successfully!')
            return redirect('farmer_list')
    else:
        form = FarmerForm(instance=farmer)
    return render(request, 'agent/farmer_form.html', {'form': form, 'title': 'Edit Farmer'})

@login_required
@user_passes_test(is_approved_agent)
def delete_farmer(request, farmer_id):
    farmer = get_object_or_404(FarmerInfoModel, id=farmer_id, created_by=request.user)
    if request.method == 'POST':
        farmer.delete()
        messages.success(request, 'Farmer deleted successfully!')
        return redirect('farmer_list')
    return render(request, 'agent/confirm_delete.html', {'object': farmer, 'type': 'Farmer'})

@login_required
@user_passes_test(is_approved_agent)
def warehouse_list(request):
    warehouses = WarehouseModel.objects.filter(created_by=request.user)
    return render(request, 'agent/warehouse_list.html', {'warehouses': warehouses})

@login_required
@user_passes_test(is_approved_agent)
def add_warehouse(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save(commit=False)
            warehouse.created_by = request.user
            warehouse.save()
            messages.success(request, 'Warehouse added successfully!')
            return redirect('warehouse_list')
    else:
        form = WarehouseForm()
    return render(request, 'agent/warehouse_form.html', {'form': form, 'title': 'Add Warehouse'})

@login_required
@user_passes_test(is_approved_agent)
def edit_warehouse(request, warehouse_id):
    warehouse = get_object_or_404(WarehouseModel, id=warehouse_id, created_by=request.user)
    if request.method == 'POST':
        form = WarehouseForm(request.POST, instance=warehouse)
        if form.is_valid():
            form.save()
            messages.success(request, 'Warehouse updated successfully!')
            return redirect('warehouse_list')
    else:
        form = WarehouseForm(instance=warehouse)
    return render(request, 'agent/warehouse_form.html', {'form': form, 'title': 'Edit Warehouse'})

@login_required
@user_passes_test(is_approved_agent)
def delete_warehouse(request, warehouse_id):
    warehouse = get_object_or_404(WarehouseModel, id=warehouse_id, created_by=request.user)
    if request.method == 'POST':
        warehouse.delete()
        messages.success(request, 'Warehouse deleted successfully!')
        return redirect('warehouse_list')
    return render(request, 'agent/confirm_delete.html', {'object': warehouse, 'type': 'Warehouse'})

@login_required
@user_passes_test(is_approved_agent)
def transaction_list(request):
    transactions = FarmerToWarehouseModel.objects.filter(created_by=request.user)
    return render(request, 'agent/transaction_list.html', {'transactions': transactions})

@login_required
@user_passes_test(is_approved_agent)
def add_transaction(request):
    if request.method == 'POST':
        form = FarmerToWarehouseForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.created_by = request.user
            transaction.save()
            messages.success(request, 'Transaction added successfully!')
            return redirect('transaction_list')
    else:
        form = FarmerToWarehouseForm()
    return render(request, 'agent/transaction_form.html', {'form': form, 'title': 'Add Transaction'})

@login_required
@user_passes_test(is_approved_agent)
def edit_transaction(request, transaction_id):
    transaction = get_object_or_404(FarmerToWarehouseModel, id=transaction_id, created_by=request.user)
    if request.method == 'POST':
        form = FarmerToWarehouseForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transaction updated successfully!')
            return redirect('transaction_list')
    else:
        form = FarmerToWarehouseForm(instance=transaction)
    return render(request, 'agent/transaction_form.html', {'form': form, 'title': 'Edit Transaction'})

@login_required
@user_passes_test(is_approved_agent)
def delete_transaction(request, transaction_id):
    transaction = get_object_or_404(FarmerToWarehouseModel, id=transaction_id, created_by=request.user)
    if request.method == 'POST':
        transaction.delete()
        messages.success(request, 'Transaction deleted successfully!')
        return redirect('transaction_list')
    return render(request, 'agent/confirm_delete.html', {'object': transaction, 'type': 'Transaction'})

@login_required
@user_passes_test(is_approved_agent)
def cultivation_cost_list(request):
    cultivation_costs = CultivationCostCalculator.objects.filter(created_by=request.user)
    return render(request, 'agent/cultivation_cost_list.html', {'cultivation_costs': cultivation_costs})

@login_required
@user_passes_test(is_approved_agent)
def add_cultivation_cost(request):
    if request.method == 'POST':
        form = CultivationCostForm(request.POST)
        if form.is_valid():
            cultivation_cost = form.save(commit=False)
            cultivation_cost.created_by = request.user
            cultivation_cost.save()
            messages.success(request, 'Cultivation cost added successfully!')
            return redirect('cultivation_cost_list')
    else:
        form = CultivationCostForm()
    return render(request, 'agent/cultivation_cost_form.html', {'form': form, 'title': 'Add Cultivation Cost'})

@login_required
@user_passes_test(is_approved_agent)
def edit_cultivation_cost(request, cost_id):
    cultivation_cost = get_object_or_404(CultivationCostCalculator, id=cost_id, created_by=request.user)
    if request.method == 'POST':
        form = CultivationCostForm(request.POST, instance=cultivation_cost)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cultivation cost updated successfully!')
            return redirect('cultivation_cost_list')
    else:
        form = CultivationCostForm(instance=cultivation_cost)
    return render(request, 'agent/cultivation_cost_form.html', {'form': form, 'title': 'Edit Cultivation Cost'})

@login_required
@user_passes_test(is_approved_agent)
def delete_cultivation_cost(request, cost_id):
    cultivation_cost = get_object_or_404(CultivationCostCalculator, id=cost_id, created_by=request.user)
    if request.method == 'POST':
        cultivation_cost.delete()
        messages.success(request, 'Cultivation cost deleted successfully!')
        return redirect('cultivation_cost_list')
    return render(request, 'agent/confirm_delete.html', {'object': cultivation_cost, 'type': 'Cultivation Cost'})

@login_required
@user_passes_test(is_admin)
def approve_agent(request, user_id):
    user = get_object_or_404(User, id=user_id, role='agent')
    
    # Check if admin has district and if it matches agent's district
    # Superusers can approve anyone
    if not request.user.is_superuser:
        if request.user.district and user.district != request.user.district:
            messages.error(request, "You can only approve agents from your own district.")
            return redirect('admin_dashboard')
            
    user.is_approved = True
    user.save()
    messages.success(request, f'Agent {user.username} has been approved!')
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
def approve_warehouse(request, warehouse_id):
    warehouse = get_object_or_404(WarehouseModel, id=warehouse_id)
    warehouse.is_approved = True
    warehouse.save()
    messages.success(request, f'Warehouse {warehouse.shop_name} has been approved!')
    return redirect('admin_dashboard')

def coming_soon(request):
    return render(request, 'coming_soon.html')

def about(request):
    content = AboutPageContent.objects.last()
    return render(request, 'about.html', {'content': content})

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'profile.html', {'form': form})

@login_required
@user_passes_test(lambda u: u.role == 'govt')
def manage_about_content(request):
    content = AboutPageContent.objects.last()
    
    if request.method == 'POST':
        form = AboutPageContentForm(request.POST, request.FILES, instance=content)
        if form.is_valid():
            form.save()
            messages.success(request, 'About page content updated successfully!')
            return redirect('manage_about_content')
    else:
        form = AboutPageContentForm(instance=content)
    
    return render(request, 'manage_about.html', {'form': form, 'content': content})