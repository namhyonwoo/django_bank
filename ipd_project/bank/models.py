from django.db import models
from django.contrib.auth.models import AbstractUser

# 유저
class User(AbstractUser):
    total_account = models.IntegerField(default=0) # 총 계좌보유수
    fee_free_of_day = models.IntegerField(default=3) #하루당 면제 가능횟수
    REQUIRED_FIELDS = ['total_account', 'fee_free_of_day']

# 계좌
class Account(models.Model):

    # -계좌번호(pk)
    account_id = models.CharField(primary_key=True, max_length=20)
    # -회원_아이디(fk)
    user = models.ForeignKey('User', on_delete=models.DO_NOTHING)
    # -계좌종류 코드(fk)
    account_type = models.ForeignKey('AccountType', on_delete=models.DO_NOTHING)
    # -총 보유액
    amount = models.BigIntegerField(default=0)

    # -예외한도설정: boolean
    exception_limit_status = (
        ('n', '설정안함'),
        ('y', '설정함'),
    )
    exception_limit = models.CharField(
        max_length=1,
        choices=exception_limit_status,
        blank=False,
        default='n',
    )
    # -1회한도: -1은 기본값에 따름, 0은 거래불가
    limit_onetime = models.IntegerField(default=-1)
    # -1일한도: -1은 기본값에 따름, 0은 거래불가
    limit_oneday = models.IntegerField(default=-1)
    
    def __str__(self):
        return self.account_id

# 계좌종류
class AccountType(models.Model):
    # 계좌종류 코드(pk)
    id = models.CharField(primary_key=True, max_length=10)
    # -계좌이름:{일반,급여,적금}
    name = models.CharField(max_length=10)
    # -기본 1회 출금한도: n만원
    default_limit_onetime = models.IntegerField()
    # -기본 1일 출금한도: n만원
    default_limit_oneday = models.IntegerField()

    def __str__(self):
        return self.name

# 이체내역
class AccountTransferReport(models.Model):
    
    # 보낸 계좌번호
    sender_account = models.ForeignKey('Account', related_name='sender_account', on_delete=models.DO_NOTHING)
    # 받는 계좌번호
    receiver_account = models.ForeignKey('Account', related_name='receiver_account', on_delete=models.DO_NOTHING)
    # 보낼때 표시
    sended_label = models.CharField(max_length=10)
    # 받을때 표시
    received_label = models.CharField(max_length=10)
    # 송금액
    remittance =  models.IntegerField()
    # 수수료
    fee =  models.IntegerField()
    # 송금 시각
    reg_date = models.DateTimeField(auto_now_add=True)


