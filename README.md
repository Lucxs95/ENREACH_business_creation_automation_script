# mytelephony-api-sample

This is an example showing the usage of the myTelephony API vesion 10.2 :

-   a login as a "Service Provider"
-   creation of an enterprise
-   creation of most of its component, i.e. users/extensions, groups, departments, sites, pstn ranges, device
-   this script was written to help developer understand the use of myTelephony API

# Pre-requisites

-   Use python3 (3.8 recommended)
-   Import the following modules: requests, json, base64, re, socket, websocket, random, time, sys, datetime

# Quick start

Clone the repository:

    git clone git@gitlab.com:centile-pub/mytelephony-api-sample/........

Make sure to edit the data.json file properly, especially:

-   url of the server to connect to
-   login / password of the Service Provider administrator
-   Enterprise name
-   login and emails of the users to create
-   login and email of the administrator to create
-   PSTN range
-   anything else you'll want to edit / add / remove

# Launch the script

    python3.8 create_myTelephony_enterprise1.py data.json

# More info

Please refer to our PartnerConnect website (https://partnerconnect.centile.com) or contact me.
