from django.db import transaction
from decimal import Decimal, ROUND_HALF_UP
import uuid

from django.db.models import Count, F, Q, Sum
from django.utils.timezone import now
from datetime import timedelta
from rest_framework import permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import CustomUser, PharmacySettings
from analytics.models import StockAuditLog
from customers.models import Customer
from inventory.models import Batch, Category, Medicine, MedicineReference
from prescriptions.models import Prescription, PrescriptionItem
from sales.models import SaleOrder, SaleOrderItem, SaleReturn, SaleReturnItem
from suppliers.models import PurchaseOrder, PurchaseOrderItem, Supplier


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    def get_role(self, user):
        return user.effective_role

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'is_active', 'is_staff', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')


class MyProfileSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    def get_role(self, user):
        return user.effective_role

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 'date_joined', 'last_login')
        read_only_fields = ('id', 'username', 'role', 'date_joined', 'last_login')


class PharmacySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PharmacySettings
        fields = '__all__'
        read_only_fields = ('id', 'updated_at')


class CustomerSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class MedicineSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_stock = serializers.IntegerField(read_only=True)
    active_batch_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Medicine
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')


class MedicineReferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicineReference
        fields = ('id', 'name', 'company', 'pack_size', 'sale_price', 'mrp', 'source_link')


class BatchSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)

    class Meta:
        model = Batch
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'


class PurchaseOrderCreateItemSerializer(serializers.Serializer):
    medicine_id = serializers.UUIDField()
    quantity_ordered = serializers.IntegerField(min_value=1)
    unit_cost = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'))


class PurchaseOrderCreateSerializer(serializers.Serializer):
    supplier_id = serializers.UUIDField()
    expected_delivery_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=(PurchaseOrder.Status.DRAFT, PurchaseOrder.Status.ORDERED), default=PurchaseOrder.Status.DRAFT)
    items = PurchaseOrderCreateItemSerializer(many=True, min_length=1)


class ReceivePurchaseItemSerializer(serializers.Serializer):
    medicine_id = serializers.UUIDField()
    batch_number = serializers.CharField(max_length=100)
    manufacture_date = serializers.DateField()
    expiry_date = serializers.DateField()
    quantity = serializers.IntegerField(min_value=1)
    purchase_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'))
    selling_price = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal('0.00'))


class ReceivePurchaseSerializer(serializers.Serializer):
    supplier_id = serializers.UUIDField()
    invoice_reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    items = ReceivePurchaseItemSerializer(many=True, min_length=1)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source='supplier.company_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class SaleOrderItemSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = SaleOrderItem
        fields = '__all__'


class SaleReturnItemInputSerializer(serializers.Serializer):
    sale_order_item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class SaleReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleReturn
        fields = '__all__'
        read_only_fields = ('id', 'return_number', 'processed_by', 'refund_amount', 'created_at')


class SaleReturnCreateSerializer(serializers.Serializer):
    reason = serializers.CharField()
    items = SaleReturnItemInputSerializer(many=True, min_length=1)


class PosCheckoutItemSerializer(serializers.Serializer):
    batch_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=Decimal('0.00'), min_value=Decimal('0.00'))


class PosCheckoutSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    customer_name = serializers.CharField(max_length=255, required=False, default='Walk-in Customer')
    customer_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    payment_method = serializers.ChoiceField(choices=SaleOrder.PaymentMethod.choices)
    discount_amount = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=Decimal('0.00'), min_value=Decimal('0.00'))
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=4, required=False, default=Decimal('0.05'), min_value=Decimal('0.00'))
    items = PosCheckoutItemSerializer(many=True, min_length=1)


class SaleOrderSerializer(serializers.ModelSerializer):
    items = SaleOrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = SaleOrder
        fields = '__all__'
        read_only_fields = ('id', 'invoice_number', 'created_at')


class PrescriptionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrescriptionItem
        fields = '__all__'


class PrescriptionSerializer(serializers.ModelSerializer):
    items = PrescriptionItemSerializer(many=True, read_only=True)
    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


class StockAuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAuditLog
        fields = '__all__'
        read_only_fields = ('id', 'timestamp', 'user')


class DashboardSerializer(serializers.Serializer):
    revenue_today = serializers.DecimalField(max_digits=14, decimal_places=2)
    sales_today = serializers.IntegerField()
    medicines_in_stock = serializers.IntegerField()
    low_stock_count = serializers.IntegerField()
    recent_sales = SaleOrderSerializer(many=True)


class BaseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]


