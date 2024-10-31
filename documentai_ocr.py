import os, time
import logging
from dotenv import load_dotenv
from utils import setup_logging
from firewall_ops import get_vpc_firewall_rules, get_firewall_policy_rules
from bigquery_ops import clean_bigquery_tables
from org_ops import get_org_projects, list_resources_using_service_account
from service_account_ops import get_service_accounts, get_service_account_keys, get_service_account_roles_org_level, check_service_account_impersonation

# Load the .env file
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Initialize logger with DEBUG level for more verbosity
logger = setup_logging(logging.DEBUG)

# Retrieve environment variables and validate them
required_env_vars = {
    'organization_id': os.getenv('ORG_ID'),
    'dataset_id': os.getenv('BQ_DATASET_ID'),
    'projects_table_id': os.getenv('BQ_PROJECTS_TABLE_ID'),
    'service_accounts_table_id': os.getenv('BQ_SERVICE_ACCOUNTS_TABLE_ID'),
    'service_account_keys_table_id': os.getenv('BQ_SERVICE_ACCOUNT_KEYS_TABLE_ID'),
    'vpc_firewall_rules_table_id': os.getenv('BQ_VPC_FIREWALL_RULES_TABLE_ID'),
    'service_account_roles_table_id': os.getenv('BQ_SERVICE_ACCOUNT_ROLES_TABLE_ID'),
    'service_account_usage_table_id': os.getenv('BQ_SERVICE_ACCOUNT_USAGE_TABLE_ID'),
    'firewall_policy_rules_table_id': os.getenv('BQ_FIREWALL_POLICY_RULES_TABLE_ID')
}

# Validate all required environment variables
missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    logger.critical(f"Missing required environment variables: {', '.join(missing_vars)}")
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

def main():
    try:
        logger.info("Cleaning BigQuery tables.")
        # clean_bigquery_tables()
        # time.sleep(5)

        logger.info("Fetching VPC firewall rules.")
        get_vpc_firewall_rules(required_env_vars['organization_id'], required_env_vars['vpc_firewall_rules_table_id'])

        logger.info("Fetching Firewall policy rules.")
        get_firewall_policy_rules(required_env_vars['organization_id'], required_env_vars['firewall_policy_rules_table_id'])

        logger.info("Listing resources using service accounts.")
        list_resources_using_service_account(
            required_env_vars['organization_id'],
            [
                "compute.googleapis.com/Instance",
                "cloudfunctions.googleapis.com/CloudFunction",
                "cloudfunctions.googleapis.com/Function",
                "run.googleapis.com/Service",
            ], 
            required_env_vars['service_account_usage_table_id']
        )

        logger.info("Fetching service accounts.")
        service_account_emails = get_service_accounts(required_env_vars['organization_id'], required_env_vars['service_accounts_table_id'])
        
        for email in service_account_emails:
            logger.info(f"Fetching service account keys for {email}.")
            get_service_account_keys(email, required_env_vars['service_account_keys_table_id'])
            
            logger.info(f"Fetching service account roles for {email}.")
            get_service_account_roles_org_level(required_env_vars['organization_id'], email, required_env_vars['service_account_roles_table_id'])

        logger.info("Fetching organization projects.")
        project_data = get_org_projects(required_env_vars['organization_id'], required_env_vars['projects_table_id'])
        
        for project in project_data:
            for email in service_account_emails:
                logger.info(f"Checking service account impersonation for project {project['project_id']} and email {email}.")
                check_service_account_impersonation(project["project_id"], email, required_env_vars['service_account_usage_table_id'])

        logger.debug("Main function execution completed.")
    
    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
        raise e

if __name__ == '__main__':
    main()


# python main.py --header "Header Text" --footer "Footer Text"
# python main.py --header "ALFONSO CHASE" --footer "LOS JUEGOS FURTIVOS"