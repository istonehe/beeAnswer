import os
from flask_migrate import Migrate, MigrateCommand
from app import create_app, db
from app.models import School, Course, Teacher, Student, Ask, Answer, Topicimage, Feedback

app = create_app(os.getenv('FLASK_ENV') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, School=School, Teacher=Teacher, Student=Student, Course=Course, Ask=Ask, Answer=Answer, Topicimage=Topicimage, Feedback=Feedback)

@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
