from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from bank.models import User, Account, AccountType, AccountTransferReport

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'total_account', 'date_joined')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name','last_name',)}),
        ('Bank Setting', {'fields': ('total_account','fee_free_of_day')}),
    )

admin.site.unregister(Group)
admin.site.register(User, UserAdmin)
# admin.site.register(Account)
admin.site.register(AccountType)

@admin.register(AccountTransferReport)
class AccountTransferReportAdmin(admin.ModelAdmin):
    list_display = ('sender_account', 'receiver_account', 'sended_label', 'received_label', 'remittance', 'fee', 'reg_date')

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('account_id', 'user', 'amount', 'account_type', 'exception_limit', 'limit_onetime', 'limit_oneday')