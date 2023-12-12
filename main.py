import cli
from aws_sso_menu import show_menu
from retrieve_aws_sso_token import retrieve_aws_sso_token
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse

def extract_region_from_url(url):
    # Send an HTTP GET request to the URL
    response = requests.get(url)

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Parse the HTML content of the page using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the <meta> tag with the name "region"
        region_meta = soup.find('meta', attrs={'name': 'region'})
        
        if region_meta:
            # Extract the content attribute of the <meta> tag
            region = region_meta.get('content')
            return region
        else:
            return None
    else:
        return None

def main(args):

    if args.start_url:
        # Check if the start_url is in a short format (e.g., "company")
        if not args.start_url.startswith("http"):
            # If it's not a full URL, assume it's a shorthand and create a full URL
            args.start_url = f"https://{args.start_url}.awsapps.com/start/"
        
        # Extract the region from the start_url
        extracted_region = extract_region_from_url(args.start_url)
        
        if extracted_region:
            args.region = extracted_region
        else:
            print("Failed to extract region from the start_url. Using the provided region.")
    
    print(f"Region: {args.region}")

    aws_sso_token = retrieve_aws_sso_token(args)

    if args.output_file:
        with open(args.output_file, 'w') as f:
            f.write(aws_sso_token)
            print(f"Wrote the AWS SSO token to {args.output_file}")

    show_menu(aws_sso_token, args.region)

if __name__ == "__main__":
    main(cli.parser.parse_args())
