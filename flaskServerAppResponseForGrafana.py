import requests
import json
import time
import string
from flask import Flask
from flask import jsonify
from flask import request
from calendar import timegm
from datetime import datetime
# Lines containing critical informations : 17 18 19 + very last line (port)
#########################################################################################################################
##                                                                                                                     ##
##                                                 Initializing server                                                 ##
##                                                                                                                     ##
#########################################################################################################################
# Riverbed AppResponse probe's address and credentials
HOST = ""
USERNAME = ""
PASSWORD = ""
userCredentials = {
    "user_credentials":
        {
            "username":USERNAME, "password":PASSWORD
        },
    "generate_refresh_token": False
}
# Creating instance of Flask (e.g app)
serverFlask = Flask(__name__)
# Session is used for SSL overriding
session = requests.Session()
# Variables for buffering all lists returned to Grafana (refreshed if 120s elapsed) exepting FamilyPageList
lastTimeHostGroupListHasBeenPicked = 0
hostGroupsList = []
lastTimeApplicationsListHasBeenPicked = 0
applicationsList = []
lastTimeWebAppsListHasBeenPicked = 0
webAppsList = []
lastTimemetricsHostGroupListHasBeenPicked = 0
metricsHostGroupList = []
lastTimeMetricsApplicationListHasBeenPicked = 0
metricsApplicationList = []
lastTimeMetricsWebAppListHasBeenPicked = 0
metricsWebAppList = []
# Variable for Pagefamilies query
globalAllRowSourceIDs = [0]*26


#########################################################################################################################
##                                                                                                                     ##
##                                              FUNCTIONS DECLARATION                                                  ##
##                                                                                                                     ##
#########################################################################################################################
# Authentication function
# Argument credentials = object with credentials
def tryAuthentication(credentials):
    # Converting credentials to JSON format
    dataLogsJSON = json.dumps(credentials)
    # URL to connect API's authentication system
    urlLogin = 'https://'+HOST+'/api/mgmt.aaa/1.0/token'
    # Sending request for authentication (without SSL certificate check)
    r = session.post(urlLogin, dataLogsJSON, verify=False)
    return r


# Refresh token function
# Argument credentials = object with credentials
def getNewToken(credentials):
    reponse = tryAuthentication(credentials)
    dictionnaire = reponse.json()
    # On extrait le token
    token = dictionnaire['access_token']
    return token


# POST request function (creation of instances e.g reports)
# Argument credentials = object with credentials
# Argument dataDefJSON = data definitions in JSON format (=metric query)
def createSyncInstance(credentials, dataDefJSON):
    global currentToken
    # URL to connect API's report creation system
    urlPOSTsync = 'https://'+HOST+'/api/npm.reports/1.0/instances/sync'
    # Adding token to headers for Riverbed access
    headers = {"Authorization": "Bearer "+ currentToken}
    response = session.post(urlPOSTsync, dataDefJSON, headers=headers, verify=False)
    # If token is expired get a brand new token
    if response.status_code == 401:
        currentToken = getNewToken(credentials)
        headers = {"Authorization": "Bearer "+ currentToken}
        response = session.post(urlPOSTsync, dataDefJSON, headers=headers, verify=False)
    return response


# GET request function (collect informations through API : hostgroups, applications, webapps...)
# Argument credentials = object with credentials
# Argument url = API's url
def retrieveInformationFromAPI(credentials, url):
    global currentToken
    # Adding token to headers for Riverbed access
    headers = {"Authorization": "Bearer "+ currentToken}
    # Querying Riverbed AppResponse
    response = session.get(url, headers=headers, verify=False)
    # If token is expired get a brand new token
    if response.status_code == 401:
        currentToken = getNewToken(credentials)
        headers = {"Authorization": "Bearer "+ currentToken}
        response = session.get(url, headers=headers, verify=False)
    # Returning server's response, containing all data returned by API
    return response


