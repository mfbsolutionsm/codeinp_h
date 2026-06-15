from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import os
import json
import time
import random

load_dotenv()

app = Flask(__name__)

SAVED_FILE = Path("saved_properties.txt")
MAX_PROPERTIES = 3

PRIMARY_COUNTY = "Santa Clara County, CA"

BAY_AREA_SEARCH_AREA = (
    "San Francisco Bay Area, California, including Santa Clara, San Mateo, Alameda, "
    "Contra Costa, San Francisco, Marin, Napa, Sonoma, and Solano counties"
)

CALIFORNIA_SEARCH_AREA = (
    "All California, prioritizing active fixer-upper, needs TLC, contractor special, "
    "handyman special, investor opportunity, as-is, value-add, and remodel candidate listings"
)

EXTRACTION_PROMPT = """
ACT AS A REAL ESTATE LISTING RESEARCH ASSISTANT.

Your job is ONLY to search the web and extract listing facts.
Do NOT calculate ARV.
Do NOT calculate repairs.
Do NOT calculate profit.
Do NOT calculate ROI.
Do NOT calculate offer price.
Python will calculate all financial analysis later.

SEARCH AREA:
{search_area}

MAXIMUM PRICE:
${max_price}

EXCLUDED ADDRESSES FROM PREVIOUS SCANS:
{excluded_addresses}

SCAN REQUEST ID:
{scan_request_id}

TASK:
Find exactly 3 different real active property listings that match the investment profile.

IMPORTANT:
- Use fresh web search.
- Do not reuse memory examples.
- Do not return general search result pages.
- Each listing_url must be the direct URL to the specific property.
- Do not return any address from the excluded list.
- Prefer properties that need renovation or value-add work.
- Prefer cheaper properties first.
- If the selected search area has poor results, choose the strongest available active listings in that area.

RENOVATION KEYWORDS TO PRIORITIZE:
fixer, fixer-upper, fixer upper, fix and flip, fix & flip, needs TLC, TLC,
contractor special, contractor's special, handyman special, investor opportunity,
sold as-is, as-is, needs work, deferred maintenance, full remodel, major remodel,
original condition, dated interior, outdated kitchen, outdated bathrooms,
cosmetic fixer, value-add, sweat equity, bring your contractor, bring your imagination,
make it your own, great bones, ADU potential, garage conversion potential,
large lot, price reduced, price decrease.

RETURN VALID JSON ONLY.

Return an array of exactly 3 objects using this structure:

[
  {{
    "address": "",
    "city": "",
    "county": "",
    "listing_url": "",
    "source": "",
    "purchase_price": 0,
    "living_area_sqft": 0,
    "lot_size_sqft": 0,
    "bedrooms": 0,
    "bathrooms": 0,
    "year_built": 0,
    "days_on_market": 0,
    "description": "",
    "renovation_keywords_found": [],
    "property_type": ""
  }}
]
"""

DEMO_PROPERTIES = [
    {
        "address": "Demo Value-Add Candidate, Vallejo, CA",
        "city": "Vallejo",
        "county": "Solano County",
        "listing_url": "https://www.realtor.com/realestateandhomes-search/Vallejo_CA/with_fixerupper",
        "source": "Demo",
        "purchase_price": 599000,
        "living_area_sqft": 1450,
        "lot_size_sqft": 6500,
        "bedrooms": 3,
        "bathrooms": 2,
        "year_built": 1964,
        "days_on_market": 42,
        "description": "Demo candidate with fixer-upper, needs TLC, dated kitchen, and value-add potential.",
        "renovation_keywords_found": ["fixer-upper", "needs TLC", "dated kitchen", "value-add"],
        "property_type": "Single Family"
    },
    {
        "address": "Demo Contractor Special, Richmond, CA",
        "city": "Richmond",
        "county": "Contra Costa County",
        "listing_url": "https://www.realtor.com/realestateandhomes-search/Richmond_CA/with_fixerupper",
        "source": "Demo",
        "purchase_price": 525000,
        "living_area_sqft": 1250,
        "lot_size_sqft": 5000,
        "bedrooms": 3,
        "bathrooms": 1,
        "year_built": 1952,
        "days_on_market": 55,
        "description": "Demo contractor special with original condition, needs work, and possible second bath potential.",
        "renovation_keywords_found": ["contractor special", "original condition", "needs work"],
        "property_type": "Single Family"
    },
    {
        "address": "Demo As-Is Opportunity, Sacramento, CA",
        "city": "Sacramento",
        "county": "Sacramento County",
        "listing_url": "https://www.realtor.com/realestateandhomes-search/Sacramento_CA/with_fixerupper",
        "source": "Demo",
        "purchase_price": 450000,
        "living_area_sqft": 1500,
        "lot_size_sqft": 7200,
        "bedrooms": 4,
        "bathrooms": 2,
        "year_built": 1971,
        "days_on_market": 60,
        "description": "Demo as-is sale with outdated bathrooms, dated interior, and sweat equity potential.",
        "renovation_keywords_found": ["as-is", "outdated bathrooms", "dated interior", "sweat equity"],
        "property_type": "Single Family"
    }
]


