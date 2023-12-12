import time
import re
import boto3
import botocore
import requests
import base64
import os

#def save_url_to_html_file():
#	print("\n")

def create_oidc_application(sso_oidc_client):
    print("Creating temporary AWS SSO OIDC application")
    client = sso_oidc_client.register_client(
        clientName='never-gonna-give-you-up',
        clientType='public'
    )
    client_id = client.get('clientId')
    client_secret = client.get('clientSecret')
    return client_id, client_secret


def initiate_device_code_flow(sso_oidc_client, oidc_application, start_url):
    print("Initiating device code flow")
    authz = sso_oidc_client.start_device_authorization(
        clientId=oidc_application[0],
        clientSecret=oidc_application[1],
        startUrl=start_url
    )

    url = authz.get('verificationUriComplete')
    deviceCode = authz.get('deviceCode')
    return url, deviceCode


def create_device_code_url(sso_oidc_client, start_url):
    oidc_application = create_oidc_application(sso_oidc_client)
    url, device_code = initiate_device_code_flow(sso_oidc_client, oidc_application, start_url)
    return url, device_code, oidc_application


def await_user_prompt_validation(sso_oidc_client, oidc_application, device_code, sleep_interval=3):
    sso_token = ''
    print("\nWaiting indefinitely for the user to validate the AWS SSO prompt...")
    while True:
        time.sleep(sleep_interval)
        try:
            token_response = sso_oidc_client.create_token(
                clientId=oidc_application[0],
                clientSecret=oidc_application[1],
                grantType="urn:ietf:params:oauth:grant-type:device_code",
                deviceCode=device_code
            )
            aws_sso_token = token_response.get('accessToken')
            return aws_sso_token
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] != 'AuthorizationPendingException':
                raise e




def retrieve_aws_sso_token(args):
    if args.sso_token_file:
        # If an SSO token file is provided, read the token from the file
        with open(args.sso_token_file) as f:
            aws_sso_token = f.read().strip()
        print(f"Read AWS SSO token from {args.sso_token_file}")
    else:
        # If no SSO token file is provided, initiate the SSO authentication process
        sso_oidc_client = boto3.client('sso-oidc', region_name=args.region)
        url, device_code, oidc_application = create_device_code_url(sso_oidc_client, args.start_url)
        print(f"Device code URL: {url}")

        # Extract the user code from the URL
        match = re.search(r'user_code=([^&]+)', url)

        if match:
            code = match.group(1)
            print(f"Extracted code: {code}")

            verification_url = f"https://oidc.{args.region}.amazonaws.com/device_verification?user_code={code}"
            print(f"\nVerification URL: {verification_url}")

            response = requests.get(verification_url)
            response_json = response.json()

            client_id = response_json.get("deviceContext", {}).get("clientId")
            device_context_id = response_json.get("deviceContext", {}).get("deviceContextId")
            location_url = response_json.get("location")

            # Encode client ID and device context ID
            encoded_client_id = base64.b64encode(client_id.encode()).decode()
            encoded_device_context_id = base64.b64encode(device_context_id.encode()).decode()

            final_url = f"{location_url}?clientId={encoded_client_id}&clientType=aGFzQ29uc2VudERldGFpbHNwdWJsaWM=&deviceContextId={encoded_device_context_id}"
            
            # Save the final URL to an HTML file
 #           save_url_to_html_file(final_url, 'index.html')
            print(f"\nFinal URL: {final_url}")

            # Prompt the user for validation and retrieve the AWS SSO token
            aws_sso_token = await_user_prompt_validation(sso_oidc_client, oidc_application, device_code)
            print("Successfully retrieved AWS SSO token!")
        else:
            print("Code not found in the URL.")
            aws_sso_token = None

    return aws_sso_token
