import os
from flask_migrate import Migrate, MigrateCommand
from app import create_app, db
from app.models import School

app = create_app(os.getenv('FLASK_ENV') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, School=School)
