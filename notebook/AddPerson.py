import pypi_xmlrpc #pip install pypi-xmlrpc
import pandas as pd
import io
import json
import requests
import base64
from requests.auth import HTTPDigestAuth
import time
def add_person_info(device_ip,employeeNo,name,username,password):
    # API endpoint
    url = f"http://{device_ip}/ISAPI/AccessControl/UserInfo/Record?format=json"
    
    # Request headers
    headers = {
        # "Authorization": f"Basic {auth}",
        "Content-Type": "application/json"
    }
    
    # Person data
    payload = {
        "UserInfo": {
            "employeeNo": employeeNo,
            "name": name,
            "userType": "normal",
            "Valid": {
                "enable": False,
                "beginTime": "2025-01-03T00:00:00",
                "endTime": "2035-01-03T23:59:59",
                "timeType" : "local",   
            },
            "doorRight": "1",
            "RightPlan":[{"doorNo":1,"planTemplateNo":"1"}],
            "localUIRight" : False,
            "maxOpenDoorTime" : 0,
            "userVerifyMode" : "",
            "groupId" : 1,
            "userLevel" : "Employee",
        }
    }
    
    # Send request
    response = requests.post(url, headers=headers,auth=HTTPDigestAuth(username,password) ,json=payload)
    
    # Check response
    if response.status_code == 200:
        # print("Person info added successfully!")
        return True
    else:
        print(f"Inser Info Error: {response.status_code}, {response.text}")
        return False

def add_person_image(device_ip,employeeNo,image_str,name,username,password):
    url = f"http://{device_ip}/ISAPI/Intelligent/FDLib/FaceDataRecord?format=json"
    # image_path = "../data/photo_2024-12-26_11-14-08.jpg"
    payload = {'FaceDataRecord': '{"faceLibType":"blackFD","FDID":"1","FPID":"'+employeeNo+'"}'}
    # with open(image_path, "rb") as image_file:
    image_file = io.BytesIO(base64.b64decode(image_str))
    files=[
      ('img',(name+'.jpg',image_file,'image/jpeg'))
    ]
    headers = {}
    
    response = requests.request("POST", url, headers=headers,auth=HTTPDigestAuth(username,password), data=payload, files=files)
        # Check response
    if response.status_code == 200:
        # print("Person image added successfully!")
        return True
    else:
        print(f"Inser image Error: {response.status_code}, {response.text}")
        return False


# Read config 
with open('config.json', 'r') as json_file:
    # Load JSON content into a Python dictionary
    config = json.load(json_file)
print(config)
department_id = config['department_id']
device_ip = config['device_ip']
username_hk = config['username']
password_hk = config['password']

# Connect to faceid
server = 'https://faceid.mobifone5.vn'
database = "faceID"
user = "doanhdai1997@gmail.com"
password = "Baodai123!"


common = pypi_xmlrpc.ServerProxy('%s/xmlrpc/2/common' % server)
print(common.version())
uid = common.authenticate(database,user,password,{})
odooApi = pypi_xmlrpc.ServerProxy('%s/xmlrpc/2/object' % server)
print('uid',uid)

hr_department_record =  odooApi.execute_kw(database,uid,password,'hr.department','read',[department_id])
print(hr_department_record[0]['name'])
# Get person
hr_employee_records =  odooApi.execute_kw(database,uid,password,'hr.employee','search_read',[[('department_id','=',department_id)]],{'limit':0,'fields':["id","name","image_512"]})
# print(hr_employee_records)
# Inser to Hikvision
for person in hr_employee_records:
    employeeNo = str(person['id'])
    name = person['name']
    image = str(person['image_512'])
    if image != "False" and image[0]!='PD94':
        if add_person_info(device_ip,employeeNo,name,username_hk,password_hk):
            if add_person_image(device_ip,employeeNo,image,name,username_hk,password_hk):
                print(name,employeeNo,'OK')

print('DONE!')
time.sleep(300)