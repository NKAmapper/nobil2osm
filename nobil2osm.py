#!/usr/bin/env python3
# -*- coding: utf8

# nobil2osm
# Converts nobil api to osm format for import/update.
# Usage: nobil2.osm
# The generated OSM file is saved to 'nobil.osm'
# New capacity types etc will produce warnings to console.
# Contact info, authentication and payment info have been removed from code because apps and RFID are mostly used.


import json
import html
import sys
import re
import urllib.request


version = "1.0.1"


# Capacities codes in kW

capacities = {
	'7':  3.6, # 3,6 kW . 230V 1-phase max 16A
	'16': 6.3, # 230V 3-phase max 16A
	'8':  7.4, # 7.4 kW - 230V 1-phase max 32A
	'10': 11,  # 11 kW - 400V 3-phase max 16A
	'17': 13,  # 230V 3-phase max 32A
	'19': 20,  # 20 KW - 500VDC max 50A
	'11': 22,  # 22 kW - 400 3-phase max 32A
	'18': 25,  # 230V 3-phase max 63A
	'12': 43,  # 43 kW - 400 3-phase max 63A	
	'13': 50,  # 50 kW - 500VDC max 100A
	'20': 50,  # Less then 100 kW + 43 kW - 500VDC max 200A + 400V 3-phase max 63A
	'21': 50,  # Less then 100 kW + 22 kW - 500VDC max 50A + 400V 3-phase max 32A
	'28': 50,  # 50 kW - 400VDC max 125A
	'29': 75,  # 75 kW DC
	'23': 100, # 100 kW - 500VDC max 200A
	'22': 135, # 135 kW - 480 VDC max 270A
	'24': 150, # 150 kW DC
	'30': 225, # 225 kW DC
	'31': 250, # 250 kW DC
	'32': 200, # 200 kW DC
	'33': 300, # 300 kW DC
	'25': 350, # 350 kW DC
	'26': 350, # 350 bar
	'0':  0}   # Unspecified

# Brand names for certain national or regional networks
# Part 1 of tuple is translated into part 2 name, to allow for translations.

network_list = [
	# Norway
	('Mer', 'Mer'),
#	('Grønn kontakt', 'Mer'),  # Rebranded to Mer
	('Lyse/Eviny', 'Lyse/Eviny'),
	('Lyse/BKK', 'Lyse/Eviny'),  # BKK rebranded to Eviny
	('BKK / Lyse', 'Lyse/Eviny'),  # Ditto
	('Eviny', 'Eviny'),
	('BKK', 'Eviny'),  # Rebranded to Eviny
	('Charge365', 'Charge365'),
	('Kople', 'Kople'),

	# Sweden
	('Bee', 'Bee'),
	('E.ON', 'E.ON'),
	('Vattenfall', 'InCharge'),
	('Göteborg Energi', 'Göteborg Energi'),
	('OKQ8', 'OKQ8'),

	# International
	('Tesla', 'Tesla'),
	('Recharge', 'Recharge'),
	('Circle K', 'Circle K'),
	('Fortum','Fortum'),
	('Ionity', 'Ionity') ]


# Output message to console

def message (text):

	sys.stderr.write(text)
	sys.stderr.flush()


# Produce a tag for OSM file

def make_osm_line(key,value):
	if value != "":
		value = html.unescape(value)
		encoded_value = html.escape(value).strip()
		file.write ('    <tag k="' + key + '" v="' + encoded_value + '" />\n')


# Return capacity/wattage of socket

def find_capacity(capacity_id):

	if capacity_id in capacity:
		return capacity[capacity_id]
	else:
		message('Unknown capacity_id: "%s"\n' % capacity_id)
		return 0


# Main program

