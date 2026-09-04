from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import EmailOrUsernameTokenObtainPairView

from .api import (
	BatchViewSet,
	CategoryViewSet,
	CustomerViewSet,
	DashboardViewSet,
	MedicineViewSet,
	PrescriptionItemViewSet,
	PrescriptionViewSet,
	PurchaseOrderItemViewSet,
	PurchaseOrderViewSet,
	SaleOrderItemViewSet,
	SaleOrderViewSet,
	StockAuditLogViewSet,
	SupplierViewSet,
	UserViewSet,
)

router = DefaultRouter()
router.register('users', UserViewSet)
router.register('categories', CategoryViewSet)
router.register('customers', CustomerViewSet)
router.register('medicines', MedicineViewSet)
router.register('batches', BatchViewSet)
router.register('suppliers', SupplierViewSet)
router.register('purchase-orders', PurchaseOrderViewSet)
router.register('purchase-order-items', PurchaseOrderItemViewSet)
router.register('sales', SaleOrderViewSet)
router.register('sale-items', SaleOrderItemViewSet)
router.register('prescriptions', PrescriptionViewSet)
router.register('prescription-items', PrescriptionItemViewSet)
router.register('stock-audits', StockAuditLogViewSet)
router.register('dashboard', DashboardViewSet, basename='dashboard')

urlpatterns = [
	path('schema/', SpectacularAPIView.as_view(), name='schema'),
	path('auth/token/', EmailOrUsernameTokenObtainPairView.as_view(), name='token_obtain_pair'),
	path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
	path('', include(router.urls)),
]