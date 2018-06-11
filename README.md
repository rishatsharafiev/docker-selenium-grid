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

### Shared memory in docker container
Add docker daemon config option
```
nano /etc/docker/daemon.json
{
"default-shm-size": "2G"
}
```

Restart docker
```
systemctl restart docker
```

Check out new shared memory size whitin container
```
docker run -it alpine /bin/sh
df -h | grep /dev/shm # shm 2.0G 0 2.0G 0% /dev/shm
```
