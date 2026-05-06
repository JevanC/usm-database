import pandas as pd
import json
import os
import streamlit as st
from thefuzz import fuzz
from thefuzz import process


def clean_data(csv, name="EVENT NAME", location="LOCATION", year=1901):

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
            except Exception:
                continue
        return df

    def correct_columns(df):
        expected_columns = [
            "First Name",
            "Last Name",
            "Birth Date",
            "Email",
            "Phone Number",
            "Ticket Type",
            "Home Address 1",
            "Home City",
            "Home State",
            "Home Zip",
            "Gender",
            "Major or Profession",
            "Order Date",
            "What school are you currently attending?",
            "Total Paid",
            "Fees Paid",
            'Please specify which nights:'

        ]

        st.subheader("📋 Column Mapping")
        st.write("Map each required field to your CSV's column names:")

        user_mapping = {}
        for col in expected_columns:
            selected_col = st.selectbox(
                f"Select column for '{col}' (or '--None--' to skip)",
                options=["--None--"] + list(df.columns),
                key=f"map_{col.replace(' ', '_')}"
            )
            user_mapping[col] = selected_col if selected_col != "--None--" else None

        st.session_state.proceed = st.button("✅ Continue with selected columns")

        if st.session_state.proceed:
            cleaned_df = pd.DataFrame()
            for standard_col, user_col in user_mapping.items():
                if user_col is not None:
                    cleaned_df[standard_col] = df[user_col]
                else:
                    cleaned_df[standard_col] = None  

            st.session_state.cleaned_df = cleaned_df
            st.success("✅ Column mapping complete. Proceeding to preprocessing.")
            st.rerun()

        if "cleaned_df" in st.session_state:
            return st.session_state.cleaned_df
        else:
            st.stop()  

    def preprocess_csv(df):
        df = correct_columns(df)
        st.write(df)
        st.write("✅ Total Paid before fill:", df.head())
        df['Order Date'] = pd.to_datetime(df['Order Date'], utc=True).dt.tz_convert('America/Los_Angeles')
        df['Total Paid'] = df['Total Paid'].fillna(float(st.session_state.at_door_cost))
        df['Fees Paid'] = df['Fees Paid'].fillna(0)
        df['Ticket Type'] = df['Ticket Type'].fillna("at the door")
        df['Last Name'] = df['Last Name'].astype(str).str.strip().replace("", "UNKNOWN").fillna("UNKNOWN")
        df['Birth Date'] = df['Birth Date'].fillna("1901-01-01")

        df['Birth Date'] = pd.to_datetime(df['Birth Date'], errors='coerce')
        df['Birth Date'] = df['Birth Date'].dt.strftime('%Y-%m-%d')
        df.loc[df['Birth Date'].isna(), 'Birth Date'] = None

        df = lowercase_columns(df)

        if 'Phone Number' in df.columns and df['Phone Number'].notna().any():
            df['Phone Number'] = df['Phone Number'].astype(str).str.replace(r'\.0$', '', regex=True)
            df['Phone Number'] = df['Phone Number'].str.replace(r'[-()\s]', '', regex=True)


        if 'Ticket Type' in df.columns:
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
                    st.session_state.index += 1
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
                            st.session_state.index += 1
                            st.rerun()
                        else:
                            st.write("NOT IN MAPPING")

            else:
                st.session_state.renamed.append(school_mapping.get(school, school))
                st.session_state.index += 1
                st.rerun()

        student_df = df.copy()

        def get_school(row):
            school = row['What school are you currently attending?']
            if pd.isna(school):
                return "N/A"
            if school and school.strip().lower() != "other":
                return school
            return row.get('What school do you currently attend?', "N/A")

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

        student_df = student_df[['Order Date', 'First Name', 'Last Name', 'Home Address 1', 'Home City', 'Home State', 'Home Zip', 'Phone Number', 'Gender', 'Birth Date', 'Major or Profession', 'What school are you currently attending?']]
        student_df = student_df.reset_index(drop=True).drop_duplicates()

        save_mapping(school_mapping_file, school_mapping)
        student_df['Order Date'] = pd.to_datetime(student_df['Order Date'], errors='coerce')
        student_df = student_df.sort_values(by=['Order Date'])
        
        student_df = student_df.groupby(['First Name', 'Last Name', 'Birth Date'], dropna=False).last().reset_index()
        return student_df

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
        sales_df = sales_df[['First Name', 'Last Name', 'Birth Date', 'Ticket Type', 'Total Paid', 'Fees Paid', 'Please specify which nights:']]
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

    def get_ticket_types_csv(df):
        tickets = df.copy()[['Ticket Type']].dropna().drop_duplicates()
        return tickets

    def clean_csv(filename, event_name, event_year, event_location):
        df =filename
        df = preprocess_csv(df)
        df.loc[df['Ticket Type'] == 'regular registration', 'Ticket Type'] = 'general registration'
        df.loc[df['Ticket Type'] == 'early bird', 'Ticket Type'] = 'early bird registration'
        participant_csv = clean_participant_csv(df)
        sales_csv = clean_sales_csv(df)
        tickets_csv = get_ticket_types_csv(df)
        clean_data = participant_csv.merge(sales_csv)
        clean_data['event_name'] = event_name
        clean_data['event_year'] = event_year
        clean_data['event_location'] = event_location

        clean_data.to_csv(f'clean_data_{event_year}.csv')

        return clean_data

    clean_data_result = clean_csv(csv, event_name=name, event_year=year, event_location=location)
    return clean_data_result


def clean_universities(raw_df):
    raw_df.columns = raw_df.columns.str.lower()
    df = raw_df[['name', 'latitude', 'longitude', 'city', 'state', 'zip', 'county', 'country']]
    return df
