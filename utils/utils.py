import fitz
import pandas as pd
import numpy as np
import fitz
import json
import re
from datetime import datetime


def is_overlapping(seq, subsequences):
    for subseq in subsequences:
        if seq['start_idx_str1'] >= subseq['start_idx_str1'] and seq['start_idx_str1'] <= subseq['end_idx_str1']:
            return True
        if seq['end_idx_str1'] >= subseq['start_idx_str1'] and seq['end_idx_str1'] <= subseq['end_idx_str1']:
            return True
    return False


def compute_similarity(str1, str2, min_length=3):
    common_subsequences = []
    str1_length = len(str1)
    str2_length = len(str2)
    for i in range(str1_length):
        for j in range(str2_length):
            if str1[i] == str2[j]:
                subseq = [str1[i]]
                x = i + 1
                y = j + 1
                while x < str1_length and y < str2_length and str1[x] == str2[y]:
                    subseq.append(str1[x])
                    x += 1
                    y += 1
                new_seq = {
                    'subsequence': ''.join(subseq),
                    'start_idx_str1': i,
                    'end_idx_str1': x - 1,
                    'start_idx_str2': j,
                    'end_idx_str2': y - 1
                }
                if len(subseq) >= min_length and not is_overlapping(new_seq, common_subsequences):
                    common_subsequences.append(new_seq)
                break
    return common_subsequences


def extract_date_from_string(input_string):
    """Extract date from a given string, else return None"""
    date_pattern = r'\b(\d{2}/\d{2}/\d{4})\b'
    matches = re.findall(date_pattern, input_string)
    if matches:
        date_str = matches[0]
        date_obj = datetime.strptime(date_str, '%d/%m/%Y').date()
        return date_obj.strftime('%d-%m-%Y')
    else:
        return None
    

def extract_integer_from_string(input_string):
    """Extract integer from a given string, else return None"""
    integer_pattern = r'\d+'
    matches = re.findall(integer_pattern, input_string)
    if matches:
        integer_str = matches[0]
        integer_obj = int(integer_str)
        return integer_obj
    else:
        return None


def extract_journal_info(page_dict):
    journal_info = {}
    journal_info_row = page_dict["blocks"][0]["lines"][0]["spans"][0]["text"]
    journal_number = extract_integer_from_string(journal_info_row.split(',')[0])
    journal_date = extract_date_from_string(journal_info_row)
    journal_class = extract_integer_from_string(journal_info_row.split('Class')[-1])
    journal_info = {
        "journal_number" : journal_number,
        "journal_date" : journal_date,
        "journal_class" : journal_class
    }
    return journal_info


def extract_brand_header(page_dict):
    try:
        brand_header = page_dict["blocks"][1]["lines"][0]["spans"][0]["text"]
        brand_header = None if re.findall(r'\xa0', brand_header) else brand_header
    except Exception as e:
        brand_header = None
    return brand_header


def extract_application_number(page_dict):
    try:
        application_number = int(page_dict["blocks"][2]["lines"][0]["spans"][0]["text"].split(" ")[0])
    except Exception as e:
        application_number = None
    return application_number


def extract_application_date(page_dict):
    application_date_row = page_dict["blocks"][2]["lines"][0]["spans"][0]["text"]
    application_date = extract_date_from_string(application_date_row)
    return application_date


def extract_company_info(page_dict):
    company_info = {}
    company_name = page_dict["blocks"][3]["lines"][0]["spans"][0]["text"]
    total_lines = len(page_dict["blocks"][3]["lines"])
    if total_lines == 1:
        company_address = None
        company_status = None
    elif total_lines == 2:
        company_address = page_dict["blocks"][3]["lines"][1]["spans"][0]["text"]
        company_status = None
    else:
        company_address = ""
        for i in range(1, total_lines-2):
            company_address += (page_dict["blocks"][3]["lines"][i]["spans"][0]["text"] + ", ")
        company_address = company_address[:-2]
        company_status = page_dict["blocks"][3]["lines"][total_lines-2]["spans"][0]["text"]
           
    company_info = {
        "company_name" : company_name,
        "company_address" : company_address,
        "company_status" : company_status
    }
    return company_info


def extract_advocate_info(page_dict):
    advocate_info = {}
    advocate_name = page_dict["blocks"][4]["lines"][0]["spans"][0]["text"]
    total_lines = len(page_dict["blocks"][4]["lines"])
    if total_lines == 1:
        advocate_address = None
    elif total_lines == 2:
        advocate_address = page_dict["blocks"][4]["lines"][1]["spans"][0]["text"]
    else:
        advocate_address = ""
        for i in range (1, total_lines-2):
            advocate_address += (page_dict["blocks"][4]["lines"][i]["spans"][0]["text"] + ", ")
        advocate_address = advocate_address[:-2]
    advocate_info = {
        "advocate_name" : advocate_name,
        "advocate_address" : advocate_address
    }
    return advocate_info


def extract_usage_status(page_dict):
    total_lines = len(page_dict["blocks"][4]["lines"])
    if total_lines > 2:
        usage_status_row = page_dict["blocks"][4]["lines"][-2]["spans"][0]["text"]
        if extract_date_from_string(usage_status_row):
            usage_status = extract_date_from_string(usage_status_row)
        else:
            usage_status = usage_status_row
    else:
        usage_status = None
    return usage_status
    

def extract_filing_office(page_dict):
    filing_office = page_dict["blocks"][4]["lines"][-1]["spans"][0]["text"]
    return filing_office