if __name__ == '__main__':


	message ("\nnobil2osm\n")

	# Load all charging stations from Nobil

	message ("Loading charging stations from Nobil...\n")
	link = "https://nobil.no/api/server/datadump.php?apikey=54f7f3c569d6f583f7ae8294966ddb68&format=json"
	request = urllib.request.Request(link)
	file = urllib.request.urlopen(request)
	nobil_data = json.load(file)
	file.close()

	# Produce OSM file header

	message ("Generating OSM file...\n")

	filename = "nobil.osm"
	file = open(filename, "w")

	file.write ('<?xml version="1.0" encoding="UTF-8"?>\n')
	file.write ('<osm version="0.6" generator="nobil2osm v%s" upload="false">\n' % version)

	count = 0
	network_count = {}
	node_id = -1000


	# Loop all charging stations and produce OSM tags

	for station in nobil_data['chargerstations']:

		node_id -= 1
		count += 1

		position = eval(station['csmd']['Position'])

		file.write('  <node id="' + str(node_id) + '" lat="' + str(position[0]) + '" lon="' + str(position[1]) + '">\n')

#		make_osm_line("amenity","charging_station")  # Moved to end due to hydrogen
		make_osm_line("ref:nobil",str(station['csmd']['id']))
#		make_osm_line("source","nobil.no")

		make_osm_line("ADDRESS",station['csmd']['Street'] + " " + station['csmd']['House_number'] + ", " +\
								station['csmd']['Zipcode'] + " " + station['csmd']['City'])

#		make_osm_line("MUNICIPALITY_ID",station['csmd']['Municipality_ID'])
#		make_osm_line("MUNICIPALITY",station['csmd']['Municipality'])
#		make_osm_line("COUNTY_ID",station['csmd']['County_ID'])
		make_osm_line("COUNTY",station['csmd']['County'])
		make_osm_line("COUNTRY",station['csmd']['Land_code'])

		make_osm_line("CREATED",station['csmd']['Created'][:10])
		make_osm_line("UPDATED",station['csmd']['Updated'][:10])

