from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
from django.core.exceptions import ValidationError
from django.conf import settings
import platform
import GPUtil
import psutil
import wmi
import random
import string
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta

class Stall(models.Model):
    store_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='stall_logos/')
    contact_number = models.CharField(max_length=15)
    is_active = models.BooleanField(default=True)  # Add is_active field with default value True

    def __str__(self):
        return self.name



class AdminProfile(models.Model):
    firstname = models.CharField(max_length=50)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    lastname = models.CharField(max_length=50)
    age = models.IntegerField()
    birthdate = models.DateField()
    address = models.TextField()
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=254, unique=True, default='', blank=True)
    password = models.CharField(max_length=100)
    contact_number = models.CharField(max_length=15)
    stall = models.ForeignKey('Stall', on_delete=models.CASCADE, related_name="admins", to_field='store_id')
  

    def clean(self):
        if self.stall:
            existing_admin = AdminProfile.objects.filter(stall=self.stall).exclude(id=self.id).exists()
            if existing_admin:
                raise ValidationError(f'Stall {self.stall.name} already has an admin assigned.')

    def save(self, *args, **kwargs):
        self.clean()
        if not self.email:
            self.email = f"{self.username}@default.com"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.stall.store_id}"

class CustomUser(AbstractUser):
    middle_name = models.CharField(max_length=50, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    birthdate = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    # Add related_name to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = 'custom_user'

class Supplier(models.Model):
    stall = models.ForeignKey(Stall, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100)
    middle_initial = models.CharField(max_length=1)
    lastname = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=200)
    license_number = models.CharField(max_length=50, unique=True)
    address = models.TextField(max_length=50)
    contact_number = models.CharField(max_length=15)
    email_address = models.EmailField()
    contract_start_date = models.DateField()
    contract_end_date = models.DateField()

    def clean(self):
        # Validate dates
        if self.contract_start_date and self.contract_end_date:
            if self.contract_start_date > self.contract_end_date:
                raise ValidationError({
                    'contract_start_date': 'Start date cannot be after end date',
                    'contract_end_date': 'End date cannot be before start date'
                })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.stall.name}"

class Supply(models.Model):
    STATUS_CHOICES = [
        ('good', 'Good'),
        ('expired', 'Expired')
    ]
    
    supply_id = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    date_added = models.DateField()
    expiration_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='good')
    stall = models.ForeignKey('Stall', on_delete=models.CASCADE, related_name='supplies', to_field='store_id')
    supplier = models.ForeignKey('Supplier', on_delete=models.CASCADE, related_name='supplies')
    supplier_name = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['supply_id', 'stall']
        
    def save(self, *args, **kwargs):
        # Update status based on expiration date
        if self.expiration_date:
            today = timezone.now().date()
            self.status = 'expired' if self.expiration_date <= today else 'good'
            
        super().save(*args, **kwargs)
        
    def __str__(self):
        supplier_info = f" ({self.supplier_name})" if self.supplier_name else ""
        return f"{self.supply_id} - {self.name}{supplier_info}"




class Item(models.Model):
    item_id = models.CharField(max_length=50)
    stall = models.ForeignKey('Stall', on_delete=models.CASCADE, related_name='items')
    name = models.CharField(max_length=255)
    picture = models.ImageField(upload_to='item_images/')
    category = models.ForeignKey('Category', on_delete=models.PROTECT, related_name='items')
    size = models.CharField(max_length=50, blank=True, null=True)
    measurement = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=0)
    expiration_date = models.DateTimeField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    supplies = models.ManyToManyField('Supply', through='ItemSupply')

    def save(self, *args, **kwargs):
        if not self.item_id:
            # Generate unique item ID when creating new item
            prefix = self.stall.name[:3].upper()
            timestamp = timezone.now().strftime('%y%m%d%H%M')
            random_suffix = ''.join(random.choices(string.digits, k=4))
            self.item_id = f"{prefix}-{timestamp}-{random_suffix}"
        super().save(*args, **kwargs)

    def __str__(self):
        size_str = f" ({self.size})" if self.size else ""
        return f"{self.item_id} - {self.name}{size_str}"

    class Meta:
        ordering = ['name']
        unique_together = ['stall', 'name', 'size']






class ItemAddOn(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='add_ons')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.item.name} - {self.name} (₱{self.price})"

    class Meta:
        ordering = ['name']

class ItemSupply(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='item_supplies')
    supply = models.ForeignKey('Supply', on_delete=models.CASCADE, related_name='item_supplies')
    quantity_per_item = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Quantity of supply used per item"
    )

    def clean(self):
        if self.quantity_per_item > self.supply.quantity:
            raise ValidationError("Quantity per item cannot exceed available supply quantity")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item.name} - {self.supply.name} ({self.quantity_per_item})"

    class Meta:
        unique_together = ['item', 'supply']
        verbose_name_plural = "Item supplies"






class Category(models.Model):
    stall = models.ForeignKey('Stall', on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)

  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.stall.name}"

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = ['stall', 'name']



















class LoginHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    admin_profile = models.ForeignKey('AdminProfile', on_delete=models.SET_NULL, null=True, blank=True)
    username = models.CharField(max_length=150)
    ip_address = models.GenericIPAddressField()
    login_time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20)  # success, failed
    user_agent = models.TextField(null=True, blank=True)
    attempt_count = models.IntegerField(default=1)
    is_blocked = models.BooleanField(default=False)
    block_expires = models.DateTimeField(null=True, blank=True)
    
    # System Information
    operating_system = models.CharField(max_length=50, null=True, blank=True)
    os_version = models.CharField(max_length=50, null=True, blank=True)
    processor_info = models.CharField(max_length=255, null=True, blank=True)
    gpu_info = models.CharField(max_length=255, null=True, blank=True)
    browser = models.CharField(max_length=50, null=True, blank=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)
    wifi_name = models.CharField(max_length=100, null=True, blank=True)
    
    class Meta:
        verbose_name_plural = 'Login History'
        ordering = ['-login_time']

    @staticmethod
    def get_system_info():
        system_info = {
            'operating_system': platform.system(),
            'os_version': platform.version(),
            'processor_info': platform.processor(),
            'gpu_info': '',
            'wifi_name': ''
        }
        
        try:
            # Get GPU information
            gpus = GPUtil.getGPUs()
            if gpus:
                system_info['gpu_info'] = f"{gpus[0].name} ({gpus[0].memoryTotal}MB)"
            
            # Get WiFi name (Windows only)
            if platform.system() == 'Windows':
                w = wmi.WMI()
                os_info = w.Win32_OperatingSystem()[0]
                processor = w.Win32_Processor()[0]
                
                # Get WiFi name using netsh command
                try:
                    import subprocess
                    result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                         capture_output=True, text=True)
                    if 'SSID' in result.stdout:
                        for line in result.stdout.split('\n'):
                            if 'SSID' in line and 'BSSID' not in line:
                                system_info['wifi_name'] = line.split(':')[1].strip()
                                break
                except:
                    pass
                
                system_info.update({
                    'os_version': os_info.Caption,
                    'processor_info': processor.Name
                })
        except Exception as e:
            print(f"Error getting system info: {str(e)}")
            
        return system_info

class Employee(models.Model):
    stall = models.ForeignKey('Stall', on_delete=models.CASCADE, related_name='employees')
    firstname = models.CharField(max_length=50)
    middle_initial = models.CharField(max_length=1, blank=True, null=True)
    lastname = models.CharField(max_length=50)
    age = models.IntegerField()
    birthdate = models.DateField()
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    religion = models.CharField(max_length=50, blank=True, null=True)
    position = models.CharField(max_length=50)
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    raw_password = models.CharField(max_length=50, default='default123', verbose_name='Visible Password')
    date_hired = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.firstname} {self.lastname} - {self.position}"

    class Meta:
        ordering = ['lastname', 'firstname']

    def save(self, *args, **kwargs):
        if not self.raw_password and self.password:
            self.raw_password = self.password
        super().save(*args, **kwargs)

class Transaction(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('gcash', 'GCash'),
        ('maya', 'Maya')
    ]
    
    transaction_id = models.CharField(max_length=50, unique=True)
    stall = models.ForeignKey('Stall', on_delete=models.CASCADE)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            prefix = self.stall.name[:3].upper()
            timestamp = timezone.now().strftime('%y%m%d%H%M')
            random_suffix = ''.join(random.choices(string.digits, k=4))
            self.transaction_id = f"TXN-{prefix}-{timestamp}-{random_suffix}"
        if not self.date:
            self.date = timezone.now().date()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.transaction_id} - ₱{self.total_amount}"

    class Meta:
        ordering = ['-date', '-created_at']

class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey('Item', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)

class TransactionItemAddOn(models.Model):
    transaction_item = models.ForeignKey(TransactionItem, on_delete=models.CASCADE, related_name='add_ons')
    add_on = models.ForeignKey('ItemAddOn', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)





class StallContract(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue')
    ]
    
    stall = models.ForeignKey(Stall, on_delete=models.CASCADE, related_name='contracts')
    start_date = models.DateField(null=True, blank=True)  # Allow null for initial creation
    duration_months = models.IntegerField()
    monthly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def end_date(self):
        if not self.start_date:
            return None
        return self.start_date + timedelta(days=self.duration_months * 30)

    @property
    def total_amount(self):
        return self.monthly_rate * self.duration_months

    def __str__(self):
        status = f"(Not Started)" if not self.start_date else f"({self.start_date} to {self.end_date})"
        return f"{self.stall.name}'s Contract {status}"

    class Meta:
        ordering = ['-created_at']

class StallPayment(models.Model):
    contract = models.ForeignKey(StallContract, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(auto_now_add=True)  # Automatically set to current date
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_number = models.CharField(max_length=50, unique=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def update_contract_status(self):
        contract = self.contract
        current_date = timezone.now().date()
        
        # Get all payments for this contract, including the current one
        total_paid = contract.payments.aggregate(
            total=models.Sum('amount_paid'))['total'] or 0
        if not self.pk:  # If this is a new payment
            total_paid += self.amount_paid
            
        total_expected = contract.monthly_rate * contract.duration_months
        
        # Update contract status based on payments and due date
        if total_paid >= total_expected:
            contract.payment_status = 'paid'
        elif contract.end_date < current_date:
            contract.payment_status = 'overdue'
        else:
            contract.payment_status = 'pending'
        
        contract.save()
    
    def save(self, *args, **kwargs):
        # Generate receipt number if not provided
        if not self.receipt_number:
            prefix = "RCPT"
            timestamp = timezone.now().strftime('%y%m%d%H%M')
            random_suffix = ''.join(random.choices(string.digits, k=4))
            self.receipt_number = f"{prefix}-{timestamp}-{random_suffix}"
        
        # Update contract payment status
        self.update_contract_status()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Payment for {self.contract.stall.name} - {self.payment_date}"
    
    class Meta:
        ordering = ['-payment_date']

class TransactionReport(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='reports')
    title = models.CharField(max_length=200)
    description = models.TextField()
    file = models.FileField(upload_to='transaction_reports/')
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Report by {self.employee.user.username} - {self.submitted_at.date()}"
    
    class Meta:
        ordering = ['-submitted_at']


