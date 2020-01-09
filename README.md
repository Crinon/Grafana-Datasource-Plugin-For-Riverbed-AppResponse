# WARNING : A new plugin has been released, the new one does not require any Python server 

# Grafana-Datasource-Plugin-For-Riverbed-AppResponse
This datasource plugin allows Grafana to submit requests to Riverbed SteelCentral AppResponse.
Use Python Flask environnement server to run the Python script.

As of 21 august 2019, this plugin does not suffer from any known bug.

Careful, this plugin use synchrone API report creation. This means that if your request is more than 50 seconds long, the panel won't display any data, but your AppResponse server will still continue to process your request.
Please increase granularity to shorten your request time.


More documentation about datasource plugins can be found in the [Docs](https://github.com/grafana/grafana/blob/master/docs/sources/plugins/developing/datasources.md).

## Installation

Add your connexion information in the Python script (credentials, adress, port).

   *Specify your AppResponse server's port at the very last line of the script.
   
   *Specify your AppResponse server's adresse at line 17.
   
   *Specify your USERNAME and PASSWORD at line 18 and 19.
   
Rebuild /dist folder with command ```npm run build```.

Place the folder 'mgent-AppResponse-json-datasource' in your Grafana's plugin folder.

Restart grafana-server.

Run a Python Flask environnement and run the script.


### Dev setup

This plugin requires node 6.10.0

```
npm install -g yarn
yarn install
npm run build
```

### Changelog

1.0.0
- Release


CRINON Nicolas ncrinon@mgen.fr
