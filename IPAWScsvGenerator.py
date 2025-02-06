# Developed for Python 3, JSON output.
import json
import csv
import xml.etree.ElementTree as ET

import requests as rq # type: ignore
import math
from datetime import datetime, timedelta

import pandas as pd # type: ignore
import numpy as np # type: ignore


print("START " + str(datetime.now()))

# API URL Functions
ogstr = "https://www.fema.gov/api/open/v1/IpawsArchivedAlerts"

def between(start, end):
    link = ogstr + "?$filter=sent ge '" + start + "T00:00:00.000Z' and sent le '" + end + "T24:00:00.000Z'"
    print("For between " + start + " and " + end + ", copy full link in brackets: [" + str(link) + "] (note: this will show 1000 entries max)")
    return link


def on(date):
    link = ogstr + "?$filter=sent ge '" + date + "T00:00:00.000Z' and sent le '" + date + "T24:00:00.000Z'"
    print("For on " + date + ", copy full link in brackets: [" + str(link) + "] (note: this will show 1000 entries max)")
    return link


def form(date):
    return str(date)[0:10] + "T" + str(date)[11:23] + "Z"


def yesterday():
    begin = datetime.utcnow() - timedelta(days=2)
    link = ogstr + "?$filter=sent ge '" + form(begin) + "'"
    print("For yesterday, copy full link in brackets: [" + str(link) + "] (note: this will show 1000 entries max)")
    return link


top = 1000  # (MAX 1000) number of records to get per call
skip = 0  # number of records to skip from top

# ------INPUT REQUESTS------
stateFilter = None
critical = False
print('Write output file\'s name (.json added automatically) [Ex: May1_2021Ipaws]')
file_name = input('File Name: ')

print('Would you like to see data ON a date, BETWEEN two dates, or YESTERDAY?')

fun = input('ON (O), BETWEEN (B), or YESTERDAY (Y): ')

if (fun.lower() == 'o' or fun.lower() == 'on'):
    print('Write date in form \'YYYY-MM-DD\'')
    date = input('Date: ')
    baseUrl = on(date)

elif (fun.lower() == 'between' or fun.lower() == 'b'):
    print('Write date in form \'YYYY-MM-DD\'')
    start = input('Start date: ')
    end = input('End date: ')
    baseUrl = between(start, end)

elif (fun.lower() == 'yesterday' or fun.lower() == 'y'):
    baseUrl = yesterday()

else:
    print('ERROR: Correct command not received, exiting')
    exit()

print('Would you like to add filters?')   
fyn = input('YES (Y) or NO (N): ')
if (fyn.lower() != 'yes' and fyn.lower() != 'y' ) and (fyn.lower() != 'no' and fyn.lower() != 'n' ):
    print('ERROR: Correct command not received, exiting')
    exit()
