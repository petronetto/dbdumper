# PostgreSQL Export/Import scripts
Uses a PostgreSQL Docker image and opens a SSH tunnel to dump and import the whole database.

### Installation
```sh
pip install -r requirements.txt
```
Then configure the necessary credentials at the .env

### Export
```sh
python exporter.py --dbname=my-db-name --tunnel
```

### Import
```sh
python importer.py --dumpfile=my-dumpfile.dump
```