class UserViewSet(BaseModelViewSet):
    queryset = CustomUser.objects.all().order_by('username')
    serializer_class = UserSerializer

    @action(detail=False, methods=['get', 'patch'], url_path='me')
    def me(self, request):
        if request.method == 'GET':
            return Response(MyProfileSerializer(request.user).data)

        serializer = MyProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SettingsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PharmacySettingsSerializer

    def list(self, request):
        return Response(self.serializer_class(PharmacySettings.load()).data)

    @action(detail=False, methods=['patch'], url_path='update')
    def update_settings(self, request):
        if request.user.effective_role != CustomUser.Role.ADMIN:
            return Response({'detail': 'Only administrators can update pharmacy settings.'}, status=403)
        serializer = self.serializer_class(PharmacySettings.load(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class CustomerViewSet(BaseModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(phone__icontains=search) | Q(email__icontains=search))
        return queryset


class CategoryViewSet(BaseModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MedicineViewSet(BaseModelViewSet):
    queryset = Medicine.objects.select_related('category').annotate(
        total_stock=Sum('batches__quantity', filter=Q(batches__is_active=True)),
        active_batch_count=Count('batches', filter=Q(batches__is_active=True)),
    ).all()
    serializer_class = MedicineSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', '').strip()
        category = self.request.query_params.get('category')
        stock_status = self.request.query_params.get('stock_status')

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(generic_name__icontains=search) | Q(barcode__icontains=search))
        if category:
            queryset = queryset.filter(category_id=category)
        if stock_status == 'low':
            queryset = queryset.filter(total_stock__lt=F('reorder_level'))
        return queryset

    @action(detail=False, methods=['get'], url_path='barcode/(?P<barcode>[^/.]+)')
    def barcode(self, request, barcode=None):
        medicine = self.get_queryset().filter(barcode=barcode).first()
        if medicine is None:
            return Response({'detail': 'Medicine not found.'}, status=404)
        batch = Batch.objects.filter(
            medicine=medicine,
            is_active=True,
            quantity__gt=0,
            expiry_date__gte=now().date(),
        ).order_by('expiry_date').first()
        if batch is None:
            return Response({'detail': 'This medicine has no sellable stock batch.'}, status=400)
        return Response({
            **self.get_serializer(medicine).data,
            'batch_id': str(batch.id),
            'selling_price': batch.selling_price,
            'available_quantity': batch.quantity,
        })

    @action(detail=False, methods=['get'], url_path='reference-search')
    def reference_search(self, request):
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response([])
        references = MedicineReference.objects.filter(
            Q(name__icontains=query) | Q(company__icontains=query)
        )[:12]
        return Response(MedicineReferenceSerializer(references, many=True).data)


class BatchViewSet(BaseModelViewSet):
    queryset = Batch.objects.select_related('medicine', 'supplier').all()
    serializer_class = BatchSerializer

    @action(detail=True, methods=['post'], url_path='adjust-stock')
    def adjust_stock(self, request, pk=None):
        if request.user.role not in (CustomUser.Role.ADMIN, CustomUser.Role.PHARMACIST):
            return Response({'detail': 'Only administrators and pharmacists can adjust stock.'}, status=403)

        try:
            quantity_changed = int(request.data.get('quantity_changed'))
        except (TypeError, ValueError):
            return Response({'detail': 'quantity_changed must be a whole number.'}, status=400)

        reason = str(request.data.get('reason', '')).strip()
        action_type = request.data.get('action_type', StockAuditLog.ActionType.MANUAL_CORRECTION)
        if not reason:
            return Response({'detail': 'A reason is required for stock adjustments.'}, status=400)
        if action_type not in StockAuditLog.ActionType.values:
            return Response({'detail': 'Invalid action_type.'}, status=400)

        with transaction.atomic():
            batch = self.get_queryset().select_for_update().get(pk=pk)
            if batch.quantity + quantity_changed < 0:
                return Response({'detail': 'Adjustment cannot reduce stock below zero.'}, status=400)
            batch.quantity += quantity_changed
            batch.save(update_fields=['quantity'])
            StockAuditLog.objects.create(
                user=request.user, batch=batch, action_type=action_type,
                quantity_changed=quantity_changed, reason=reason,
            )
        return Response(self.get_serializer(batch).data)


class SupplierViewSet(BaseModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class PurchaseOrderViewSet(BaseModelViewSet):
    queryset = PurchaseOrder.objects.select_related('supplier', 'created_by').prefetch_related('items').all()
    serializer_class = PurchaseOrderSerializer

    @action(detail=False, methods=['post'], url_path='receive-stock')
    def receive_stock(self, request):
        receive_serializer = ReceivePurchaseSerializer(data=request.data)
        receive_serializer.is_valid(raise_exception=True)
        payload = receive_serializer.validated_data
        with transaction.atomic():
            supplier = Supplier.objects.filter(id=payload['supplier_id'], is_active=True).first()
            if supplier is None:
                return Response({'detail': 'Select an active supplier.'}, status=400)
            medicine_ids = [item['medicine_id'] for item in payload['items']]
            medicines = {medicine.id: medicine for medicine in Medicine.objects.filter(id__in=medicine_ids)}
            if len(medicines) != len(set(medicine_ids)):
                return Response({'detail': 'One or more selected medicines no longer exist.'}, status=400)
            seen_batches = set()
            for item in payload['items']:
                key = (item['medicine_id'], item['batch_number'])
                if key in seen_batches or Batch.objects.filter(medicine_id=item['medicine_id'], batch_number=item['batch_number']).exists():
                    return Response({'detail': 'Each medicine batch number must be unique.'}, status=400)
                seen_batches.add(key)
            total_amount = sum(item['quantity'] * item['purchase_price'] for item in payload['items'])
            suffix = payload.get('invoice_reference', '').strip() or uuid.uuid4().hex[:8].upper()
            purchase_order = PurchaseOrder.objects.create(
                po_number=f'PO-{now().year}-{suffix}', supplier=supplier, order_date=now().date(),
                expected_delivery_date=now().date(), status=PurchaseOrder.Status.RECEIVED,
                total_amount=total_amount, created_by=request.user,
            )
            for item in payload['items']:
                medicine = medicines[item['medicine_id']]
                batch = Batch.objects.create(
                    medicine=medicine, batch_number=item['batch_number'],
                    manufacture_date=item['manufacture_date'], expiry_date=item['expiry_date'],
                    purchase_price=item['purchase_price'], selling_price=item['selling_price'],
                    quantity=item['quantity'], supplier=supplier,
                )
                PurchaseOrderItem.objects.create(
                    purchase_order=purchase_order, medicine=medicine,
                    quantity_ordered=item['quantity'], quantity_received=item['quantity'],
                    unit_cost=item['purchase_price'],
                )
                StockAuditLog.objects.create(
                    user=request.user, batch=batch, action_type=StockAuditLog.ActionType.STOCK_ADD,
                    quantity_changed=item['quantity'], reason=f'Received through purchase order {purchase_order.po_number}.',
                )
        purchase_order = self.get_queryset().get(id=purchase_order.id)
        return Response(self.get_serializer(purchase_order).data, status=201)

    @action(detail=False, methods=['post'], url_path='create-order')
    def create_order(self, request):
        order_serializer = PurchaseOrderCreateSerializer(data=request.data)
        order_serializer.is_valid(raise_exception=True)
        payload = order_serializer.validated_data
        with transaction.atomic():
            supplier = Supplier.objects.filter(id=payload['supplier_id'], is_active=True).first()
            if supplier is None:
                return Response({'detail': 'Select an active supplier.'}, status=400)
            medicine_ids = [item['medicine_id'] for item in payload['items']]
            medicines = {medicine.id: medicine for medicine in Medicine.objects.filter(id__in=medicine_ids)}
            if len(medicines) != len(set(medicine_ids)):
                return Response({'detail': 'One or more selected medicines no longer exist.'}, status=400)
            if len(medicine_ids) != len(set(medicine_ids)):
                return Response({'detail': 'A medicine can only appear once in a purchase order.'}, status=400)
            total_amount = sum(item['quantity_ordered'] * item['unit_cost'] for item in payload['items'])
            po_number = f'PO-{now().year}-{uuid.uuid4().hex[:8].upper()}'
            order = PurchaseOrder.objects.create(
                po_number=po_number, supplier=supplier, order_date=now().date(),
                expected_delivery_date=payload.get('expected_delivery_date'), status=payload['status'],
                total_amount=total_amount, created_by=request.user,
            )
            PurchaseOrderItem.objects.bulk_create([
                PurchaseOrderItem(
                    purchase_order=order, medicine=medicines[item['medicine_id']],
                    quantity_ordered=item['quantity_ordered'], unit_cost=item['unit_cost'],
                ) for item in payload['items']
            ])
        order = self.get_queryset().get(id=order.id)
        return Response(self.get_serializer(order).data, status=201)

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', '').strip()
        status = self.request.query_params.get('status')
        period = self.request.query_params.get('period')
        if search:
            queryset = queryset.filter(Q(po_number__icontains=search) | Q(supplier__company_name__icontains=search))
        if status:
            queryset = queryset.filter(status=status)
        if period == 'today':
            queryset = queryset.filter(order_date=now().date())
        elif period == '7days':
            queryset = queryset.filter(order_date__gte=now().date() - timedelta(days=6))
        elif period == 'month':
            today = now().date()
            queryset = queryset.filter(order_date__year=today.year, order_date__month=today.month)
        return queryset


class PurchaseOrderItemViewSet(BaseModelViewSet):
    queryset = PurchaseOrderItem.objects.select_related('purchase_order', 'medicine').all()
    serializer_class = PurchaseOrderItemSerializer


class SaleOrderViewSet(BaseModelViewSet):
    queryset = SaleOrder.objects.select_related('sold_by').prefetch_related('items').all()
    serializer_class = SaleOrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', '').strip()
        status = self.request.query_params.get('status')
        period = self.request.query_params.get('period')
        if search:
            queryset = queryset.filter(Q(invoice_number__icontains=search) | Q(customer_name__icontains=search) | Q(customer_phone__icontains=search))
        if status:
            queryset = queryset.filter(payment_status=status)
        if period == 'today':
            queryset = queryset.filter(created_at__date=now().date())
        elif period == '7days':
            queryset = queryset.filter(created_at__date__gte=now().date() - timedelta(days=6))
        elif period == 'month':
            today = now().date()
            queryset = queryset.filter(created_at__year=today.year, created_at__month=today.month)
        return queryset

    @action(detail=True, methods=['post'], url_path='return-sale')
    def return_sale(self, request, pk=None):
        if request.user.effective_role not in (CustomUser.Role.ADMIN, CustomUser.Role.PHARMACIST):
            return Response({'detail': 'Only administrators and pharmacists can process returns.'}, status=403)
        return_serializer = SaleReturnCreateSerializer(data=request.data)
        return_serializer.is_valid(raise_exception=True)
        payload = return_serializer.validated_data
        sale = self.get_queryset().filter(pk=pk).first()
        if sale is None:
            return Response({'detail': 'Sale not found.'}, status=404)
        if sale.payment_status == SaleOrder.PaymentStatus.CANCELLED:
            return Response({'detail': 'Cancelled sales cannot be returned.'}, status=400)

        with transaction.atomic():
            sale_items = {item.id: item for item in SaleOrderItem.objects.select_for_update().select_related('batch', 'medicine').filter(sale_order=sale)}
            requested_ids = [item['sale_order_item_id'] for item in payload['items']]
            if len(requested_ids) != len(set(requested_ids)):
                return Response({'detail': 'Each sale item can only be returned once per request.'}, status=400)
            refund_amount = Decimal('0.00')
            prepared_items = []
            for item in payload['items']:
                sale_item = sale_items.get(item['sale_order_item_id'])
                if sale_item is None:
                    return Response({'detail': 'A selected item does not belong to this sale.'}, status=400)
                previously_returned = SaleReturnItem.objects.filter(sale_order_item=sale_item).aggregate(total=Sum('quantity'))['total'] or 0
                available = sale_item.quantity - previously_returned
                if item['quantity'] > available:
                    return Response({'detail': f'Only {available} units of {sale_item.medicine.name} can still be returned.'}, status=400)
                item_refund = (sale_item.subtotal / sale_item.quantity * item['quantity']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                refund_amount += item_refund
                prepared_items.append((sale_item, item['quantity'], item_refund))
            sale_return = SaleReturn.objects.create(sale_order=sale, processed_by=request.user, reason=payload['reason'], refund_amount=refund_amount)
            for sale_item, quantity, item_refund in prepared_items:
                SaleReturnItem.objects.create(sale_return=sale_return, sale_order_item=sale_item, quantity=quantity, refund_amount=item_refund)
                batch = Batch.objects.select_for_update().get(pk=sale_item.batch_id)
                batch.quantity += quantity
                batch.save(update_fields=['quantity'])
                StockAuditLog.objects.create(user=request.user, batch=batch, action_type=StockAuditLog.ActionType.STOCK_ADD, quantity_changed=quantity, reason=f'Returned from invoice {sale.invoice_number} via {sale_return.return_number}.')
            sale.payment_status = SaleOrder.PaymentStatus.REFUNDED
            sale.save(update_fields=['payment_status'])
        return Response(SaleReturnSerializer(sale_return).data, status=201)

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        checkout_serializer = PosCheckoutSerializer(data=request.data)
        checkout_serializer.is_valid(raise_exception=True)
        payload = checkout_serializer.validated_data
        quantized = lambda amount: amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

        with transaction.atomic():
            prepared_items = []
            subtotal = Decimal('0.00')
            for item in payload['items']:
                batch = Batch.objects.select_for_update().select_related('medicine').filter(id=item['batch_id'], is_active=True).first()
                if batch is None:
                    return Response({'detail': 'An item batch is unavailable.'}, status=400)
                if batch.quantity < item['quantity']:
                    return Response({'detail': f'Insufficient stock for {batch.medicine.name}. Available: {batch.quantity}.'}, status=400)
                line_total = quantized((batch.selling_price * item['quantity']) - item['discount'])
                if line_total < 0:
                    return Response({'detail': f'Line discount cannot exceed the price for {batch.medicine.name}.'}, status=400)
                subtotal += line_total
                prepared_items.append((batch, item, line_total))

            order_discount = payload['discount_amount']
            if order_discount > subtotal:
                return Response({'detail': 'Order discount cannot exceed the subtotal.'}, status=400)
            taxable_amount = subtotal - order_discount
            tax_amount = quantized(taxable_amount * payload['tax_rate'])
            grand_total = quantized(taxable_amount + tax_amount)
            sale = SaleOrder.objects.create(
                customer=Customer.objects.filter(id=payload.get('customer_id'), is_active=True).first() if payload.get('customer_id') else None,
                customer_name=payload['customer_name'] or 'Walk-in Customer',
                customer_phone=payload.get('customer_phone') or None,
                sold_by=request.user,
                subtotal=quantized(subtotal),
                discount_amount=quantized(order_discount),
                tax_amount=tax_amount,
                grand_total=grand_total,
                payment_method=payload['payment_method'],
                payment_status=SaleOrder.PaymentStatus.COMPLETED,
            )
            if sale.customer:
                sale.customer_name = sale.customer.full_name
                sale.customer_phone = sale.customer.phone
                sale.save(update_fields=['customer_name', 'customer_phone'])
            for batch, item, line_total in prepared_items:
                SaleOrderItem.objects.create(
                    sale_order=sale, medicine=batch.medicine, batch=batch,
                    quantity=item['quantity'], unit_price=batch.selling_price,
                    discount=item['discount'], subtotal=line_total,
                )
                batch.quantity -= item['quantity']
                batch.save(update_fields=['quantity'])
                StockAuditLog.objects.create(
                    user=request.user, batch=batch,
                    action_type=StockAuditLog.ActionType.MANUAL_CORRECTION,
                    quantity_changed=-item['quantity'],
                    reason=f'Sold through invoice {sale.invoice_number}.',
                )
        return Response(SaleOrderSerializer(sale).data, status=201)


class SaleOrderItemViewSet(BaseModelViewSet):
    queryset = SaleOrderItem.objects.select_related('sale_order', 'medicine', 'batch').all()
    serializer_class = SaleOrderItemSerializer


class PrescriptionViewSet(BaseModelViewSet):
    queryset = Prescription.objects.select_related('created_by').prefetch_related('items').all()
    serializer_class = PrescriptionSerializer


class PrescriptionItemViewSet(BaseModelViewSet):
    queryset = PrescriptionItem.objects.select_related('prescription', 'medicine').all()
    serializer_class = PrescriptionItemSerializer


class StockAuditLogViewSet(BaseModelViewSet):
    queryset = StockAuditLog.objects.select_related('user', 'batch').all()
    serializer_class = StockAuditLogSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DashboardSerializer

    def get_serializer_class(self):
        return self.serializer_class

    def list(self, request):
        today = now().date()
        sales = SaleOrder.objects.filter(created_at__date=today, payment_status=SaleOrder.PaymentStatus.COMPLETED)
        total_stock = Batch.objects.filter(is_active=True).aggregate(total=Sum('quantity'))['total'] or 0
        low_stock = Medicine.objects.filter(batches__is_active=True).annotate(stock=Sum('batches__quantity')).filter(stock__lt=F('reorder_level')).count()
        return Response({
            'revenue_today': sales.aggregate(total=Sum('grand_total'))['total'] or 0,
            'sales_today': sales.count(), 'medicines_in_stock': total_stock,
            'low_stock_count': low_stock,
            'recent_sales': SaleOrderSerializer(SaleOrder.objects.all()[:5], many=True).data,
        })