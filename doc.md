平台管理方
------
******

### 获取token
curl -u user:password -i -X GET /v1/admin/token  

    http --json --auth user:password GET :5000/v1/admin/token

### 创建学校
v1/admin/school   post    
name  
intro (可选)  
admin_phone  

    curl -u user:password -i -X POST -H "Content-Type: application/json" -d '{"name":"教学机构名称","intro":"这是一个教学机构","admin_phone":"13720331113"}' /v1/admin/schools

    http --json --auth user:password POST :5000/v1/admin/schools name=教学机构名称 intro=教学机构介绍 admin_phone=13700001234

### 查询学校列表
v1/admin/school   get  
page   第几页  （默认1）  
per_page   每页多少条  （默认10）

    curl -u user:password -i -X GET -H "Content-Type: application/json" /v1/admin/schools\?page\=2\&per_page\=4

### 查询学校
v1/admin/school/id   get  

    curl -u user:password -i -X GET -H "Content-Type: application/json" /v1/admin/school/9

### 搜索学校
/v1/admin/schools/search?name=  
page   第几页  （默认1）  
per_page   每页多少条  （默认10）

    curl -u user:password -i -X GET -H "Content-Type: application/json" /v1/admin/school/search?name=机构名称&page=2&per_page=4

    httpie
    http --json --auth user:password GET /v1/admin/school/search name=机构名称 page=2 per_page=4  


### 修改学校
v1/admin/school/id   put  
name  
intro (可选)  
admin_phone  

    curl -u user:password -i -X PUT -H "Content-Type: application/json" -d '{"name":"修改的机构名称","intro":"修改的机构内容","admin_phone":"13700000000"}' /v1/admin/school/15


### 删除学校
v1/admin/school/id   delete  

    curl -u user:password -i -X DELETE /v1/admin/school/16


### 查询教师列表
v1/admin/teachers   get  
school_id (可选)  
page   第几页  （默认1）  
per_page   每页多少条  （默认20）

    http --json --auth user:password GET :5000/v1/admin/teachers school_id=1 page=1 per_page=2


### 查询教师
v1/admin/teacher/id   get

    curl -u user:password -i -X GET -H "Content-Type: application/json" /v1/admin/teacher/1

### 修改教师
v1/admin/teacher/id   put  
nickname  
rename  
intro  
imgurl  
telephone  
gender  

    curl -u user:password -i -X PUT -H "Content-Type: application/json" -d '{"nickname":"jack","rename":"JACK","telephone":"13200000001"}' /v1/admin/teacher/15 


### 删除教师
/v1/admin/teacher/<id> delete  

    http --json --auth user:password DELETE /v1/admin/teacher/<id>


### 搜索教师
/v1/admin/teachers/search  get  

    http --json --auth user:password GET /v1/admin/teacher/search telephone=13711111111


### 解除教师与学校关系
/v1/admin/dismiss   delete  

    http --json --auth user:password DELETE /v1/admin/dismiss teacher_id=<id> school_id=<id>


### 学生列表
v1/admin/students  get  
school_id  不填默认列出所有学生 
pape  
per_page  

    http --json --auth user:password GET :5000/v1/admin/students school_id=2  pape=1 per_page=2


### 某学校学生详情
v1/admin/<int:school_id>/student/<int:student_id>  get  

    http --json --auth user:password GET :5000/v1/admin/1/student/2


### 学生详情
v1/admin/student/<int:id>  get  

    http --json --auth user:password GET :5000/v1/admin/student/2


### 修改学生资料
v1/admin/student/<int:id>  put  

    http --json --auth user:password PUT :5000/v1/admin/student/2 telephone=15900000002 nickname=Noah rename=realname password=123456


### 搜索学生
/v1/admin/student/search GET 
telephone

    http --json --auth user:password GET :5000/v1/admin/student/search telephone=15900000001




教学机构方
------
******

### 教师注册
v1/public/teacher/register  
telephone  
nickname  
tcode  
password  
inputvalue
uuid

    http --json POST :5000/v1/public/teacher/register telephone=13700000001 password=123456 nickname=huadou tcode=ZYSjkccO25UV uuid= inputvalue=


### token获取
/v1/school/token  

    http --json --auth user:password GET :5000/v1/school/token


### 教师加入学校
v1/school/bind
tcode  

    http --json --auth teacher:password PUT /v1/school/bind tcode=<str>


### 管理课程
v1/school/course
school_id=<int>  
course_name=<str>  
course_intro=<str>  
nomal_times=<int>  
vip_times=<int>

    http --json --auth teacher:password PUT /v1/school/course school_id=<int> course_name=<str> course_intro=<str> nomal_times=<int> vip_times=<int>


### 查看本校详情
v1/school/<int:s_id>

    http --json --auth teacher:password GET :5000/v1/school/<int>


### 查看老师详情
v1/school/<int:s_id>/teacher/<int:t_id>  

    http --json --auth teacher:password GET :5000/v1/school/<int>/teacher/<int>


