import pandas as pd
import os
import csv
import sys

# Access the environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
EMU_USERS_FILE = os.getenv("EMU_USERS_FILE")
USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE")
ORG_NAME = os.getenv("ORG_NAME")

# Extract base organization name (e.g., 'mgmri' from 'mgmri-dge')
ORG_SUFFIX = ORG_NAME.split('-')[0] if ORG_NAME else ''

def read_excel_file(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Excel file {file_name} not found")
    print(f"Reading Excel file: {file_name}")
    return pd.read_excel(file_name)

def read_csv_file(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"CSV file {file_name} not found")
    print(f"Reading CSV file: {file_name}")
    with open(file_name, mode='r', newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))

def update_csv_file(file_name, mappings):
    print(f"Writing updates back to the CSV file: {file_name}")
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["mannequin-user", "mannequin-id", "target-user"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)
    print("CSV file updated successfully.")

def process_user_mappings(user_mappings_file, emu_users_df, org_suffix):
    print("Processing user mappings...")
    mappings = read_csv_file(user_mappings_file)

    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        matched_user = emu_users_df[emu_users_df['login'] == mannequin_user]
        if matched_user.empty:
            print(f"No match found for mannequin-user: {mannequin_user}")
            continue

        email = matched_user.iloc[0]["saml_name_id"]
        empirical_part = email.split('@')[0]
        target_user = f"{empirical_part}_{org_suffix}"

        mapping["target-user"] = target_user
        print(f"Updated target-user for {mannequin_user} to {target_user}")

    update_csv_file(user_mappings_file, mappings)

def main():
    print("Executing migration script...")
    if not all([GITHUB_TOKEN, EMU_USERS_FILE, USER_MAPPINGS_FILE, ORG_NAME]):
        print("Missing required environment variables. Ensure they are set correctly.")
        print(f"GITHUB_TOKEN: {'Set' if GITHUB_TOKEN else 'Not Set'}")
        print(f"EMU_USERS_FILE: {EMU_USERS_FILE}")
        print(f"USER_MAPPINGS_FILE: {USER_MAPPINGS_FILE}")
        print(f"ORG_NAME: {ORG_NAME}")
        sys.exit(1)

    try:
        emu_users_df = read_excel_file(EMU_USERS_FILE)
        required_columns = {'login', 'name', 'saml_name_id'}
        if not required_columns.issubset(emu_users_df.columns):
            raise ValueError(f"Excel file must contain the following columns: {required_columns}")
        
        process_user_mappings(USER_MAPPINGS_FILE, emu_users_df, ORG_SUFFIX)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()