## Riverbed AppResponse Datasource

More documentation about datasource plugins can be found in the [Docs](https://github.com/grafana/grafana/blob/master/docs/sources/plugins/developing/datasources.md).


## Installation

Add your connexion information in the Python script (credentials, adress, port).
    *Specify your AppResponse server's port at the very last line of the script.
    *Specify your AppResponse server's adresse at line 17.
    *Specify your USERNAME and PASSWORD at line 18 and 19.
Rebuild /dist with command 'npm run build'.
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