def money_number(value):
    try:
        return float(value or 0)
    except (ValueError, TypeError):
        return 0


def keyword_score(property_item):
    keywords = property_item.get("renovation_keywords_found", [])
    description = str(property_item.get("description", "")).lower()
    text = description + " " + " ".join([str(k).lower() for k in keywords])

    strong_terms = [
        "fixer", "fixer-upper", "fixer upper", "needs tlc", "contractor special",
        "contractor's special", "handyman special", "as-is", "needs work",
        "deferred maintenance", "full remodel", "major remodel", "original condition",
        "investor opportunity"
    ]

    moderate_terms = [
        "dated", "outdated", "cosmetic", "value-add", "sweat equity",
        "bring your contractor", "bring your imagination", "make it your own",
        "great bones", "large lot", "adu potential", "garage conversion",
        "price reduced", "price decrease"
    ]

    score = 0
    for term in strong_terms:
        if term in text:
            score += 3
    for term in moderate_terms:
        if term in text:
            score += 1
    return score


def estimate_repair_budget(property_item):
    sqft = money_number(property_item.get("living_area_sqft")) or 1400
    score = keyword_score(property_item)

    if score >= 10:
        return round(sqft * 110), "Heavy", score
    if score >= 6:
        return round(sqft * 85), "Moderate to Heavy", score
    if score >= 3:
        return round(sqft * 65), "Moderate", score
    return round(sqft * 45), "Light to Moderate", score


def estimate_arv(property_item):
    purchase_price = money_number(property_item.get("purchase_price"))
    sqft = money_number(property_item.get("living_area_sqft")) or 1400
    city = str(property_item.get("city", "")).lower()
    county = str(property_item.get("county", "")).lower()

    price_per_sqft = 650
    if any(x in city for x in ["sunnyvale", "cupertino", "palo alto", "mountain view", "los altos"]):
        price_per_sqft = 1200
    elif any(x in city for x in ["santa clara", "san jose", "campbell", "milpitas"]):
        price_per_sqft = 900
    elif any(x in city for x in ["oakland", "hayward", "union city", "fremont", "san leandro"]):
        price_per_sqft = 650
    elif any(x in city for x in ["richmond", "vallejo", "antioch", "pittsburg"]):
        price_per_sqft = 475
    elif any(x in city for x in ["sacramento", "stockton", "modesto", "fresno", "bakersfield"]):
        price_per_sqft = 340
    elif "monterey" in county or "santa cruz" in county:
        price_per_sqft = 750

    sqft_based_arv = sqft * price_per_sqft
    return round(max(sqft_based_arv, purchase_price * 1.12))


