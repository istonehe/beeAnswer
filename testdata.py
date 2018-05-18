from app import db
from app.models import School, Teacher, Student, Course


def somedata():
    school01 = School(name='这是学校01', admin=13700000001)
    school02 = School(name='这是学校02', admin=13700000004)
    school03 = School(name='这是学校03', admin=13700000007)

    teacher01 = Teacher(telephone=13700000001, password='123456')
    teacher02 = Teacher(telephone=13700000002, password='123456')
    teacher03 = Teacher(telephone=13700000003, password='123456')
    teacher04 = Teacher(telephone=13700000004, password='123456')
    teacher05 = Teacher(telephone=13700000005, password='123456')
    teacher06 = Teacher(telephone=13700000006, password='123456')
    teacher07 = Teacher(telephone=13700000007, password='123456')
    teacher08 = Teacher(telephone=13700000008, password='123456')
    teacher09 = Teacher(telephone=13700000009, password='123456')

    teacher01.schools.append(school01)
    teacher01.schools.append(school02)

    teacher02.schools.append(school01)
    teacher02.schools.append(school02)

    teacher03.schools.append(school02)
    teacher03.schools.append(school03)

    teacher04.schools.append(school02)
    teacher04.schools.append(school03)

    teacher05.schools.append(school01)
    teacher05.schools.append(school02)

    teacher06.schools.append(school01)
    teacher07.schools.append(school03)
    teacher08.schools.append(school03)
    teacher09.schools.append(school01)

    student01 = Student(telephone=15900000001, password='123456')
    student02 = Student(telephone=15900000002, password='123456')
    student03 = Student(telephone=15900000003, password='123456')
    student04 = Student(telephone=15900000004, password='123456')
    student05 = Student(telephone=15900000005, password='123456')
    student06 = Student(telephone=15900000006, password='123456')
    student07 = Student(telephone=15900000007, password='123456')
    student08 = Student(telephone=15900000008, password='123456')
    student09 = Student(telephone=15900000009, password='123456')
    student10 = Student(telephone=15900000010, password='123456')
    student11 = Student(telephone=15900000011, password='123456')
    student12 = Student(telephone=15900000012, password='123456')
    student13 = Student(telephone=15900000013, password='123456')
    student14 = Student(telephone=15900000014, password='123456')
    student15 = Student(telephone=15900000015, password='123456')

    db.session.add_all([
        school01,
        school02,
        school03,
        teacher01,
        teacher02,
        teacher03,
        teacher04,
        teacher05,
        teacher06,
        teacher07,
        teacher08,
        teacher09,
        student01,
        student02,
        student03,
        student04,
        student05,
        student06,
        student07,
        student08,
        student09,
        student10,
        student11,
        student12,
        student13,
        student14,
        student15
    ])

    db.session.commit()

    course01 = Course(course_name='课程01', school_id=school01.id)
    course02 = Course(course_name='课程02', school_id=school02.id)
    course03 = Course(course_name='课程03', school_id=school03.id)

    db.session.add_all([course01, course02, course03])
    db.session.commit()

    student01.join_school(school01.id)
    student02.join_school(school01.id)
    student03.join_school(school01.id)
    student04.join_school(school01.id)
    student05.join_school(school01.id)
    student06.join_school(school02.id)
    student07.join_school(school02.id)
    student08.join_school(school02.id)
    student09.join_school(school02.id)
    student10.join_school(school02.id)
    student11.join_school(school03.id)
    student12.join_school(school03.id)
    student13.join_school(school03.id)
    student14.join_school(school03.id)
    student15.join_school(school03.id)
