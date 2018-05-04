import os
from flask_migrate import Migrate, MigrateCommand
from app import create_app, db
from app.models import School, Course, Teacher, Student, Ask, Answer, Topicimage, Feedback

app = create_app(os.getenv('FLASK_ENV') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, School=School, Course=Course, Teacher=Teacher, Student=Student, Ask=Ask, Answer=Answer, Topicimage=Topicimage, Feedback=Feedback)
