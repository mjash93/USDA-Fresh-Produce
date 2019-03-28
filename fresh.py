import requests
import time
import numpy as np
import pandas as pd

def read_key(keyfile):
	"""
		reads the content of a file (api key) into a variable to use for further usage
	"""
	with open(keyfile) as f:
		return f.readline().strip("\n")

def food_search(key, food, ds):
	"""
		searches the given url api and returns a json onject as a list. 

		Inputs:
			key: api key
			food: food name to look up
			df: data source, Branded, standard, default
		Output:
			list containing the result query
	"""
	try:
		response = requests.get('https://api.nal.usda.gov/ndb/search', params={
			'api_key': key,
			'q': food,
			'ds': ds,
			})
		response.raise_for_status()
		return response.json()['list']['item']
	except KeyError:
		return []

def match_food(key, series):
	"""
		match_food iterates through the series containing names of food and
		searches for them, adding ',raw' at the end to ensure that we obtain
		the raw product. All our products are unbranded as well, so we pass 'SR'
		to food_search as well to ensure that it doesn't search for branded products.

		observation has told us that 
	"""
	food_dict = {}
	for food_item in series:
		search_term = food_item + ', raw'
		result = food_search(key, search_term, 'Standard Reference')
		if len(result) != 0:
			food_dict[food_item] = [result[0]['ndbno']] 
		time.sleep(0.1)
	return food_dict

def ndb_report(key, ndb_num):
	"""
		ndb_report takes API key as well as ndb number as inputs and returns the list of 
		nutrients in the report. 
	"""
	try:
		response = requests.get('https://api.nal.usda.gov/ndb/V2/reports',params={
			'api_key': key,
			'ndbno': ndb_num
			})
		response.raise_for_status()
		return response.json()['foods'][0]['food']['nutrients']
	except KeyError:
		return []

def nutrient_counter(key, df):
	"""
		returns the dataframe with a nutrient count column that details 
		how many nutrients a particular produce product has. To filter our search
		we compute each nutrient value as a percentage and then round to the .1%. Nutrients
		that make up less than .1% of the whole are assumed 0. 
	"""
	nutrient_count = []

	for x in df['ndb number']:
		nutrient_report = ndb_report(key, x)
		nut_tot_value = []

		for y in nutrient_report:
			y['value'] = float(y['value'])
			nut_tot_value.append(y['value'])

		nut_tot_value = np.sum(nut_tot_value)
		# take total amount of nutrients and convert to a percentage, rounded to .1%
		for y in nutrient_report:
			y['value'] = round((100*y['value'] / nut_tot_value),1)
			if y['value'] == 0.0:
				nutrient_report.remove(y)

		nutrient_count.append(len(nutrient_report))

	# merge nutrient count with existing data frame and return  
	df_temp = pd.DataFrame({'food': df['food'], 'nutrient count': nutrient_count})
	df = df.set_index('food')
	df_temp = df_temp.set_index('food')
	df = df.merge(df_temp, left_index=True, right_index=True)
	return df.reset_index()
