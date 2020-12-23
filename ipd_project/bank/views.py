from django.http import HttpResponse, HttpResponseRedirect
from http import HTTPStatus
from django.urls import reverse
from django.shortcuts import render
from django.contrib import auth
from .models import User, Account, AccountTransferReport
from django.core import serializers
import json
from django.utils import timezone
from django.db import transaction
from celery import shared_task
import redis
from .redisqueue import RedisQueue

# 모든 사용자와 공유할 수있는 스태틱 큐를 생성
# 송신자 계좌를 구분자로 갖고, 총 송금가능 누적 정보를 담는다
# class StaticQueue:
#     # queue =[] # Access through class
#     queue = redis.Redis(host='localhost', port=6379, db=0)
# instance = StaticQueue()

def index(request):
    return render(request, 'index.html')

# 큐를 담는 클래스 생성    

rq = RedisQueue('my-queue', host='localhost', port=6379, db=0)

# 계좌이체 실행
# 트랜잭션 추가
def transfer(request):

    r = rq.getInstance()

    # logined user
    user = request.user

    if request.method == 'POST':

        response = {
            'is_succeful'  : True,
            'error'  : ''
        }
        # 받은 파라미터 
        received_json_data = json.loads(request.body.decode("utf-8"))
        sender_account = received_json_data['sender_account']
        receiver_account = received_json_data['receiver_account']
        sended_label = received_json_data['sended_label']
        received_label = received_json_data['received_label']
        remittance = received_json_data['remittance']
        fee = received_json_data['fee']

        # 파라미터가 비었다면
        if sender_account is None or receiver_account is None or sended_label is None or received_label is None or remittance is None or fee is None:
            response['error'] = 'param error'
            return HttpResponse(json.dumps(response), 'application/javascript; charset=utf8')
       
        # 송금액과 수수료를 정수로 바꿈
        remittance = int(remittance)
        fee = int(fee)
        # 통장에서 차감될 금액
        ready_amount = remittance + fee
        #  내 계좌에서 금액 남았는지 다시한번 조회
        my_account = Account.objects.get(pk=sender_account)

        # 큐에서 같은 계좌아이디 값의 대기정보 객체를 찾음
        trasfer_info = r.get(sender_account)

        # 찾았다면
        if trasfer_info is not None:
            trasfer_info_d = json.loads(trasfer_info)
            # print(f"founded expectTotalAmount : {trasfer_info_d['expectTotalAmount']}")
            # print(f"ready_amount : {ready_amount}")
            # print(f"my_account amount : {my_account.amount}")
            # print(f"sum : {trasfer_info_d['expectTotalAmount']+ready_amount}")
        # 없다면 
        else:
            trasfer_info_d = {
                'id' : sender_account,
                'expectTotalAmount' : 0
            }
            
        # 남은금액이 모자라면
        if trasfer_info_d['expectTotalAmount']+ready_amount > my_account.amount:
            response['is_succeful'] = False
            response['error'] = '남은금액 없음'
            return HttpResponse(json.dumps(response), 'application/javascript; charset=utf8')
        else:
        # 충분하다면
            trasfer_info_d['expectTotalAmount'] += ready_amount
            trasfer_info = json.dumps(trasfer_info_d)
            r.set(sender_account, trasfer_info)

        taskTansfer.delay(received_json_data)

        return HttpResponse(json.dumps(response), 'application/javascript; charset=utf8')
    
    # get요청이면
    else:    
        account_list = Account.objects.filter(user=user)
        context = {
            'account_list' : account_list
        }
        return render(request, 'bank/transfer.html', context)

@shared_task
def taskTansfer(received_json_data):
    
    r = rq.getInstance()
    
    sender_account = received_json_data['sender_account']
    receiver_account = received_json_data['receiver_account']
    sended_label = received_json_data['sended_label']
    received_label = received_json_data['received_label']
    remittance = int(received_json_data['remittance'])
    fee = int(received_json_data['fee'])
    ready_amount = remittance + fee

    try:
        # Start test code
        validate_transfer()
        # END test code

        AccountTransferReport.objects.create(sender_account=Account.objects.get(pk=sender_account), receiver_account=Account.objects.get(pk=receiver_account), sended_label=sended_label, received_label=received_label, remittance=remittance, fee=fee)
        
        # 저장전에 총액을 다시 불러온다 refresh form db
        my_account = Account.objects.get(pk=sender_account)
        # my_account.refresh_from_db()

        with transaction.atomic():
            # 내 계좌에서 빼고
            my_account.amount -= ready_amount
            my_account.save()

            # 받는계좌에 더함
            receiver_account = Account.objects.get(pk=receiver_account)
            receiver_account.amount += remittance
            receiver_account.save()

    except Exception as e:
        print('예외가 발생했습니다.', e)

    finally:   
        trasfer_info = r.get(sender_account)
        print(trasfer_info)
        trasfer_info_d = json.loads(trasfer_info)
        trasfer_info_d['expectTotalAmount'] -= ready_amount
        if trasfer_info_d['expectTotalAmount'] <= 0:
            r.delete(sender_account)
        else:
            trasfer_info = json.dumps(trasfer_info_d)
            r.set(sender_account, trasfer_info)



from time import sleep
from random import uniform as uniform_random
def validate_transfer():
    """
    Internal Product Developer 기술 과제 2
    이 함수는 본래 이체 결과를 검증하기 위한 함수입니다.
    7 - 30초의 지연을 발생시킬 뿐이지만, 편의를 위해 본래의 역할을 한다고 가정해주세요.
    """
    sleep(uniform_random(7, 30))
    return True



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

    # 하루 무료건수 조회: fee_free_of_day
    user = User.objects.get(pk=request.user.id)
    fee_free_of_day = user.fee_free_of_day
        
    count = 0 # 무료건수확인변수
    # 당월 이체건수 조회 후 (내계좌인데 타행계좌 또는 타계좌) n회 이하면 무료
    today = timezone.now()
    reports = AccountTransferReport.objects.filter(reg_date__year=today.year, reg_date__month=today.month, sender_account=sender_account).select_related('sender_account','receiver_account')

    # print(reports.query)

    for report in reports:
        if report.sender_account.user == report.receiver_account.user:
            # 보낸 유저 아이디와 받은 유저 아이디 같으면서 통장종류가 같은 것을 제외
            if report.sender_account.account_type == report.receiver_account.account_type:
                # print(report.receiver_account)
                continue
        count+=1

    # print(f'count: {count}' )
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
    # 응답 보냄
    response.content = json.dumps(content)
    return response