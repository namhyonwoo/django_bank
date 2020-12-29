파이썬 django와 celery, redis로 비동기 작업 큐 만들기
=======

프로젝트 개요
-------------
서버에 오랜시간이 걸리는 작업이 들어와도 클라이언트의 빠른 응답을 보장하고, 여러 작업의 동시적 요청이 들어와도 관련된 데이터가 정상적으로 처리가 되어야 한다.

주요 구현스택
>서버:python 3.6.4, django 2.2.17, celery 5.0, redis
>클라이언트:javascript, bootstrap, jquery

기능요구사항
1. 회원가입, 계좌, 계좌이체내역 조회 가능해야함 (admin 에서)
2. 계좌이체 가능해야함
3. 계좌이체시 이체작업 직전에 슬립 함수로 임의로 병목을 준 상황에서 다른 입금 요청시 정상적으로 처리가 되어야하고 클라이언트는 바로 응답(2초이내)을 받아야 함.

데이터베이스
------------
> USER(id, username, total_account, fee_free_of_day)

> ACCOUNT(account_id, user, account_type, amount, exception_limit, limit_onetime, limit_oneday)

> ACCOUNT_TYPE(id, name, default_limit_onetime, default_limit_oneday)

> ACCOUNT_TRANSFER_REPORT(sender_account, receiver_account, sended_label, received_label, remittance, fee, reg_date)


구현컨셉
-------------
1. 여러 작업 요청시 보유 계좌의 금액 총량 > 출금액의 시점에서 실행을 보장해야 하므로
2. 서로 다른 요청을 저장과 공유 할 수있는 데이터공간이 필요하기 떄문에 내역을 담을 메모리 캐쉬를 사용
3. 클라이언트 응답을 2초내에 보장 받아야 하므로 결과를 일단주고 실행은 서버에서 따로 동작하는 비동기 응답 방식을 사용하기로 함
4. 파이썬에서 쉽게 사용할수 있는 작업큐 celery를 선택하고, 메시지 브로커와 메모리저장소의 역할을 동시에 하는 redis를 선택.

##핵심기능(계좌이체) 구현 과정
1. 메모리공간(redis)에 보내는 계좌번호를 식별자로 지정하여 대기열의 금액 +현재 이체금액을 저장하여 요청작업을 생성함. 
2. 총 대기 이체금액보다 계좌 보유액이 적으면 금액부족 리턴
3. celery 워커가 대기한 작업 큐(db저장)를 실행후 성공 또는 실패시 대기 잔고를 지움

*redis 적용 이유: 동시에 계좌이체가 발생한 상황을 가정해서 계좌의 잔고와 대기 송금요청을 비교하기 위해 worker와 어플리케이션간에 메모리공간을 공유할수 있어야 했다*


localhost:8000에서 Django 서버 어플리케이션 실행 방법
-------------

0. 구동에 필요한 패키지 설치
> pip install -r requirements.txt

1. redis 설치 후 redis서버 실행 
> https://redis.io/download

2. celery 워커 실행
> celery --app  ipd_project worker -l DEBUG

3. 타 터미널에서 django manage.py와 동일한 디렉토리에서 서버 실행
> python manage.py runserver


테스트 방법
-------------
1. django admin 에서 테스트에 필요한 자원(사용자 / 계좌/ 계좌종류 / 계좌이체 정보)을 생성/관리 할수 있습니다.(admin /123) <br>
2. 회원은 로그인후 계좌이체 메뉴에서 계좌정보 입력후 수수료가 계산되고나면 
3. 모달창이 뜨고 화면에서 이체 할 수있습니다.
4. 이체결과는 테스트를 위해 웹브라우져 콘솔로 표시됩니다.


알게된 것
-------------
1. 병목(슬립)중인 프로세스의 자원을 다른 프로세스가 조회하여 실행시 의도 하지 않은 불일치(나중실행이 이전실행의 자원을 덮어씀)가 발생할수 있다. 
2. 자원의 위치가 데이터 베이스의 경우 트랜잭션 도중 다른 트랜잭션이 개입 할 수 있으므로 고립 레벨을 설정해 주거나 또는 select for update로 레코드를 잠가야한다.
3. celery 서비스 워커는 기본적으로 process로 fork하지만 쓰레드로도 실행할 수 있다. disk io작업이 많을시 유리, cpu작업을 위주로한다면 프로세스 방식이나 sole옵션으로 작업을 cpu 집약적으로 처리할 수있다
4. 작업 큐에서 대기중인 작업은 비동기식으로 (앞 작업과 상관없이) 다른 서비스 워커에 의해 실행된다.
