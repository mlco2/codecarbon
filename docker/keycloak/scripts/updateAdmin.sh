#!/bin/bash -e
cd $JBOSS_HOME/bin

# Connection
./kcadm.sh config credentials \
    --server http://localhost:8080/auth \
    --realm master --user admin
    
set -x

# Get UUID of admin user
ADMIN_ID=$(./kcadm.sh get users -q username=admin --fields "id" --format csv --noquotes)

# Update user 
./kcadm.sh update users/$ADMIN_ID \
    -r master \
    -s 'firstName="admin"' \
    -s 'lastName="admin"' \
    -s 'email="admin.admin@localdomain"'

#Create user 
./kcadm.sh create users -s email=test@test -s firstName=test -s enabled=true -r CodeCarbon
./kcadm.sh set-password -r CodeCarbon --email test --new-password test


# Show result
./kcadm.sh get users -q username=admin
#./kcadm.sh get users -q username=admin | jq .

