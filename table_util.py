import difflib
from difflib import SequenceMatcher
import utils
import re
# Find & extract line item table (Start)
def extract_expense_items(result_list):
  table_list = []
  for result in result_list:
    expense_documents = result.get('ExpenseDocuments')
    for document in expense_documents:
      table_groups = extract_table_group(document)
      table_list.extend(table_groups)

  table_list = merge_tables(table_list)  
  return table_list
  
# Extract all line item groups as table groups
# def extract_table_group(document):
#   table_groups = []
#   expense_item_groups = document.get('LineItemGroups')
#   for expense_item_group in expense_item_groups:
#     table = extract_table(expense_item_group)
#     table_groups.append(table)

#   return table_groups


def extract_table_group(document):
  table_groups = []
  expense_item_groups = document.get('LineItemGroups')
  for expense_item_group in expense_item_groups:
    expense_items = expense_item_group.get('LineItems')
    if expense_items !=[]:
      table = extract_table(expense_item_group)
      table_groups.append(table)
    else:
      continue

  return table_groups

# Extract line items as table
def extract_table(expense_item_group):
  table = []
  expense_items = expense_item_group.get('LineItems')
  objectcount=0
  for line_item in expense_items:
    row = extract_row(line_item,objectcount)
    objectcount=objectcount+1
    table.append(row)
  return table

# Extract each line item as row
def extract_row(line_item,objectcount):
  row = {}
  confidencelist=[]
  fields = line_item.get('LineItemExpenseFields')
  for field in fields:
    confidence=field.get('LabelDetection', {}).get('Confidence','0')
    confidencelist.append(confidence)
    confidence=field.get('ValueDetection', {}).get('Confidence','0')
    # confidencelist.append(confidence)
    
    label = field.get('LabelDetection', {}).get('Text')
    if label==None:
      label = field.get('Type', {}).get('Text')
      
      
      if objectcount==0:
        if label=='EXPENSE_ROW':
          label=""
        else:
          row[label+'/labelCheck']="recommended"
      
        
    if label=='EXPENSE_ROW' or label=='EXPENSE_ROW/labelCheck':
      label=""
    # for taxkey in utils.taxKeyList:
    
    input_string = re.sub(r"\([^\)]*\)", "", label)

    # Remove special characters
    input_string = re.sub(r"[^\w\s]", "", input_string)
    
    # Remove words inside brackets
    
    
    input_string = re.sub(r"\d+", "", input_string)
    
    res = re.sub(' +', ' ', input_string)

    if res.lower().strip() in utils.taxKeyList:
      label=res.strip()
    label = label and label.replace('\n', ' ')
    label = label or ''
    value = field.get('ValueDetection', {}).get('Text')
    row[label] = value
  # row['confidencelist']=confidencelist
  # print(confidencelist,'confidencelist')
  return row
  
# Merge similar tables and group them
def merge_tables(table_list, pointer = 0):
  host_table = table_list[pointer]
  host_header = list(host_table[0].keys())
  new_table_list = [host_table]
  
  for index in range(pointer + 1, len(table_list)):
    table = table_list[index]
    header = list(table[0].keys())
    if len(header) == len(host_header) and is_similar(header, host_header):
      new_table = restructure_table(table, host_header)
      host_table.extend(new_table)
    else:
      new_table_list.append(table)

  # if pointer + 2 < len(new_table_list):
  #   return merge_tables(new_table_list, pointer + 1)

  return new_table_list

# Restructure table by renaming the columns as the host table
def restructure_table(table, host_headers):
  new_table = []
  for row in table:
    host_row = {}
    for host_header in host_headers:
      if host_header in row:
        host_row[host_header] = row[host_header]
      else:
        headers = list(row.keys())
        matches = difflib.get_close_matches(host_header, headers, 1)
        if len(matches) == 1:
          host_row[host_header] = row[matches[0]]          
    new_table.append(host_row)
  return new_table

# Are headers of two different tables similar?
def is_similar(x_header, y_header):
  x_header = sorted(x_header)
  y_header = sorted(y_header)
  for index, header in enumerate(x_header):
    if SequenceMatcher(None, x_header[index], y_header[index]).ratio() < 0.8:
      return False
  return True  