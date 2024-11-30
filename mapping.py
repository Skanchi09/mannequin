import pandas as pd
import os
import csv

# Access the environment variables
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Set in GitHub Secrets
EMU_USERS_FILE = os.getenv("EMU_USERS_FILE")  # Non-sensitive, from GitHub Variables
USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE")  # Non-sensitive, from GitHub Variables
ORG_NAME = os.getenv("ORG_NAME")  # Set in GitHub Secrets or Variables

# Extract base organization name (e.g., 'mgmri' from 'mgmri-dge')
ORG_SUFFIX = ORG_NAME.split('-')[0] if ORG_NAME else ''

# Function to read the Excel file
def read_excel_file(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"Excel file {file_name} not found")
    print(f"Reading Excel file: {file_name}")
    return pd.read_excel(file_name)

# Function to read the user mappings CSV file
def read_csv_file(file_name):
    if not os.path.exists(file_name):
        raise FileNotFoundError(f"CSV file {file_name} not found")
    print(f"Reading CSV file: {file_name}")
    with open(file_name, mode='r', newline='', encoding='utf-8') as file:
        return list(csv.DictReader(file))

# Function to update target-user column in the CSV file
def update_csv_file(file_name, mappings):
    print(f"Writing updates back to the CSV file: {file_name}")
    with open(file_name, mode='w', newline='', encoding='utf-8') as file:
        fieldnames = ["mannequin-user", "mannequin-id", "target-user"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mappings)
    print("CSV file updated successfully.")

# Function to process user mappings
def process_user_mappings(user_mappings_file, emu_users_df, org_suffix):
    print("Processing user mappings...")
    mappings = read_csv_file(user_mappings_file)

    for mapping in mappings:
        mannequin_user = mapping.get("mannequin-user")
        if not mannequin_user:
            print(f"Skipping row due to missing 'mannequin-user': {mapping}")
            continue

        # Find the user in the Excel sheet (matching mannequin-user with login or name)
        matched_user = emu_users_df[emu_users_df['login'] == mannequin_user]
        if matched_user.empty:
            print(f"No match found for mannequin-user: {mannequin_user}")
            continue

        # Assuming email-like data is in the 'saml_name_id' field
        email = matched_user.iloc[0]["saml_name_id"]

        # Extract the empirical part before the '@' and append '_ORG_SUFFIX'
        empirical_part = email.split('@')[0]
        target_user = f"{empirical_part}_{org_suffix}"

        # Update the target-user column in the mapping
        mapping["target-user"] = target_user
        print(f"Updated target-user for {mannequin_user} to {target_user}")

    # Update the CSV file with the new target-user values
    update_csv_file(user_mappings_file, mappings)

# Main function to execute the process
def main():
    print("Executing migration script...")
    if not (GITHUB_TOKEN and EMU_USERS_FILE and USER_MAPPINGS_FILE and ORG_NAME):
        raise ValueError("Missing required environment variables. Ensure they are set correctly.")

    # Load the EMU users Excel file
    emu_users_df = read_excel_file(EMU_USERS_FILE)

    # Check if the required columns are present in the Excel file
    required_columns = {'login', 'name', 'saml_name_id'}
    if not required_columns.issubset(emu_users_df.columns):
        raise ValueError(f"Excel file must contain the following columns: {required_columns}")

    # Process user mappings and update the CSV file
    process_user_mappings(USER_MAPPINGS_FILE, emu_users_df, ORG_SUFFIX)

if __name__ == "__main__":
    main()