def analyze_property(property_item):
    purchase_price = money_number(property_item.get("purchase_price"))
    repair_budget, renovation_level, remodel_signal_score = estimate_repair_budget(property_item)
    estimated_arv = estimate_arv(property_item)

    closing_costs = round(purchase_price * 0.03)
    financing_costs = round(purchase_price * 0.045)
    holding_costs = round(max(25000, purchase_price * 0.025))
    selling_costs = round(estimated_arv * 0.06)
    contingency = round(repair_budget * 0.07)

    total_project_cost = (
        purchase_price + repair_budget + closing_costs + financing_costs +
        holding_costs + selling_costs + contingency
    )

    estimated_net_profit = round(estimated_arv - total_project_cost)
    estimated_roi = round((estimated_net_profit / total_project_cost) * 100, 2) if total_project_cost else 0
    profit_margin_arv = round((estimated_net_profit / estimated_arv) * 100, 2) if estimated_arv else 0

    non_purchase_costs = repair_budget + closing_costs + financing_costs + holding_costs + selling_costs + contingency
    target_offer_for_yellow = round(estimated_arv - (estimated_arv * 0.05) - non_purchase_costs)
    target_offer_for_green = round(estimated_arv - (estimated_arv * 0.15) - non_purchase_costs)

    maximum_allowable_offer = target_offer_for_green
    recommended_offer = round(min(purchase_price, maximum_allowable_offer))
    spread_to_mao = round(maximum_allowable_offer - purchase_price)

    if purchase_price <= maximum_allowable_offer:
        mao_status = "BELOW MAO"
    else:
        mao_status = "NEGOTIATION REQUIRED"

    hidden_defect_alert = False
    hidden_defect_notes = ""

    if maximum_allowable_offer > 0 and purchase_price < maximum_allowable_offer * 0.70:
        hidden_defect_alert = True
        hidden_defect_notes = (
            "Property is significantly below MAO. Verify hidden defects before offering: "
            "foundation, roof, electrical, plumbing, HVAC, permits, flood zone, title issues, "
            "code violations, liens, insurance issues, and occupancy problems."
        )

    if profit_margin_arv >= 15:
        color, rating, score, deal_label = "GREEN", "Excellent Opportunity", 10, "EXCELLENT DEAL"
    elif profit_margin_arv >= 10:
        color, rating, score, deal_label = "DARK GREEN", "Good Opportunity", 8, "GOOD DEAL"
    elif profit_margin_arv >= 5:
        color, rating, score, deal_label = "YELLOW", "Marginal Opportunity", 6, "MARGINAL DEAL"
    else:
        color, rating, score, deal_label = "RED", "Poor Opportunity", 4, "POOR DEAL"

    if remodel_signal_score >= 10:
        remodel_signal = "Strong Remodel Candidate"
    elif remodel_signal_score >= 5:
        remodel_signal = "Moderate Remodel Candidate"
    else:
        remodel_signal = "Weak Remodel Signal"

    risk_level = "High" if renovation_level == "Heavy" else "Medium"
    strategy = "Fix & Flip / Value-Add"

    if money_number(property_item.get("bathrooms")) <= 1:
        strategy = "Add Bathroom / Fix & Flip"
    if money_number(property_item.get("lot_size_sqft")) >= 6500:
        strategy += " / ADU Research"

    property_item.update({
        "estimated_arv": estimated_arv,
        "repair_budget": repair_budget,
        "renovation_level": renovation_level,
        "closing_costs": closing_costs,
        "financing_costs": financing_costs,
        "holding_costs": holding_costs,
        "selling_costs": selling_costs,
        "contingency": contingency,
        "total_project_cost": total_project_cost,
        "estimated_net_profit": estimated_net_profit,
        "estimated_roi": estimated_roi,
        "profit_margin_arv": profit_margin_arv,
        "max_offer_price": maximum_allowable_offer,
        "maximum_allowable_offer": maximum_allowable_offer,
        "recommended_offer": recommended_offer,
        "spread_to_mao": spread_to_mao,
        "mao_status": mao_status,
        "hidden_defect_alert": hidden_defect_alert,
        "hidden_defect_notes": hidden_defect_notes,
        "target_offer_for_yellow": target_offer_for_yellow,
        "target_offer_for_green": target_offer_for_green,
        "risk_level": risk_level,
        "score": score,
        "rating": rating,
        "color": color,
        "deal_label": deal_label,
        "strategy": strategy,
        "remodel_signal": remodel_signal,
        "remodel_signal_score": remodel_signal_score,
        "notes": "Financial analysis calculated in Python. OpenAI only extracted listing facts. Verify ARV with real comps before making an offer."
    })
    return property_item


