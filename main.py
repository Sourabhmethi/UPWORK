import os
import pandas as pd
import requests
import time
import google.generativeai as genai
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load environment variables from .env file
load_dotenv()

# Configure API keys
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
MODEL_NAME = "gemini-2.0-flash"  # Fixed model name

def test_api_keys():
    """Test if API keys are working correctly."""
    print("=" * 50)
    print("API KEY VALIDATION TEST")
    print("=" * 50)
    
    success = True
    
    # Test Google Maps API
    print("\nTesting Google Maps API key...")
    if not GOOGLE_MAPS_API_KEY:
        print("✗ Google Maps API key not found in environment variables.")
        success = False
    else:
        try:
            url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
            params = {
                "input": "Google Headquarters",
                "inputtype": "textquery",
                "fields": "place_id,name",
                "key": GOOGLE_MAPS_API_KEY
            }
            response = requests.get(url, params=params)
            result = response.json()
            
            if result.get('status') == 'OK':
                print("✓ Google Maps API key is working!")
            elif result.get('status') == 'REQUEST_DENIED':
                print("✗ Google Maps API key is invalid or has issues.")
                print(f"Error message: {result.get('error_message')}")
                success = False
            else:
                print(f"✗ Google Maps API returned status: {result.get('status')}")
                print(f"Error message: {result.get('error_message', 'No specific error message')}")
                success = False
        except Exception as e:
            print(f"✗ Error testing Google Maps API: {e}")
            success = False
    
    # Test Gemini API
    print("\nTesting Gemini API key...")
    if not GEMINI_API_KEY:
        print("✗ Gemini API key not found in environment variables.")
        success = False
    else:
        try:
            # Directly test the Gemini 2.0 Flash model
            print(f"Testing specific model: {MODEL_NAME}")
            model = genai.GenerativeModel(MODEL_NAME)
            response = model.generate_content("Hello, this is a test message.")
            
            if response and hasattr(response, 'text'):
                print("✓ Gemini API key is working!")
                print(f"✓ Successfully connected to {MODEL_NAME} model")
                print(f"Sample response: {response.text[:50]}...")
            else:
                print("✗ Gemini API responded but with an unexpected format.")
                success = False
        except Exception as e:
            print(f"✗ Error testing Gemini API with {MODEL_NAME}: {e}")
            print("Checking for alternative Gemini models...")
            
            try:
                # List available models as fallback
                available_models = genai.list_models()
                gemini_models = [model.name for model in available_models if 'gemini' in model.name.lower()]
                
                if gemini_models:
                    print(f"Available Gemini models: {gemini_models}")
                    print(f"Note: Could not access {MODEL_NAME}, but other Gemini models are available.")
                else:
                    print("No Gemini models found.")
                    
                success = False
            except Exception as inner_e:
                print(f"✗ Error listing Gemini models: {inner_e}")
                success = False
    
    print("\nAPI TEST SUMMARY:")
    if success:
        print("✓ All API keys are working correctly!")
    else:
        print("✗ Some API keys are not working. Please check the details above.")
    
    print("=" * 50)
    return success

