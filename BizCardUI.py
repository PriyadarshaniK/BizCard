import streamlit as st
import easyocr
import numpy as np
import os
import re
import cv2
import pymysql
from PIL import Image
import pandas as pd


# __file__ is the pathname of the file from which this module was loaded
# However, it can be a relative path, so the os.path.abspath() function is used to turn that into an absolute path before removing just the filename and storing the full path to the directory the module lives in
# This will be same root directory in which a tempDir will be created to store the biz card image files.
STREAMLIT_SCRIPT_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = ""



def convertToBinaryData(filepath):
    # Convert digital data to binary format
    with open(filepath, 'rb') as file: # opens the file in binary format for reading
        binaryData = file.read() # returns a byte object
    return binaryData


def get_data(res):

    for i in range(0,len(res)):
    
        # To get WEBSITE_URL
        if "www " in res[i][1].lower() or "www." in res[i][1].lower():
            card_data["website"] = (res[i][1])
        elif "WWW" in res[i][1]:
            card_data["website"] = res[i][1]
        
        # To get EMAIL ID
        elif "@" in res[i][1]:
            card_data["email"] = (res[i][1])

        # To get MOBILE NUMBER
        elif "-" in res[i][1]:
            # print(data["mobile_number"])
            if card_data["mobile_number"] == '':
                card_data["mobile_number"] = card_data["mobile_number"] + res[i][1]
            else:
                card_data["mobile_number"] = card_data["mobile_number"] + "," + res[i][1]
            
        # To get COMPANY NAME   - last value
        elif i == len(res)-1:
            card_data["company_name"]=(res[i][1])
        
        # To get CARD HOLDER NAME - first value
        elif i == 0:
            card_data["card_holder"]=(res[i][1])
        
        # To get DESIGNATION - second value
        elif i == 1:
            card_data["designation"]=(res[i][1])
        
        # To get AREA
        if re.findall('^[0-9].+, [a-zA-Z]+',res[i][1]):
            card_data["area"] = res[i][1]
        elif re.findall('[0-9] [a-zA-Z]+',res[i][1]):
            card_data["area"] = (res[i][1])
        
        # To get CITY NAME
        
        match1 = re.findall('.+St , ([a-zA-Z]+).+', res[i][1])
        match2 = re.findall('.+St,, ([a-zA-Z]+).+', res[i][1])
        match3 = re.findall('^[E].*',res[i][1])
        
        if match1:
            card_data["city"]=(match1[0])
        elif match2:
            card_data["city"]=(match2[0])
        elif match3:
            card_data["city"]=(match3[0])
        
        # To get STATE
        state_match = re.findall('[a-zA-Z]{9} +[0-9]',res[i][1])
        if state_match:
            card_data["state"]=(res[i][1][:9])
        elif re.findall('^[0-9].+, ([a-zA-Z]+);',res[i][1]):
            card_data["state"]=(res[i][1].split()[-1])
        
        # To get PINCODE        
        if len(res[i][1])>=6 and res[i][1].isdigit():
            card_data["pin_code"] = (res[i][1])
        elif re.findall('[a-zA-Z]{9} +[0-9]',res[i][1]):
            card_data["pin_code"] = (res[i][1][10:])
    
    
icon = Image.open("BizCardIcon.png") # loads the image to be used as icon

st.set_page_config(
    page_title="Business Card Data Extraction and Manipulation",
    page_icon= icon,
    layout="wide",
    initial_sidebar_state="expanded")

#Connect to MySQL DB using pymysql. DB and table created using BizCardDB script
mydb = pymysql.connect(
  host="localhost",
  user="root",
  password="123456789",
  database="bizcarddb"
  
)

mycursor = mydb.cursor()

