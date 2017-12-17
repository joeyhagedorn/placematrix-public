from application import db
from application.models import Placement, Representation, User

db.create_all()

print("DB created.")
