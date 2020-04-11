MON = 2**0
TUE = 2**1
WED = 2**2
THU = 2**3
FRI = 2**4
SAT = 2**5
SUN = 2**6
WEEKDAY = MON + TUE + WED + THU + FRI
WEEKEND = SAT + SUN
DAYSET = [MON, TUE, WED, THU, FRI, SAT, SUN]
ALL = WEEKEND + WEEKDAY

def on_day(test, days):
	if isinstance(days,int):
		return test & days == days
	elif isinstance(days,(dt.date, dt.datetime)):
		return test & 2**days.weekday() == 2**days.weekday()

def combine(pattern, days):
	return pattern | days

def remove(pattern, days):
	return pattern & ~days

def get_date(d):
	return dt.date(year=d.year, month=d.month, day=d.day)
def get_time(t):
	return dt.time(hour=t.hour, minute=t.minute, second=t.second)

def add_date_time(date, time):
	return dt.datetime(year=date.year,
					   month=date.month,
					   day=date.day,
					   hour=time.hour,
					   minute=time.minute,
					   second=time.second)

def daterange(start_date, end_date, include_last =False):
	offset = 1 if include_last else 0
	for n in range(int ((end_date - start_date).days + offset)):
		yield start_date + dt.timedelta(n)

def human_readable(pattern):
    days = ["Monday","Tuesday","Wednesday","Thursday",
                    "Friday", "Saturday", "Sunday"]
    output = []
    for name, day in zip(days,DAYSET):
        if on_day(pattern, day):
            output.append(name)
    return ', '.join(output)
