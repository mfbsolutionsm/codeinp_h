# Property Investment Scanner

**Stanford Python Final Project**

Property Investment Scanner is a Python/Flask web application designed to analyze fixer-upper and value-add real estate opportunities for fix-and-flip investments.

## Project Objective

The app scans real estate listings, identifies properties with renovation potential, and calculates whether they may be viable investment opportunities.

## Key Features

- Web-based property dashboard
- Scan button to search for properties
- Direct listing links
- Renovation keyword detection
- Python-based fix-and-flip analysis
- Estimated ARV
- Repair budget estimate
- Closing costs
- Financing costs
- Holding costs
- Selling costs
- Contingency
- Net profit
- ROI
- Profit margin vs ARV
- Maximum Allowable Offer (MAO)
- Recommended Offer
- Spread to MAO
- Hidden defect alert
- Color-coded deal ranking
- Save selected properties to a TXT file
- Download saved properties
- Show Prompt button for debugging

## Search Expansion Logic

The app searches in this order:

1. Santa Clara County
2. San Francisco Bay Area
3. All California

## Architecture

```text
User clicks Scan Properties
        ↓
Flask backend receives request
        ↓
OpenAI web search extracts listing facts only
        ↓
Python calculates financial analysis
        ↓
Frontend displays property cards
        ↓
User saves selected properties to TXT
```

## Why Python Calculates the Financial Analysis

To reduce API cost and improve consistency, OpenAI only extracts property facts:

- Address
- Listing URL
- Price
- Living area
- Lot size
- Bedrooms
- Bathrooms
- Year built
- Description
- Renovation keywords

Python calculates:

- ARV estimate
- Repair budget
- Total project cost
- Net profit
- ROI
- Profit margin vs ARV
- Maximum Allowable Offer
- Recommended offer
- Hidden defect alert
- Color classification

## Color Classification

```text
GREEN       = Net Profit >= 15% of ARV
DARK GREEN  = Net Profit >= 10% and < 15% of ARV
YELLOW      = Net Profit >= 5% and < 10% of ARV
RED         = Net Profit < 5% of ARV or negative
```

## Maximum Allowable Offer (MAO)

```text
MAO = ARV - Target Profit - Repairs - Closing Costs - Financing Costs - Holding Costs - Selling Costs - Contingency
```

The app also calculates:

```text
Recommended Offer = min(Asking Price, MAO)
Spread to MAO = MAO - Asking Price
```

This prevents the app from recommending an offer above the current asking price.

## Hidden Defect Alert

If the asking price is significantly below the calculated MAO, the app displays a warning.

A property listed far below MAO may have hidden issues such as:

- Foundation damage
- Roof damage
- Electrical issues
- Plumbing issues
- HVAC failure
- Permit problems
- Flood zone risk
- Title issues
- Code violations
- Liens
- Occupancy problems
- Insurance limitations

## Tech Stack

- Python
- Flask
- OpenAI API
- HTML
- CSS
- JavaScript
- GitHub

## Setup Instructions

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```text
OPENAI_API_KEY=YOUR_API_KEY_HERE
OPENAI_MODEL=gpt-4.1-mini
```

Run the app:

```bash
python app.py
```

Open in browser:

```text
http://127.0.0.1:5000
```

## Security

The repository include `.env.example`, but not `.env`.


```text
.env
__pycache__/
*.pyc
saved_properties.txt
```

## Project Limitations

This project is for educational purposes.

The ARV and repair budgets are estimates and should not be treated as professional appraisals, contractor bids, or investment advice.

Before making a real offer, an investor should verify:

- Comparable sales
- Inspection reports
- Contractor estimates
- Permit history
- Zoning
- Flood zone
- Title status
- Local resale demand

## Future Improvements

- ATTOM Data integration
- Comparable sales engine
- County permit lookup
- GIS zoning lookup
- Flood zone lookup
- PDF investment reports
- Saved property database
- User authentication
- Property photo analysis
- Deal pipeline dashboard
- HMLs list
- LCs list
- Roofing pictures with measures and estimates


##If you've made it this far, thank you.

