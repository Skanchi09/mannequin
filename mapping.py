import pandas as pd
import os
import csv
import sys
import subprocess
import re
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
EMU_USERS_FILE = os.getenv("EMU_USERS_FILE")
USER_MAPPINGS_FILE = os.getenv("USER_MAPPINGS_FILE")
ORG_NAME = os.getenv("ORG_NAME")
github_pat = os.getenv("GITHUB_TOKEN")

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

def verify_organization(org_name, gh_pat):
    command = ['gh', 'api', f'orgs/{org_name}', '--header', f'Authorization: token {gh_pat}']
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Organization {org_name} verified successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error verifying organization: Command returned non-zero exit status {e.returncode}")
        masked_command = [re.sub(r'(Authorization: token ).*', r'\1[REDACTED]', arg) if 'Authorization:' in arg else arg for arg in e.cmd]
        print(f"Command: {' '.join(masked_command)}")
        print(f"Return code: {e.returncode}")
        masked_output = re.sub(r'(Authorization: token ).*', r'\1[REDACTED]', e.output)
        print(f"Output: {masked_output}")
        masked_stderr = re.sub(r'(Authorization: token ).*', r'\1[REDACTED]', e.stderr)
        print(f"Error output: {masked_stderr}")

def run_reclaim_command(org_name, csv_file, gh_pat):
    command = f"gh gei reclaim-mannequin --github-target-org {org_name} --csv {csv_file} --github-target-pat {gh_pat}"
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("Reclaim command executed successfully:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error executing reclaim command: Command returned non-zero exit status {e.returncode}")
        masked_command = re.sub(r'(--github-target-pat ).*', r'\1[REDACTED]', e.cmd)
        print(f"Command: {masked_command}")
        print(f"Return code: {e.returncode}")
        masked_output = re.sub(r'(--github-target-pat ).*', r'\1[REDACTED]', e.output)
        print(f"Output: {masked_output}")
        masked_stderr = re.sub(r'(--github-target-pat ).*', r'\1[REDACTED]', e.stderr)
        print(f"Error output: {masked_stderr}")

def main():
    print("Executing migration script...")
    print(f"GITHUB_TOKEN: {'Set' if GITHUB_TOKEN else 'Not Set'}")
    print(f"ORG_NAME: {ORG_NAME}")
    print(f"EMU_USERS_FILE: {EMU_USERS_FILE}")
    print(f"USER_MAPPINGS_FILE: {USER_MAPPINGS_FILE}")

    if not GITHUB_TOKEN:
        print("GitHub token is not set. Please set the GITHUB_TOKEN environment variable.")
        sys.exit(1)

    if not all([EMU_USERS_FILE, USER_MAPPINGS_FILE, ORG_NAME]):
        print("Missing required environment variables. Ensure they are set correctly.")
        sys.exit(1)

    try:
        emu_users_df = read_excel_file(EMU_USERS_FILE)
        required_columns = {'login', 'name', 'saml_name_id'}
        if not required_columns.issubset(emu_users_df.columns):
            raise ValueError(f"Excel file must contain the following columns: {required_columns}")
        
        process_user_mappings(USER_MAPPINGS_FILE, emu_users_df, ORG_SUFFIX)
        
        verify_organization(ORG_NAME, github_pat)
        
        run_reclaim_command(ORG_NAME, USER_MAPPINGS_FILE, github_pat)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()