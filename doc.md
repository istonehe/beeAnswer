平台管理方
------
******

### 获取token
curl -u user:password -i -X GET /v1/admin/token

### 创建学校
v1/admin/school   post    
name  
intro (可选)  
admin_phone  

    curl -u user:password -i -X POST -H "Content-Type: application/json" -d '{"name":"教学机构名称","intro":"这是一个教学机构","admin_phone":"13720331113"}' /v1/admin/schools

    http --json --auth user:password POST /v1/admin/schools name=教学机构名称 intro=教学机构介绍 admin_phone=13700001234

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
v1/admin/teacher   get  
school_id (可选)  
page   第几页  （默认1）  
per_page   每页多少条  （默认20）

    curl -u user:password -i -X GET -H "Content-Type: application/json" /v1/admin/teacher\?school_id\=9\&page\=1\&per_page\=3


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



教学机构方
------
******

### 教师注册
v1/teacher/register  
telephone  
nickname  
tcode  

    curl -i -X POST -H "Content-Type: application/json" -d '{"telephone":"13712341234","nickname":"教师昵称","tcode":"7IBfG1dd","password":"123456"}' /v1/school/register

    http --json POST 127.0.0.1:5000/v1/school/register telephone=13700000001 password=123456 nickname=huadou tcode=ZYSjkccO25UV


### token获取
curl -u user:password -i -X GET /v1/teacher/token


### 教师加入学校
v1/school/bind

    http --json --auth teacher:password PUT /v1/school/bind tcode=<str>


### 管理课程
v1/school/course

    http --json --auth teacher:password PUT /v1/school/course school_id=<int> course_name=<str> course_intro=<str> nomal_times=<int> vip_times=<int>


### 查看本校详情
v1/school/<int:s_id>

    http --json --auth teacher:password GET :5000/v1/school/<int>


### 查看老师详情
v1/school/<int:s_id>/<int:t_id>

    http --json --auth teacher:password GET :5000/v1/school/<int>/<int>