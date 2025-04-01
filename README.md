# Business Data Processor

A Python utility that takes business information from an Excel file, retrieves Google Maps information, and generates AI-powered "About Us" sections.

## Overview

This script processes business data by:
1. Reading business information (name, address, telephone) from an Excel file
2. Finding each business on Google Maps to retrieve its URL and review score
3. Using Google's Gemini AI to generate a professional 200-word "About Us" section
4. Saving all results back to a new Excel file

## Prerequisites

- Python 3.7+
- Google Maps API key
- Google Gemini API key

## Installation

1. Clone this repository:
   ```
   git clone [repository-url]
   cd business-data-processor
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root with your API keys:
   ```
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

## Required Python Packages

- pandas
- requests
- google-generativeai
- python-dotenv
- openpyxl (for Excel file handling)

## Input Format

Prepare an Excel file named `input_businesses.xlsx` with the following columns:
- Business Name
- Address
- Telephone

Example:
| Business Name | Address | Telephone |
|---------------|---------|-----------|
| ABC Cafe | 123 Main St, Anytown, CA | 555-123-4567 |

## Usage

Run the script:
```
python main.py
```

The script will:
1. Validate your API keys
2. Ask for confirmation before proceeding
3. Allow you to limit the number of businesses to process
4. Process each business and save results to `processed_businesses.xlsx`

## Output

The script will generate an Excel file named `processed_businesses.xlsx` with the original data plus:
- Google Maps URL
- Review Score
- AI-generated About Section
- Processing Status
- Error Message (if any)

## Features

- **Multiple Search Strategies**: Uses several search approaches to find businesses on Google Maps
- **Intermediate Saving**: Saves results after every 5 businesses to prevent data loss
- **Error Handling**: Detailed error reporting for troubleshooting
- **Fallback Mechanisms**: Attempts alternative approaches if primary methods fail
- **Rate Limiting**: Includes delays to respect API rate limits

## How It Works

1. **Data Loading**: Validates that the input Excel file contains all required columns
2. **Maps Data Retrieval**: Uses Google Places API to find the business and retrieve its information
3. **AI Content Generation**: Uses Google's Gemini AI to create a customized About section for each business
4. **Data Saving**: Writes all processed data back to Excel with status information

## Troubleshooting

- **API Key Issues**: Ensure your API keys are correctly set in the `.env` file
- **Business Not Found**: Try updating the business name or address to be more precise
- **Rate Limiting**: The script includes delays to respect API limits; increase these if needed
- **Model Not Found**: The script tries to use `gemini-2.0-flash` but will fall back to other available models

## Error Codes

- **Success**: Business processed successfully
- **Partial - No Maps Data**: Business name and address couldn't be found on Google Maps
- **Failed**: An error occurred during processing (details in Error Message column)
