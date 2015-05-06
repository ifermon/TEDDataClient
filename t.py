'''
	Every minute has a temperature, humidity, datetime, light level, 
			power start, power end
	Corresponds to line in google sheets
	

'''
import pytz
import ephem
import time
import datetime
import requests

eastern = pytz.timezone('US/Eastern')
utc = pytz.timezone('UTC')

PWR = -101
HUMID = -102
TEMP = -103
LIGHT = -104
CLASSIFICATIONS = [PWR, HUMID, TEMP, LIGHT]

class WrongDayException(Exception):
	pass
class InvalidReadingTypeException(Exception):
	pass

		
'''
'''
class DayReading(object):

	'''
		Initialize with just a timestamp, it will build the rest
	'''
	def __init__(self, ts):
		dt = datetime.datetime.fromtimestamp(ts)
		self.dt = datetime.datetime(dt.year, dt.month, dt.day, tzinfo=eastern)
		
		# Setup some of the basics, yes it's redundant
		self.day = self.dt.day
		self.month = self.dt.month
		self.year = self.dt.year
		self.week_number = self.dt.isocalendar()[1]
		self.beg_ts = time.mktime(self.dt.timetuple())
		self.end_ts = self.beg_ts + 86400 #secs in a day

		# Now some more complicated stuff, get the sunset and sunrise,
		# both as datetimes and timestamps
		self.sunset = ephem.city('New York').next_setting(ephem.Sun(),
				start=self.dt).datetime().replace(
				tzinfo=utc).astimezone(eastern)
		self.sunset_ts = time.mktime(self.sunset.timetuple())
		self.sunrise = ephem.city('New York').next_rising(ephem.Sun(),
				start=self.dt).datetime().replace(
				tzinfo=utc).astimezone(eastern)
		self.sunrise_ts = time.mktime(self.sunrise.timetuple())

		# An array for each type of reading, one per hour
		hourly_values = dict.fromkeys(CLASSIFICATIONS)
		for classification in hourly_values.iterkeys():
			hourly_values[classification] = []
			hourly_values[classification][:] = [[0,0,False] for 
					hour_index in range(24)]

		# Some daily readings
		daily_values = dict.fromkeys(CLASSIFICATIONS)
		for classfication in daily_values.iterkeys():
			daily_values[classification] = [0, None]
		return

	'''
		This function takes a number (reading), timestamp, and type
		Types must be supported and are listed in top of file
		TEMP, HUMID, LIGHT, PWR
	'''
	def add_value(self, ts, reading, classification):
		# Check to see if it's the right day
		if ts < self.beg_ts or ts > self.end_ts:
			raise WrongDayException

		# Validate that we it's a valid classification
		if classification not in CLASSIFICATIONS:
			raise InvalidReadingTypeException

		# Ensure reading is positive
		reading = abs(reading)

		# Log the reading
		dt = datetime.datetime.fromtimestamp(ts)
		self.log_values(classification, dt, 1, reading)

		# First update the daily values, then the hourly values
		# 60 secs in a minute, 60 mins in an hour
		# TED gives total power at time intervals - total power to date
		# so to calc power over an hour you need to subtract 
		# last value - first value. For the other readings you need to 
		# average. So two logic streams, one for power and one for all else
		seconds_since_day_beginning = ts - self.beg_ts
		minute_index = int(seconds_since_day_beginning/60)
		hour_index = int(minute_index/60)
		if classification == PWR:
			beg, end = daily_values[classification]
			if beg == 0:
				beg = reading
			else:
				end = reading
			daily_values[classification] = [beg, end]
			
			# Now the hourly
			beg, end, logged = hourly_values[classification][hour_index]
			if beg == 0:
				beg = reading
			else:
				end = reading
			hourly_values[classification][hour_index] = [beg, end, logged]
				
		# We only want to look at light levels between sunrise and
		# sunset, so only collect values if it's not light, OR if it's daytime
		elif classification != LIGHT or (
				ts > self.sunrise_ts and ts < self.sunset_ts):
			count, avg = daily_values[classification]
			avg = (count * avg + reading) / (count + 1)
			count += 1
			daily_values[classification] = [count, avg]

			# now the hourly
			count, avg, logged = hourly_values[classification][hour_index]
			avg = (count * avg + reading) / (count + 1)
			count += 1
			hourly_values[classification] = [count, avg, logged]

		# Now check to see if we have logged all the past hourly values
		for h in range(0, hour_index - 1):
			count, avg, logged = hourly_values[classification][h]
			if logged == False:
				dt = datetime.datetime(self.year, self.month, self.day,
						h, 0, 0, tzinfo=eastern)
				self.log_values(classification, dt, count, avg)
				hourly_values[classification][h] = [count, avg, True]
		return

	'''
		Log values
	'''
	def log_values(self, classification, dt, count, avg):
		url = 'http://192.168.0.5:5000/post_logging'
		payload = {'type':classification, 'datetime':dt, 'count':count, 
				'average':avg}
		r = requests.post(url, data=payload)
		print r.text
		return
			

dr = DayReading(time.time())

print dr.day
print dr.month
print dr.year
print dr.week_number
print dr.beg_ts
print dr.end_ts
print dr.sunrise
print dr.sunset
dr.log_values(PWR, datetime.datetime.now(), 1, 23)