# Time converting to epoch time format (seconds elapsed from 1970)
def convert_to_epoch(timestamp):
    return timegm(datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').timetuple())


# Get the very first token (server initilization)
currentToken = getNewToken(userCredentials)

#########################################################################################################################
##                                                                                                                     ##
##                                                     HEALTH TEST                                                     ##
##                                                                                                                     ##
#########################################################################################################################
# Response when adding new datasource in Grafana, must return a 200 http_code to be accepted
@serverFlask.route("/", methods = ['GET'])
def healthTest():
    return "OK"


#########################################################################################################################
##                                                                                                                     ##
##                                          HOST_GROUPS LIST RETRIEVING                                                ##
##                                                                                                                     ##
#########################################################################################################################
@serverFlask.route("/getHost_group", methods = ['POST'])
def getHost_group():
    global lastTimeHostGroupListHasBeenPicked
    global hostGroupsList
    # If it has been less than 120 seconds since the last creation of the hostGroupsList, no query is made to Riverbed's API
    timeIsHostGroupsListOutdated = round((time.time() - lastTimeHostGroupListHasBeenPicked),0)
    if timeIsHostGroupsListOutdated < 120 :
        return jsonify(hostGroupsList)
    else :
        global currentToken
        # API for host_groups retrieving
        urlGET = 'https://'+HOST+'/api/npm.classification/2.0/hostgroups'
        # Retrieving hostgroups
        response = retrieveInformationFromAPI(userCredentials, urlGET)
        # Making a dict to easly access to the listing part
        dictionnaire = json.loads(response.text)
        # Field 'items' contains all host groups (name and id)
        valeurs = dictionnaire['items']
        hostGroupsList= []
        # For each host group, if enabled, add object{name, id} (angular will interpret it, user click on name but JS retrieves id) 
        for value in valeurs:
            if value["enabled"] :
                hostGroupsList.append({'text': value["name"], 'value':str(value['id'])})
        lastTimeHostGroupListHasBeenPicked = time.time()
        return jsonify(hostGroupsList)


#########################################################################################################################
##                                                                                                                     ##
##                                          APPLICATIONS LIST RETRIEVING                                               ##
##                                                                                                                     ##
#########################################################################################################################
@serverFlask.route("/getApplicationOptions", methods = ['POST'])
def getApplicationOptions():
    global lastTimeApplicationsListHasBeenPicked
    global applicationsList
    # If it has been less than 120 seconds since the last creation of the applicationsList, no query is made to Riverbed's API
    timeIsApplicationsListOutdated = round((time.time() - lastTimeApplicationsListHasBeenPicked),0)
    if timeIsApplicationsListOutdated < 120 :
        return jsonify(applicationsList)
    else :
        global currentToken
        # API for applications retrieving
        urlGET = 'https://'+HOST+'/api/npm.classification/2.0/applications'
        # Retrieving applications
        response = retrieveInformationFromAPI(userCredentials, urlGET)
        # Making a dict to easly access to the listing part
        parsed = json.loads(response.text)
        # Field 'items' contains all applications (name and id)
        valeurs = parsed['items']
        applicationsList= []
        # For each application, if enabled, add object{name, id} (angular will interpret it, user click on name but JS retrieves id)
        for value in valeurs:
            if value["enabled"] :
                applicationsList.append({'text': value["name"], 'value':str(value['id'])})
        lastTimeApplicationsListHasBeenPicked = time.time()
        return jsonify(applicationsList)


#########################################################################################################################
##                                                                                                                     ##
##                                          WEBAPPS LIST RETRIEVING                                                    ##
##                                                                                                                     ##
#########################################################################################################################
@serverFlask.route("/getWebAppOptions", methods = ['POST'])
def getWebAppOptions():
    global lastTimeWebAppsListHasBeenPicked
    global webAppsList
    # If it has been less than 120 seconds since the last creation of the webAppsList, no query is made to Riverbed's API
    timeIsWebAppsListOutdated = round((time.time() - lastTimeWebAppsListHasBeenPicked),0)
    if timeIsWebAppsListOutdated < 120 :
        return jsonify(webAppsList)
    else :
        global currentToken
        # API for WebApps retrieving
        urlGET = 'https://'+HOST+'/api/npm.wta_config/1.0/wta_webapps'
        # Retrieving WebApps
        response = retrieveInformationFromAPI(userCredentials, urlGET)
        # Making a dict to easly access to the listing part
        parsed = json.loads(response.text)
        # Field 'items' contains all WebApps (name and id)
        valeurs = parsed['items']
        webAppsList= []
        # For each WebApp, add object{name, id} (angular will interpret it, user click on name but JS retrieves id)
        for value in valeurs:
            webAppsList.append({'text': value["name"], 'value':str(value['id'])})
        lastTimeWebAppsListHasBeenPicked = time.time()
        return jsonify(webAppsList)


#########################################################################################################################
##                                                                                                                     ##
##                                          METRICS LIST RETRIEVING                                                    ##
##                                                                                                                     ##
#########################################################################################################################
# Metrics for hostgroups
@serverFlask.route("/metricsHG", methods = ['POST'])
def metricsHG():
    global lastTimemetricsHostGroupListHasBeenPicked
    global metricsHostGroupList
    # If it has been less than 120 seconds since the last creation of the metricsHostGroupList, no query is made to Riverbed's API
    timeIsMetricsHostGroupListOutdated = round((time.time() - lastTimemetricsHostGroupListHasBeenPicked),0)
    if timeIsMetricsHostGroupListOutdated < 120 :
        return jsonify(metricsHostGroupList)
    else :
        global currentToken
        # API for aggregate metrics retrieving
        urlGET = 'https://'+HOST+'/api/npm.reports.sources/1.0/sources/items/aggregates'
        # Retrieving metrics for aggregate source type
        response = retrieveInformationFromAPI(userCredentials, urlGET)
        # Making a dict to easly access to the listing part
        parsed = json.loads(response.text)
        # Field 'columns' contains metrics
        valeurs = parsed['columns']
        metricsHostGroupList= []
        # Pushing metrics in array, exepting not calculable metrics and not RTP metrics (not relevant)
        for value in valeurs:
            if  not value["id"].endswith('.id') and not value["id"].endswith('_id') and \
                not value["id"].endswith('.name') and not value["id"].endswith('_name') and \
                not value["id"].endswith('.ip') and not value["id"].endswith('_ip') and \
                not value["id"].endswith('.dns') and not value["id"].endswith('_dns') and \
                not value["id"].endswith('.type') and not value["id"].endswith('_type') and \
                not value["id"].endswith('start_time') and not value["id"].endswith('end_time') and \
                not "rtp" in value["id"]:
                # If metric has no unit then diplay 'occurence' instead of 'none'
                if value["unit"]=='none':
                    unit = 'occurence'
                else :
                    unit = value["unit"]
                # If rate is available display unit/rate
                try:
                    # For each metric, add object{label (unit/rate), id} (angular will interpret it, user click on name but JS retrieves id)
                    metricsHostGroupList.append({'text': value["label"]+"  ("+unit+"/"+value["rate"]+")", 'value':value['id']})
                # Else just display unit
                except KeyError as e:
                    # or add object{label (unit), id} if rate is not applicable (angular will interpret it, user click on name but JS retrieves id)
                    metricsHostGroupList.append({'text': value["label"]+"  ("+unit+")", 'value':value['id']})
                # only id displayed : 
                # metricsHostGroupList.append([value["id"], value['unit']])
        lastTimemetricsHostGroupListHasBeenPicked = time.time()
        return jsonify(metricsHostGroupList)


# Metrics for application
@serverFlask.route("/metricsApplication", methods = ['POST'])
def metricsApplications():
    global lastTimeMetricsApplicationListHasBeenPicked
    global metricsApplicationList
    # If it has been less than 120 seconds since the last creation of the metricsApplicationList, no query is made to Riverbed's API
    timeIsMetricsApplicationListOutdated = round((time.time() - lastTimeMetricsApplicationListHasBeenPicked),0)
    if timeIsMetricsApplicationListOutdated < 120 :
        return jsonify(metricsApplicationList)
    else :
        global currentToken
        # API for aggregate metrics retrieving
        urlGET = 'https://'+HOST+'/api/npm.reports.sources/1.0/sources/items/aggregates'
        # Retrieving metrics for aggregate
        response = retrieveInformationFromAPI(userCredentials, urlGET)
        # Making a dict to easly access to the listing part
        parsed = json.loads(response.text)
        # Field 'columns' contains metrics
        valeurs = parsed['columns']
        metricsApplicationList= []
        # Pushing metrics in array, exepting not calculable metrics and not RTP, web (not relevant)
        for value in valeurs:
            if  not value["id"].endswith('.id') and not value["id"].endswith('_id') and \
                not value["id"].endswith('.name') and not value["id"].endswith('_name') and \
                not value["id"].endswith('.ip') and not value["id"].endswith('_ip') and \
                not value["id"].endswith('.dns') and not value["id"].endswith('_dns') and \
                not value["id"].endswith('.type') and not value["id"].endswith('_type') and \
                not value["id"].endswith('start_time') and not value["id"].endswith('end_time') and \
                not "rtp" in value["id"] and not "web" in value["id"] and \
                not "p2m" in value["id"] and not "m2p" in value["id"] : 
                # If metric has no unit then diplay 'occurence' instead of 'none'
                if value["unit"]=='none':
                    unit = 'occurence'
                else :
                    unit = value["unit"]
                # If rate is available display unit/rate
                try:
                    # For each metric, add object{label (unit/rate), id} (angular will interpret it, user click on name but JS retrieves id)
                    metricsApplicationList.append({'text': value["label"]+"  ("+unit+"/"+value["rate"]+")", 'value':value['id']})
                # Else just display unit
                except KeyError as e:
                    # or add object{label (unit), id} if rate is not applicable (angular will interpret it, user click on name but JS retrieves id)
                    metricsApplicationList.append({'text': value["label"]+"  ("+unit+")", 'value':value['id']})
        lastTimeMetricsApplicationListHasBeenPicked = time.time()
        return jsonify(metricsApplicationList)


# Metrics for WebApps
@serverFlask.route("/metricsWebApp", methods = ['POST'])
def metricsWebbApp():
    global lastTimeMetricsWebAppListHasBeenPicked
    global metricsWebAppList
    # If it has been less than 120 seconds since the last creation of the metricsHostGroupList, no query is made to Riverbed's API
    timeIsMetricsWebAppListOutdated = round((time.time() - lastTimeMetricsWebAppListHasBeenPicked),0)
    if timeIsMetricsWebAppListOutdated < 120 :
        return jsonify(metricsWebAppList)
    else :
        
        global currentToken
        # API for aggregate metrics retrieving
        urlGET = 'https://'+HOST+'/api/npm.reports.sources/1.0/sources/items/aggregates'
        # Retrieving metrics for aggregates
        response = retrieveInformationFromAPI(userCredentials, urlGET)
        # Making a dict to easly access to the listing part
        parsed = json.loads(response.text)
        # Field 'columns' contains metrics
        valeurs = parsed['columns']
        metricsWebAppList= []
        # Pushing metrics in array, exepting not calculable metrics
        print("Ajout des valeurs de Riverbed dans un JSON")
        for value in valeurs:
            if  not value["id"].endswith('.id') and not value["id"].endswith('_id') and \
                not value["id"].endswith('.name') and not value["id"].endswith('_name') and \
                not value["id"].endswith('.ip') and not value["id"].endswith('_ip') and \
                not value["id"].endswith('.dns') and not value["id"].endswith('_dns') and \
                not value["id"].endswith('.type') and not value["id"].endswith('_type') and \
                not value["id"].endswith('start_time') and not value["id"].endswith('end_time') and \
                "web" in value["id"] :
                # If metric has no unit then diplay 'occurence' instead of 'none'
                if value["unit"]=='none':
                    unit = 'occurence'
                else :
                    unit = value["unit"]
                # If rate is available display unit/rate
                try:
                    # For each metric, add object{label (unit/rate), id} (angular will interpret it, user click on name but JS retrieves id)
                    metricsWebAppList.append({'text': value["label"]+"  ("+unit+"/"+value["rate"]+")", 'value':value['id']})
                # Else just display unit
                except KeyError as e:
                    # or add object{label (unit), id} if rate is not applicable (angular will interpret it, user click on name but JS retrieves id)
                    metricsWebAppList.append({'text': value["label"]+"  ("+unit+")", 'value':value['id']})
        lastTimeMetricsWebAppListHasBeenPicked = time.time()
        return jsonify(metricsWebAppList)


#########################################################################################################################
##                                                                                                                     ##
##                                          FAMILY PAGES LIST RETRIEVING                                               ##
##                                                                                                                     ##
#########################################################################################################################
# Cannot get page.family.id from API, getting all pages requested for 24 hours (large granularity for light query)
@serverFlask.route("/getPageFamilyOptions", methods = ['POST'])
def getPageFamilyOptions():
    # This global variable is set when picking a source in /query
    global globalAllRowSourceIDs
    # Retrieving JSON from Grafana in order to extract row letter (and number)
    grafanaData = request.get_json()
    # Letter from Grafana's row (converted to integer, alphabetical position)
    currentRowLetter = grafanaData['target'].lower()
    currentRowNumber = string.lowercase.index(grafanaData['target'].lower())
    sourceID = globalAllRowSourceIDs[currentRowNumber]
    if sourceID == 0:
        return "0"

    dataDefs = {'data_defs': [
        {
            "source": {
                "origin": "",
                "path": 'aggregates:App',
                "type": "",
                "name": "aggregates"
            },
            "time": {
                "duration": "last 24 hours",
                "granularity": "86400",
            },
            "group_by": [
                "start_time",
                "app.id"
            ],
            "columns": [
                "app.name",
                "app.id",
                "start_time",
                "sum_web.pages",
                "web.page.family.id",
                "web.page.family.name"
            ],
            "filters": [
                {
                "value": "app.id == "+sourceID,
                "type": "STEELFILTER",
                "id": "rowFilter"
            }]
        }
    ]}

    # dataDefs to json conversion 
    dataDefsJSON = json.dumps(dataDefs)
    # Sending request and credentials to Riverbed
    responseSync = createSyncInstance(userCredentials, dataDefsJSON)
    # Response is parsed in order to access some fields
    parsed = json.loads(responseSync.text)
    # Trying to get results, if no result returns '0'
    try:
        allPageFamily = parsed['data_defs'][0]["data"]
    except KeyError as e:
        return "0"
    
    # Resetting the list in case of multiple page family row
    pageFamilyList = []
    for eachPageFamily in allPageFamily:
        # position in array from 0 to 5 : app.name, app.ip, timestamp, page.views, page.family.id, page.family.name
        pageID = str(eachPageFamily[4])
        pagename = str(eachPageFamily[5])
        # encoding is 99% sure useless
        pagename = pagename.encode()
        pagename.encode(encoding="ascii",errors="backslashreplace")
        # Keep both id and name, id will be extracted in /query
        pageFamilyIDandName = pagename + '@' + pageID
        pageFamilyList.append(pageFamilyIDandName)
    return jsonify(pageFamilyList)


#########################################################################################################################
##                                                                                                                     ##
##                 RETRIEVING GRAFANA'S JSON && SENDING TO RIVERBED && SENDING RIVERBED RESPONSE                       ##
##                                                                                                                     ##
#########################################################################################################################
@serverFlask.route("/query", methods = ['POST'])
def query():
                            ##################################################################
                            ##                 Gathering Grafana's data                     ##
                            ##################################################################
    # This global variable is dedicated to page family gathering (route /getPageFamilyOptions")
    # It contains all of  (route /getPageFamilyOptions")
    global globalAllRowSourceIDs
    # List returned to Grafana, contains results
    dataPointsForGrafana = []
    # Variable for debug purpose, distinguishing value 0 and no value
    notDEFINEalarm = 0

    # Catch the JSON sent by Grafana 
    grafanaFieldsForQuery = request.get_json()

    # If you need to debug, enable this 3 lines, show JSON sent by Grafana to Python endpoint
    # print('\n\n\n###### BEGIN : JSON BUILT BY GRAFANA #######')
    # print(json.dumps(grafanaFieldsForQuery, indent=4, sort_keys=True))
    # print('###### END : JSON BUILT BY GRAFANA #######\n\n\n')

    # For each row of Grafana query (A, B, C, D...)
    for currentTarget in grafanaFieldsForQuery['targets']:

        # RefId is identification for one row in Grafana (A, B, C ...) automaticly created by Grafana
        grafanaRefId = currentTarget['refId']
        grafanaRefIdNumber = string.lowercase.index(grafanaRefId.lower())

        # sourceID is one of host_group.id, app.id (default is '')
        try:
            sourceID = currentTarget['targetID']
        except KeyError as e:
            continue
        
        globalAllRowSourceIDs[grafanaRefIdNumber] = sourceID

        # SourceType is one of Host_group, Application, Application/HG, WebApp or PageFamily (combobox)
        sourceType = currentTarget['type']

        # Retrieving times queried from Grafana's JSON (string epoch format needed)
        queryTimeFrom = str(convert_to_epoch(grafanaFieldsForQuery['range']['from']))
        queryTimeTo = str(convert_to_epoch(grafanaFieldsForQuery['range']['to']))

        # Retrieving metric queried by Grafana (default is '')
        metricQueried = currentTarget['metricID']

        # Retrieving specified granularity, if granularity has not been set yet, the query is not ready (moving to next target . . .)
        try:
            granularityQueried = str(currentTarget['granularity'])
        except KeyError as e:
            granularityQueried = ''
        if granularityQueried == '':
            continue    

                            ##################################################################
                            ##                 Building AppResponse query                   ##
                            ##################################################################
        # Declaring all fields needed for a Riverbed creating instance request (data_defs)
        # If query is not ready, we stop here for this currentTarget, or Grafana will crash (due to Python error, route gives err500)
        if sourceType == 'Host group':
            # A host group query requires both a source and a metric (granularity has already been checked)
            if sourceID == '' or metricQueried == '':
                continue
            tableauSource = {
                        "name": "aggregates"
                    }
            tableauGroupBy = ["start_time", "host_group.id"]
            tableauColumns = ["start_time", "host_group.id", "host_group.name", metricQueried]
            filters_value1= "host_group.id == "+sourceID
            # filters_value2 is only used in  Application/HG query
            filters_value2=""

        if sourceType == "Application" :
            # A application query requires both a source and a metric (granularity has already been checked)
            if sourceID == '' or metricQueried == '':
                continue
            tableauSource = {
                        "name": "aggregates"
                    }
            tableauGroupBy = ["start_time", "app.id"]
            tableauColumns = ["start_time", "app.id", "app.name", metricQueried]
            filters_value1= "app.id == "+sourceID
            # filters_value2 is only used in  Application/HG query
            filters_value2=""

        if sourceType == "Application/HG" :
            # A Application/HG query requires both a source (application), another source (host group) ,and a metric (granularity has already been checked)
            if sourceID == '' or metricQueried == '' or currentTarget['secondTargetID'] =='':
                continue
            tableauSource = {
                        "name": "aggregates"
                    }
            tableauGroupBy = ["start_time", "app.id"]
            tableauColumns = ["start_time", "app.id", "app.name", metricQueried]
            filters_value1= "app.id == "+sourceID
            filters_value2= "host_group.id == "+currentTarget['secondTargetID']

        if sourceType == 'WebApp':
            # A WebApp query requires both a source and a metric (granularity has already been checked)
            if sourceID == '' or metricQueried == '':
                continue
            tableauSource = {
                        "origin": "",
                        "path": "aggregates:App",
                        "type": "",
                        "name": "aggregates"
                    }
            tableauGroupBy = ["start_time", "app.id"]
            tableauColumns = ["start_time", "app.id", "app.name", metricQueried]
            filters_value1= "app.id == "+sourceID
            # filters_value2 is only used in  Application/HG query
            filters_value2=""
        if sourceType == 'PageFamily':
            familyPageID = currentTarget['pageFamilyID']
            # Extracting id
            familyPageID = familyPageID.split('@')
            familyPageID=familyPageID[1]
            # A PageFamily query requires both a source (id of page), and a metric (granularity has already been checked)
            if metricQueried == '' or familyPageID =='':
                continue
            tableauSource = {
                        "origin": "",
                        "path": "aggregates:App",
                        "type": "",
                        "name": "aggregates"
                    }
            tableauGroupBy = ["start_time", "app.id"]
            tableauColumns = ["start_time", "app.id", "app.name", metricQueried]
            filters_value1= "web.page.family.id == "+familyPageID
            filters_value2=""

        # Implementing fields in data definition for Riverbed
        # Commentaries of the following object come from Riverbed support's documentation
        # The data definition (request) has the following properties: source, time, group_by, and filters
        dataDefs = {'data_defs': [
            {
                # Data source to handle the data request. The source property is an object
                # It has the following required sub-properties: name (required) and path (optional)
                'source': tableauSource,
                # Specify the time duration of the data requests
                # The time property also includes a few properties that help refine time-series requests.
                "time": {
                    # Epoch start time of the request, the start time is inclusive, the unit is seconds.
                    "start": queryTimeFrom,
                    # Epoch end time of the request, the end time is exclusive, the unit is seconds.
                    "end":  queryTimeTo,
                    # This refers to the amount of time for which the data source computes a summary of the metrics it received
                    # The data source examines all data and creates summaries for 1 minute, 5 minutes, 1 hour, 6 hours, and 1 day
                    'granularity' : granularityQueried,
                },
                # The group by property specifies the keys in the request. It is usually used to determine what kind of data is requested
                # If the start_time (or end_time) column is in the group_by, then the request is considered time series
                "group_by": tableauGroupBy,
                # Request columns, the client can specify the requested key/metric columns, as well as their order
                "columns": tableauColumns,
                # The filters property is an array with filter objects (STEELFILTER is default filter)
                "filters": [
                        {
                            "type": "STEELFILTER",
                            "value": filters_value1
                        },
                        {
                            "type": "STEELFILTER",
                            "value": filters_value2
                        } ]
        }]}

        # Converting data_defs in JSON, JSON format is required by Riverbed AppResponse server
        dataDefsJSON = json.dumps(dataDefs)
        
        # Query is now ready to be sent to RiverBed AppResponse probe

        # Measuring time needed to Riverbed for datapoints collection (if time>50s then sync mode returns no data but still continue to collect data queried)
        # Important thing is, datapoints collection is still running, even if API does not return the result (when collection is over, datapoints can be manually retrieve with instance ID)
        # Multiple request > 50s may overload the probe, keep it in mind
        timeSyncStart = time.time()
        # Sending datadefs to Riverbed and waiting for response
        syncReportFromRiverbed = createSyncInstance(userCredentials, dataDefsJSON)
        # Save collection time, if no datapoints are found in 'syncReportFromRiverbed' then timeToCollection will be check [NOT IMPLEMENTED]
        timeToCollection = round((time.time() - timeSyncStart),2)

# If you need to debug, enable this 3 lines, showing JSON results sent by AppResponse
        # print('\n\n\n###### DEBUT RIVERBED JSON #######')
        # print(json.dumps(syncReportFromRiverbed.json(), indent=4, sort_keys=True))
        # print('###### FIN RIVERBED JSON #######\n\n\n')


                            ##################################################################
                            ##                 Gathering AppResponse's data                 ##
                            ##################################################################
        # Response is parsed in order to access some fields
        parsedReport = json.loads(syncReportFromRiverbed.text)

        # WORKING BUT NO MORE DIFFERENCE BETWEEN VALUE=0 AND NO VALUE
        # Get it off for debug purpose
        try:
            parsedReport["data_defs"][0]['data']
        except KeyError as e:
            print("##### NO DATA POINT #####")
            continue

        # caption will be the curve's caption
        caption = parsedReport["data_defs"][0]['data'][0][2]

        # Label contains both caption and metric name
        label = caption +' : '+ metricQueried

        # valeurs is a list containing summary data from Riverbed AppResponse probe
        valeurs = parsedReport["data_defs"][0]['data']

        # Datapoint is a list which will receive all datapoints in correct format [value, timestamp]
        datapoints = []

        # Filling datapoints
        for value in valeurs:
            # Timestamp is at position value[0] in unicode type, converting to int in milliseconde (*1000)
            # Adding 60 seconds to synchronize probe's clock and Grafana's clock
            timeStampInteger= (int(value[0])+60)*1000

            # Depending to the format of the result
            if type(value[3]) == type(unicode()) :
                try:
                    # Change unicode to float
                    res = float(value[3])
                except ValueError as e:
                    # Encountering '#N/D' which means data cannot be retrieved
                    notDEFINEalarm = 1
                    res = 0
            # Change int to float
            if type(value[3]) == type(int()) :
                res = float(value[3])
            # Change string to float 
            if type(value[3]) == type(str()) :
                res = float(value[3])
            # No change if float encountered
            if type(value[3]) == type(float()) :
                res = value[3]
            # Adding couple [value, timestamp] to datapoints list
            datapoints.append([res,timeStampInteger])

        # Object representating each row's of Grafana (contains caption, meta informations, row's id, collection time, and datapoints)
        newTarget = {
                # target is curve's caption
                "target": label,
                # meta is miscellaneous informations
                "meta" :   { 'info 1' : "nothing"},
                # refId is the letter of the row (A, B, C, D ...)
                'refId' :  grafanaRefId,
                # collectionTime is the time needed to complete the query, sync must be <50 [REQUIRE MORE THAN DATASOURCE PLUGIN TO BE USEFUL]
                'collection time' : timeToCollection,
                # datapoints is a list containing all points retrieved by Riverbed AppResponse probe
                "datapoints": datapoints    
                }
        # Each target (or row) is insert into a list (will be send to Grafana)
        dataPointsForGrafana.append(newTarget)
 
    # For debug purpose, warning if not define encountered
    if notDEFINEalarm == 1 :
        print('################################# <NOT DEFINE> =  <#N/D> ALARM ################################################')

    # Finaly, sending data to Grafana in JSON format
    return jsonify(dataPointsForGrafana) 

# Server started, accepts external connection on port 0000, debug set to false in oreder to avoid security issue
if (__name__ == "__main__"):
    serverFlask.run(host = '0.0.0.0', port = 0000, debug=False)