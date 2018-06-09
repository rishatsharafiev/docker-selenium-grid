# Selenium Grid Cluster

### TODO
- install docker
- install docker-machine
- environment initialization
- server configuration
- create machines

### PostgreSQL Database
# https://medium.com/coding-blocks/creating-user-database-and-adding-access-on-postgresql-8bfcd2f4a91e
```
su - postgres
createuser ra
createdb ra
psql
alter user ra with encrypted password 'ra';
grant all privileges on database ra to ra ;
\q
```
