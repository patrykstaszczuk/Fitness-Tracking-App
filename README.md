# przepisyCBV_REST

To make app works with docker-compose add these files to main folder (where docker-compose is located)

- .env (information needed for django settings to connect with db) with:  <br />

DB_NAME=yourdbname <br />
DB_USER=youdbuser <br />
DB_PASS=yourdbpass <br />
DB_HOST='db'  <br />

- .env.db (information needed for postgres to startup) with: <br /> 
POSTGRES_DB=yourdbname  <br />
POSTGRES_USER=yourdbuser <br />
POSTGRES_PASSWORD=yourdbpass  <br />
  
Database location is mounted direclty to 'db' folder inside main folder
