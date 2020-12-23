// transfer.js
const transfer = (function(){

	const exports = {};
    const element = {};
    const data = {
        sender_account :'',
        receiver_account :'',
        sended_label :'',
        received_label :'',
        remittance : 0,
        fee : 0,
    };
    
	const setElements = function(){
		element.csrftoken = $('input[name="csrfmiddlewaretoken"]');
        
        element.form = document.querySelector('#account_form');
		element.inputSenderAccount = $('#sender_account');
		element.inputReceiverAccount = $('#receiver_account');
		element.inputSendedLabel = $('#sended_label');
		element.inputReceivedLabel = $('#received_label');
		element.inputRemittance = $('#remittance');
        element.inputFee = $('#fee');
        
		element.viewSenderAccount = $('#view_sender_account');
		element.viewReceiverAccount = $('#view_receiver_account');
		element.viewSendedLabel = $('#view_sended_label');
		element.viewReceivedLabel = $('#view_received_label');
		element.viewRemittance = $('#view_remittance');
        element.viewFee = $('#view_fee');

	}
	const addEvent = function(){
        formBinder(element.form, beforeSave);

        element.inputSenderAccount.change(function() {
            getAmount($(this).val());
        });

        $('#exampleModal').on('shown.bs.modal', function () {
            console.log('modal')
        })
    }

	const ajaxSetup = function (){
		$.ajaxSetup({
			beforeSend:function(xhr, settings){
                // show gif here, eg:
                xhr.setRequestHeader("X-CSRFToken", element.csrftoken.val());
				$("#wait").css("display", "block");
			},
			complete:function(){
				// hide gif here, eg:
				$("#wait").css("display", "none");
			}
		});
	}

	const formBinder = function (form, callback) {
		if(!form) return;
		form.addEventListener('submit', function(event) {
			event.preventDefault();
			event.stopPropagation();
			if (form.checkValidity() === false) {
				form.classList.add('was-validated');
				form.querySelectorAll(':invalid')[0].focus();
			}
			else{
				callback();
			}
		});
    }
    
    // 계좌이체 데이터 저장
	const makeData = function () {
        data.sender_account = element.inputSenderAccount.val();
        data.receiver_account = element.inputReceiverAccount.val();
        data.sended_label = element.inputSendedLabel.val();
        data.received_label = element.inputReceivedLabel.val();
        data.remittance = element.inputRemittance.val();
        data.fee = element.inputFee.val();
    }

    // 계좌이체 데이터 세팅후 컴펌창 띄우기
	const beforeSave = function () {
        //수수료 계산
        calcFee(function(){
            //전역 data 세팅
            makeData(); 
            // 모달필드에 뷰값 채움
            setModalView();
            //컨펌창 모달 띄우기
            $('#exampleModal').modal('show');
        });
    }

	const setModalView = function () {
        element.viewSenderAccount.text(data.sender_account);
		element.viewReceiverAccount.text(data.receiver_account);
		element.viewSendedLabel.text(data.sended_label);
		element.viewReceivedLabel.text(data.received_label);
		element.viewRemittance.text(data.remittance);
        element.viewFee.text(data.fee);
    }

    // 계좌이체 실행
	const save = function () {
        console.log('save call!');
        //요청
        $.ajax({
            method:'POST',
            url: '/bank/trasfer/',
            dataType: 'json',
            data: JSON.stringify(data),
            contentType:'application/json; charset=utf-8',
        }).done(function(response) {
            console.log(response);
          
        }).fail(function (error) {
            console.log(JSON.stringify(error));
        });
    }

    // 유효한 계좌인지 검사
    const validateAccount = function () {
        //상대계좌
        receive_account = element.inputReceiverAccount.val();
        if(!receive_account){
            console.log("계좌번호입력");
            return;
        }
        
        const data={
            account_id: receive_account
        };
        //요청
        $.ajax({
            method:'POST',
			url: '/bank/validateAccount/',
			data: JSON.stringify(data),
			contentType:'application/json; charset=utf-8',
			dataType: 'json',
		}).done(function(response) {
            console.log(response);
            if(response.isValidAccount == true){
                $('.receiver-account-info').html("<p>"+"올바른 계좌입니다. 소유자: "+response.owner_name+"</p>")
            }else{
                $('.receiver-account-info').html("<p>"+"없는 계좌입니다. </p>")
            }
     
		}).fail(function (error) {
			console.log(JSON.stringify(error));
		});
    }
    // 계좌에 얼마들었는지 조회
    const getAmount = function(sender_account){
          //상대계좌
        //   sender_account = element.inputSenderAccount.val();
          console.log('sender_account: '+sender_account);
          if(!sender_account){
              console.log("내계좌를 선택하세요");
              return;
          }
          const account_id = sender_account
          //요청
          $.ajax({
              method:'GET',
              url: '/bank/amount/'+account_id,
              dataType: 'json',
          }).done(function(response) {
              console.log(response);
      
          }).fail(function (error) {
              console.log(JSON.stringify(error));
          });
    }

    // 수수료 계산
    const calcFee = function(callback){
        
        //내 계좌와 상대계좌를
          const param_data={
            sender_account : element.inputSenderAccount.val(),
            receiver_account : element.inputReceiverAccount.val(),
          };
          $.ajax({
              method:'GET',
              url: '/bank/fee/',
              dataType: 'json',
              data: param_data
          }).done(function(response) {
            console.log(response)
            fee = response.fee
            data.fee=fee;
            element.viewFee.html(fee);
            callback();
          }).fail(function (error) {
             console.log('수수료 계산 실패',error);
          });
    }


    /*exports*/

	exports.init = function(){
		setElements();
		addEvent();
		ajaxSetup();
	};
	exports.validateAccount = function(){
		validateAccount();
	};
	exports.getAmount = function(){
		getAmount();
	};
	exports.beforeSave = function(){
		beforeSave();
	};
	exports.save = function(){
		save();
	};


	return exports;
})();

transfer.init();