def analyze_properties(raw_properties):
    analyzed = [analyze_property(item) for item in raw_properties[:MAX_PROPERTIES]]
    return sorted(analyzed, key=lambda p: (p.get("profit_margin_arv", -999), p.get("remodel_signal_score", 0)), reverse=True)


def keep_yellow_and_green(properties):
    return [p for p in properties if p.get("color") in ["GREEN", "DARK GREEN", "YELLOW"]]


def build_prompt(max_price, excluded_addresses, search_area):
    if isinstance(excluded_addresses, list):
        excluded_addresses_text = "\n".join([f"- {address}" for address in excluded_addresses])
    else:
        excluded_addresses_text = str(excluded_addresses)

    return EXTRACTION_PROMPT.format(
        max_price=max_price,
        excluded_addresses=excluded_addresses_text,
        scan_request_id=f"{int(time.time())}-{random.randint(1000,9999)}",
        search_area=search_area
    )


def extract_json_array(text):
    """
    Robust JSON array parser.
    Handles markdown, text before/after JSON, and extra data.
    Returns the first valid JSON array found.
    """
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    decoder = json.JSONDecoder()

    for index, character in enumerate(cleaned):
        if character != "[":
            continue
        try:
            parsed, end_position = decoder.raw_decode(cleaned[index:])
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            continue

    start = cleaned.find("[")
    end = cleaned.rfind("]")

    if start != -1 and end != -1 and end > start:
        return json.loads(cleaned[start:end + 1])

    raise ValueError("No valid JSON array found in model response.")


def create_openai_response(client, prompt):
    return client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        tools=[{"type": "web_search"}],
        input=prompt,
        temperature=0.1
    )


def run_live_scan(client, max_price, excluded_addresses, search_area):
    prompt = build_prompt(max_price, excluded_addresses, search_area)
    response = create_openai_response(client, prompt)
    raw_properties = extract_json_array(response.output_text)
    analyzed = analyze_properties(raw_properties)
    filtered = keep_yellow_and_green(analyzed)
    return {"prompt": prompt, "analyzed": analyzed, "filtered": filtered}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/scan", methods=["POST"])
def scan():
    data = request.get_json()
    max_price = data.get("max_price", "1500000")
    excluded_addresses = data.get("excluded_addresses", [])
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        analyzed_demo = analyze_properties(DEMO_PROPERTIES)
        return jsonify({
            "mode": "demo",
            "search_area_used": "Demo mode only",
            "message": "DEMO MODE: OpenAI extracts listing facts only; Python calculates the investment analysis.",
            "prompt_sent": build_prompt(max_price, excluded_addresses, PRIMARY_COUNTY),
            "properties": analyzed_demo
        })

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        for mode, area in [
            ("live_web_search", PRIMARY_COUNTY),
            ("live_web_search_bay_area", BAY_AREA_SEARCH_AREA),
            ("live_web_search_california", CALIFORNIA_SEARCH_AREA)
        ]:
            result = run_live_scan(client, max_price, excluded_addresses, area)
            if result["filtered"]:
                return jsonify({
                    "mode": mode,
                    "search_area_used": area,
                    "message": "LIVE WEB SEARCH: OpenAI extracted listing facts. Python calculated the investment analysis.",
                    "prompt_sent": result["prompt"],
                    "properties": result["filtered"]
                })

        # If no yellow/green, show best analyzed California candidates instead of hiding everything.
        result = run_live_scan(client, max_price, excluded_addresses, CALIFORNIA_SEARCH_AREA)
        return jsonify({
            "mode": "live_web_search_california_best_candidates",
            "search_area_used": CALIFORNIA_SEARCH_AREA,
            "message": "No yellow/green found. Showing best analyzed candidates with Python calculations.",
            "prompt_sent": result["prompt"],
            "properties": result["analyzed"]
        })

    except Exception as error:
        analyzed_demo = analyze_properties(DEMO_PROPERTIES)
        return jsonify({
            "mode": "error_demo_fallback",
            "search_area_used": "Demo fallback",
            "message": f"Live scan failed. Demo shown. Error: {str(error)}",
            "prompt_sent": build_prompt(max_price, excluded_addresses, PRIMARY_COUNTY),
            "properties": analyzed_demo
        }), 200