elif (fyn.lower() == 'yes' or fyn.lower() == 'y' ): 
    
    print('Would you like to filter for a specific type of event?')
    yn1 = input('YES (Y) or NO (N): ')
    if (yn1.lower() != 'yes' and yn1.lower() != 'y' ) and (yn1.lower() != 'no' and yn1.lower() != 'n' ):
        print('ERROR: Correct command not received, exiting')
        exit()
    elif (yn1.lower() == 'yes' or yn1.lower() == 'y' ):
        print('The following is the list of accepted event codes:\nSVR - Severe Thunderstorm Warning\nFFW - Flash Flood Warning\nFLW - Flood Warning\nFLS - Flood Statement\nHLS - Hurricane Statement\nHUW - Hurricane Warning\nTOE - 911 Telephone Outage')
        code = input('Event code: ')
        baseUrl = ogstr+'?$filter=contains(info/eventCode/value, \''+ code.upper() +'\') and ('+baseUrl[61:]+')'

    print('Would you like to exclude NWS weather alerts?')
    yn2 = input('YES (Y) or NO (N): ')
    if (yn2.lower() != 'yes' and yn2.lower() != 'y' ) and (yn2.lower() != 'no' and yn2.lower() != 'n' ):
        print('ERROR: Correct command not received, exiting')
        exit()
    elif (yn2.lower() == 'yes' or yn2.lower() == 'y'):
        baseUrl += ' and sender ne \'w-nws.webmaster@noaa.gov\''

    stateFilter = None
    print('Would you like to filter for a specific state or region? Notice: Record count may not match csv')
    yn3 = input('YES (Y) or NO (N): ')
    if (yn3.lower() != 'yes' and yn3.lower() != 'y' ) and (yn3.lower() != 'no' and yn3.lower() != 'n' ):
        print('ERROR: Correct command not received, exiting')
        exit()
    elif (yn3.lower() == 'yes' or yn3.lower() == 'y'):
        print('For list of accepted states, visit [https://en.wikipedia.org/wiki/Federal_Information_Processing_Standard_state_code] Ex: Texas')
        stateFilter = input('State: ')

    print('Would you like to filter for a specific block channel?')
    yn4 = input('YES (Y) or NO (N): ')
    if (yn4.lower() != 'yes' and yn4.lower() != 'y' ) and (yn4.lower() != 'no' and yn4.lower() != 'n' ):
        print('ERROR: Correct command not received, exiting')
        exit()
    elif (yn4.lower() == 'yes' or yn4.lower() == 'y'):
        print("The following is the list of accepted event codes: 'CMAS', 'EAS', 'NWEM', 'PUBLIC'")
        block = input('Blockchannel: ')
        baseUrl = ogstr+'?$filter=contains(info/parameter/value, \''+ block.upper() +'\') and ('+baseUrl[61:]+')'

    print('Would you like to see only the critical fields?   ---')
    yn5 = input('YES (Y) or NO (N): ')
    if (yn5.lower() != 'yes' and yn5.lower() != 'y' ) and (yn5.lower() != 'no' and yn5.lower() != 'n' ):
        print('ERROR: Correct command not received, exiting')
        exit()
    elif (yn5.lower() == 'yes' or yn5.lower() == 'y'):
        critical = True
# ------END OF INPUT REQUESTS------

print('API link for your data is: [' + baseUrl + "] (note: this will display 1000 entries max")

# Return single record with given criteria, allows us to view total record count using inlinecount
jsonData = rq.get(baseUrl[0:53] + "&$inlinecount=allpages&$top=1&" + baseUrl[53:])

# Calculate number of calls necessary to get all our data (w/ maximum of 1000 per iteration)
recCount = jsonData.json()['metadata']['count']
if recCount == 0:
    print('There are no entries with your criteria, exiting')
    exit()
loopNum = math.ceil(recCount / top)


# Send some logging info to the console so we can see what is happening
print(str(recCount) + " records, " + str(top) + " returned per call, " + str(loopNum) + " iterations needed.")

# Initialize output file and begin writing data into it
outFile = open(file_name + ".json", "a")
outFile.write('[')

processed_ids = set()
unique_records = []
# Loop and call the API endpoint changing the record start each iteration
i = 0
while (i < loopNum):
    # Get string of data for given iteration
    webUrl = rq.get(baseUrl + "&$skip=" + str(skip) + "&$top=" + str(top))
    results = (webUrl.json()['IpawsArchivedAlerts'])

    for result in results:
        unique_id = result.get('id')  # Replace 'unique_id' with the actual unique identifier field
        if unique_id not in processed_ids:
            processed_ids.add(unique_id) 
            unique_records.append(result)

    # Update iteration and skip values
    i += 1
    skip = i * top

    print("Iteration " + str(i) + " done")

results_str = json.dumps(unique_records)

# Write the final JSON string to the file
with open(file_name + ".json", "w") as outFile:
    outFile.write(results_str)

outFile.close()

# Re-opens the file so we can see if we got the correct number of entries
inFile = open(file_name + ".json", "r")
my_data = inFile.read()
#final_count = len(json.loads(my_data)['IpawsArchivedAlerts'])

#print(str(final_count) + " records in file named " + file_name + ".json")
#if recCount == final_count:
print("Success! Correct number of records in output")
#else:
 #   print("ERROR: Output file does not contain correct number of records")
print("END " + str(datetime.now()))
inFile.close()