#		make_osm_line("CHARGING_POINTS",str(station['csmd']['Number_charging_points']))

		# Produce description tag

		make_osm_line("DESCRIPTION", station['csmd']['Description_of_location'])
		make_osm_line("COMMENT", station['csmd']['User_comment'])

		'''
		# Removed the following section to simplify tagging

		if station['csmd']['Description_of_location'] != '':
			description = station['csmd']['Description_of_location']
			if station['csmd']['User_comment'] != '':
				if not(description[len(description)-1] in ['.','!','?']):
					description = description + "."
				description = description + " " + station['csmd']['User_comment']

		else:
			description = station['csmd']['User_comment']

		description = " ".join(description.split())
		make_osm_line("DESCRIPTION",description)

		# Generate contact email tag

#		make_osm_line("CONTACT",station['csmd']['Contact_info'])

		reg = re.search(r'\b([a-zA-Z][a-zA-Z0-9_.+-]*@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)\b', station['csmd']['Contact_info'])
		if reg:
			make_osm_line("contact:email",reg.group(1).lower())

		# Generate contact phone tag

		reg = re.search(r'(\+?[0-9]{5,15})', station['csmd']['Contact_info'].replace("(","").replace(")","").replace("-","").replace(" ",""))
		if reg:
			phone = reg.group(1)
			if phone[:2] == "00":
				phone = "+" + phone[2:]

			if phone[:3] == "+47" or phone[:3] == "+46" or phone[:3] == "+45" or phone[:3] == "+31":
				if phone[3] == "0":
					phone = phone[:3] + " " + phone[4:]
				else:
					phone = phone[:3] + " " + phone[3:]

			elif phone[:4] == "+358":
				if phone[4] == "0":
					phone = "+358 " + phone[5:]
				else:
					phone = "+358 " + phone[4:]

			if phone[:1] == "0":
				phone = phone[1:]

			if phone[0] != "+":
				if station['csmd']['Land_code'] == "NOR":
					phone = "+47 " + phone
				elif station['csmd']['Land_code'] == "SWE":
					phone = "+46 " + phone
				elif station['csmd']['Land_code'] == "FIN":
					phone = "+358 " + phone
				elif station['csmd']['Land_code'] == "DAN":
					phone = "+45 " + phone

			if len(phone) < 10:
				phone = phone[:4] + "0" + phone[4:] 

			if phone == "+481750809":
				phone = "+46 481750809"
			elif phone == "+045578300":
				phone = "+46 45578300"

			make_osm_line("contact:phone",phone)

		# Generate contact website

		reg = re.search(r'(^|\s)([htps/:]*[a-z0-9.-]+[.][a-z]{2,5}[a-z0-9.?=#&_/-]*)[,]*(\s|$)', station['csmd']['Contact_info'].lower())
		if reg:
			website = reg.group(2).lower()
			website = website.replace("www.","")
			if website[:4] != "http":
				website = "http://" + website
			if website != "http://e.on":	
				make_osm_line("contact:website", website)
		'''

		# Loop each extra information item

		for key, info in station['attr']['st'].items():

			# Produce OSM tag for availability

			if key == '2':
				if info['attrvalid'] == '1':        # Public
					make_osm_line("access", "yes")

				elif info['attrvalid'] == '2':      # Visitors
					make_osm_line("access", "customers")

				elif info['attrvalid'] == '3':      # Employees
					make_osm_line("access", "employees")	

				elif info['attrvalid'] == '4':      # By appointment
					make_osm_line("access", "permissive")

				elif info['attrvalid'] == '5':      # Residents
					make_osm_line("access", "residents")

				else:
					message('Unknown availability id: "%s" - %s\n' % (info['attrvalid'], info['trans']))

			# Produce OSM tag for location

			elif key == '3':
				make_osm_line("LOCATION",info['trans'])

			# Produce OSM tag for parking fee

			elif key == '7':
				if info['trans'] == 'Yes':
					make_osm_line("parking:fee", "yes")

				elif info['trans'] == 'No':
					make_osm_line("parking:fee", "no")

			'''
			# Produce OSM tag for reservable

			elif key == '18':
				if info['trans'] == 'Yes':
					make_osm_line("reservation", "yes")

				elif info['trans'] == 'No':
					make_osm_line("reservation", "no")

			# Produce OSM tag for opening hours

			elif key == '24':
				make_osm_line("opening_hours", "24/7")

			# Produce OSM tag for time limit

			elif key == '6':
				if info['trans'] == 'Yes':
					make_osm_line("TIME_LIMIT", "yes")

				elif info['trans'] == 'No':
					make_osm_line("TIME_LIMIT", "no")
			'''

		# Loop all connectors for station and fetch info

		sockets = {
			'schuko': 0,
			'tesla_roadster': 0,
			'cee_blue': 0,
			'cee_red': 0,
			'type1': 0,
			'type2': 0,
			'type2_combo': 0,
			'chademo': 0,
			'tesla_supercharger': 0
			}

		capacity = {
			'schuko': 0,
			'tesla_roadster': 0,
			'cee_blue': 0,
			'cee_red': 0,	
			'type1': 0,
			'type2': 0,
			'type2_combo': 0,
			'chademo': 0,
			'tesla_supercharger': 0
			}

		authentication = {
			'open': False,
			'standard_key': False,
			'rfid': False,
			'payment': False,
			'cellular': False
			}

		payment = {
			'cellular': False,
			'visa': False,	
			'mastercard': False,
			'charging_card': False,
			'coin': False,
			'subscription': False,
			'cards': False
			}

		vehicle = {
			'battery': False,
			'plugin': False,
			'van': False,
			'moped': False,
			'bike': False,
			'short': False
			}

		hydrogen = False

		capacity_adjustment = 0

		for connector in station['attr']['conn'].values():

			if '4' in connector:  # "Connector"

				# Find capacity

				if "5" in connector:
					if connector['5']['attrvalid'] in capacities:
						connector_capacity = capacities[ connector['5']['attrvalid'] ]

					elif connector['5']['attrvalid'] in ['26', '27']:  # Hydrogen
						hydrogen = True
						connector_capacity = 0
					else:
						connector_capacity = 0
						message('Unexpected capacity: "%s" - %s\n' % (connector['5']['attrvalid'], connector['5']['trans']))
						make_osm_line("FIXME", "Socket output (kW)")
				else:
					connector_capacity = 0


				# Increase number of connectors by 1 and set capacity

				if connector['4']['attrvalid'] == '14':  # Schuko / Schucko CEE 7/4
					sockets['schuko'] += 1
					if '5' in connector:
						capacity['schuko'] = max(capacity['schuko'],connector_capacity)

				elif connector['4']['attrvalid'] == '29':  # Tesla Connector Roadster
					sockets['tesla_roadster'] += 1
					if '5' in connector:
						capacity['tesla_roadster'] = max(capacity['tesla_roadster'],connector_capacity)

				elif connector['4']['attrvalid'] == '34':  # Blue industrial 3-pin
					sockets['cee_blue'] += 1
					if '5' in connector:
						capacity['cee_blue'] = max(capacity['cee_blue'],connector_capacity)

				elif connector['4']['attrvalid'] == '35':  # Blue industrial 4-pin
					sockets['cee_blue'] += 1
					if '5' in connector:
						capacity['cee_blue'] = max(capacity['cee_blue'],connector_capacity)

				elif connector['4']['attrvalid'] == '36':  # Red industrial 5-pin
					sockets['cee_red'] += 1
					if '5' in connector:
						capacity['cee_red'] = max(capacity['cee_red'],connector_capacity)

				elif connector['4']['attrvalid'] == '31':  # Type 1
					sockets['type1'] += 1
					if '5' in connector:
						capacity['type1'] = max(capacity['type1'],connector_capacity)

				elif connector['4']['attrvalid'] == '32':  # Type 2
					sockets['type2'] += 1
					if '5' in connector:
						capacity['type2'] = max(capacity['type2'],connector_capacity)

				elif connector['4']['attrvalid'] == '60':  # Type 1/Type 2
					sockets['type1'] += 1
					sockets['type2'] += 1
					capacity_adjustment +=1
					if '5' in connector:
						capacity['type2'] = max(capacity['type2'],connector_capacity)

				elif connector['4']['attrvalid'] == '50':  # Type 2 + Chucko CEE 7/4
					sockets['schuko'] += 1
					sockets['type2'] += 1
					capacity_adjustment +=1
					capacity['schuko'] = max(capacity['schuko'],3.6)
					if '5' in connector:
						capacity['type2'] = max(capacity['type2'],connector_capacity)

				elif connector['4']['attrvalid'] == '39':  # CCS/Combo
					sockets['type2_combo'] += 1
					if '5' in connector:
						capacity['type2_combo'] = max(capacity['type2_combo'],connector_capacity)

				elif connector['4']['attrvalid'] == '41':  # Combo + CHAdeMO
					sockets['type2_combo'] += 1
					sockets['chademo'] += 1
					if '5' in connector:
						capacity['type2_combo'] = max(capacity['type2_combo'],connector_capacity)
						capacity['chademo'] = max(capacity['chademo'],connector_capacity)

				elif connector['4']['attrvalid'] == '42':  # CHAdeMO + Type 2
					sockets['chademo'] += 1
					sockets['type2'] += 1
					capacity_adjustment += 1
					if '5' in connector:
						capacity['chademo'] = max(capacity['chademo'],connector_capacity)

				elif connector['4']['attrvalid'] == '30':  # CHAdeMO
					sockets['chademo'] += 1
					if '5' in connector:
						capacity['chademo'] = max(capacity['chademo'],connector_capacity)

				elif connector['4']['attrvalid'] == '40':  # Tesla Connector
					if connector_capacity < 50:  # Probably Tesla destination charger
						sockets['type2'] += 1
						if '5' in connector:
							capacity['type2'] = max(capacity['type2'],connector_capacity)
					elif connector_capacity > 150:  # It is a V3 station, which is CCS/Combo
						sockets['type2_combo'] += 1
						if '5' in connector:
							capacity['type2_combo'] = max(capacity['type2_combo'],connector_capacity)
					else:
						sockets['tesla_supercharger'] += 1
						if '5' in connector:
							capacity['tesla_supercharger'] = max(capacity['tesla_supercharger'],connector_capacity)

				elif connector['4']['attrvalid'] == '43':  # CHAdeMO + Combo + AC-Type2
					sockets['chademo'] += 1
					sockets['type2_combo'] += 1
					sockets['type2'] += 1
					capacity_adjustment += 1

					if '5' in connector:
						if connector['5']['attrvalid'] == 21:
							# Less then 100 kW + 22 kW - 500VDC max 50A + 400V 3-phase max 32A
							capacity['chademo'] = max(capacity['chademo'],50)
							capacity['type2_combo'] = max(capacity['type2_combo'],50)
							capacity['type2'] = max(capacity['chademo'],22)

						elif connector['5']['attrvalid'] == 20:
							# Less then 100 kW + 43 kW - 500VDC max 200A + 400V 3-phase max 63A
							capacity['chademo'] = max(capacity['chademo'],50)
							capacity['type2_combo'] = max(capacity['type2_combo'],50)
							capacity['type2'] = max(capacity['chademo'],43)

						else:
							capacity['chademo'] = max(capacity['chademo'],connector_capacity)					
							capacity['type2_combo'] = max(capacity['type2_combo'],connector_capacity)

				elif connector['4']['attrvalid'] == '70':  # Hydrogen
					hydrogen = True	

				elif connector['4']['attrvalid'] != "0":   # Unspecified
					message('Unexpected connector: "%s" - %s\n' % (connector['4']['attrvalid'], connector['4']['trans']))

				'''
				# Removed the following section to simplify tagging

				# Fetch accessibility / authentication info for connector

				if '1' in connector:

					if connector['1']['attrvalid'] == '1':  # Open
						authentication['open'] = True

					elif connector['1']['attrvalid'] == '2':  # Standard key
						authentication['standard_key'] = True

					elif connector['1']['attrvalid'] == '4':  # RFID
						authentication['rfid'] = True

					elif connector['1']['attrvalid'] == '5':  # Payment
						authentication['payment'] = True
				
					elif connector['1']['attrvalid'] == '6':  # Cellular phone
						authentication['cellular'] = True

					elif connector['1']['attrvalid'] != '3':  # Not Other
						message('Unexpected accessibility: "%s" - %s\n' % (connector['1']['attrvalid'], connector['1']['trans']))

				# Fetch payment info for connector

				if '19' in connector:

					if connector['19']['attrvalid'] == '1':  # Cellular phone
						payment['cellular'] = True

					elif connector['19']['attrvalid'] == '2':  # VISA
						payment['visa'] = True

					elif connector['19']['attrvalid'] == '3':  # Mastervard and VISA
						payment['visa'] = True
						payment['mastercard'] = True

					elif connector['19']['attrvalid'] == '21':  # VISA, Mastercard and Charging card
						payment['visa'] = True
						payment['mastercard'] = True
						payment['charging_card'] = True
				
					elif connector['19']['attrvalid'] == '20':  # Cellular phone and Charging card
						payment['cellular'] = True
						payment['charging_card'] = True

					elif connector['19']['attrvalid'] == '7':  # Subscription
						payment['subscription'] = True
				
					elif connector['19']['attrvalid'] == '8':  # Coin
						payment['token'] = True

					elif connector['19']['attrvalid'] == '6':  # Other cards
						payment['cards'] = True

					elif connector['19']['attrvalid'] == '9':  # Miscellaneous cards
						payment['cards'] = True				

					elif connector['19']['attrvalid'] != '10': # Not Miscellaneous
						message('Unexpected payment method: "%s" - %s\n' % (connector['19']['attrvalid'], connector['19']['trans']))
				'''

				# Fetch vehicle type

				if '17' in connector:
					if connector['17']['attrvalid'] == '1':  # All (battery only) vehicles
						vehicle['battery'] = True
					elif connector['17']['attrvalid'] == '2':  # Short vehicles
						vehicle['short'] = True
					elif connector['17']['attrvalid'] == '3':  # Two-wheel mopeds
						vehicle['moped'] = True
					elif connector['17']['attrvalid'] == '4':  # Electrical bikes
						vehicle['bike'] = True						
					elif connector['17']['attrvalid'] == '5':  # Plug-in hybrid
						vehicle['plugin'] = True
					elif connector['17']['attrvalid'] == '6':  # Van
						vehicle['van'] = True
					elif connector['17']['attrvalid'] in ['7','8','9']:
						hydrogen = True
					else:
						message('Unexpected vehicle type: "%s" - %s\n' % (connector['17']['attrvalid'], connector['17']['trans']))

			# Check for hydrogen

			if '26' in connector and connector['26']['attrvalid'] == "2":
				hydrogen == True


		# Produce osm tags with number of sockets per connector type

		for connector_type, number_of_sockets in sockets.items():
			if number_of_sockets > 0:
				make_osm_line("socket:" + connector_type, str(number_of_sockets))
		
		# Produce osm tags with capacity per connector type

		for connector_type, capacity_per_connector in capacity.items():
			if capacity_per_connector > 0.0:
				make_osm_line("socket:" + connector_type + ":output", str(capacity_per_connector) + "kW")

		max_capacity = max(capacity.values())

		# Estimate capacity and produce osm tag

		est_capacity = max(sockets['chademo'], sockets['type2_combo']) + sum(sockets.values()) - sockets['chademo'] - sockets['type2_combo'] - capacity_adjustment

		if est_capacity > 0:
			make_osm_line("capacity", str(est_capacity))

		'''
		# Removed the following section to simplify tagging

		# Produce osm tags for authentication

		if authentication['open']:
			make_osm_line("authentication:none", "yes")

		if authentication['standard_key']:
			make_osm_line("authentication:key", "yes")

		if authentication['rfid']:
			make_osm_line("authentication:nfc", "yes")

		if authentication['cellular']:
			make_osm_line("authentication:app", "yes")

		if authentication['payment']:
			make_osm_line("authentication:payment", "yes")

		# Produce osm tags for payment method

		if payment['visa']:
			make_osm_line("payment:visa", "yes")

		if payment['mastercard']:
			make_osm_line("payment:mastercard", "yes")

		if payment['charging_card']:
			make_osm_line("payment:contactless", "yes")

		if payment['cellular']:
			make_osm_line("payment:app", "yes")

		if payment['subscription']:
			make_osm_line("payment:subscription", "yes")

		if payment['coin']:
			make_osm_line("payment:token", "yes")

		if payment['cards']:
			make_osm_line("payment:cards", "yes")

		if True in payment.values() or authentication['payment']:
			make_osm_line("fee", "yes")
		'''

		# Produce osm access tags for some vehicle types

		if vehicle['van']:
			make_osm_line("hgv", "yes")
		if vehicle['plugin']:
			make_osm_line("hybrid_car", "yes")
		if vehicle['moped']:
			make_osm_line("moped", "yes")
		if vehicle['bike']:
			make_osm_line("bicycle", "yes")


		# Fix name in the following sections

		name = station['csmd']['name']
		original_name = name

		# Remove "fastcharger" etc from name. Fixme: Finnish equivalents

		for delete_word in ['hurtiglader', 'hurtigladestasjon', 'semihurtiglader', 'semihurtigladestasjon', 'fastcharger',
	    					'snabbladdare', 'snabbladdstation', 'snabbladdningsstation', 'snabbladdning', '(snabb)', 'semiladdare',
	    					'lader', 'ladestasjon', 'laddstation', 'laddplats', 'laddpunkten',  'laddgata', 'laddgatan',
	    					'destinationsladdning', 'destinationsladdare',
	    					'superladestasjon', 'superladerstasjon', 'superlader', 'teslalader', 'roadster', 'SC', 'supercharger',
	    					'ved', 'på', 'AS', 'AB', 'Vattenfall', 'Charge and Drive']:

		    reg = re.search(r'\b(%s)\b' % delete_word, name, flags=re.IGNORECASE|re.UNICODE)
		    if reg:
		        name = name.replace(reg.group(1), '')

		# Insert network name at the start of station name (only for high capacity chargers)

		network_name = ""

		for network in network_list:
			if network[0].lower() in station['csmd']['Owned_by'].lower():
				name = network[1] + " " + name.replace(network[0], "").replace(network[1], "").lstrip(", ").strip()
				network_name = network[1]
				break

		if network_name == "Tesla" and max_capacity < 50:
			network_name = ""

		if network_name in network_count:
			network_count[ network_name ] += 1
		elif network_name:
			network_count[ network_name ] = 1

			'''
			# First remove any existing network name from station name
			reg1 = re.search(r'\b(%s)\b' % network[0], name, flags=re.IGNORECASE|re.UNICODE)
			if reg1:
				name = name.replace(reg1.group(1), '')

			# If network present in station name, operator name or contact then insert network name at start of station name

			reg2 = re.search('(%s)' % network[0], station['csmd']['Owned_by'], flags=re.IGNORECASE|re.UNICODE)
			reg3 = re.search('(%s)' % network[0], station['csmd']['Contact_info'], flags=re.IGNORECASE|re.UNICODE)
			reg4 = re.search('(%s)' % network[0], station['csmd']['User_comment'], flags=re.IGNORECASE|re.UNICODE)

			if network[1] != "":
				reg5 = re.search('(%s)' % network[1], station['csmd']['Contact_info'], flags=re.IGNORECASE|re.UNICODE)
				reg6 = re.search('(%s)' % network[1], station['csmd']['User_comment'], flags=re.IGNORECASE|re.UNICODE)
			else:
				reg5 = None
				reg6 = None

			if reg1 or reg2 or reg3 or reg4 or reg5 or reg6:
				name = network[0].replace("\\", "") + " " + name.lstrip(", ")
				network_name = network[0].replace("\\", "")
				break
			'''

		# Lowercase certain words; uppercase others (or a mix)

		for case in ['p-plass', 'p-plats', 'p-hus', 'p-anlegg', 'garasje', 'fellesparkering', 'parkering', 'bygg', 'gästparkering', 'utomhusparkering',
					 'hotel', 'hotell', 'turisthotell', 'camping', 'fjellstove', 'turisthytte', 'slott', 'gård',
					 'airport', 'flyplass', 'flygplats', 'lufthamn', 'terminal',
					 'jernbanestasjon', 'järnvägsstation', 'stasjon', 'station', 't-bane', 'tågstation',
					 'sentrum', 'centrum', 'torg', 'resecentrum', 'central', 'plass', 'allé', 'allè',
					 'storsenter', 'senter', 'kjøpesenter', 'köpcenter', 'köpcentrum', 'møbelsenter', 'shopping', 'handelspark', 'handelsområde',
					 'industriområde', 'næringspark', 'konferanse', 'konferens',
					 'rådhus', 'kommunehus', 'kommunhus', 'omsorgssenter', 'vgs', 'sykehus', 'sjukhus',
					 'borettslag', 'sameie', 'boligsameie',
					 'besøkende', 'ansatte',
					 'Amfi', 'Coop', 'Q-Park']:

			reg = re.search(r'\b(%s)\b' % case, name, flags=re.IGNORECASE|re.UNICODE)
			if reg:
				name = name.replace(reg.group(1), case)

		# Remove superfluous spaces

		name = name.replace("- ","")
		name = name.replace("– ","")
		name = name.replace(" ,", ",")
		name = name.strip(", ")
		name = name.replace("  "," ")
		name = name.strip(" ")

		if name[0:6] != "eRoute" and len(name) > 1:
			name = name[0].upper() + name[1:]

		if network_name == "Tesla":
			name += " supercharger"  # Official Tesla station name

		# Remove municipality name at the end (for Norway only)

		if station['csmd']['Land_code'] == "NOR":
			split_name = name.split()
			network_length = len(network_name.split())
			if len(split_name) > network_length and split_name[-1].upper() == station['csmd']['Municipality'] and ", " in name:
				name = name.rstrip(split_name[-1])
				name = name.strip(", ")

		# Produce osm tags for name and network

		make_osm_line("name",name)

		if network_name != "":
			make_osm_line("brand",network_name)
		elif station['csmd']['Owned_by'] and station['csmd']['Owned_by'] not in ["-", "Tesla"]:
			make_osm_line("operator",station['csmd']['Owned_by'])

		make_osm_line("OWNER", station['csmd']['Owned_by'])

		if name != original_name:
			make_osm_line("NOBIL_NAME",original_name)

		# Produce amnity station tag

		if not hydrogen or est_capacity > 0:
			make_osm_line("amenity", "charging_station")
		else:
			make_osm_line("amenity", "fuel_station")

		# Questionable data quality
#		if hydrogen:
#			make_osm_line("fuel:h70", "yes")

		# Done with OSM station node

		file.write('  </node>\n')


	# Produce OSM file footer

	file.write('</osm>\n')
	file.close()

	message("Networks:\n")
	for network in sorted(network_count, key=network_count.get, reverse=True):
		message("\t%-20s %5i\n" % (network, network_count[ network ]))

	message ("Saved %i charging stations to '%s'\n\n" % (count, filename))
