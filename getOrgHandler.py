import utils
import requests



def getOrgId(destinationEmail):
    destinationEmail=destinationEmail[0]
    checkorg=False
    response=requests.get( url=f'{utils.GET_ORG_DETAIL}{destinationEmail}',
                          
                         headers=utils.API_V2_HEADER )
    

    # response=response.json()

    print(response,'res')

    if response.status_code==200:
        checkorg=True
        


    return checkorg


