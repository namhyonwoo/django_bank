from django.http import HttpResponse, HttpResponseRedirect
from http import HTTPStatus
from django.urls import reverse
from django.shortcuts import render
from django.contrib import auth
from .models import User, Account, AccountTransferReport
from django.core import serializers
import json
from django.utils import timezone
# Create your views here.

# @login_required
def index(request):

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html')

def transter(request):
    # book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        return 
    else:
        #  내 계좌리스트 조회
        user = request.user
        account_list = Account.objects.filter(user=user)
        sended_label = user.last_name+user.first_name
        # print(account_list)
        

    context = {
        'account_list': account_list,
        'sended_label': sended_label
    }
    return render(request, 'bank/transfer.html', context)

# 유효한 계좌인지 조회
def validateAccount(request):
    received_json_data = json.loads(request.body.decode("utf-8"))
    reponse = {
        'isValidAccount' : False,
        'owner_name'  : ''
    }
    account_id = received_json_data['account_id']
    try:
        account = Account.objects.get(pk=account_id)
        reponse['isValidAccount'] = True
        reponse['owner_name'] =  account.user.last_name + account.user.first_name

    except Account.DoesNotExist:
        pass
    finally:
        return HttpResponse(json.dumps(reponse),
        content_type = 'application/javascript; charset=utf8')

# 계좌에서 보유한 금액 조회
def getAmount(request, account_id):
    # 계좌번호
    # account_id = request.GET['account_id']
    content = {
        'amount' : 0,
    }
    # 있으면 반환
    response = HttpResponse('', 'application/javascript; charset=utf8')
    try:
        account = Account.objects.get(pk=account_id)
        content['amount'] =  account.amount
        response.content = json.dumps(content)

        return response

    except Account.DoesNotExist:

        response.status_code = HTTPStatus.NO_CONTENT
        return response

# 수수료 조회
def getFee(request):
    # 계좌번호
    sender_account = request.GET['sender_account']
    receiver_account = request.GET['receiver_account']
    
    content = {
        'fee' : 500,
    }
    response = HttpResponse(content, 'application/javascript; charset=utf8')
    # 세션이 없다면 종료
    if request.user is None:
        response.status_code = HTTPStatus.FORBIDDEN
        return response
    
    try:
        # 하루 무료건수 조회: fee_free_of_day
        user = User.objects.get(pk=request.user.id)
        fee_free_of_day = user.fee_free_of_day
            
        count = 0 # 무료건수확인변수
        # 당월 이체건수 조회 후 (내계좌인데 타행계좌 또는 타계좌) n회 이하면 무료
        today = timezone.now()
        reports = AccountTransferReport.objects.filter(reg_date__year=today.year, reg_date__month=today.month, sender_account=sender_account).select_related('sender_account','receiver_account').all()

        for report in reports:
            if report.sender_account.user == report.receiver_account.user:
                # 보낸 유저 아이디와 받은 유저 아이디 같으면서 통장종류가 같은 것을 제외
                if report.sender_account.account_type == report.receiver_account.account_type:
                    print(report.receiver_account)
                    continue
            count+=1

        print(f'count: {count}' )
        # 수수료 한도 넘었나
        if count >= fee_free_of_day:
            receive_account = Account.objects.get(pk=receiver_account)
            sender_account = Account.objects.get(pk=sender_account)
            receive_user = receive_account.user
            # 타 계좌일경우 :500원
            if receive_user.id != user.id:
                pass
            # 내계좌인데 같은 종류:0원
            elif receive_account.account_type == sender_account.account_type:
                content['fee'] = 0
        else:
            content['fee'] = 0

        response.content = json.dumps(content)
        return response

    except User.DoesNotExist:

        response.status_code = HTTPStatus.NOT_FOUND
        response.content = json.dumps(content)
        return response
