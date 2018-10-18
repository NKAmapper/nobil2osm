#!/usr/bin/env python
# -*- coding: utf8

# nobil2osm v0.9.1
# Converts nobil json dump to osm format for import/update
# Usage: nobil2.osm [input_filename.json] > output_filename.osm
# Default input file name is "NOBILdump_all_forever.json"


import json
import cgi
import HTMLParser
import sys
import re


# Produce a tag for OSM file

def make_osm_line(key,value):
    if value != "":
		parser = HTMLParser.HTMLParser()
		value = parser.unescape(value)
		encoded_value = cgi.escape(value.encode('utf-8'),True)
		print ('    <tag k="' + key + '" v="' + encoded_value + '" />')


# Return capacity/wattage of socket

def find_capacity(capacity_id):

	capacity = {
		'7':  3.6, # 3,6 kW . 230V 1-phase max 16A
		'16': 6.3, # 230V 3-phase max 16A
		'8':  7.4, # 7.4 kW - 230V 1-phase max 32A
		'10': 11,  # 11 kW - 400V 3-phase max 16A
		'17': 13,  # 230V 3-phase max 32A
		'19': 20,  # 20 KW - 500VDC max 50A
		'11': 22,  # 22 kW - 400 3-phase max 32A
		'12': 43,  # 43 kW - 400 3-phase max 63A	
		'13': 50,  # 50 kW - 500VDC max 100A
		'23': 100, # 100 kW - 500VDC max 200A
		'22': 135, # 135 kW - 480 VDC max 270A
		'24': 150, # 150 kW DC
		'20': 50,  # Less then 100 kW + 43 kW - 500VDC max 200A + 400V 3-phase max 63A
		'21': 50,  # Less then 100 kW + 22 kW - 500VDC max 50A + 400V 3-phase max 32A
		'0':  0}   # Unspecified

	try:
		return capacity[capacity_id]
	except KeyError:
		raise KeyError('Unknown capacity_id: "%s"' % capacity_id)


# Main program

