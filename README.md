# przepisyCBV_REST

To make app works with docker-compose add these files to main folder (where docker-compose is located)

- .env (information needed for django settings to connect with db) with:  

DB_NAME = <dbname>  
DB_USER = <dbuser>  
DB_PASS = <dbpass>  
DB_HOST = 'db'  

- .env.db (information needed for postgres to startup) with:  
POSTGRES_DB=<dbname>  
POSTGRES_USER=<dbuser>  
POSTGRES_PASSWORD=<dbpass>  
  
Database location is mounted direclty to 'db' folder inside main folder
