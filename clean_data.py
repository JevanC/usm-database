import pandas as pd
import json
import os
import streamlit as st
from thefuzz import fuzz
from thefuzz import process

def clean_data(csv, name="EVENT NAME", location = "LOCATION", year=1901):

    def load_mapping(file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as file:
                return json.load(file)
        else:
            return {}

    def save_mapping(file_path, mapping):
        with open(file_path, 'w') as file:
            json.dump(mapping, file, indent=4)

    def lowercase_columns(df):
        for col in df.columns:
            try:
                df[col] = df[col].str.lower()
            except:
                continue
        return df

    def preprocess_csv(df):
        df['Last Name'] = df['Last Name'].astype(str).str.strip().replace("", "UNKNOWN").fillna("UNKNOWN")

        df['Birth Date'] = df['Birth Date'].astype(str).str.strip().replace("", "1901-01-01").fillna("1901-01-01")
        df['Birth Date'] = pd.to_datetime(df['Birth Date'], errors='coerce').fillna(pd.Timestamp("1901-01-01"))

        #df['Order Date'] = df['Order Date'].astype(str).str.strip().replace("", "2023-11-10 00:00:00").fillna("2023-11-10 00:00:00")
        #df['Order Date'] = pd.to_datetime(df['Order Date'], errors='coerce').fillna(pd.Timestamp("2023-11-10 00:00:00"))


        # Try multiple formats to correctly parse all dates
        df['Birth Date'] = pd.to_datetime(df['Birth Date'], errors='coerce')
        # Convert back to string in YYYY-MM-DD format
        df['Birth Date'] = df['Birth Date'].dt.strftime('%Y-%m-%d')
        df = lowercase_columns(df)
        df['Cell Phone'] = df['Cell Phone'].astype(str).str.replace(r'[-()\s]', '', regex=True)
        df.loc[df['Ticket Type'] == 'no hotel - 3 day pass', 'Ticket Type'] = 'no-hotel ticket option'
        df.loc[df['First Name'].str.split(' ').str.len() == 2, 'First Name'] = df['First Name'].str.split(' ').str.get(0)
        df.loc[df['Last Name'].str.split(' ').str.len() == 2, 'Last Name'] = df['Last Name'].str.split(' ').str.get(1)

        return df



    def clean_participant_csv(df):

        school_mapping_file = 'Raw Data/school_mapping.json'
        school_mapping = load_mapping(school_mapping_file)

        def normalize_schools(school):
            if pd.isna(school):
                return "N/A"

            school = school.strip().lower()
            

            if school not in school_mapping:
                if "high school" in school or "highschool" in school:
                    st.session_state.index+=1
                    st.session_state.renamed.append("high school")
                    st.rerun()
                else:
                    school_key = f"input_{st.session_state.index}"
                    new_name = st.text_input("New Name For this School", key=school_key, value=school)
                    add_to_mapping = st.text_input("What Should this be mapped to?", key=f"{school_key}_mapping")
                    if st.button("Next School"):
                        new_name = new_name.lower().strip()
                        if add_to_mapping != "":
                            add_to_mapping = add_to_mapping.lower().strip()
                            school_mapping[new_name] = add_to_mapping
                            save_mapping(file_path=school_mapping_file, mapping=school_mapping)
                        if new_name in school_mapping:
                            st.session_state.renamed.append(school_mapping.get(new_name, school))
                            st.session_state.index+=1
                            st.rerun()
                        else:
                            st.write("NOT IN MAPPING")
                
            else:
                st.session_state.renamed.append(school_mapping.get(school, school))
                st.session_state.index+=1
                st.rerun()
            
            

        student_df = df.copy()

        def get_school(row):
            school = row['What school are you currently attending?']
            if pd.isna(school):
                return "N/A"
            if school and school.strip().lower() != "other":
                return school
            return row['What school do you currently attend?']
        
        student_df['What school are you currently attending?'] = student_df.apply(get_school, axis=1)
        
        
        if "index" not in st.session_state:
            st.session_state.index = 0
        if "renamed" not in st.session_state:
            st.session_state.renamed = []
        
        if st.session_state.index < len(student_df['What school are you currently attending?']):
            st.write(f"Processing {st.session_state.index + 1} of {len(student_df)}")
            st.write(student_df['What school are you currently attending?'].iloc[st.session_state.index])
            normalize_schools(student_df['What school are you currently attending?'].iloc[st.session_state.index])
        else:
            st.success("All Done!")
            student_df['What school are you currently attending?'] = st.session_state.renamed

        student_df = student_df[['Order Date', 'First Name', 'Last Name', 'Home Address 1', 'Home City', 'Home State', 'Home Zip', 'Cell Phone', 'Gender', 'Birth Date', 'What is your major/profession?', 'What school are you currently attending?']]
        student_df = student_df.reset_index(drop=True).drop_duplicates()

        save_mapping(school_mapping_file, school_mapping)
        student_df['Order Date'] = pd.to_datetime(student_df['Order Date'], errors='coerce')
        student_df = student_df.sort_values(by=['Order Date'])
        student_df = student_df.groupby(['First Name', 'Last Name', 'Birth Date']).last().reset_index()
        return student_df
        student_df.to_csv('USM_Participant_table.csv', index=False)


    def clean_sales_csv(df):
        def combine(string):
            new_string = ""
            for i in string:
                if not pd.isna(i):
                    if new_string == "":
                        new_string += i
                    else:
                        if i not in new_string:
                            new_string += f' | {i}'
            return new_string

        def nights_stayed(df):
            df['friday_hotel'] = df['Please specify which nights:'].str.contains('friday', case=False, na=False)
            df['saturday_hotel'] = df['Please specify which nights:'].str.contains('saturday', case=False, na=False)
            df['sunday_hotel'] = df['Ticket Type'].str.contains('sunday night hotel accomodation', case=False, na=False)
            df = df.drop(columns=['Please specify which nights:'])
            return df

        sales_df = df.copy()
        sales_df = sales_df[['First Name', 'Last Name', 'Birth Date', 'Ticket Type', 'Price Tier', 'Total Paid', 'Fees Paid', 'Please specify which nights:']]
        sales_df['Price Tier'] = sales_df['Price Tier'].fillna('')
        sales_df = (sales_df.groupby(['First Name', 'Last Name', 'Birth Date']).agg({
            'Ticket Type': combine,
            'Total Paid': 'sum', 
            'Fees Paid': 'sum',
            'Please specify which nights:': combine
        }).reset_index())

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None) 
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)

        sales_df = nights_stayed(sales_df)
        sales_df['Ticket Type'] = sales_df['Ticket Type'].str.replace('sunday night hotel accomodation *optional*', '').str.replace('|', '').str.strip()
        return sales_df
        sales_df.to_csv('USM_sales_table.csv', index=False)

    def get_ticket_types_csv(df):
        tickets = df.copy()[['Ticket Type']].dropna().drop_duplicates()
        return tickets
        tickets.to_csv('USM_ticket_types_table.csv', index=False)

    def clean_csv(filename, event_name, event_year, event_location):
        df = preprocess_csv(filename)
        df[df['Ticket Type'] == 'regular registration']['Ticket Type'] = 'general registration'
        df[df['Ticket Type'] == 'early bird']['Ticket Type'] = 'early bird registration'
        participant_csv =  clean_participant_csv(df)
        sales_csv = clean_sales_csv(df)
        tickets_csv = get_ticket_types_csv(df)
        clean_data = participant_csv.merge(sales_csv)
        clean_data['event_name'] = event_name
        clean_data['event_year'] = event_year
        clean_data['event_location'] = event_location
        
        return clean_data

    clean_data = clean_csv(csv, event_name=name, 
            event_year=year, event_location=location)
    clean_data.to_csv(f'clean_data_{year}csv')

    return clean_data

def clean_universities(raw_df):
    raw_df.columns = raw_df.columns.str.lower()
    df = raw_df[['name', 'latitude', 'longitude', 'city', 'state', 'zip', 'county', 'country']]
    return df

#raw_df = pd.read_csv('Raw Data/raw_us_colleges_and_universities.csv', delimiter=';')
#clean_universities(raw_df).to_csv('Clean Data/clean_us_colleges_and_universities.csv')

#clean_data(pd.read_csv('Raw Data/USM_attendee_2022.csv'))
df = pd.read_csv('Clean Data/clean_us_colleges_and_universities.csv')
with open("Raw Data/school_mapping.json", 'r') as file:
    schools = list(json.load(file).values())


for i in schools:
    best_match = process.extractOne(i, list(df['name']))
    print(f"{i} is being matched with {best_match}\n\n")