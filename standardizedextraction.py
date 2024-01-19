import boto3
import json
import re
from datetime import datetime
import utils
from dateutil import parser
import time
import logging
import utils
import get_invoice_handler
import requests


        


def handle(event,invoice_response):
    gettextractedjson=gettractjson(event)
    
    ### get standardized object

    summaryobject=getsummaryobject(gettextractedjson)

    getinvoicedata=get_invoice_handler.get_invoiceby(invoice_response['invoiceId'])
    getdtecedentities={}
    try:
        getdtecedentities=getdetectedentities(event)
    except Exception as e:
        pass


    updating_invoice_data=standardizedextraction(utils.comparefieldobject,summaryobject,getinvoicedata,getdtecedentities)
    print(json.dumps(updating_invoice_data),"standardized response data")
    response_update = requests.put(utils.UPDATE_INVOICE_URL, data = json.dumps(updating_invoice_data), headers = utils.API_V2_HEADER)
    print(response_update,"standardized update")
            # 








def gettractjson(event):
    document_json_path = event.get('expenseJsonPath')
    # tablevalue_filepath=event.get('filePath')
    # if tablevalue_filepath:
    #     tablevalue_filepath=tablevalue_filepath.replace(f'https://{utils.BUCKET_NAME}.s3.amazonaws.com/','')
    #     tablevalue_filepath=tablevalue_filepath+'-textracted-table.json'

    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
        Bucket = utils.BUCKET_NAME,
        Key =    document_json_path

    )
        
    document_json_str = document_json_s3_response.get('Body').read()
    document_json_list = json.loads(document_json_str)

    # # Extract table values from document json content
    # table_list = table_util.extract_expense_items(document_json_list)
    return document_json_list

def getdetectedentities(event):
    documentpath=event.get('expenseJsonPath')
    documentpath=documentpath.replace('-textracted-table.json','-form-values.json')
    print('newupdatedocumentpath',documentpath)
    s3_client = boto3.client('s3', region_name = utils.BUCKET_REGION)
    document_json_s3_response = s3_client.get_object(
    Bucket = utils.BUCKET_NAME,
    Key = documentpath
    )
            
    document_json_str = document_json_s3_response.get('Body').read()    
    document_json_list = json.loads(document_json_str)
    # print(document_json_list.get('detectedEntities'))
    detectedentities=document_json_list.get('detectedEntities',{})
    return detectedentities


# with open('testjson.json','r') as file:

#     fileopen=json.load(file)

# print(fileopen)
def getsummaryobject(gettextractedjson):

    summaryobject={}
    v=0
    try:
        for i in gettextractedjson:
            
            expense=i['ExpenseDocuments']
            
            for j in expense :
                summaryfiels=j['SummaryFields']
                # print(summaryfiels)
                for sum1 in summaryfiels:
                    summaryobject[sum1['Type']['Text']]=sum1['ValueDetection']['Text']
            # print(v)
            # v=v+1

        print(summaryobject)
        return summaryobject
    except Exception as e:
        return None