def extract_gs_info(page_dict):
    gs_info = {}
    goods_services = ""
    comments = ""
    for i in range (len(page_dict["blocks"][5]["lines"])):
        if 'italic' not in page_dict["blocks"][5]["lines"][i]["spans"][0]['font'].lower():
            goods_services += (page_dict["blocks"][5]["lines"][i]["spans"][0]["text"] + ", ")
        else:
            comments += (page_dict["blocks"][5]["lines"][i]["spans"][0]["text"] + ", ")
    goods_services = goods_services[:-2]
    comments = comments[:-2]
    gs_info = {
        "goods_services" : goods_services,
        "comments" : comments if len(comments) else None
    }
    return gs_info


def read_pdf(file):
    doc = fitz.open(stream = file.read(), filetype = "pdf")
    total_pages = doc.page_count
    # Finding Initial Page
    for page_n in range(total_pages):
        page = doc.load_page(page_n)
        page_json = page.get_text("json")
        page_dict = json.loads(page_json)
        if "Class" in page_dict["blocks"][0]["lines"][0]["spans"][0]["text"]:
            break
    init_page = page_n
    # Data Extraction from PDF
    result_list = []
    for page_n in range(init_page, total_pages):   
        result_dict = {
            "journal_page" : page_n + 1
        }
        try:
            page = doc.load_page(page_n)
            page_json = page.get_text("json")
            page_dict = json.loads(page_json)
            # Journal Information Extraction
            journal_info = extract_journal_info(page_dict)
            result_dict["journal_number"] = journal_info.get("journal_number")
            result_dict["journal_date"] = journal_info.get("journal_date")
            result_dict["journal_class"] = journal_info.get("journal_class")
            # Brand Header Extraction
            result_dict["brand_header"] = extract_brand_header(page_dict)
            # Application Number Extraction
            result_dict["application_number"] = extract_application_number(page_dict)
            # Application Date Extraction
            result_dict["application_date"] = extract_application_date(page_dict)
            # Company Information Extraction
            company_info = extract_company_info(page_dict)
            result_dict["company_name"] = company_info.get("company_name")
            result_dict["company_address"] = company_info.get("company_address")
            result_dict["company_status"] = company_info.get("company_status")
            # Advocate Information Extraction
            advocate_info = extract_advocate_info(page_dict)
            result_dict["advocate_name"] = advocate_info.get("advocate_name")
            result_dict["advocate_address"] = advocate_info.get("advocate_address")
            # Usage Status Extraction
            result_dict["usage_status"] = extract_usage_status(page_dict)
            # Filing Office Extraction
            result_dict["filing_office"] = extract_filing_office(page_dict)
            # Goods & Services Information Extraction
            gs_info = extract_gs_info(page_dict)
            result_dict["goods_services"] = gs_info.get("goods_services")
            result_dict["comments"] = gs_info.get("comments")
            result_list.append(result_dict)       
        except Exception as e:
            result_list.append(
                {
                    "journal_page" : page_n + 1
                }
            )
    # Convert List of Dictionaries to DataFrame
    result_df = pd.DataFrame(result_list)
    return result_df



def generate_result(client_df, journal_df):
    # Base Condition
    if client_df.shape[0] == 0 or journal_df.shape[0] == 0:
        return pd.DataFrame([{
            "journal_class" : None,
            "journal_trademark" : None,
            "journal_page" : None,
            "journal_date" : None,
            "application_date" : None
        }]), pd.DataFrame([{
            "client_class" : None,
            "client_trademark" : None,
            "journal_class" : None,
            "journal_trademark" : None,
            "journal_page" : None,
            "journal_date" : None,
            "application_date" : None
        }])
    empty_list, result_list = [], []
    for _, journal_row in journal_df.iterrows():
        if journal_row["brand_header"] is None or journal_row["journal_class"] is None:
            empty_list.append(
                {
                    "journal_class" : journal_row["journal_class"],
                    "journal_image" : None,
                    "journal_page" : journal_row["journal_page"],
                    "journal_date" : journal_row["journal_date"],
                    "application_date" : journal_row["application_date"]
                }
            )
        else:
            for _, client_row in client_df.iterrows():
                similarity_list = compute_similarity(journal_row["brand_header"], client_row["trade_mark"])
                if len(similarity_list):
                    result_list.append(
                        {
                            "client_class" : client_row["class"],
                            "client_trademark" : client_row["trade_mark"],
                            "journal_class" : journal_row["journal_class"],
                            "journal_trademark" : journal_row["brand_header"],
                            "journal_page" : journal_row["journal_page"],
                            "journal_date" : journal_row["journal_date"],
                            "application_date" : journal_row["application_date"]
                        }
                    )
    # Convert List of Dictionaries to DataFrame
    if len(empty_list) == 0:
        empty_df = pd.DataFrame([{
            "journal_class" : None,
            "journal_trademark" : None,
            "journal_page" : None,
            "journal_date" : None,
            "application_date" : None
        }])
    else:
        empty_df = pd.DataFrame(empty_list)
    if len(result_list) == 0:    
        result_df = pd.DataFrame([{
            "client_class" : None,
            "client_trademark" : None,
            "journal_class" : None,
            "journal_trademark" : None,
            "journal_page" : None,
            "journal_date" : None,
            "application_date" : None
        }])
    else:    
        result_df = pd.DataFrame(result_list)
    return empty_df, result_df