### 学校移除老师
v1/school/dismiss  
eacher_id  
school_id  

    http --json --auth 13700000021:123456 DELETE :5000/v1/school/dismiss teacher_id=1 school_id=1


### 老师退出学校
v1/school/teacher/dismiss  
school_id  

    http --json --auth teacher:password DELETE :5000/v1/school/teacher/dismiss school_id=1


### 查看学生列表
v1/<int:school_id>/students get  
school_id  
page   第几页  （默认1） 
per_page   每页多少条  （默认20）   

    http --json --auth teacher:password GET :5000/v1/school/1/students



### 查看学生详情
v1/<int:school_id>/student/<int:student_id>  get  

    http --json --auth teacher:password GET :5000/v1/school/1/student/1



### 设置学生会员状态
v1/<int:school_id>/student/<int:student_id>  put  
vip_times  
nomal_times  
vip_expire  

    http --json --auth teacher:password PUT :5000/v1/school/1/student/1 vip_times=50 nomal_times=5 vip_expire=2018-05-19T07:47:06.000Z


### 获取学生问题列表
v1/school/student/asks  
school_id  
student_id  默认为0（表示全部）
answered  0  1  2  

    http --auth 13700000001:123456 GET :5000/v1/school/student/asks school_id=1 student_id=1


### 获取学生问题详情
v1/school/student/ask/<id>  

    http --auth 13700000001:123456 GET:5000/v1/school/student/ask/1


### 回答问题
v1/school/student/ask/<ask_id>/answers  
answer_text  
voice_url  
voice_duration  
img_ids  

    http --json --auth 13700000001:123456 POST :5000/v1/school/student/ask/1/answers answer_text=回答内容001 img_ids=2,3


### 查看回答列表
v1/school/student/<ask_id>/answers

    http --json --auth 13700000001:123456 GET :5000/v1/school/student/ask/1/answers


### 查看教师个人详情
v1/school/teacher/

    http --json --auth 13700000001:123456 :5000/v1/school/teacher/10



学生方
------

### 学生注册
v1/public/student/register  
telephone  
nickname  
password  

    http --json POST :5000/v1/public/student/register telephone=15900000001 nickname=huadou password=123456


### 获取token
v1/student/token

    http --json --auth user:password Get :5000/v1/student/token


### 提交问题
v1/student/asks  post  
school_id  
ask_text  
img_ids  

    http --json --auth 15900000001:123456 POST :5000/v1/student/asks school_id=1 ask_text=问题内容 img_ids=1,2,3


### 获取问题列表
v1/student/asks  
school_id  
page  
per_page  
answered  0  1  2  

    http --json --auth 15900000001:123456 GET :5000/v1/student/asks school_id=1


### 获取问题详情
v1/student/ask/<id>  get  

    http --auth 15900000001:123456 GET :5000/v1/student/ask/2


### 删除问题
v1/student/ask/<id>  delete  

    http --auth 15900000002:123456 delete :5000/v1/student/ask/49


### 增加答案评论
v1/student/ask/<id>  post    
answer_text  
voice_url  
voice_duration  
img_ids  

    http --json --auth 15900000002:123456 POST :5000/v1/student/ask/1/answers answer_text=学生回复内容 img_ids=1,3
    
    
### 查看答案列表
v1/student/ask/<ask_id>/answers  

    http --json --auth 15900000001:123456 GET :5000/v1/student/ask/1/answers


### 删除答案评论
v1/student/ask/answers/<id>  DELETE  

    http --json --auth 15900000001:123456 DELETE :5000/v1/student/ask/answers/5


### 加入学校
v1/student/joinschool/<school_id> post

    http --json --auth 15900000001:123456 post :5000/v1/student/joinschool/3


### 答案评分反馈
v1/student/ask/1/answergrate  put
grate 0 1 2  default=0未选  1听懂  2没听懂

    http --json --auth 15900000001:123456 PUT :5000/v1/student/ask/1/answergrate grate=0


### 答案评分值
v1/student/ask/1/answergrate  get  

    http --json --auth 15900000001:123456 GET :5000/v1/student/ask/1/answergrate


### 获取个人信息
v1/student/<student_id>  get  
school_id  

    http --json --auth 15900000001:123456 GET :5000/v1/student/1


Public
------

### 上传文件
v1/public/uploads 

    http -f --auth user:password :5000/v1/public/uploads file@bee.jpg


### 小程序login鉴权  
v1/public/wxstlogin post  
school_id  
code  

    http --json POST :5000/v1/public/wxstlogin school_id=7 code=0010Rkok2inZ8F9847394k20Rko9


### 获取学校信息  
v1/public/school/<school_id>

    http --json GET :5000/v1/public/school/1


### 获取验证图片

http GET :5000/v1/public/imgcode


### 短信发送

http --json POST :5000/v1/public/sendsms uuid= phone_numbers= inputvalue=

------
bug  

------
images one to many is wrong