def standardizedextraction(comparefieldobject,summaryobject,invoiceData,getdtecedentities):

    for i in comparefieldobject:
        value=invoiceData.get(i['Clyear Target Varriable'])
        print(f'{i["Clyear Target Varriable"]}:{value}')
        if (not value or value=="0.00" or value=="N/A") and i['Clyear Target Varriable'] not in getdtecedentities:
            print(i["Clyear Target Varriable"])
            if i['awsTargetvariable'] in summaryobject:
                print(i['awsTargetvariable'])
                if i['Clyear Target Varriable']=='dueAmount' or i['Clyear Target Varriable']=='subTotal':
                    try:
                        s1=re.sub("[^0-9.],*","",summaryobject[i['awsTargetvariable']])
                        try:
                            ress = "{:.2f}".format(float(s1))
                        except:
                            ress=s1
                            
                            pass
                        invoiceData[i['Clyear Target Varriable']]=s1
                    except Exception as e:
                        invoiceData[i['Clyear Target Varriable']]=summaryobject[i['awsTargetvariable']]
                        pass

                    
                    
                elif i['Clyear Target Varriable']=="invoiceDate" or i['Clyear Target Varriable']=="dueDate":
                    try:
                        date_values=summaryobject[i['awsTargetvariable']]
                        print(date_values,'date_values')
                        
                        updated_date=parser.parse(str(date_values)).date()
                        print(updated_date,'updated_date')
                        # updated_date=try_parsing_date(date_values)
                        invoiceData[i['Clyear Target Varriable']] = str(updated_date)
                        
                        
                    
                    except Exception as e:
                        invoiceData[i['Clyear Target Varriable']]=summaryobject[i['awsTargetvariable']]
                        pass
                elif i['Clyear Target Varriable']=="invoiceAmount":
                    try:
                        invoiceamount= summaryobject[i['awsTargetvariable']]
                        if invoiceamount:
                                for currcheck in utils.currencylist1:
                                    if currcheck in invoiceamount:
                                        if currcheck=='BZR':
                                            currcheck='BRL'
                                        elif currcheck=='CA':
                                            currcheck='CAD'
                                        invoiceData['invoiceCurrency']=currcheck

                        
                                s1=re.sub("[^0-9.],*","",invoiceamount).strip()
                                print(s1,'strings1')
                                ress='0.00'
                                try:
                                    ress = "{:.2f}".format(float(s1))
                                except:
                                    ress=s1
                                    pass
                            
                                invoiceData['invoiceAmount'] =str(ress)
                                    
                    except Exception as e:
                        invoiceData['invoiceAmount'] =summaryobject[i['awsTargetvariable']]
                
                        pass
                
                
                # elif i["Clyear Target Varriable"]=="taxTotal":
                #     try:
                #         taxamount=summaryobject[i['awsTargetvariable']]
                #         print(i['awsTargetvariable'],'tax key',taxamount)
                #         taxtotal=re.sub("[^0-9.%],*","",taxamount).strip()
                #         invoiceData['taxTotal']=taxtotal

                        
                #         pass
                #     except Exception as e:
                #         pass
                #     try:
                #         subtotal=invoiceData.get('subTotal'):
                #         if not subtotal or subtotal=="0.00":
                #             taxtotal=summaryobject[i["awsTargetvariable"]]
                #             if '%'  in taxtotal:

                
                
                else:
                    print(summaryobject[i['awsTargetvariable']],'check value')
                    invoiceData[i['Clyear Target Varriable']] =summaryobject[i['awsTargetvariable']]



    print(invoiceData)

    taxtotal=str(invoiceData.get('taxTotal',''))
    taxRate=invoiceData.get('taxRate','')
    subtotal=invoiceData.get('subTotal')
    print(taxtotal,'taxtotalcheck')
    print(taxRate,'chcektaxrate')
    if  (taxtotal=="0.00" or '%' in taxtotal)  and  (taxRate=="0.00"or taxRate==''):
        print('its workingtax')
        try:
            taxtotal=summaryobject.get('TAX',None)
            print('standarizedtaxtotal',taxtotal)
            if '%' in taxtotal:
                removal_percentage=taxtotal.replace('%', "")
                taxtotal=re.sub("[^0-9.],*","",removal_percentage).strip()
                # taxtotal=removal_percentage.strip()
                print(taxtotal,'percentage')
                # invoiceData['taxRate']=str(float(taxtotal))
                if subtotal!="0.00":
                    taxtoalcalculate=(float(taxtotal)/100)*float(subtotal)
                    print(taxtoalcalculate,'taxtoalcalculate')
                    invoiceData['taxTotal']=str(taxtoalcalculate)
            else:
                try:
                    s1=re.sub("[^0-9.],*","",taxtotal).strip()
                    print(s1,'strings1')
                    try:
                        ress = "{:.2f}".format(float(s1))
                    except Exception as e:
                        logging.exception(e)
                        ress=s1
                        pass
                    print(ress)
                    invoiceData['taxTotal'] = str(ress)
                    # if subtotal!=0:
                    #     taxrate=(float(ress)/float(subtotal))*100
                    #     invoiceData['taxRate']=str(float(taxRate))
                    
                except Exception as err:
                    logging.exception( err)
                    invoiceData['taxTotal'] = taxtotal


                
            print(taxtotal)
        except Exception as e:
            taxtotal=None

    print(invoiceData)
    return invoiceData







        # for expense in summaryfiels:

        