@app.route("/debug-prompt", methods=["POST"])
def debug_prompt():
    data = request.get_json()
    max_price = data.get("max_price", "1500000")
    excluded_addresses = data.get("excluded_addresses", [])
    return jsonify({
        "mode": "debug",
        "has_openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        "search_area": PRIMARY_COUNTY,
        "prompt": build_prompt(max_price, excluded_addresses, PRIMARY_COUNTY)
    })


@app.route("/save-property", methods=["POST"])
def save_property():
    property_data = request.get_json()
    saved_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    keywords = property_data.get("renovation_keywords_found", [])
    if isinstance(keywords, list):
        keywords = ", ".join(keywords)

    block = [
        "=" * 80,
        f"SAVED PROPERTY - {saved_at}",
        "=" * 80,
        f"Address: {property_data.get('address', '')}",
        f"City: {property_data.get('city', '')}",
        f"County: {property_data.get('county', '')}",
        f"Listing URL: {property_data.get('listing_url', '')}",
        f"Source: {property_data.get('source', '')}",
        f"Purchase Price: ${property_data.get('purchase_price', 0):,}",
        f"Living Area Sq Ft: {property_data.get('living_area_sqft', 0)}",
        f"Lot Size Sq Ft: {property_data.get('lot_size_sqft', 0)}",
        f"Bedrooms: {property_data.get('bedrooms', 0)}",
        f"Bathrooms: {property_data.get('bathrooms', 0)}",
        f"Year Built: {property_data.get('year_built', 0)}",
        f"Estimated ARV: ${property_data.get('estimated_arv', 0):,}",
        f"Repair Budget: ${property_data.get('repair_budget', 0):,}",
        f"Total Project Cost: ${property_data.get('total_project_cost', 0):,}",
        f"Estimated Net Profit: ${property_data.get('estimated_net_profit', 0):,}",
        f"Profit Margin ARV: {property_data.get('profit_margin_arv', 0)}%",
        f"Maximum Allowable Offer (MAO): ${property_data.get('maximum_allowable_offer', property_data.get('max_offer_price', 0)):,}",
        f"Recommended Offer: ${property_data.get('recommended_offer', 0):,}",
        f"Spread to MAO: ${property_data.get('spread_to_mao', 0):,}",
        f"MAO Status: {property_data.get('mao_status', '')}",
        f"Hidden Defect Alert: {property_data.get('hidden_defect_alert', False)}",
        f"Hidden Defect Notes: {property_data.get('hidden_defect_notes', '')}",
        f"Target Yellow Offer: ${property_data.get('target_offer_for_yellow', 0):,}",
        f"Target Green Offer: ${property_data.get('target_offer_for_green', 0):,}",
        f"Color: {property_data.get('color', '')}",
        f"Rating: {property_data.get('rating', '')}",
        f"Strategy: {property_data.get('strategy', '')}",
        f"Renovation Keywords Found: {keywords}",
        f"Description: {property_data.get('description', '')}",
        "",
        "RAW JSON:",
        json.dumps(property_data, indent=4),
        "\n"
    ]

    with SAVED_FILE.open("a", encoding="utf-8") as file:
        file.write("\n".join(block))
    return jsonify({"message": "Property saved to saved_properties.txt"})


@app.route("/saved-properties")
def saved_properties():
    if not SAVED_FILE.exists():
        return jsonify({"content": "No saved properties yet."})
    return jsonify({"content": SAVED_FILE.read_text(encoding="utf-8")})


@app.route("/download-saved")
def download_saved():
    if not SAVED_FILE.exists():
        SAVED_FILE.write_text("No saved properties yet.", encoding="utf-8")
    return send_file(SAVED_FILE, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)
