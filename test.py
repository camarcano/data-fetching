import requests
MY_TOKEN = "Uxsk4V7VKpJzQ6sqq_4YEeqDTxP3exBzJEy_X8sqedk"
"""
response = requests.get('https://api.baseballcv.com/models/phc_detector', 
                        headers={'Authorization': f'Bearer: {MY_TOKEN}'})
print(response.status_code)
"""

response = requests.get('https://api.baseballcv.com/models/', 
                        headers={'Authorization': f'Bearer: {MY_TOKEN}'})
print(response.json())