print("Converting JSON data into CSV format")
def get_nested_value(key, dic, default=None):
    '''Get the value of a nested key. Keys can be list of keys or single key'''
    if isinstance(key, list):
        for k in key:
            if isinstance(dic, dict) and k in dic:
                dic = dic[k]
            else:
                return default
        return dic
    return dic.get(key, default)

# Opens the newly downloaded json file
with open(file_name + ".json") as json_file:
    data = json.load(json_file)

csv_data = []

# Capture the availble fields in the json data 
for item in data:
    id = item.get("id", "")
    identifier = item.get("identifier", "")
    sent = item.get("sent", "")
    addresses = item.get("addresses", "")
    code = ",".join(item.get("code", []))
    info = item.get("info") or [{}]
    info = info[0]
    areas = info.get("areas", [{}])[0]
    event = info.get("event", "")
    expires = info.get("expires", "")
    urgency = info.get("urgency", "")
    category = ",".join(info.get("category", []))
    headline = info.get("headline", "")
    severity = info.get("severity", "")
    certainty = info.get("certainty", "")
    senderName = info.get("senderName", "")
    description = info.get("description", "")
    cogId = item.get("cogId", "")
    msgType = item.get("msgType", "")
    originalMessage = item.get("originalMessage", "")
    scope = item.get("scope", "")
    searchGeometry = item.get("searchGeometry", "")
    sender = item.get("sender", "")
    source = item.get("source", "")
    status = item.get("status", "")
    xmlns = item.get("xmlns", "")

    # The original message contains the raw xml data, which we will now parse for additional fields
    if originalMessage:
            root = ET.fromstring(originalMessage) # To parse xml data
            block_channel = None    # Initially declare fields as none (i.e empty cells)
            response_type = None
            effective = None
            onset = None
            instruction = None
            references = None
            web = None
            event_value = None
            loc_value = None
            areaDesc = None
            areaPoly = None
            areaCircle = None
            cmamValue = None
            cmamLongValue = None
            resourceDesc = None
            mimeType = None
            orgCode = None
            timezone = None
            AudioSource = None
            uri = None
            # derefuri = None
            state = None
            WEAHandling = None
            EASText = None
            DBGF = None
            language = None

        # Define the namespace
            namespaces = {'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}

        # Find parameters considering namespace
            temp2 = ""
            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                # Find valuename within parameter
                valueName_element = parameter.find('cap:valueName', namespaces)
                # Ensure the valueName is not empty and contains blockchannel information
                if valueName_element is not None and valueName_element.text == 'BLOCKCHANNEL':
                    # Find the value element
                    value_element = parameter.find('cap:value', namespaces)
                    # Ensure the element is not none
                    if value_element is not None:
                    # Set the variable equal to the text within the value element
                    # Since this code loops, new values found are appeneded to previous values with '|' inbetween
                        temp = value_element.text
                        if block_channel is not None:
                            if temp not in block_channel:
                                block_channel = temp2 + temp + "|"
                                temp2 = block_channel
                        else:
                            block_channel = temp2 + temp + "|"
                            temp2 = block_channel

            # Find the response type element
            responseType_element = root.find('.//cap:responseType', namespaces)
            if responseType_element is not None:
                # If the response type element is not none set the variable equal to the text in the element
                response_type = responseType_element.text

            temp2 = ''
            # Find the language element
            infos = root.findall('.//cap:info', namespaces)
            # Traverse list of parameters
            for info in infos:
                language_element = root.find('.//cap:language', namespaces)
                if language_element is not None:
                    # If the language element is not none set the variable equal to the text in the element
                    temp = language_element.text  
                    language = temp2 + temp + "|"
                    temp2 = language 

            # Find the effective element
            effective_element = root.find('.//cap:effective', namespaces)
            if effective_element is not None:
                # If the effective element is not none set the variable equal to the text in the element
                effective = effective_element.text

            # Find the onset element
            onset_element = root.find('.//cap:onset', namespaces)
            if onset_element is not None:
                # If the onset element is not none set the variable equal to the text in the element
                onset = onset_element.text

            # Find the instruction element
            instruction_element = root.find('.//cap:instruction', namespaces)
            if instruction_element is not None:
                # If the instruction element is not none set the variable equal to the text in the element
                instruction = instruction_element.text

            # Find the references element
            references_element = root.find('.//cap:references', namespaces)
            if references_element is not None:
                # If the references element is not none set the variable equal to the text in the element
                references = references_element.text

            # Find the web element
            web_element = root.find('.//cap:web', namespaces)
            if web_element is not None:
                # If the web element is not none set the variable equal to the text in the element
                web = web_element.text

            # Find eventCode elements considering namespace
            temp2 = ""
            temp = ""
            eventCodes = root.findall('.//cap:eventCode', namespaces)
            # Traverse list of event codes
            for eventCode in eventCodes:
                valueName_element = eventCode.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == "SAME":
                    value_element = eventCode.find('cap:value', namespaces)
                    if value_element is not None:
                        # Set the variable equal to the text within the value element
                        # Since this code loops, new values found are appeneded to previous values with '|' inbetween
                        temp = value_element.text
                        if event_value is not None:
                            if temp not in event_value:
                                event_value = temp
                        else:
                            event_value = temp

            codeLetters = ["ADR","AVA","AVW","BLU","CAE","CDW","CEM","DMO","EQW","EVI","FRW","HMW","LAE","LEW","NUW","RHW","RMT","RWT","SPW","TOE","VOW","BZW","CFW","DSW","EWW","FFA","FLA","FFS","FFW","FLW","HUA","HUW","HWW","SMW","SPS","SSA","SSW","SVR","SVS","TOA","TOR","TRA","TRW","TSW","WSW","EAN","NPT"]
            codeType = ["Administative Message", "Avalanche Watch", "Avalanche Warning", "Law Enforcement Blue Alert", "Child Abduction Emergency", "Civil Danger Warning", "Civil Emergency Message", "Practice/Demo Warning", "Earthquake Warning", "Evacuation Immediate", "Fire Warning", "Hazardous Materials Warning", "Local Area Emergency", "Law Enforcement Warning", "Nuclear Power Plant Warning", "Radiological Hazard Warning", "Required Monthly Test", "Required Weekly Test", "Shelter in Place Warning", "911 Telephone Outage Emergency", "Volcano Warning", "Blizzard Warning", "Coastal Flood Warning", "Dust Storm Warning", "Extreme Wind Warning", "Flash Flood Watch", "Flood Watch", "Flash Flood Statement", "Flash Flood Warning", "Flood Warning", "Hurricane Watch", "Hurricane Warning", "High Wind Warning", "Special Marine Warning", "Special Weather Statement", "Storm Surge Watch", "Storm Surge Warning", "Severe Thunderstorm Warning", "Severe Weather Statement", "Tornado Watch", "Tornado Warning", "Tropical Storm Watch", "Tropical Storm Warning", "Tsunami Warning", "Winter Storm Warning", "Presidential Alert", "National Periodic Test"]
            codeEnglish = None
            if event_value is not None and event_value in codeLetters:
                codeEnglish = codeType[codeLetters.index(event_value)]

            # Find locationCode elements considering namespace
            temp2 = ""
            temp = ""
            locationCodes = root.findall('.//cap:geocode', namespaces)
            # Traverse list of location codes
            for locationCode in locationCodes:
                valueName_element = locationCode.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'SAME':
                    value_element = locationCode.find('cap:value', namespaces)
                    if value_element is not None:
                        # Set the variable equal to the text within the value element
                        # Since this code loops, new values found are appeneded to previous values with '|' inbetween
                        temp = value_element.text  
                        loc_value = temp2 + temp + "|"
                        temp2 = loc_value 

            # Find the area desc element
            areaDesc_element = root.find('.//cap:areaDesc', namespaces)
            if areaDesc_element is not None:
                # If the area desc element is not none set the variable equal to the text in the element
                areaDesc = areaDesc_element.text
            
            StateIndex = ["02","01","05","60","04","06","08","09","11","10","12","13","66","15","19","16","17","18","20","21","22","25","24","23","26","27","29","28","30","37","38","31","33","34","35","32","36","39","40","41","42","72","44","45","46","47","48","49","51","78","50","53","55","54","56","81","64","84","86","67","89","68","71","76","69","70","95","74","79","57","58","59","61","65","73","75","77","91","92","93","94","96","97","98"]
            StateName = ["Alaska", "Alabama", "Arkansas", "American Samoa", "Arizona", "California", "Colorado", "Connecticut", "District of Columbia", "Delaware", "Florida", "Georgia", "Guam", "Hawaii", "Iowa", "Idaho", "Illinois", "Indiana", "Kansas", "Kentucky", "Louisiana", "Massachusetts", "Maryland", "Maine", "Michigan", "Minnesota", "Missouri", "Mississippi", "Montana", "North Carolina", "North Dakota", "Nebraska", "New Hampshire", "New Jersey", "New Mexico", "Nevada", "New York", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Puerto Rico", "Rhode Island", "South Carolina", "South Dakota", "Tennessee", "Texas", "Utah", "Virginia", "Virgin Islands", "Vermont", "Washington", "Wisconsin", "West Virginia", "Wyoming", "Baker Island", "Federated States of Micronesia", "Howland Island", "Jarvis Island", "Johnston Atoll", "Kingman Reef", "Marshall Islands", "Midway Islands", "Navassa Island", "Northern Mariana Islands", "Palau", "Palmyra Atoll", "U.S. Minor Outlying Islands", "Wake Island", "Pacific coast from Washington to California", "Alaskan coast", "Hawaiian coast", "American Samoa waters", "Mariana Islands waters (including Guam)", "Atlantic coast from Maine to Virginia", "Atlantic coast from North Carolina to Florida, and the coasts of Puerto Rico and Virgin Islands", "Gulf of Mexico", "Lake Superior", "Lake Michigan", "Lake Huron", "St. Clair River, Detroit River, and Lake St. Clair", "Lake Erie", "Niagara River and Lake Ontario", "St. Lawrence River"]
            if loc_value is not None:
                if len(loc_value) == 7:
                    stateCode = loc_value[1:3]
                    if stateCode in StateIndex:
                        state = StateName[StateIndex.index(stateCode)]
                    else:
                        state = None
                else:
                    stateCode = loc_value[1:3]
                    if stateCode in StateIndex:
                        state = StateName[StateIndex.index(stateCode)]
                    else:
                        state = None
                    for x in loc_value:
                        if x == '|':
                            stateCode = loc_value[loc_value.index(x) + 2 :loc_value.index(x) + 4]
                            if stateCode in StateIndex:
                                if StateName[StateIndex.index(stateCode)] not in state:
                                    state = state + "|" + StateName[StateIndex.index(stateCode)]


            # Find the area poly element
            areaPoly_element = root.find('.//cap:polygon', namespaces)
            if areaPoly_element is not None:
                # If the area poly element is not none set the variable equal to the text in the element
                areaPoly = areaPoly_element.text  
            
            # Find area circle element
            areaCircle_element = root.find('.//cap:circle', namespaces) 
            if areaCircle_element is not None:
                # If the area circle is not none set the variable equal to the text in the element
                areaCircle = areaCircle_element.text      

            # Cut signature values

            temp2 = ""
            # Find parameters considering namespace
            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                valueName_element = parameter.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'CMAMtext':
                   value_element = parameter.find('cap:value', namespaces)
                   if value_element is not None:
                        temp = value_element.text  
                        cmamValue = temp2 + temp + "|"
                        temp2 = cmamValue 

            temp2 = ""
            # Find parameters considering namespace
            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                valueName_element = parameter.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'CMAMlongtext':
                   value_element = parameter.find('cap:value', namespaces)
                   if value_element is not None:
                        cmamLongValue = value_element.text   

            temp2 = ""
            # Find resources considering namespace
            resources = root.findall('.//cap:resource', namespaces)
            # Traverse list of resources
            for resource in resources:
                # Find the resource desc element
                valueName_element = resource.find('cap:resourceDesc', namespaces)
                if valueName_element is not None:
                   # If resource desc element is not none set the variable equal to the text in the element 
                   temp = valueName_element.text  
                   resourceDesc = temp2 + temp + "|"
                   temp2 = resourceDesc

            temp2 = ""
            # Find resources considering namespace
            resources = root.findall('.//cap:resource', namespaces)
            # Traverse list of resources
            for resource in resources:
                # Find the mime type element
                valueName_element = resource.find('cap:mimeType', namespaces)
                if valueName_element is not None:
                   # If mime type element is not none set the variable equal to the text in the element  
                   temp = valueName_element.text  
                   mimeType = temp2 + temp + "|"
                   temp2 = mimeType

            temp2 = ""
            # Find parameters considering namespace
            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                valueName_element = parameter.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'EAS-ORG':
                   value_element = parameter.find('cap:value', namespaces)
                   if value_element is not None:
                        temp = value_element.text  
                        orgCode = temp2 + temp + "|"
                        temp2 = orgCode 

            temp2 = ""
            # Find parameters considering namespace
            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                valueName_element = parameter.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'timezone':
                   value_element = parameter.find('cap:value', namespaces)
                   if value_element is not None:
                        temp = value_element.text  
                        timezone = temp2 + temp + "|"
                        temp2 = timezone

            # Find parameters considering namespace
            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                valueName_element = parameter.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'AudioSource':
                   value_element = parameter.find('cap:value', namespaces)
                   if value_element is not None:
                        AudioSource = value_element.text

            # Find parameters considering namespace
            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                valueName_element = parameter.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'WEAHandling':
                   value_element = parameter.find('cap:value', namespaces)
                   if value_element is not None:
                        WEAHandling = value_element.text

            # Find parameters considering namespace
            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                valueName_element = parameter.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'EASText':
                   value_element = parameter.find('cap:value', namespaces)
                   if value_element is not None:
                        EASText = value_element.text

            # Find resources considering namespace
            resources = root.findall('.//cap:resource', namespaces)
            # Traverse list of resources
            for resource in resources:
                # Find the mime type element
                valueName_element = resource.find('cap:uri', namespaces)
                if valueName_element is not None:
                   # If mime type element is not none set the variable equal to the text in the element
                   uri = valueName_element.text


            parameters = root.findall('.//cap:parameter', namespaces)
            # Traverse list of parameters
            for parameter in parameters:
                valueName_element = parameter.find('cap:valueName', namespaces)
                if valueName_element is not None and valueName_element.text == 'DBGFBYPASS':
                   value_element = parameter.find('cap:value', namespaces)
                   if value_element is not None and value_element.text == 'TRUE':
                        DBGF = value_element.text

    #type = "image/mp3"
    #if derefuri is None:
        #State filter here (if stateFilter is not None:)
    if critical is False:
        if stateFilter is not None:
            if state is not None:
                if stateFilter.lower() in state.lower():
                    csv_data.append([id, sent, event, expires, urgency, category, headline, language, severity, certainty, senderName, description, cogId, msgType, sender, source, status, block_channel, response_type, effective, onset, instruction, web, event_value, codeEnglish, loc_value, areaDesc, state, areaPoly, areaCircle, cmamValue, cmamLongValue, resourceDesc, orgCode, timezone, AudioSource, uri, WEAHandling, EASText, DBGF])
        else:
            # Append each row in the csv file
            csv_data.append([id, sent, event, expires, urgency, category, headline, language, severity, certainty, senderName, description, cogId, msgType, sender, source, status, block_channel, response_type, effective, onset, instruction, web, event_value, codeEnglish, loc_value, areaDesc, state, areaPoly, areaCircle, cmamValue, cmamLongValue, resourceDesc, orgCode, timezone, AudioSource, uri, WEAHandling, EASText, DBGF])
    else:
        if stateFilter is not None:
            if state is not None:
                if stateFilter.lower() in state.lower():
                    csv_data.append([id, sent, senderName, description, block_channel, instruction, event_value, areaDesc, state, areaPoly, areaCircle, cmamValue, cmamLongValue, uri, WEAHandling, EASText])
        else:
            # Append each row in the csv file
            csv_data.append([id, sent, senderName, description, block_channel, instruction, event_value, areaDesc, state, areaPoly, areaCircle, cmamValue, cmamLongValue, uri, WEAHandling, EASText])

csv_df = pd.DataFrame(csv_data)

print(csv_df)

# Open and fill csv file with specified name
with open(file_name + ".csv", "w", newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    # Fill collumn headers
    if critical is False:
        writer.writerow(["id\nUniversally unique and permanent URI to identify the feed.", "sent\nThe date and time from the <sent> element when the alert message was sent.", "event\nThe text from the <event> element denoting the type of the subject event associated with the alert message.", "expires\nWhen the alert expires.", "urgency\nThe code from the <urgency> element denoting the urgency associated with the subject event of the alert message (See CAPv1.2 standard for code values).", "category\nThe code from the <category> element denoting the category associated with the subject event of the alert message (See CAPv1.2 standard for code values).", "headline\nThe text headline from the <headline> element of the alert message.", "language\nThe first <language> element for the alert message.", "severity\nThe code from the <severity> element denoting the severity associated with the subject event of the alert message (See CAPv1.2 standard for code values).", "certainty\nThe code from the <certainty> element denoting the certainty associated with the subject event of the alert message (See CAPv1.2 standard for code values).", "senderName\nThe text from the <sendername> element naming the originator of the alert message.", "description\nThe COG description associated with the COG Profile.", "cogId\nSending COG-ID – The COG-ID associated with <logonCogId> element provided in the SOAP header", "msgtype\nThe code from <msgType> element denoting the nature of the alert message (See CAPv1.2 standard for code values).", "sender\nText from the <sender> element identifying the sender for the alert message.", "source\nThe <source> value may be publicly presented as a human readable signature line in some delivery systems.", "status\nThe code from the <status> element denoting the appropriate handling of the alert message (See CAPv1.2 standard for code values).", "blockchannel\none of the following four values will restrict a message dissemination channel: 'CMAS', 'EAS', 'NWEM', 'PUBLIC'. A single or multiple channels can be blocked", "responseType\nThe code from the <responseType> element denoting the type of action for the target audience for the alert message (See CAPv1.2 standard for code values).", "effective\nThe effective time of the information of the alert message.", "onset\nThe expected time of the beginning of the subject event of the alert message.", "instruction\nThe text describing the recommended action to be taken by recipients of the alert message.", "web\nThe identifier of the hyperlink associating additional information with the alert message.", "eventCode\nThe code from the <eventCode> element identifying the event type of the alert message.", "Event Code Description\nNon abbreviated event code", "geoCode\nThe geographic code in the <geocode> element delineating the affected area of alert message.", "areaDesc\nThe text from the <areadescription> element describing the affected area of the alert message.", "state/region\nThe state in which the event was recorded was extracted from the second and third digits of the geocode using a lookup table.", "polygon\nThe paired value of points defining a polygon that delineates the affected area of the alert message.", "circle\nThe paired value of a point and radius defining a circle that delineates the affected area of the alert message.", "cmamText\nThe format for the CMAM Text is as follows: [WHAT IS HAPPENING text string] in this area [WHEN EVENT EXPIRES text string] [WHAT ACTION SHOULD BE TAKEN text string] [WHO IS SENDING THE ALERT text string]", "cmamLongText\nA non-abbreviated form of the cmamtext containing more specific information.", "resourceDesc\nThe text from the <resourceDesc> element describing the type and content of the resource file.", "eas-org\nContains the value of the originator’s SAME organization code: CIV - Civil authorities, PEP - Primary Entry Point System, EAS - Broadcast station or cable system, WXR - National Weather Service", "timezone\nContains the value of the originator’s timezone code.", "AudioSource\nIndicates whether or not there is an audio source attached to the alert.", "uri\nThe code in the <uri> element providing the hyperlink for the resource file.", "WEAHandling", "EASText", "DBGF"])
    else:
        writer.writerow(["id\nUniversally unique and permanent URI to identify the feed.", "sent\nThe date and time from the <sent> element when the alert message was sent.", "senderName\nThe text from the <sendername> element naming the originator of the alert message.", "description\nThe COG description associated with the COG Profile.", "blockchannel\none of the following four values will restrict a message dissemination channel: 'CMAS', 'EAS', 'NWEM', 'PUBLIC'. A single or multiple channels can be blocked", "instruction\nThe text describing the recommended action to be taken by recipients of the alert message.", "eventCode\nThe code from the <eventCode> element identifying the event type of the alert message.", "areaDesc\nThe text from the <areadescription> element describing the affected area of the alert message.", "state/region\nThe state in which the event was recorded was extracted from the second and third digits of the geocode using a lookup table.", "polygon\nThe paired value of points defining a polygon that delineates the affected area of the alert message.", "circle\nThe paired value of a point and radius defining a circle that delineates the affected area of the alert message.", "cmamText\nThe format for the CMAM Text is as follows: [WHAT IS HAPPENING text string] in this area [WHEN EVENT EXPIRES text string] [WHAT ACTION SHOULD BE TAKEN text string] [WHO IS SENDING THE ALERT text string]", "cmamLongText\nA non-abbreviated form of the cmamtext containing more specific information.", "uri\nThe code in the <uri> element providing the hyperlink for the resource file.", "WEAHandling", "EASText"])
    writer.writerows(csv_data)

print("Success! JSON data Converted to CSV Speadsheet '"+file_name+".csv'")

unprocessed_df = pd.read_csv(f'{file_name}.csv')

print(unprocessed_df.head())

coordinates = unprocessed_df['''polygon
The paired value of points defining a polygon that delineates the affected area of the alert message.'''] 

coordinates_list = coordinates.values.tolist()

def create_coordinates_df(coordinates_list):
    # Function to split coordinates and return as separate columns
    def split_coordinates(coordinates):
        if isinstance(coordinates, str):
            pairs = coordinates.split()  # Splitting the coordinates by space
            lats = []
            lons = []
            for pair in pairs:
                lat, lon = map(float, pair.split(','))  # Splitting each pair into latitude and longitude
                lats.append(lat)
                lons.append(lon)
            return lats, lons
        else:
            return [], []

    # Initialize empty lists to store latitudes and longitudes
    all_latitudes = []
    all_longitudes = []

    # Splitting coordinates into separate columns for each row
    for coordinates in coordinates_list:
        latitudes, longitudes = split_coordinates(coordinates)
        all_latitudes.append(latitudes)
        all_longitudes.append(longitudes)

    # Identify the maximum number of pairs across all rows
    max_pairs = max(len(latitudes) for latitudes in all_latitudes)

    # Create DataFrame with dynamic column names
    data = {}
    for j in range(1, max_pairs + 1):
        lat_col_name = f'lat{j}'
        lon_col_name = f'lon{j}'
        latitudes = []
        longitudes = []
        for latitudes_row, longitudes_row in zip(all_latitudes, all_longitudes):
            if len(latitudes_row) >= j:
                latitudes.append(latitudes_row[j - 1])
                longitudes.append(longitudes_row[j - 1])
            else:
                latitudes.append(np.nan)
                longitudes.append(np.nan)
        data[lat_col_name] = latitudes
        data[lon_col_name] = longitudes

    return pd.DataFrame(data)

coordinates_df = create_coordinates_df(coordinates_list)

# Splitting all geocodes
geocodes = unprocessed_df['''geoCode
The geographic code in the <geocode> element delineating the affected area of alert message.'''].str.split('|',expand=True)

geocodes.columns = [f'geocode_{i+1}' for i in range(geocodes.shape[1])]

# Splitting all areaDescs
areaDescs = unprocessed_df['''areaDesc
The text from the <areadescription> element describing the affected area of the alert message.'''].str.split('; ',expand=True)

areaDescs.columns = [f'areaDesc_{i+1}' for i in range(areaDescs.shape[1])]

cleaned_df = pd.concat([unprocessed_df, coordinates_df, geocodes, areaDescs], axis=1)

cleaned_file_path = f'{file_name}_for_mapping.csv'

cleaned_df.to_csv(cleaned_file_path,index=False)