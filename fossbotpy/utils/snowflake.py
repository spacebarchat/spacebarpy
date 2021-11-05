import time, datetime

class Snowflake:
	@staticmethod
	def snowflake_to_unixts(self,snowflake):
		return (int(float(snowflake))/4194304+1420070400000)/1000

	@staticmethod
	def unixts_to_snowflake(self,unixts):
		return str((int(float(unixts))*1000-1420070400000)*4194304)

	@staticmethod
	def get_snowflake(date='now'):
		if date == 'now':
			date = datetime.datetime.now()
		unixts = time.mktime(date.timetuple())
		return str((int(unixts)*1000-1420070400000)*4194304)