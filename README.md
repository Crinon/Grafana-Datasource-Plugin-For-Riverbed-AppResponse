# Grafana-Datasource-Plugin-For-Riverbed-AppResponse
This datasource plugin allow Grafana to submit requests to Riverbed SteelCentral AppResponse.
Use Python Flask environnement server to run the Python script.

As of 21 august 2019, this plugin does not suffer from any known bug.

Careful, this plugin use synchrone API report creation. This means that if your request is more than 50 seconds long, the panel won't display any data, but your AppResponse server will still continue to process your request.
Please increase granularity to shorten your request time.

Specify your AppResponse server's adress at the very last line of the script.
Specify your USERNAME and PASSWORD line 18 and 19.
