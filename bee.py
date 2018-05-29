import os
import click
from flask_migrate import Migrate
from app import create_app, db
from app.models import Admin, School, Tcode, Course, Teacher, Student, Ask, Answer, Topicimage, Feedback, SchoolStudent

app = create_app(os.getenv('FLASK_ENV') or 'default')
migrate = Migrate(app, db)
 
print('oooooooooooooooooooooooooooo', os.getenv('FLASK_ENV'))

@app.shell_context_processor
def make_shell_context():
    return dict(
        db=db,
        Admin=Admin,
        School=School,
        Tcode=Tcode,
        SchoolStudent=SchoolStudent,
        Teacher=Teacher,
        Student=Student,
        Course=Course,
        Ask=Ask,
        Answer=Answer,
        Topicimage=Topicimage,
        Feedback=Feedback
    )


@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@app.cli.command()
@click.option('--name', prompt='username')
@click.password_option()
def create_admin(name, password):
    """设置平台管理员。"""
    if Admin.query.filter_by(name=name).first():
        click.echo('用户已经存在，请重新设置。')
        return

    admin = Admin(name=name, password=password)
    db.session.add(admin)
    db.session.commit()
    click.echo('管理员 ' + name + ' 设置成功')
