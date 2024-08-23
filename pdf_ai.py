import requests
import base64
import json
import os
from PyPDF2 import PdfReader, PdfWriter, errors
from pdf2image import convert_from_path, exceptions
from g4f.client import Client
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

directory_path = r'c:/_mydata/JobNSTDAOCR'  # path ที่เก็บ PDF file
output_folder_jpg = 'c:/_mydata/JobNSTDAOCR/jpg_temp'  # path temp สำหรับ หน้า pdf ที่เป็น jpg
output_folder_jpg = r"c:/t1/"
script_url = ""  # แทนที่ด้วย URL Apps Script

# ฟังก์ชันสำหรับสรุปข้อความ
def summarize_text(text):
    client = Client()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "คุณเป็นผู้ช่วยที่เชี่ยวชาญในการสรุปความข้อความภาษาไทย."},
            {"role": "user", "content": f"กรุณาสรุปข้อความต่อไปนี้ในแบบสั้นในภาษาไทย: [{text}]"},
        ]
    )
    return response.choices[0].message.content

# ฟังก์ชันสำหรับสรุปคำสำคัญจากข้อความ
def summarize_keyword(text):
    client = Client()
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "คุณเป็นผู้ช่วยที่เชี่ยวชาญในการสรุปคำสำคัญจากข้อความภาษาไทย."},
            {"role": "user", "content": f"กรุณาดึงคำสำคัญจากข้อความต่อไปนี้โดยเน้นที่คีย์: การตลาด, เทคโนโลยี จากข้อความ: [{text}]"},
        ]
    )
    return response.choices[0].message.content


def send_image_to_apps_script(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')

    payload = {"image": encoded_string}
    headers = {"Content-Type": "application/json"}
    response = requests.post(script_url, data=json.dumps(payload), headers=headers)

    if response.status_code == 200:
        return response.content.decode('utf-8')
    else:
        print("Error:", response.status_code, response.text)
        return None


def split_pdf_to_pages(pdf_path, output_folder):
    with open(pdf_path, 'rb') as file:
        reader = PdfReader(file)
        for page_num in range(len(reader.pages)):
            writer = PdfWriter()
            writer.add_page(reader.pages[page_num])
            output_filename = f'{output_folder}/{page_num + 1}.pdf'
            with open(output_filename, 'wb') as output_file:
                writer.write(output_file)
            convert_pdf_pages_to_jpg(output_filename, output_folder)


def convert_pdf_pages_to_jpg(pdf_path, output_folder):
    poppler_path = r'C:\JobNSTDAOCR\poppler\bin'  # Replace with your actual path
    try:
        images = convert_from_path(pdf_path, poppler_path=poppler_path)
        filename = os.path.splitext(os.path.basename(pdf_path))[0]
        for i, image in enumerate(images):
            image.save(f'{output_folder}/{filename}-{i + 1}.jpg', 'JPEG')
    except exceptions.PDFPageCountError as e:
        print(f"Error processing {pdf_path}: {e}")
        return None

def get_page_count(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            return len(reader.pages)
    except (errors.PdfReadError, OSError) as e:
        print(f"Error: Unable to read {pdf_path}. PDF may be corrupted or invalid. Error: {e}")
        return 0

dic = []
if os.path.exists("dic.json"):
    with open("dic.json", "r", encoding="utf-8") as f:
        dic = json.load(f)
directory_path = r'C:\JobNSTDAOCR\t1'

for root, dirs, files in os.walk(directory_path):
    for file_name in files:
        if file_name.endswith(".pdf") and file_name not in [d['filename'] for d in dic]:
            full_path = os.path.join(root, file_name)

            page_count = get_page_count(full_path)
            if page_count == 0:
                print(f"Skipping file {file_name} due to unreadable PDF.")
                continue

            convert_pdf_pages_to_jpg(full_path, output_folder_jpg)
            
            file_data = {
                "filename": file_name,
                "path": full_path,
                "pages": []
            }

            # file_data = {
            #     "filename": file_name,
            #     "path": full_path,
            #     "pages": [],
            #     "sumtext": "",
            #     "keytext": ""
            # }

            combined_text = ""

            for i in range(1, page_count + 1):
                file_name_only = os.path.splitext(file_name)[0]
                filename_jpg = f"{output_folder_jpg}/{file_name_only}-{i}.jpg"
                
                if os.path.exists(filename_jpg):
                    text = send_image_to_apps_script(filename_jpg)
                    if text:
                        file_data["pages"].append({"page": str(i), "text": text})
                        combined_text += " " + text
                    # os.remove(filename_jpg)
                else:
                    break
            
            # if combined_text:
            #     file_data["sumtext"] = summarize_text(combined_text)
            #     file_data["keytext"] = summarize_keyword(combined_text)

            dic.append(file_data)
            # Print the current count of items in dic
            print(f"Total files processed: {len(dic)}")

            with open("dic.json", "w", encoding="utf-8") as f:
                json.dump(dic, f, indent=4, ensure_ascii=False)
