

# Importing some useful libraries

import requests
import json
import base64
import re
import socket
import websocket
import random
import time
import sys
from datetime import datetime

if len(sys.argv) == 2:

    # Reading data from data.json file entered as an argument

    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)

    url = data['admin_cred']['url']
    message = data['admin_cred']['login'] + \
        ":" + data['admin_cred']['password']

    # Encoding base64 the login/password

    message_bytes = message.encode()
    base64_bytes = base64.b64encode(message_bytes)
    base64_message = base64_bytes.decode()
    type(base64_message)
    rd = random.random()

    # Defining the initial header

    payload = {
        'X-Application': 'myTelephony',
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*'}
    payload['Authorization'] = "Basic " + base64_message

    # Login phase

    login = requests.post(url + "/v1/service/Login?rd=" +
                          str(rd), headers=payload)

    print(login)

    if str(login.status_code) == "401":
        print("====================================")
        print(f"Check your credentials (Error {login.status_code})")
        print("====================================")
        sys.exit()

    if str(login.status_code) == "200":
        print("\n")
        print(
            "==============================================================================")
        print(f"Login ({data['admin_cred']['login']}) successful ")
        print(
            "==============================================================================")

    else:
        print("Login failed. Check your credentials or the server availability! ")

    r_dict = login.headers
    print(r_dict)

    # Getting X-Application and Set-Cookie headers, beautifying them

    xapp = r_dict['X-Application']
    cookie = r_dict['Set-Cookie'].split(
        'myTelephony_SESSIONID')[-1].split(';')[0]
    cookie = "myTelephony_SESSIONID" + cookie

    payload_auth = {
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/plain, */*'}
    payload_auth['X-Application'] = xapp
    payload_auth['Cookie'] = cookie

    # Importing the Enterprise payload from data.json file

    enterprise_payload = data['enterprise_payload']
    fullName = data['enterprise_payload']['fullName']

    # Enterprise creation

    createEnteprise = requests.post(
        url + "/v1/telephony/Enterprise", headers=payload_auth, json=enterprise_payload)

    print(createEnteprise)

    if "200" in str(createEnteprise):
        print("")

    else:
        print("Problem during the enterprise creation")

    # Get the list of enterprises

    enterprise_list = requests.get(
        url + "/v1/telephony/Enterprise/", headers=payload_auth)
    json_ent = json.loads(enterprise_list.text)

    # Loop on the list of enterprises to get the ID of the enterprise we just created
    print("\n")
    print("==============================================================================")
    print("General Information")
    print("==============================================================================")

    for x in range(0, json_ent['count']):
        if json_ent['results'][x]['name'] == enterprise_payload['fullName']:
            entID = json_ent['results'][x]['entID']
            print("Enterprise ID: " + str(json_ent['results'][x]['entID']))
            print("Enterprise name: " + json_ent['results'][x]['name'])

    # Get administrative domains

    get_adm_id = requests.get(
        url + "/v1/telephony/AdmtiveDomain", headers=payload_auth)
    json_adm = get_adm_id.json()

    # Get the Ent Adm Domain ID

    for y in range(0, int(json_adm['count'])):
        if str(json_adm['results'][y]['domainName']) == fullName:
            ent_domainID = json_adm['results'][y]['restUri']
            ent_domainID = str(ent_domainID).split('/')[-1]
            print(f"Enterprise domain ID: {ent_domainID}")
            break

    # Get the SP Adm Domain ID

    for x in range(0, int(json_adm['count'])):
        if str(json_adm['results'][x]['domainName']) == data['admin_cred']['domain']:
            domainName = data['admin_cred']['domain']
            domainID = json_adm['results'][x]['restUri']
            print(f"Service Provider domain ID: {domainID} ")
            break

    data['pstn_range']['ownerAdmtiveDomain'] = domainID
    data['enterprise_extra']['assignedTo'] = ent_domainID

    print("==============================================================================")

    # Open again json to write in the PSTN range the Adm Domain ID (optional)
    with open(sys.argv[1], 'w') as json_file:
        json.dump(data, json_file, indent=4)

    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)

    pstn_range = data['pstn_range']
    pstn_range_start = data['pstn_range']['rangeStart']
    pstn_range_end = data['pstn_range']['rangeEnd']

    # Creating the enterprise site

    print("\n")
    print("==============================================================================")
    print("Enterprise Sites creation")
    print("==============================================================================")

    site_payload = data['site_payload']

    for x in range(0, len(site_payload)):
        site_payload_increm = site_payload[x]
        create_site = requests.post(url + "/v1/telephony/Enterprise/" +
                                    entID + "/Site", headers=payload_auth, json=site_payload_increm)
        print(f"Enterprise site {site_payload_increm['name']} created")

    if "200" in str(create_site):
        print(
            "==============================================================================")

    else:
        print(f"Problem during the site  creation ({site_payload_increm})")
        print(create_site.content)

    # Creating the PSTN Range

    print("\n")
    print("==============================================================================")
    print("PSTN Range creation")
    print("==============================================================================")

    create_pstn_range = requests.post(
        url + "/v1/telephony/PstnRange", headers=payload_auth, json=pstn_range)

    print(create_pstn_range)

    if "200" in str(create_pstn_range):
        print(f"PSTN range ({pstn_range_start}:{pstn_range_end}) created")
        create_pstn_range_json = create_pstn_range.json()
        pstn_range_id = create_pstn_range_json['pstnRangeID']
        pstn_range_domain_uri = create_pstn_range_json['restUri']
        print("\n")

    else:
        print("Problem during the PSTN range creation")
        print(create_pstn_range.content)

    # Assigning the PSTN range to enterprie (with id ent_domainID)

    enterprise_extra = data['enterprise_extra']
    assign_pstn_range = requests.put(
        url + "/" + pstn_range_domain_uri, headers=payload_auth, json=enterprise_extra)

    if "200" in str(assign_pstn_range.status_code):
        print(
            f"PSTN range has been moved from {domainName} to {fullName} ({ent_domainID})")
        print("\n")
    else:
        print("Problem during the PSTN range assignment")

    print("==============================================================================")

    # Importing the Users payload from json file

    user_payload = data['user_payload']

    # Creating Users and Extensions

    print("\n")
    print("==============================================================================")
    print("Creating Users / Extensions: ")
    print("==============================================================================")

    group_members = data['group_members']
    acd_members = data['acd_members']

    for x in range(0, len(user_payload)):
        user_payload_increm = user_payload[x]
        createExtension = requests.post(url + "/v1/telephony/Enterprise/" +
                                        entID + "/Extension", headers=payload_auth, json=user_payload_increm)
        createExtension_json = json.loads(createExtension.text)

        # Getting the user_uri to store it into a dictionary of group members

        user_uri = createExtension_json['restUri']
        group_members['members'][x]['restUri'] = createExtension_json['restUri']
        RemoteTerminal_payload = data['remoteterminal_payload']
        RemoteTerminal_payload[x]['extension'] = createExtension_json['restUri']

        if "200" in str(createExtension):
            print("Extension " + str(user_payload_increm) +
                  " has been created successfully!")
            print("\n")
        else:
            print(
                "Problem during the extension creation (check login does not already exist)")
    print("==============================================================================")

    # Creating a dummy device

    print("\n")
    print("==============================================================================")
    print("Creating Device: ")
    print("==============================================================================")

    device_payload = data['device_payload']
    device_specific = "v1/telephony/Enterprise/" + entID + "/DeviceModel/185"
    device_payload['deviceModel'] = device_specific
    device_creation = requests.post(
        url + "/v1/telephony/Enterprise/" + entID + "/Device", headers=payload_auth, json=device_payload)

    if "200" in str(device_creation):
        print(
            f"Device ({device_payload['label']} - {device_payload['macAddress']}) successfully created")
        print("\n")
    else:
        print("Problem during the device creation")

    print("==============================================================================")

    print("\n")
    print("==============================================================================")
    print("Receptionist, Pilot number, PSTN assignment: ")
    print("==============================================================================")

    # Assigning a Receptionist

    pilot_number = data['pilot_nb_payload']

    get_recep_uri = requests.get(url + "/v1/telephony/Enterprise/" + entID +
                                 "/Receptionist?addressNumber=" + pilot_number['receptionist'], headers=payload_auth)
    get_recep_uri_json = json.loads(get_recep_uri.text)
    recep_uri = get_recep_uri_json['results'][0]['restUri']
    assign_recep = requests.put(url + "/v1/telephony/Enterprise/" +
                                entID, headers=payload_auth, json={"receptionist": recep_uri})

    if "200" in str(assign_recep.status_code):
        print(
            f"Receptionist {pilot_number['receptionist']} assigned to {fullName}")
        print("\n")
    else:
        print("Problem during the receptionist assignment")

    # Assigning first PSTN to first extension

    # First, we get the extension uri
    get_ext_for_pstn = requests.get(url + "/v1/telephony/Enterprise/" + entID +
                                    "/InternalAddress?addressNumber=" + user_payload[0]['addressNumber'], headers=payload_auth)
    get_ext_for_pstn_json = json.loads(get_ext_for_pstn.text)
    user_uri = get_ext_for_pstn_json['results'][0]['restUri']
    user_id = get_ext_for_pstn_json['results'][0]['addressNumber']

    # Second, we get the PSTN number uri
    get_pstn_nb = requests.get(
        url + "/v1/telephony/Enterprise/" + entID + "/PstnNumber", headers=payload_auth)
    get_pstn_nb_json = json.loads(get_pstn_nb.text)
    pstn_nb_id = get_pstn_nb_json['results'][0]['pstnNumberID']
    pstn_nb_uri = get_pstn_nb_json['results'][0]['restUri']
    pstn_nb = get_pstn_nb_json['results'][0]['pstnNumber']

    # Third, we assign extension (user_uri) to PSTN number (psnt_nb_uri)
    assign_pstn_to_usr = requests.put(url + "/v1/telephony/Enterprise/" + entID +
                                      "/PstnNumber/" + pstn_nb_id, headers=payload_auth, json={'internalAddress': user_uri})

    if "200" in str(assign_pstn_to_usr.status_code):
        print(f"PSTN number {pstn_nb} assigned to extension {user_id}")
        print("\n")
    else:
        print("Problem during the PSTN number assignment")

    # Assigning the enterprise pilot number (first pstn in the range).
    # This PSTN must belong to an extension first (otherwise it wont appear in the list of available numbers)

    assign_pilot_number = requests.put(
        url + "/v1/telephony/Enterprise/" + entID, headers=payload_auth, json={'pilotNumber': pstn_nb_uri})

    if "200" in str(assign_pilot_number.status_code):
        print(f"Pilot number {pstn_nb} defined")
        print("\n")
    else:
        print("Problem during the Pilot number assignment")

    print("==============================================================================")

    print("\n")
    print("==============================================================================")
    print("Creating Administrator: ")
    print("==============================================================================")

    # Creating an enterprise administrator

    admin_payload = data['admin_payload']
    create_admin = requests.post(url + "/v1/telephony/Enterprise/" +
                                 entID + "/Administrator", headers=payload_auth, json=admin_payload)

    if "200" in str(createEnteprise):
        print("Enterprise Administrator (" +
              str(data['admin_payload']['login']) + ") created")
        print("\n")
    else:
        print("Problem during the administrator creation")
        print("----------------------------")
    print("==============================================================================")

    print("\n")
    print("==============================================================================")
    print("Creating Departments: ")
    print("==============================================================================")

    # Importing the Departments payload from json file

    department_payload = data['department_payload']
    sub_dep_payload = data['sub_department_payload']

    # Creating departments

    for x in range(0, len(department_payload)):

        # Creating the parent department
        department_payload_increm = department_payload[x]
        department_creation = requests.post(
            url + "/v1/telephony/Enterprise/" + entID + "/Department", headers=payload_auth, json=department_payload_increm)

        if "200" in str(department_creation):
            print("Department " +
                  str(department_payload_increm['name']) + " created")

        else:
            print("Problem during the department creation")
            print("----------------------------")

        # Getting its Uri and storing it
        department_creation_json = json.loads(department_creation.text)
        dep_uri = department_creation_json['restUri']
        dep_name = department_creation_json['name']

        # Writing parent_dep Uri into data.json
        for z in range(0, len(sub_dep_payload)):
            data['sub_department_payload'][z]['ownerDepartment'] = dep_uri

    with open(sys.argv[1], 'w') as my_file:
        json.dump(data, my_file, indent=4)

    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)

    sub_dep_payload = data['sub_department_payload']

    for x in range(0, len(sub_dep_payload)):
        sub_dep_creation = requests.post(
            url + "/v1/telephony/Enterprise/" + entID + "/Department", headers=payload_auth, json=sub_dep_payload[x])
        print(f"  -- Sub-Department {sub_dep_payload[x]['name']} created")
    print("==============================================================================")

    print("\n")
    print("==============================================================================")
    print("Creating Groups: ")
    print("==============================================================================")

    # Importing the Groups payload from json file after filling it with users' restUri's

    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)

    group_payload = data['group_payload']

    # Creating groups and assigning extensions

    for x in range(0, len(group_payload)):
        group_payload_increm = group_payload[x]
        group_creation = requests.post(url + "/v1/telephony/Enterprise/" + entID +
                                       "/GroupAddress", headers=payload_auth, json=group_payload_increm)
        group_creation_json = json.loads(group_creation.text)
        groupID = group_creation_json['restUri']

        # Assigning the group members

        for y in range(0, len(group_members['members'])):
            assign_ext = requests.put(
                url + "/" + groupID, headers=payload_auth, json=group_members)

        if "200" in str(group_creation):
            print("Group " + str(group_payload_increm) +
                  " has been created successfully!")
            print("\n")
        else:
            print("Problem during the group creation")
    print("==============================================================================")

   # Creating ACD Groups

    print("\n==============================================================================")
    print("Creating ACD Groups:")
    print("==============================================================================")

    # Importing the Groups payload from json file after filled it with users' restUri's

    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)

    acd_payload = data['acd_payload']
    acd_members = data['acd_members']

    # Creating ACD groups and assigning extensions

    for x in range(0, len(acd_payload)):
        acd_payload_increm = acd_payload[x]
        acd_creation = requests.post(url + "/v1/telephony/Enterprise/" + entID +
                                     "/ACDGroupAddress", headers=payload_auth, json=acd_payload_increm)
        acd_creation_json = json.loads(acd_creation.text)
        ACDgroupID = acd_creation_json['restUri']

        # Assigning the group members

        for y in range(0, len(acd_members['members'])):
            assign_ext = requests.put(
                url + "/" + ACDgroupID, headers=payload_auth, json=acd_members)

        if "200" in str(acd_creation):
            print("ACD Group " + str(acd_payload_increm) +
                  " has been created successfully!\n")
        else:
            print("Problem during the ACD group creation")
    print("==============================================================================")

    voicemail_payload = {"label": "Voicemail",
                         "addressNumber": "555", "isDefaultByServiceType": "true"}
    conference_payload = {"label": "Conference", "addressNumber": "559",
                          "ivrName": "Conference", "alias": "IVRService"}

    print("==============================================================================")
    print("Voicemail and Conference creation")
    print("==============================================================================")

    # Importing the Voicemail and Conference payloads from data.json file

    voicemail_payload = data['voicemail_payload']
    conference_payload = data['conference_payload']

    # Creating Voicemail and Conference

    createVm = requests.post(url + "/v1/telephony/Enterprise/" + entID +
                             "/Voicemail", headers=payload_auth, json=voicemail_payload)

    if "200" in str(createVm):
        print(
            "Voicemail (" + str(voicemail_payload['addressNumber']) + ") has been created successfully!")
        print("\n")

    else:
        print("Problem during the voicemail creation")
        print("\n")

    createConf = requests.post(url + "/v1/telephony/Enterprise/" + entID +
                               "/IVRService", headers=payload_auth, json=conference_payload)

    if "200" in str(createConf):
        print("Conference (" +
              str(conference_payload['addressNumber']) + ") has been created successfully!")
        print("\n")
    else:
        print("Problem during the conference creation")
    print("==============================================================================")

    print("\n")
    print("==============================================================================")
    print("Forwarding Rules Creation")
    print("==============================================================================")

    # Importing the FWD payload from data.json file
    fwd_na_payload = data['fwd_na_payload']
    fwd_bu_payload = data['fwd_bu_payload']
    fwd_unr_payload = data['fwd_unr_payload']

    # Creating Forwarding Rules

    createFwd_na = requests.post(url + "/v1/telephony/Enterprise/" +
                                 entID + "/Forwarding/", headers=payload_auth, json=fwd_na_payload)
    if "200" in str(createFwd_na):
        print("Fwd Rule On No Answer created")
        print("\n")
    else:
        print("Problem during the Fwd creation")

    createFwd_bu = requests.post(url + "/v1/telephony/Enterprise/" +
                                 entID + "/Forwarding/", headers=payload_auth, json=fwd_bu_payload)
    if "200" in str(createFwd_bu):
        print("Fwd Rule On Busy created")
        print("\n")
    else:
        print("Problem during the Fwd creation")

    createFwd_unr = requests.post(url + "/v1/telephony/Enterprise/" +
                                  entID + "/Forwarding/", headers=payload_auth, json=fwd_unr_payload)
    if "200" in str(createFwd_unr):
        print("Fwd Rule On Unreachable created")
        print("\n")
    else:
        print("Problem during the Fwd creation")
    print("==============================================================================")


##########################################################################################################################################
    # Creating an Auto-Attendant
    print("==============================================================================")
    print("Creating Auto Attendant:")
    print("==============================================================================")

    payload_aa = data['payload_aa']
    auto_at_post = requests.post(url + "/v1/telephony/Enterprise/" +
                                 entID + "/AutoAttendant/", headers=payload_auth, json=payload_aa)
    auto_at_json = json.loads(auto_at_post.text)
    aa_id = auto_at_json['restUri'].split('/')[-1]

    if "200" in str(auto_at_post):
        print("Auto Attendant created")
        print("\n")
    else:
        print("Problem during the Auto Attendant creation")
    print("==============================================================================")

##########################################################################################################################################

    # Creating a Call barring rule

    print("==============================================================================")
    print("Creating Call Barring:")
    print("==============================================================================")
    barring_payload = data['barring_payload']
    cb_noext = requests.post(url + "/v1/telephony/Enterprise/" + entID +
                             "/RestrictedCallRule/", headers=payload_auth, json=barring_payload)
    if "200" in str(cb_noext):
        print("Call Barring created")
        print("\n")
    else:
        print("Problem during the Call Barring creation")

    # Importing the DialPrefixe payload from json file

    DialPrefixe_payload = data['dialprefixe_payload']

    # Creating a DialPrefixe
    print("\n")
    print("==============================================================================")
    print("Creating DialPrefixe:")
    print("==============================================================================")

    for x in range(0, len(DialPrefixe_payload)):
        dialprefixe_payload_increm = DialPrefixe_payload[x]
        createDialPrefixe = requests.post(url + "/v2/telephony/Enterprise/" + entID +
                                          "/DialPrefix", headers=payload_auth, json=dialprefixe_payload_increm)

        if "200" in str(createDialPrefixe):
            print("DialPrefixe " + str(dialprefixe_payload_increm) +
                  " has been created successfully!")
            print("\n")
        else:
            print(
                "Problem during the DialPrefixe creation (check DialPrefixe does not already exist)")
            print("\n")
    print("==============================================================================")

    # Importing the SpeedDials payload from json file

    SpeedDials_payload = data['speeddials_payload']

    # Creating a SpeedDials
    print("\n")
    print("==============================================================================")
    print("Creating SpeedDials:")
    print("==============================================================================")

    for x in range(0, len(SpeedDials_payload)):
        speeddials_payload_increm = SpeedDials_payload[x]
        createSpeedDial = requests.post(url + "/v2/telephony/Enterprise/" + entID +
                                        "/SpeedDial", headers=payload_auth, json=speeddials_payload_increm)

        if "200" in str(createSpeedDial):
            print("SpeedDial " + str(speeddials_payload_increm) +
                  " has been created successfully!")
            print("\n")
        else:
            print(
                "Problem during the SpeedDial creation (check SpeedDial does not already exist)")
            print("\n")
    print("==============================================================================")

    # Importing the PagingGroupAddress payload from json file

    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)
    PagingGroupAddress_payload = data['paginggroup_payload']

    # Creating a PagingGroupAddress extension
    print("\n")
    print("==============================================================================")
    print("Creating PagingGroupAddress:")
    print("==============================================================================")

    for x in range(0, len(PagingGroupAddress_payload)):
        PagingGroupAddress_payload_increm = PagingGroupAddress_payload[x]
        createPagingGroupAddress = requests.post(url + "/v1/telephony/Enterprise/" + entID +
                                                 "/PagingGroupAddress", headers=payload_auth, json=PagingGroupAddress_payload_increm)
        group_creationPaging_json = json.loads(createPagingGroupAddress.text)
        groupIDPaging = group_creationPaging_json['restUri']

        # Assigning the group members
        for y in range(0, len(group_members['members'])):
            assign_ext = requests.put(
                url + "/" + groupIDPaging, headers=payload_auth, json=group_members)

        if "200" in str(createPagingGroupAddress):
            print("PagingGroupAddress " + str(PagingGroupAddress_payload_increm) +
                  " has been created successfully!")
            print("\n")
        else:
            print(
                "Problem during the PagingGroupAddress creation (check PagingGroupAddress does not already exist)")
    print("==============================================================================")

    # Creating a RemoteTerminal extension
    print("\n")
    print("==============================================================================")
    print("Creating RemoteTerminal:")
    print("==============================================================================")

    for x in range(0, len(RemoteTerminal_payload)):
        RemoteTerminal_payload_increm = RemoteTerminal_payload[x]
        createRemoteTerminal = requests.post(url + "/v1/telephony/Enterprise/" + entID +
                                             "/LogicalTerminal", headers=payload_auth, json=RemoteTerminal_payload_increm)
        if "200" in str(createRemoteTerminal):
            print("RemoteTerminal " + str(RemoteTerminal_payload_increm) +
                  " has been created successfully!")
            print("\n")
        else:
            print(
                "Problem during the RemoteTerminal creation (check RemoteTerminal does not already exist)")

    dataID = data['group_members']
    remoteterminal_assign = data['remoteterminal_assign']

    for y in range(0, len(group_members['members'])):
        restUri = dataID['members'][y]['restUri']
        RT_number = remoteterminal_assign[y]
        assign_RT = requests.put(
            url + "/" + restUri, headers=payload_auth, json=RT_number)
        if "200" in str(assign_RT):
            print("RemoteTerminal " + str(RT_number) +
                  " has been created successfully!")
            print("\n")
        else:
            print(
                "Problem during the RemoteTerminal assignement (check RemoteTerminal does not already exist)")

    print("==============================================================================")

# Importing the Calendar payload from json file

    with open(sys.argv[1]) as json_file:
        data = json.load(json_file)
    Calendar_payload = data['calendar_payload']

    # Creating a Calendar extension
    print("\n")
    print("==============================================================================")
    print("Creating Calendar:")
    print("==============================================================================")

    Calendar_assign = data['calendar_assign']
    Calendar_exceptions = data['calendar_exceptions']
    for x in range(0, len(Calendar_payload)):
        Calendar_payload_increm = Calendar_payload[x]
        createCalendar = requests.post(url + "/v2/telephony/Enterprise/" + entID +
                                             "/Calendar", headers=payload_auth, json=Calendar_payload_increm)

    # Assigning the Calendar dates
    id = requests.get(url + "/v2/telephony/Enterprise/" +
                      entID + "/Calendar", headers=payload_auth)
    json_id = json.loads(id.text)
    json_id_results = json_id['results']
    calendarID = json_id['results'][x]['calendarID']

    for z in range(0, len(json_id_results)):
        if json_id_results[z]['name'] == Calendar_payload[0]['name']:
            calendarID = json_id_results[z]['calendarID']
            for w in range(0, len(Calendar_assign)):
                Calendar_assign[w]['calendar'] = json_id_results[z]['restUri']
            for l in range(0, len(Calendar_exceptions)):
                Calendar_exceptions[l]['calendar'] = json_id_results[z]['restUri']

    for y in range(0, len(Calendar_assign)):
        CalendarSlot_payload_increm = Calendar_assign[y]
        assign_ext = requests.post(
            url + "/v2/telephony/Enterprise/" + entID + "/Calendar/" + calendarID + "/CalendarSlot", headers=payload_auth, json=CalendarSlot_payload_increm)

    for y in range(0, len(Calendar_exceptions)):
        Calendar_exceptions_payload_increm = Calendar_exceptions[y]
        assign_exceptions = requests.post(
            url + "/v2/telephony/Enterprise/" + entID + "/Calendar/" + calendarID + "/CalendarSlot", headers=payload_auth, json=Calendar_exceptions_payload_increm)

    if "200" in str(createCalendar) and "200" in str(assign_ext) and "200" in str(assign_exceptions):
        print("Calendar " + str(Calendar_payload_increm) +
              " has been created successfully!")
        print("\n")
    else:
        print(
            "Problem during the Calendar cretaion/assignement (check Calendar does not already exist)")
    print("==============================================================================")

    # Printing Recap of the Enterprise created

    print("\n\n")
    print("==============================================================================")
    print("Summary of the enterprise created")
    print("==============================================================================")

    dashboard = requests.get(
        url + "/v1/telephony/Enterprise/" + entID + "/Dashboard/", headers=payload_auth)
    entreprise_json = json.loads(dashboard.content)
    print("Enterprise name: " + str(entreprise_json['fullName']))
    print("Number of group(s): " +
          str(entreprise_json['summaryGroups'][0]['count']))
    print("Number of extension(s): " +
          str(entreprise_json['summaryExtensions']['total']))
    print("Number of voicemail(s): " +
          str(entreprise_json['summaryVoicemails']['total']))
    print("Number of device(s): " +
          str(entreprise_json['summaryDevices']['total']))
    print("Number of department(s): " +
          str(entreprise_json['summaryDepartments']['total']))
    print("Number of administrator(s): " +
          str(entreprise_json['summaryAdministrators']['total']))
    print("Number of site(s): " +
          str(entreprise_json['summarySites']['total']))
    print("==============================================================================")
    print("\n")

    # Block entreprise

    print("\n")
    print("==============================================================================")
    print("Block entreprise")
    print("==============================================================================")
    enterprise_blocked = data['enterprise_blocked']

    print("Would you blocked the entreprise you just created ?")
    b = input("1 : yes, other : no\n")
    if b == "1":
        blockedEnteprise = requests.put(
            url + "/v1/telephony/Enterprise/" + entID, headers=payload_auth, json=enterprise_blocked)

        if "200" in str(blockedEnteprise):
            print("Entreprise blocked successfully !")

        else:
            print("Problem when blocking the entreprise !")
    else:
        print("Entreprise not blocked")

    # Logout

    logout = requests.get(url + "/v1/service/Logout", headers=payload)
    logout_status = str(logout.status_code)

    print("==============================================================================")
    if logout_status == "204":

        print(f"End of the operations - Logout OK ({logout_status}) - ")
    else:
        print(f"End of the operations - Error during logout ({logout_status})")
    print("==============================================================================")

else:
    print("========================")
    print("Script argument missing")
    print(f"Use {sys.argv[0]} with <enterprise.json> in argument")
    print(f"Example: {sys.argv[0]} MyEnterprise.json")
    print("========================")
