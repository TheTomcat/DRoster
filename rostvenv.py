from app import app

from app.models import *
from app.models import _generate_functions

@app.shell_context_processor
def make_shell_context():
	return {'db':db,
			'generate_filler':generate_filler,
			'generate_functions':_generate_functions,
			'User':User,
			'Department':Department,
			'Pool':Pool,
			'Role':Role,
			'Shift':Shift,
			'Employee':Employee,
			'Roster':Roster,
			'RosterVersion':RosterVersion,
			'DefaultCover':DefaultCover,
			'Allocation':Allocation,
			'Colour':Colour,
			'Function':Function,
			'Policy':Policy,
			'Group':Group}