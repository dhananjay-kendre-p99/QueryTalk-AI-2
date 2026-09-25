import re
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Pre-load the model once at module level on import
model = SentenceTransformer('all-MiniLM-L6-v2')

COLUMN_ALIASES = {
    "Product_ID": "product identifier product ID",
    "Sale_Date": "sale date transaction date purchase date when sold",
    "Sales_Rep": "sales representative salesperson rep employee name",
    "Region": "region area location territory zone",
    "Sales_Amount": "sales amount revenue total sales income earnings money",
    "Quantity_Sold": "quantity sold units sold number of items volume",
    "Product_Category": "product category type group classification",
    "Unit_Cost": "unit cost cost price expense",
    "Unit_Price": "unit price selling price price per unit",
    "Customer_Type": "customer type segment buyer category retail wholesale",
    "Discount": "discount offer reduction percentage off",
    "Payment_Method": "payment method mode of payment cash card online",
    "Sales_Channel": "sales channel online offline store direct",
    "Region_and_Sales_Rep": "region and sales rep combined territory representative"
}

# Pre-encode column aliases once at module level
column_embeddings = model.encode(list(COLUMN_ALIASES.values()))
COLUMN_NAMES = list(COLUMN_ALIASES.keys())

def match_columns(user_query: str, all_columns: list[str]) -> dict:
    print(f"--- MATCH COLUMNS REQUEST ---")
    print(f"User Query: {user_query}")

    # STAGE 1 — Keyword matching
    user_query_lower = user_query.lower()
    query_tokens = set(re.findall(r'[a-zA-Z0-9]+', user_query_lower))
    
    keyword_matched = []
    for col in all_columns:
        col_lower = col.lower()
        col_tokens = set(col_lower.split('_'))
        
        token_match = any(token in query_tokens for token in col_tokens)
        substring_match = any(q_token in col_lower for q_token in query_tokens)
        
        if token_match or substring_match:
            keyword_matched.append(col)
            
    print(f"Keyword matched columns: {keyword_matched}")

    # STAGE 2 — Semantic matching
    query_embedding = model.encode([user_query])
    
    # Check for domain-specific keywords to boost semantic matching scores
    temporal_boost = any(t in query_tokens for t in ["month", "year", "date", "day", "when", "today", "yesterday", "last", "between", "during", "before", "after", "time", "period"])
    financial_boost = any(f in query_tokens for f in ["earn", "revenue", "amount", "sales", "income", "money", "spend", "profit", "cost", "price", "discount", "sold", "most"])
    sales_rep_boost = any(s in query_tokens for s in ["who", "salesperson", "rep", "representative", "employee", "salesman", "sold", "seller"])
    region_boost = any(r in query_tokens for r in ["region", "area", "location", "territory", "zone", "north", "south", "east", "west"])
    quantity_boost = "how many" in user_query_lower or any(q in query_tokens for q in ["quantity", "units", "items", "volume", "sold", "most"])

    semantic_matched = []
    semantic_log = []
    
    for col in all_columns:
        if col in COLUMN_NAMES:
            idx = COLUMN_NAMES.index(col)
            col_emb = column_embeddings[idx]
        else:
            col_emb = model.encode([col.replace('_', ' ')])[0]
            
        sim = cosine_similarity(query_embedding, col_emb.reshape(1, -1))[0][0]
        score = float(sim)
        
        # Apply keyword-based semantic boosts
        boost = 0.0
        if col == "Sale_Date" and temporal_boost:
            boost += 0.35
        if col in ["Sales_Amount", "Unit_Cost", "Unit_Price", "Discount"]:
            if financial_boost:
                boost += 0.20
            if "most" in query_tokens or "highest" in query_tokens or "top" in query_tokens:
                boost += 0.15
        if col in ["Sales_Rep", "Region_and_Sales_Rep"]:
            if sales_rep_boost:
                boost += 0.20
            if "who" in query_tokens:
                boost += 0.15
            if "sold" in query_tokens or "seller" in query_tokens:
                boost += 0.15
        if col in ["Region", "Region_and_Sales_Rep"]:
            if region_boost:
                boost += 0.20
            if "territory" in query_tokens or "zone" in query_tokens or "area" in query_tokens:
                boost += 0.15
        if col == "Quantity_Sold" and quantity_boost:
            boost += 0.20
            
        final_score = min(score + boost, 1.0)
        semantic_log.append(f"{col}: {final_score:.4f} (raw: {score:.4f}, boost: {boost:.2f})")
        if final_score >= 0.35:
            semantic_matched.append((col, final_score))
            
    semantic_matched.sort(key=lambda x: x[1], reverse=True)
    semantic_matched_names = [col for col, score in semantic_matched]
    
    print(f"Semantic matched columns with scores: {semantic_log}")
    print(f"Passed Threshold (>= 0.35): {semantic_matched}")

    # STAGE 3 — MERGE RESULTS:
    merged_set = set(keyword_matched) | set(semantic_matched_names)
    merged_columns = [col for col in all_columns if col in merged_set]

    fallback_used = False
    if len(merged_columns) < 2:
        fallback_used = True
        final_columns = all_columns
    else:
        final_columns = merged_columns

    print(f"Final merged columns: {final_columns}")
    print(f"Fallback used: {fallback_used}")
    print(f"-----------------------------")

    return {
        "matched_columns": final_columns,
        "keyword_matched": keyword_matched,
        "semantic_matched": [
            {"column": col, "score": score} for col, score in semantic_matched
        ],
        "fallback_used": fallback_used
    }
