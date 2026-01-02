from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public URLs
    path('', views.public_dashboard, name='public_dashboard'),
    path('crop/<int:crop_id>/', views.crop_details, name='crop_details'),
    path('about/', views.about, name='about'),
    path('coming-soon/', views.coming_soon, name='coming_soon'),
    
    # Authentication URLs
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

        # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('govt/dashboard/', views.govt_dashboard, name='govt_dashboard'),
    path('govt/dashboard/delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    
    # Farmer management URLs
    path('agent/farmers/', views.farmer_list, name='farmer_list'),
    path('agent/farmer/add/', views.add_farmer, name='add_farmer'),
    path('agent/farmer/edit/<int:farmer_id>/', views.edit_farmer, name='edit_farmer'),
    path('agent/farmer/delete/<int:farmer_id>/', views.delete_farmer, name='delete_farmer'),
    
    # Add these crop management URLs with the other agent URLs
    path('agent/crops/', views.crop_list, name='crop_list'),
    path('agent/crop/add/', views.add_crop, name='add_crop'),
    path('agent/crop/edit/<int:crop_id>/', views.edit_crop, name='edit_crop'),
    path('agent/crop/delete/<int:crop_id>/', views.delete_crop, name='delete_crop'),

    # Warehouse management URLs
    path('agent/warehouses/', views.warehouse_list, name='warehouse_list'),
    path('agent/warehouse/add/', views.add_warehouse, name='add_warehouse'),
    path('agent/warehouse/edit/<int:warehouse_id>/', views.edit_warehouse, name='edit_warehouse'),
    path('agent/warehouse/delete/<int:warehouse_id>/', views.delete_warehouse, name='delete_warehouse'),
    
    # Transaction management URLs
    path('agent/transactions/', views.transaction_list, name='transaction_list'),
    path('agent/transaction/add/', views.add_transaction, name='add_transaction'),
    path('agent/transaction/edit/<int:transaction_id>/', views.edit_transaction, name='edit_transaction'),
    path('agent/transaction/delete/<int:transaction_id>/', views.delete_transaction, name='delete_transaction'),
    
    # Cultivation cost management URLs
    path('agent/cultivation-costs/', views.cultivation_cost_list, name='cultivation_cost_list'),
    path('agent/cultivation-cost/add/', views.add_cultivation_cost, name='add_cultivation_cost'),
    path('agent/cultivation-cost/edit/<int:cost_id>/', views.edit_cultivation_cost, name='edit_cultivation_cost'),
    path('agent/cultivation-cost/delete/<int:cost_id>/', views.delete_cultivation_cost, name='delete_cultivation_cost'),
    
    # Admin approval URLs
    path('govt/approve-agent/<int:user_id>/', views.approve_agent, name='approve_agent'),
    path('govt/approve-warehouse/<int:warehouse_id>/', views.approve_warehouse, name='approve_warehouse'),
    
    # Profile URL
    path('profile/', views.profile, name='profile'),
    
    # System Login Check URL
    path('login_system/', views.login_system, name='login_system'),
    path('logout_system/', views.logout_system, name='logout_system'),
    
    # Manage About Content
    path('govt/manage-about/', views.manage_about_content, name='manage_about_content'),
]