# Insert card holder details into the table.
def InsertToTable():
    query = "SELECT EXISTS (SELECT * FROM card_details WHERE card_holder = '"+ card_data["card_holder"] + "') "
    mycursor.execute(query)
    result = mycursor.fetchall()
        
    if (result[0][0]):
        st.write("Biz Card Details of person:", card_data["card_holder"], " already exist in MySQL. Please choose a different card to upload!")
        return 0
    else:
        sql = """INSERT INTO card_details (company_name,card_holder,designation,mobile_number,email,website,area,city,state,pin_code,image)
                     VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
    
        insert_blob_tuple = (card_data["company_name"], card_data["card_holder"], card_data["designation"], card_data["mobile_number"],card_data["email"],card_data["website"],card_data["area"],card_data["city"],card_data["state"],card_data["pin_code"],card_data["image"])
        mycursor.execute(sql, insert_blob_tuple)
        
        # the connection is not autocommitted by default, so we must commit to save our changes
        mydb.commit()
        return 1

#select different card holder names from table - to be displayed in the drop down.
def cardholder_list():
    mycursor.execute(
        "SELECT DISTINCT card_holder FROM card_details " )
    names = mycursor.fetchall()
    name_list = [i[0] for i in names]
    return name_list

#Getting the reader ready for image processing
reader = easyocr.Reader(['en'])

#to highlight each part of the image from where data has been extracted.
def box_text(img,text):
    for t in text:
        # print(t)
        bbox, text, score = t
        l_bbox = bbox[0][0] # x co-ord of left top corner
        l_bbox1 = bbox[0][1] #y co-ord of left top corner
        r_bbox = bbox[2][0] #x co-ord of right bottom corner
        r_bbox1 = bbox[2][1] #y co-ord of right bottom corner

        cv2.rectangle(img, (int(l_bbox), int(l_bbox1)), (int(r_bbox), int(r_bbox1)), (0, 255, 0),2) #rectangle in green
        cv2.putText(img, text, (int(l_bbox), int(l_bbox1)), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0 ,0), 2) # text in red
    st.image(img) # display the image with the highlighted text areas and the text



#Create the first screen of the streamlit application, to display few radio buttons on the sidebar and for user inputs on the right.
header = st.container()

if 'card_content' not in st.session_state:
    st.session_state.card_content = [] # to hold the data read from the biz card.

sidebar1 = st.sidebar

with header:
    st.subheader("Business Card Data Extraction and Manipulation")

with sidebar1:
    selection = sidebar1.radio("What's your choice of task?",[":house: Home",":camera:(Extract Data)",":writing_hand:(Modify Data)" ])

#display general information about this project
if selection == ":house: Home": 
    st.markdown(" This application allows users to upload an image of a business card and extract relevant information from it using easyOCR.")
    st.markdown("The extracted information includes the company name, card holder name, designation, mobile number, email address, website URL, area, city, state, and pin code.")
    st.markdown("The extracted information is then displayed in the application's graphical user interface (GUI) rendered using Streamlit.")
    st.markdown("In addition, the application allows users to save the extracted information into a database along with the uploaded business card image.")
    st.markdown("The database has been created such that it is able to store multiple entries, each with its own business card image and extracted information.")
    st.markdown("To achieve this - Python, Streamlit, easyOCR, MySQL have been used.")
    st.markdown("The application has a simple and intuitive user interface that guides users through the process of uploading the business card image and extracting its information.")
    st.markdown("The extracted information is then displayed in a clean and organized manner, and users can easily add it to the database with the click of a button.")
    st.markdown("The user can Read the data, Update the data and delete the data through the streamlit UI.")
    st.markdown("This project required skills in image processing, OCR, GUI development, and database management.")

#Options to load the image file, save the extracted data, view the uploaded file and view the image with the text extracted, store the data into MySQl
if selection == ":camera:(Extract Data)":
    
    
    uploaded_file = st.file_uploader("Select a Business Card for Data Extraction",type=["png","jpeg","jpg"])
    
       
    if uploaded_file is not None :
        #get the file name and extension of the file uploaded and print it
        file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type}
        st.write(file_details)

        #save the uploaded file to hard disk.
        with open(os.path.join("tempDir", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("Saved File")
        IMAGE_PATH = f'{STREAMLIT_SCRIPT_FILE_PATH}/tempDir/{uploaded_file.name}'

        #dictionary to hold the card holder data
        card_data = {"company_name" : '',
            "card_holder" : '',
            "designation" : '',
            "mobile_number" :'',
            "email" : '',
            "website" : '',
            "area" : '',
            "city" : '',
            "state" : '',
            "pin_code" : '',
            "image" : convertToBinaryData(IMAGE_PATH)
           }

        
        st.session_state.card_content = reader.readtext(IMAGE_PATH)
        get_data(st.session_state.card_content) # function call to extract specific data from the complete bizcard data
            
        col2,col3 = st.columns([2,2]) # to view the uploaded image as it is, and to view the image after extracting data.
        with col2:
            ViewBtn = st.button("View uploaded business card image")
            if ViewBtn:
                st.image(uploaded_file)
        with col3:
            ViewMoreBtn = st.button("View extracted text image")
            if ViewMoreBtn:
                image= cv2.imread(IMAGE_PATH)                    
                box_text(image,  st.session_state.card_content)   # this function will display the image with the boxes highlighting the text read.

        col4,col5 = st.columns([2,2]) # Store card info in table and view card info after parsing the data.
        
        with col4:
            StoreDataBtn = st.button("Store Card Info in MySQL")
            if StoreDataBtn :
                retVal = InsertToTable() #function to store the card holder data into card_details table in MySQL
                if retVal == 1:
                    st.success("#### Uploaded to database successfully!")

        with col5:        
            ViewInfoBtn = st.button("View Card Info")
            
            if ViewInfoBtn:
                st.text("Company Name  - "+ card_data['company_name'])
                st.text("Card Holder   - " + card_data['card_holder'])
                st.text("Designation   - "+ card_data['designation'] )
                st.text("Mobile Number - "+card_data['mobile_number'])
                st.text("Email id      - "+card_data['email'])
                st.text("Website       - "+card_data['website'])
                st.text("Area          - "+card_data['area'])
                st.text("City          - "+card_data['city'])
                st.text("State         - "+card_data['state'])
                st.text("Pin Code      - "+card_data['pin_code'])
            
#options to edit the existing data or Delete data
if selection == ":writing_hand:(Modify Data)":

    ModifyCH = st.selectbox('Select the card holder to modify', options = cardholder_list())

    if (len(cardholder_list()) == 0):
        st.write("Please upload card details into database") #no details exist in table, first upload to modify/delete
    else:
        ConfirmDisp = st.checkbox("Display Details of selected Card Holder")
        
        if ConfirmDisp:
            col6,col7 = st.columns([2,2])
            with col6:
                mycursor.execute("select company_name,designation,mobile_number,email,website,area,city,state,pin_code from card_details WHERE card_holder=%s",
                                    (ModifyCH))
                result = mycursor.fetchone()
                
                comp_new = st.text_input('Company name: ', result[0])
                design_new = st.text_input('Designation: ', result[1])
                mob_new = st.text_input('Mobile Number: ', result[2])
                email_new = st.text_input('Email: ', result[3])
                website_new = st.text_input('Website: ', result[4])
            with col7:
                area_new = st.text_input('Area: ', result[5])
                city_new = st.text_input('City: ', result[6])
                state_new = st.text_input('State: ', result[7])
                pin_new = st.text_input('PinCode: ', result[8])
        
            if st.button("Save Changes"):
                # Update the information for the selected business card in the database
                mycursor.execute("""UPDATE card_details SET company_name=%s,designation=%s,mobile_number=%s,email=%s,website=%s,area=%s,city=%s,state=%s,pin_code=%s
                                    WHERE card_holder=%s""", (comp_new,design_new,mob_new,email_new,website_new,area_new,city_new,state_new,pin_new,ModifyCH))
                mydb.commit()
                st.success("Information updated in database successfully.")
    
        ConfirmDel = st.checkbox("Delete Details of selected Card Holder")
        if ConfirmDel:
            st.error("Are you sure you want to delete?")
            if st.button("Yes"):
                mycursor.execute("""DELETE FROM card_details WHERE card_holder = %s""", (ModifyCH))
                mydb.commit()
                st.success("Business card information deleted from database.")        
