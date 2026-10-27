import os
from datetime import date, datetime, timedelta
import random
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup engine to demo.db
engine = create_engine("sqlite:///backend/demo.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_analytics():
    session = SessionLocal()
    try:
        sales = session.execute(text("SELECT amount, date, user_id FROM sales")).fetchall()
        users = session.execute(text("SELECT id, region, segment, acquisition_cost FROM users")).fetchall()
        print(f"Successfully fetched {len(sales)} sales and {len(users)} users from database.")
    except Exception as e:
        print(f"Error fetching data: {e}")
        session.close()
        return

    session.close()

    # Robust date parsing helper
    def parse_db_date(d):
        if d is None:
            return date.today()
        if isinstance(d, date):
            if isinstance(d, datetime):
                return d.date()
            return d
        if isinstance(d, str):
            try:
                return datetime.fromisoformat(d.replace("Z", "+00:00")).date()
            except ValueError:
                try:
                    return datetime.strptime(d[:10], "%Y-%m-%d").date()
                except ValueError:
                    pass
        return date.today()

    parsed_sales = [(s[0], parse_db_date(s[1]), s[2]) for s in sales]

    # Aggregate Data in Python
    total_revenue = sum(s[0] for s in parsed_sales) if parsed_sales else 0
    active_customers = len(set(s[2] for s in parsed_sales))
    
    # Dates
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    sixty_days_ago = today - timedelta(days=60)
    
    sales_this_month = [s for s in parsed_sales if s[1] >= thirty_days_ago]
    sales_last_month = [s for s in parsed_sales if sixty_days_ago <= s[1] < thirty_days_ago]
    
    rev_this_month = sum(s[0] for s in sales_this_month)
    rev_last_month = sum(s[0] for s in sales_last_month)
    
    growth_pct = 0
    if rev_last_month > 0:
        growth_pct = ((rev_this_month - rev_last_month) / rev_last_month) * 100
        
    # Monthly Growth Data
    monthly_data = {}
    for s in parsed_sales:
        month_key = s[1].strftime("%b")
        if month_key not in monthly_data:
            monthly_data[month_key] = 0
        monthly_data[month_key] += s[0]
        
    print(f"Total Revenue: {total_revenue}")
    print(f"Active Customers: {active_customers}")
    print(f"Growth %: {growth_pct}")
    print(f"Sales this month: {len(sales_this_month)}")
    print(f"Monthly Data Keys: {list(monthly_data.keys())}")

if __name__ == "__main__":
    test_analytics()