if __name__ == '__main__':

	# Read all data into memory

	if len(sys.argv) == 1:
		filename = 'NOBILdump_all_forever.json'
	else:
		filename = sys.argv[1]

	with open(filename) as f:
		nobil_data = json.load(f)
		f.close()

	# Produce OSM file header

	print ('<?xml version="1.0" encoding="UTF-8"?>')
	print ('<osm version="0.6" generator="nobil2osm v0.9.1">')

	node_id = -1000
	position = ()

	# Loop through all charging stations and produce OSM tags

	for station in nobil_data['chargerstations']:

		node_id -= 1

		position = eval(station['csmd']['Position'])

		print('  <node id="' + str(node_id) + '" lat="' + str(position[0]) + '" lon="' + str(position[1]) + '">')

		make_osm_line("amenity","charging_station")
		make_osm_line("ref:nobil",str(station['csmd']['id']))
		make_osm_line("operator",station['csmd']['Owned_by'])
		make_osm_line("source","nobil.no")

		make_osm_line("STREET",station['csmd']['Street'])
		make_osm_line("HOUSE_NUMBER",station['csmd']['House_number'])
		make_osm_line("POSTCODE",station['csmd']['Zipcode'])
		make_osm_line("CITY",station['csmd']['City'])
		make_osm_line("MUNICIPALITY_ID",station['csmd']['Municipality_ID'])
		make_osm_line("MUNICIPALITY",station['csmd']['Municipality'])
		make_osm_line("COUNTY_ID",station['csmd']['County_ID'])
		make_osm_line("COUNTY",station['csmd']['County'])
		make_osm_line("COUNTRY",station['csmd']['Land_code'])

		make_osm_line("CREATED",station['csmd']['Created'][:10])
		make_osm_line("UPDATED",station['csmd']['Updated'][:10])

		make_osm_line("CHARGING_POINTS",str(station['csmd']['Number_charging_points']))

		# Produce description tag

		if station['csmd']['Description_of_location'] != '':
			if station['csmd']['User_comment'] != '':
				description = station['csmd']['Description_of_location']
				if not(description[len(description)-1] in ['.','!','?']):
					description = description + "."
				description = description + " " + station['csmd']['User_comment']

		else:
			description = station['csmd']['User_comment']

		make_osm_line("description:da",description)

		# Generate contact email tag

		make_osm_line("CONTACT",station['csmd']['Contact_info'])

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
					raise KeyError('Unknown availability id: "%s"' % info['attrvalid'])

			# Produce OSM tag for location

			elif key == '3':
				make_osm_line("LOCATION",info['trans'])

			# Produce OSM tag for parking fee

			elif key == '7':
				if info['trans'] == 'Yes':
					make_osm_line("parking:fee", "yes")

				elif info['trans'] == 'No':
					make_osm_line("parking:fee", "no")

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


		# Loop thorough all connectors for station and fetch info

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
			'bike': False,
			'short': False
			}

		capacity_adjustment = 0

		for connector in station['attr']['conn'].values():

			if '4' in connector:

				# Increase number of connectors by 1 and set capacity

				if connector['4']['attrvalid'] == '14':  # Schuko / Schucko CEE 7/4
					sockets['schuko'] += 1
					if '5' in connector:
						capacity['schuko'] = max(capacity['schuko'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '29':  # Tesla Connector Roadster
					sockets['tesla_roadster'] += 1
					if '5' in connector:
						capacity['tesla_roadster'] = max(capacity['tesla_roadster'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '34':  # Blue industrial 3-pin
					sockets['cee_blue'] += 1
					if '5' in connector:
						capacity['cee_blue'] = max(capacity['cee_blue'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '35':  # Blue industrial 4-pin
					sockets['cee_blue'] += 1
					if '5' in connector:
						capacity['cee_blue'] = max(capacity['cee_blue'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '36':  # Red industrial 5-pin
					sockets['cee_red'] += 1
					if '5' in connector:
						capacity['cee_red'] = max(capacity['cee_red'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '31':  # Type 1
					sockets['type1'] += 1
					if '5' in connector:
						capacity['type1'] = max(capacity['type1'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '32':  # Type 2
					sockets['type2'] += 1
					if '5' in connector:
						capacity['type2'] = max(capacity['type2'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '60':  # Type 1/Type 2
					sockets['type1'] += 1
					sockets['type2'] += 1
					capacity_adjustment +=1
					if '5' in connector:
						capacity['type2'] = max(capacity['type2'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '50':  # Type 2 + Chucko CEE 7/4
					sockets['schuko'] += 1
					sockets['type2'] += 1
					capacity_adjustment +=1
					capacity['schuko'] = max(capacity['schuko'],3.6)
					if '5' in connector:
						capacity['type2'] = max(capacity['type2'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '39':  # CCS/Combo
					sockets['type2_combo'] += 1
					if '5' in connector:
						capacity['type2_combo'] = max(capacity['type2_combo'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '41':  # Combo + CHAdeMO
					sockets['type2_combo'] += 1
					sockets['chademo'] += 1
					if '5' in connector:
						capacity['type2_combo'] = max(capacity['type2_combo'],find_capacity(connector['5']['attrvalid']))
						capacity['chademo'] = max(capacity['chademo'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '42':  # CHAdeMO + Type 2
					sockets['chademo'] += 1
					sockets['type2'] += 1
					capacity_adjustment += 1
					if '5' in connector:
						capacity['chademo'] = max(capacity['chademo'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '30':  # CHAdeMO
					sockets['chademo'] += 1
					if '5' in connector:
						capacity['chademo'] = max(capacity['chademo'],find_capacity(connector['5']['attrvalid']))

				elif connector['4']['attrvalid'] == '40':  # Tesla Connector
					sockets['tesla_supercharger'] += 1
					if '5' in connector:
						capacity['tesla_supercharger'] = max(capacity['tesla_supercharger'],find_capacity(connector['5']['attrvalid']))

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
							capacity['chademo'] = max(capacity['chademo'],find_capacity(connector['5']['attrvalid']))					
							capacity['type2_combo'] = max(capacity['type2_combo'],find_capacity(connector['5']['attrvalid']))					

				elif connector['4']['attrvalid'] != "0":   # Unspecified
					raise KeyError('Unexpected connector: "%s"' % connector['4']['attrvalid'])		

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
						raise KeyError('Unexpected Accessibility: "%s"' % connector['1']['attrvalid'])

				# Fetch payment info for connector

				if '19' in connector:

					if connector['19']['attrvalid'] == '1':  # Cellular phone
						payment['cellular'] = True

					elif connector['19']['attrvalid'] == '2':  # VISA
						payment['visa'] = True

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
						raise KeyError('Unexpected Payment method: "%s"' % connector['19']['attrvalid'])

				# Fetch vehicle type

				if '17' in connector:
					if connector['17']['attrvalid'] == '1':  # All (battery only) vehicles
						vehicle['battery'] = True
					elif connector['17']['attrvalid'] == '2':  # Short vehicles
						vehicle['short'] = True
					elif connector['17']['attrvalid'] == '3':  # Two-wheel mopeds
						vehicle['bike'] = True
					elif connector['17']['attrvalid'] == '5':  # Plug-in hybrid
						vehicle['plugin'] = True
					elif connector['17']['attrvalid'] == '6':  # Van
						vehicle['van'] = True
					else:
						raise KeyError('Unexpected Vehicle type: "%s"' % connector['17']['attrvalid'])


		# Produce osm tags with number of sockets per connector type

		for connector_type, number_of_sockets in sockets.items():

			if number_of_sockets > 0:
				make_osm_line("socket:" + connector_type, str(number_of_sockets))
		
		# Produce osm tags with capacity per connector type

		for connector_type, capacity_per_connector in capacity.items():

			if capacity_per_connector > 0.0:
				make_osm_line("socket:" + connector_type + ":output", str(capacity_per_connector) + "kW")

		# Estimate capacity and produce osm tag

		est_capacity = max(sockets['chademo'], sockets['type2_combo']) + sum(sockets.itervalues()) - sockets['chademo'] - sockets['type2_combo'] - capacity_adjustment
		make_osm_line("capacity", str(est_capacity))

		# Produce osm tags for authentication

		if authentication['open']:
			make_osm_line("authentication:none", "yes")

		if authentication['standard_key']:
			make_osm_line("authentication:key", "yes")

		if authentication['rfid']:
			make_osm_line("authentication:nfc", "yes")

		if authentication['cellular']:
			make_osm_line("authentication:mobile_phone", "yes")

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
			make_osm_line("payment:mobile_phone", "yes")

		if payment['subscription']:
			make_osm_line("payment:subscription", "yes")

		if payment['coin']:
			make_osm_line("payment:token", "yes")

		if payment['cards']:
			make_osm_line("payment:cards", "yes")

		if True in payment.values() or authentication['payment']:
			make_osm_line("fee", "yes")

		# Produce osm access tags for some vehicle types

		if vehicle['van']:
			make_osm_line("hgv", "yes")
		if vehicle['plugin']:
			make_osm_line("hybrid_car", "yes")
		if vehicle['bike']:
			make_osm_line("moped", "yes")


		# Fix name in the following sections

		name = station['csmd']['name']
		original_name = name

		# Remove "fastcharger" etc from name. Fixme: Finnish equivalents

		for delete_word in ['hurtiglader', 'hurtigladestasjon', 'semihurtiglader', 'semihurtigladestasjon', 'fastcharger',
	    					'snabbladdare', 'snabbladdstation', 'snabbladdningsstation', 'snabbladdning', '(snabb)', 'semiladdare',
	    					'lader', 'ladestasjon', 'laddstation', 'laddplats', 'laddpunkten',  'laddgata', 'laddgatan',
	    					'destinationsladdning', 'destinationsladdare',
	    					'superladestasjon', 'superladerstasjon', 'superlader', 'supercharger', 'teslalader', 'roadster', 'SC',
	    					'ved', u'på', 'AS', 'AB', 'Vattenfall', 'Charge and Drive']:

		    reg = re.search(r'\b(%s)\b' % delete_word, name, flags=re.IGNORECASE|re.UNICODE)
		    if reg:
		        name = name.replace(reg.group(1), '')

		# Insert network name at the start of station name

		network_list = [
			('Fortum','chargedrive'),
			(u'Grønn kontakt','gronnkontakt'),
			('Clever',''),
			('Tesla',''),
			('BKK','bilkraft'),
			('Charge365',''),
			(u'Laddregion Mälardalen',''),
			('InCharge',''),
			('Ionity','') ]

		network_name = []

		for network in network_list:

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
				name = network[0] + " " + name.lstrip(", ")
				network_name = network[0]

		# Lowercase certain words; uppercase others

		for case in ['p-plass', 'p-plats', 'p-hus', 'p-anlegg', 'garasje', 'fellesparkering', 'parkering', 'bygg', u'gästparkering', 'utomhusparkering',
					 'hotel', 'hotell', 'turisthotell', 'camping', 'fjellstove', 'turisthytte', 'slott', u'gård',
					 'airport', 'flyplass', 'flygplats', 'lufthamn', 'terminal',
					 'jernbanestasjon', u'järnvägsstation', 'stasjon', 'station', 't-bane', u'tågstation',
					 'sentrum', 'centrum', 'torg', 'resecentrum', 'central',
					 'storsenter', 'senter', u'kjøpesenter', u'köpcenter', u'köpcentrum', u'møbelsenter', 'shopping', 'handelspark', u'handelsområde',
					 u'industriområde', u'næringspark', 'konferanse', 'konferens',
					 u'rådhus', 'kommunehus', 'kommunhus', 'omsorgssenter', 'vgs', 'sykehus', 'sjukhus',
					 'borettslag', 'sameie', 'boligsameie',
					 u'besøkende', 'ansatte',
					 'Amfi', 'Coop']:

			reg = re.search(r'\b(%s)\b' % case, name, flags=re.IGNORECASE|re.UNICODE)
			if reg:
				name = name.replace(reg.group(1), case)

		# Remove superfluous spaces

		name = name.replace("- ","")
		name = name.replace(u"– ","")
		name = name.replace(" ,", ",")
		name = name.strip(", ")
		name = name.replace("  "," ")
		name = name[0].upper() + name[1:]


		# Produce osm tags for name and network

		make_osm_line("name",name)

		if network_name:
			make_osm_line("brand",network_name)

		if name != original_name:
			make_osm_line("ORIGINAL_NAME",original_name)

		# Done with OSM station node

		print('  </node>')


	# Produce OSM file footer

	print('</osm>')