class BusinessDataProcessor:
    def __init__(self, input_file, output_file):
        """Initialize the Business Data Processor with input and output files."""
        self.input_file = input_file
        self.output_file = output_file
        self.df = None
        self.gemini_model_name = MODEL_NAME  # Use the fixed model name
        
    def load_data(self):
        """Load business data from Excel file."""
        try:
            if not os.path.exists(self.input_file):
                print(f"Error: Input file '{self.input_file}' not found.")
                return False
                
            self.df = pd.read_excel(self.input_file)
            
            # Check if dataframe is empty
            if len(self.df) == 0:
                print(f"Error: Input file '{self.input_file}' contains no data.")
                return False
                
            required_columns = ['Business Name', 'Address', 'Telephone']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            if missing_columns:
                print(f"Error: Required columns {missing_columns} not found in input file.")
                return False
                
            print(f"Loaded {len(self.df)} business records from {self.input_file}")
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False
            
    def process_businesses(self, limit=None):
        """Process businesses in the dataframe.
        
        Args:
            limit (int, optional): Limit the number of businesses to process.
        """
        if self.df is None:
            print("No data loaded. Please load data first.")
            return False
            
        # Add new columns if they don't exist
        new_columns = {
            'Google Maps URL': None,
            'Review Score': None,
            'About Section': None,
            'Processing Status': None,
            'Error Message': None
        }
        
        for col, default in new_columns.items():
            if col not in self.df.columns:
                self.df[col] = default
        
        # Process only a subset if limit is provided
        businesses_to_process = self.df.iloc[:limit] if limit else self.df
        
        total = len(businesses_to_process)
        success_count = 0
        
        # Process each business
        for index, row in businesses_to_process.iterrows():
            business_name = row['Business Name']
            address = row['Address']
            telephone = row['Telephone']
            
            print(f"\nProcessing {index+1}/{total}: {business_name}...")
            
            try:
                # Get Google Maps URL and Review Score
                maps_url, review_score = self.get_maps_url_and_review(business_name, address, telephone)
                
                # Update dataframe with results
                self.df.at[index, 'Google Maps URL'] = maps_url
                self.df.at[index, 'Review Score'] = review_score
                
                # Generate About Section if we have successful maps data
                if maps_url and review_score:
                    about_section = self.generate_about_section(business_name, address, review_score)
                    self.df.at[index, 'About Section'] = about_section
                    self.df.at[index, 'Processing Status'] = 'Success'
                    success_count += 1
                else:
                    self.df.at[index, 'Processing Status'] = 'Partial - No Maps Data'
                    self.df.at[index, 'Error Message'] = 'Could not find business on Google Maps'
                
            except Exception as e:
                error_message = str(e)
                print(f"Error processing {business_name}: {error_message}")
                self.df.at[index, 'Processing Status'] = 'Failed'
                self.df.at[index, 'Error Message'] = error_message
            
            # Save intermediate results after each business
            if index % 5 == 0 or index == len(businesses_to_process) - 1:
                self.save_results()
            
            # Add delay to respect API rate limits
            time.sleep(2)
        
        # Final save
        self.save_results()
        
        print(f"\nProcessing complete. Successfully processed {success_count} out of {total} businesses.")
        return True

    def get_maps_url_and_review(self, business_name, address, telephone):
        """Get Google Maps URL and review score for a business."""
        try:
            # Try multiple search strategies
            search_strategies = [
                f"{business_name} {address}",  # Full search
                f"{business_name} {address.split(',')[0]}",  # Business name with first part of address
                f"{business_name}",  # Just business name
                ' '.join(business_name.split()[:2]) + f" {address.split(',')[0]}"  # Simplified name and address
            ]
            
            for query in search_strategies:
                # Endpoint for the Places API
                url = "https://maps.googleapis.com/maps/api/place/findplacefromtext/json"
                
                # Parameters for the API request
                params = {
                    "input": query,
                    "inputtype": "textquery",
                    "fields": "place_id,name,formatted_address,rating,user_ratings_total",
                    "key": GOOGLE_MAPS_API_KEY
                }
                
                # Make the request
                response = requests.get(url, params=params)
                places_result = response.json()
                
                if places_result.get('status') == 'OK' and len(places_result.get('candidates', [])) > 0:
                    place = places_result['candidates'][0]
                    place_id = place.get('place_id')
                    
                    # Get more details about the place
                    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
                    details_params = {
                        "place_id": place_id,
                        "fields": "url,rating",
                        "key": GOOGLE_MAPS_API_KEY
                    }
                    details_response = requests.get(details_url, params=details_params)
                    place_details = details_response.json()
                    
                    if place_details.get('status') == 'OK':
                        maps_url = place_details.get('result', {}).get('url', '')
                        review_score = place.get('rating', 'N/A')
                        
                        print(f"Found result using query: {query}")
                        print(f"Maps URL: {maps_url}")
                        print(f"Review Score: {review_score}")
                        
                        return maps_url, review_score
                    
            print(f"No results found for {business_name} at {address}")
            return None, None
                
        except Exception as e:
            print(f"Error retrieving Google Maps data: {e}")
            return None, None
            
    def generate_about_section(self, business_name, address, review_score):
        """Generate an 'About' section for the business using Gemini AI."""
        try:
            # Use the configured Gemini model directly
            print(f"Generating about section using {self.gemini_model_name} model...")
            
            # Create prompt for Gemini
            prompt = f"""
            Write a professional, engaging 200-word 'About Us' section for a business with the following details:
            - Business Name: {business_name}
            - Location: {address}
            - Google Review Score: {review_score}
            
            The content should be informative, highlight the business's commitment to quality and customer service,
            and include a mention of their review score if it's good (4.0+). Keep the tone professional but warm.
            Do not include any made-up information like founding year, specific services, or team members unless
            they are mentioned in the provided information.
            """
            
            # Generate content with Gemini
            model = genai.GenerativeModel(self.gemini_model_name)
            
            # Set parameters appropriate for generation
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 250,
            }
            
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Clean up the response and ensure it's around 200 words
            about_text = response.text.strip()
            words = about_text.split()
            if len(words) > 220:  # Allow some flexibility
                about_text = ' '.join(words[:220]) + '...'
            
            print(f"Generated about section: {len(words)} words")
            return about_text
            
        except Exception as e:
            print(f"Error generating about section: {e}")
            error_msg = str(e)
            
            # Handle specific model not found error by trying to fallback
            if "Model not found" in error_msg or "not found" in error_msg.lower():
                print("Specified model not found. Attempting to use fallback Gemini model...")
                try:
                    available_models = genai.list_models()
                    gemini_models = [model.name for model in available_models if 'gemini' in model.name.lower()]
                    
                    if gemini_models:
                        fallback_model_name = gemini_models[0]
                        print(f"Using fallback model: {fallback_model_name}")
                        
                        # Try again with fallback model
                        model = genai.GenerativeModel(fallback_model_name)
                        response = model.generate_content(prompt)
                        
                        about_text = response.text.strip()
                        words = about_text.split()
                        if len(words) > 220:
                            about_text = ' '.join(words[:220]) + '...'
                        
                        print(f"Generated about section using fallback model: {len(words)} words")
                        return about_text
                except Exception as fallback_error:
                    print(f"Fallback model also failed: {fallback_error}")
            
            return f"About section could not be generated. Error: {error_msg}"
            
    def save_results(self):
        """Save processed data to Excel file."""
        try:
            self.df.to_excel(self.output_file, index=False)
            print(f"Results saved to {self.output_file}")
            return True
        except Exception as e:
            print(f"Error saving results: {e}")
            return False

def main():
    """Main function to run the Business Data Processor."""
    # Configuration
    input_file = "input_businesses.xlsx"
    output_file = "processed_businesses.xlsx"
    
    # Test API keys first
    print("Testing API keys before processing...")
    if not test_api_keys():
        print("API key test failed. Please fix the issues and try again.")
        proceed = input("\nDo you want to continue anyway? (y/n): ").lower()
        if proceed != 'y':
            print("Operation cancelled by user.")
            return
    
    # Ask for confirmation before proceeding
    proceed = input("\nDo you want to proceed with processing businesses? (y/n): ").lower()
    if proceed != 'y':
        print("Operation cancelled by user.")
        return
    
    # Get limit if user wants to process a subset
    limit_input = input("Enter the number of businesses to process (leave blank for all): ").strip()
    limit = int(limit_input) if limit_input and limit_input.isdigit() else None
    
    # Initialize and run processor
    processor = BusinessDataProcessor(input_file, output_file)
    if processor.load_data():
        processor.process_businesses(limit=limit)
    
if __name__ == "__main__":
    main()