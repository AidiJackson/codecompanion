"""
Personal Expense Tracker Web App
Features: Receipt scanning, AI categorization, budget management, analytics, reports
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import hashlib
import base64
import io
import json
import re
from typing import Dict, List, Optional, Tuple
import openai
import os
from PIL import Image

# OpenAI Configuration
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Database initialization
def init_database():
    """Initialize SQLite database with required tables"""
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            receipt_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Budgets table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            period TEXT DEFAULT 'monthly',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#1f77b4',
            icon TEXT DEFAULT '💰'
        )
    ''')
    
    # Insert default categories
    default_categories = [
        ('Food & Dining', '#ff7f0e', '🍽️'),
        ('Transportation', '#2ca02c', '🚗'),
        ('Shopping', '#d62728', '🛍️'),
        ('Entertainment', '#9467bd', '🎬'),
        ('Bills & Utilities', '#8c564b', '💡'),
        ('Healthcare', '#e377c2', '🏥'),
        ('Education', '#7f7f7f', '📚'),
        ('Travel', '#bcbd22', '✈️'),
        ('Personal Care', '#17becf', '💅'),
        ('Other', '#aec7e8', '📝')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO categories (name, color, icon) VALUES (?, ?, ?)
    ''', default_categories)
    
    conn.commit()
    conn.close()

# Authentication functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username: str, password: str, email: str = None) -> bool:
    """Create new user account"""
    try:
        conn = sqlite3.connect('expense_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password_hash, email) VALUES (?, ?, ?)
        ''', (username, hash_password(password), email))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def authenticate_user(username: str, password: str) -> Optional[int]:
    """Authenticate user and return user ID if successful"""
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM users WHERE username = ? AND password_hash = ?
    ''', (username, hash_password(password)))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# AI Receipt Processing
def process_receipt_with_ai(image_data: bytes) -> Dict:
    """Process receipt image using OpenAI Vision API"""
    try:
        # Convert image to base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this receipt image and extract the following information in JSON format:
                            {
                                "merchant": "store/restaurant name",
                                "total_amount": "total amount as number",
                                "date": "date in YYYY-MM-DD format",
                                "items": [{"item": "item name", "price": "price as number"}],
                                "category": "suggested category from: Food & Dining, Transportation, Shopping, Entertainment, Bills & Utilities, Healthcare, Education, Travel, Personal Care, Other"
                            }
                            Only return the JSON, no other text."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=500
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error processing receipt: {e}")
        return None

def categorize_expense_with_ai(description: str, amount: float) -> str:
    """Categorize expense using AI based on description and amount"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {
                    "role": "system",
                    "content": """You are an expense categorization expert. Categorize the expense into one of these categories:
                    Food & Dining, Transportation, Shopping, Entertainment, Bills & Utilities, Healthcare, Education, Travel, Personal Care, Other
                    
                    Respond with only the category name, nothing else."""
                },
                {
                    "role": "user",
                    "content": f"Categorize this expense: {description} - ${amount}"
                }
            ],
            max_tokens=50
        )
        
        category = response.choices[0].message.content.strip()
        
        # Validate category
        valid_categories = [
            'Food & Dining', 'Transportation', 'Shopping', 'Entertainment',
            'Bills & Utilities', 'Healthcare', 'Education', 'Travel',
            'Personal Care', 'Other'
        ]
        
        return category if category in valid_categories else 'Other'
    except Exception as e:
        st.error(f"Error categorizing expense: {e}")
        return 'Other'

# Database operations
def add_expense(user_id: int, amount: float, category: str, description: str, date: str, receipt_data: str = None):
    """Add new expense to database"""
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (user_id, amount, category, description, date, receipt_data)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, amount, category, description, date, receipt_data))
    conn.commit()
    conn.close()

def get_expenses(user_id: int, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """Get expenses for user within date range"""
    conn = sqlite3.connect('expense_tracker.db')
    
    query = '''
        SELECT id, amount, category, description, date, created_at
        FROM expenses 
        WHERE user_id = ?
    '''
    params = [user_id]
    
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date)
    
    query += ' ORDER BY date DESC'
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    
    return df

def set_budget(user_id: int, category: str, amount: float, period: str = 'monthly'):
    """Set budget for category"""
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    
    # Update existing or insert new
    cursor.execute('''
        INSERT OR REPLACE INTO budgets (user_id, category, amount, period)
        VALUES (?, ?, ?, ?)
    ''', (user_id, category, amount, period))
    
    conn.commit()
    conn.close()

def get_budgets(user_id: int) -> pd.DataFrame:
    """Get budgets for user"""
    conn = sqlite3.connect('expense_tracker.db')
    df = pd.read_sql_query('''
        SELECT category, amount, period FROM budgets WHERE user_id = ?
    ''', conn, params=[user_id])
    conn.close()
    return df

def get_categories() -> List[Tuple[str, str, str]]:
    """Get all available categories"""
    conn = sqlite3.connect('expense_tracker.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, color, icon FROM categories')
    categories = cursor.fetchall()
    conn.close()
    return categories

# Analytics functions
def calculate_budget_status(user_id: int, period: str = 'monthly') -> Dict:
    """Calculate budget vs actual spending"""
    current_date = datetime.now()
    
    if period == 'monthly':
        start_date = current_date.replace(day=1)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    else:  # weekly
        start_date = current_date - timedelta(days=current_date.weekday())
        end_date = start_date + timedelta(days=6)
    
    # Get budgets
    budgets_df = get_budgets(user_id)
    
    # Get expenses for period
    expenses_df = get_expenses(
        user_id, 
        start_date.strftime('%Y-%m-%d'), 
        end_date.strftime('%Y-%m-%d')
    )
    
    budget_status = {}
    
    if not budgets_df.empty:
        period_budgets = budgets_df[budgets_df['period'] == period]
        
        for _, budget in period_budgets.iterrows():
            category = budget['category']
            budget_amount = budget['amount']
            
            # Calculate spent amount
            category_expenses = expenses_df[expenses_df['category'] == category]
            spent_amount = category_expenses['amount'].sum() if not category_expenses.empty else 0
            
            budget_status[category] = {
                'budget': budget_amount,
                'spent': spent_amount,
                'remaining': budget_amount - spent_amount,
                'percentage': (spent_amount / budget_amount * 100) if budget_amount > 0 else 0
            }
    
    return budget_status

def generate_spending_insights(user_id: int) -> Dict:
    """Generate AI-powered spending insights"""
    # Get last 3 months of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    expenses_df = get_expenses(
        user_id,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    if expenses_df.empty:
        return {"insights": ["No expenses found for analysis."]}
    
    # Calculate insights
    insights = []
    
    # Top spending categories
    category_spending = expenses_df.groupby('category')['amount'].sum().sort_values(ascending=False)
    if not category_spending.empty:
        top_category = category_spending.index[0]
        top_amount = category_spending.iloc[0]
        insights.append(f"Your highest spending category is {top_category} with ${top_amount:.2f}")
    
    # Average daily spending
    daily_avg = expenses_df['amount'].sum() / 90
    insights.append(f"Your average daily spending is ${daily_avg:.2f}")
    
    # Spending trends
    expenses_df['week'] = expenses_df['date'].dt.isocalendar().week
    weekly_spending = expenses_df.groupby('week')['amount'].sum()
    
    if len(weekly_spending) >= 2:
        recent_avg = weekly_spending.tail(2).mean()
        previous_avg = weekly_spending.head(-2).mean() if len(weekly_spending) > 2 else recent_avg
        
        if recent_avg > previous_avg * 1.1:
            insights.append("Your spending has increased recently compared to earlier weeks.")
        elif recent_avg < previous_avg * 0.9:
            insights.append("Great! Your spending has decreased recently.")
    
    return {"insights": insights}

# Streamlit UI Components
def render_login_page():
    """Render login/registration page"""
    st.title("💰 Personal Expense Tracker")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_submit = st.form_submit_button("Login")
            
            if login_submit:
                user_id = authenticate_user(username, password)
                if user_id:
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Create Account")
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_email = st.text_input("Email (optional)")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register_submit = st.form_submit_button("Create Account")
            
            if register_submit:
                if len(new_username) < 3:
                    st.error("Username must be at least 3 characters")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    if create_user(new_username, new_password, new_email):
                        st.success("Account created successfully! Please login.")
                    else:
                        st.error("Username already exists")

def render_expense_input():
    """Render expense input form with receipt scanning"""
    st.subheader("📝 Add New Expense")
    
    # Receipt scanning option
    scan_tab, manual_tab = st.tabs(["📷 Scan Receipt", "✍️ Manual Entry"])
    
    with scan_tab:
        st.write("Upload a receipt image for automatic processing")
        uploaded_file = st.file_uploader(
            "Upload Receipt Image", 
            type=['png', 'jpg', 'jpeg'],
            help="Upload a clear image of your receipt"
        )
        
        if uploaded_file is not None:
            # Display image
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Receipt", width=300)
            
            if st.button("Process Receipt"):
                with st.spinner("Processing receipt with AI..."):
                    # Process with AI
                    receipt_data = process_receipt_with_ai(uploaded_file.getvalue())
                    
                    if receipt_data:
                        st.success("Receipt processed successfully!")
                        
                        # Show extracted data for confirmation
                        with st.form("receipt_confirmation"):
                            st.write("**Extracted Information:**")
                            
                            amount = st.number_input(
                                "Amount", 
                                value=float(receipt_data.get('total_amount', 0)),
                                min_value=0.01,
                                step=0.01
                            )
                            
                            categories = [cat[0] for cat in get_categories()]
                            suggested_category = receipt_data.get('category', 'Other')
                            category_index = categories.index(suggested_category) if suggested_category in categories else 0
                            
                            category = st.selectbox(
                                "Category",
                                categories,
                                index=category_index
                            )
                            
                            description = st.text_input(
                                "Description",
                                value=receipt_data.get('merchant', '')
                            )
                            
                            expense_date = st.date_input(
                                "Date",
                                value=datetime.strptime(receipt_data.get('date', datetime.now().strftime('%Y-%m-%d')), '%Y-%m-%d').date() if receipt_data.get('date') else datetime.now().date()
                            )
                            
                            if st.form_submit_button("Add Expense"):
                                add_expense(
                                    st.session_state.user_id,
                                    amount,
                                    category,
                                    description,
                                    expense_date.strftime('%Y-%m-%d'),
                                    json.dumps(receipt_data)
                                )
                                st.success("Expense added successfully!")
                                st.rerun()
    
    with manual_tab:
        with st.form("manual_expense"):
            col1, col2 = st.columns(2)
            
            with col1:
                amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
                categories = [cat[0] for cat in get_categories()]
                category = st.selectbox("Category", categories)
            
            with col2:
                expense_date = st.date_input("Date", value=datetime.now().date())
                
            description = st.text_input("Description")
            
            # AI categorization suggestion
            if description and st.button("Get AI Category Suggestion"):
                suggested_category = categorize_expense_with_ai(description, amount)
                st.info(f"AI suggests category: {suggested_category}")
            
            if st.form_submit_button("Add Expense"):
                if amount > 0 and description:
                    add_expense(
                        st.session_state.user_id,
                        amount,
                        category,
                        description,
                        expense_date.strftime('%Y-%m-%d')
                    )
                    st.success("Expense added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill in all required fields")

def render_expense_list():
    """Render expense list with filtering"""
    st.subheader("📊 Your Expenses")
    
    # Date range filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        start_date = st.date_input(
            "From Date",
            value=datetime.now().replace(day=1).date()
        )
    
    with col2:
        end_date = st.date_input(
            "To Date",
            value=datetime.now().date()
        )
    
    with col3:
        categories = ['All'] + [cat[0] for cat in get_categories()]
        selected_category = st.selectbox("Filter by Category", categories)
    
    # Get expenses
    expenses_df = get_expenses(
        st.session_state.user_id,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    if not expenses_df.empty:
        # Filter by category if selected
        if selected_category != 'All':
            expenses_df = expenses_df[expenses_df['category'] == selected_category]
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Expenses", f"${expenses_df['amount'].sum():.2f}")
        
        with col2:
            st.metric("Number of Transactions", len(expenses_df))
        
        with col3:
            st.metric("Average Amount", f"${expenses_df['amount'].mean():.2f}")
        
        with col4:
            st.metric("Largest Expense", f"${expenses_df['amount'].max():.2f}")
        
        # Display expenses table
        st.dataframe(
            expenses_df[['date', 'category', 'description', 'amount']],
            use_container_width=True,
            hide_index=True
        )
        
        # Export functionality
        if st.button("📥 Export to CSV"):
            csv = expenses_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"expenses_{start_date}_to_{end_date}.csv",
                mime="text/csv"
            )
    else:
        st.info("No expenses found for the selected period.")

def render_budget_management():
    """Render budget setting and monitoring"""
    st.subheader("🎯 Budget Management")
    
    budget_tab, status_tab = st.tabs(["Set Budgets", "Budget Status"])
    
    with budget_tab:
        st.write("Set monthly spending limits for each category")
        
        categories = [cat[0] for cat in get_categories()]
        existing_budgets = get_budgets(st.session_state.user_id)
        
        with st.form("budget_form"):
            for category in categories:
                current_budget = 0
                if not existing_budgets.empty and category in existing_budgets['category'].values:
                    current_budget = existing_budgets[existing_budgets['category'] == category]['amount'].iloc[0]
                
                budget_amount = st.number_input(
                    f"{category} Monthly Budget ($)",
                    value=float(current_budget),
                    min_value=0.0,
                    step=10.0,
                    key=f"budget_{category}"
                )
                
                if budget_amount > 0:
                    set_budget(st.session_state.user_id, category, budget_amount, 'monthly')
            
            if st.form_submit_button("Update Budgets"):
                st.success("Budgets updated successfully!")
                st.rerun()
    
    with status_tab:
        budget_status = calculate_budget_status(st.session_state.user_id, 'monthly')
        
        if budget_status:
            st.write("**Current Month Budget Status**")
            
            for category, status in budget_status.items():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Progress bar
                    progress = min(status['percentage'] / 100, 1.0)
                    
                    # Color coding
                    if status['percentage'] <= 75:
                        color = 'normal'
                    elif status['percentage'] <= 90:
                        color = 'inverse'
                    else:
                        color = 'off'
                    
                    st.progress(progress, text=f"{category}: ${status['spent']:.2f} / ${status['budget']:.2f}")
                
                with col2:
                    if status['remaining'] >= 0:
                        st.success(f"${status['remaining']:.2f} left")
                    else:
                        st.error(f"${abs(status['remaining']):.2f} over")
        else:
            st.info("Set budgets to see your spending status")

def render_analytics():
    """Render spending analytics and charts"""
    st.subheader("📈 Spending Analytics")
    
    # Get data for last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    expenses_df = get_expenses(
        st.session_state.user_id,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    if expenses_df.empty:
        st.info("No data available for analytics. Add some expenses first!")
        return
    
    # Category spending pie chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Spending by Category**")
        category_spending = expenses_df.groupby('category')['amount'].sum().reset_index()
        
        fig_pie = px.pie(
            category_spending,
            values='amount',
            names='category',
            title="Spending Distribution"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.write("**Monthly Spending Trend**")
        expenses_df['month'] = expenses_df['date'].dt.to_period('M')
        monthly_spending = expenses_df.groupby('month')['amount'].sum().reset_index()
        monthly_spending['month'] = monthly_spending['month'].astype(str)
        
        fig_line = px.line(
            monthly_spending,
            x='month',
            y='amount',
            title="Monthly Spending Trend",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)
    
    # Weekly spending pattern
    st.write("**Weekly Spending Pattern**")
    expenses_df['weekday'] = expenses_df['date'].dt.day_name()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_spending = expenses_df.groupby('weekday')['amount'].sum().reindex(weekday_order, fill_value=0).reset_index()
    
    fig_bar = px.bar(
        weekly_spending,
        x='weekday',
        y='amount',
        title="Average Spending by Day of Week"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # AI Insights
    st.write("**AI-Powered Insights**")
    insights = generate_spending_insights(st.session_state.user_id)
    
    for insight in insights['insights']:
        st.info(insight)

def render_monthly_report():
    """Render detailed monthly spending report"""
    st.subheader("📋 Monthly Report")
    
    # Month selector
    selected_month = st.selectbox(
        "Select Month",
        options=pd.date_range(
            start=datetime.now() - timedelta(days=365),
            end=datetime.now(),
            freq='M'
        ).strftime('%Y-%m'),
        index=11  # Current month
    )
    
    # Get month data
    start_date = datetime.strptime(selected_month, '%Y-%m').replace(day=1)
    end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    expenses_df = get_expenses(
        st.session_state.user_id,
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    if expenses_df.empty:
        st.info(f"No expenses found for {selected_month}")
        return
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Spent", f"${expenses_df['amount'].sum():.2f}")
    
    with col2:
        st.metric("Transactions", len(expenses_df))
    
    with col3:
        st.metric("Daily Average", f"${expenses_df['amount'].sum() / end_date.day:.2f}")
    
    with col4:
        largest_expense = expenses_df.loc[expenses_df['amount'].idxmax()]
        st.metric("Largest Expense", f"${largest_expense['amount']:.2f}")
        st.caption(f"{largest_expense['category']} - {largest_expense['description']}")
    
    # Category breakdown
    st.write("**Category Breakdown**")
    category_summary = expenses_df.groupby('category').agg({
        'amount': ['sum', 'count', 'mean']
    }).round(2)
    category_summary.columns = ['Total', 'Count', 'Average']
    category_summary = category_summary.sort_values('Total', ascending=False)
    
    st.dataframe(category_summary, use_container_width=True)
    
    # Top expenses
    st.write("**Top 10 Expenses**")
    top_expenses = expenses_df.nlargest(10, 'amount')[['date', 'category', 'description', 'amount']]
    st.dataframe(top_expenses, use_container_width=True, hide_index=True)
    
    # Generate report download
    if st.button("📄 Generate PDF Report"):
        st.info("PDF report generation would be implemented here with libraries like ReportLab")

# Initialize session state
def init_session_state():
    """Initialize Streamlit session state"""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'username' not in st.session_state:
        st.session_state.username = None

# Main application
def main():
    """Main application function"""
    st.set_page_config(
        page_title="Personal Expense Tracker",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database and session
    init_database()
    init_session_state()
    
    # Custom CSS for mobile responsiveness
    st.markdown("""
    <style>
    .main-header {
        padding: 1rem 0;
        border-bottom: 2px solid #f0f0f0;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.5rem;
        }
        
        .metric-card {
            padding: 0.5rem;
        }
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0 0;
        gap: 8px;
        padding-left: 12px;
        padding-right: 12px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check authentication
    if not st.session_state.user_id:
        render_login_page()
        return
    
    # Main app interface
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("💰 Personal Expense Tracker")
        st.write(f"Welcome back, {st.session_state.username}!")
    
    with col2:
        if st.button("🚪 Logout"):
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "➕ Add Expense",
        "📊 Expenses",
        "🎯 Budgets",
        "📈 Analytics",
        "📋 Reports",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_expense_input()
    
    with tab2:
        render_expense_list()
    
    with tab3:
        render_budget_management()
    
    with tab4:
        render_analytics()
    
    with tab5:
        render_monthly_report()
    
    with tab6:
        st.subheader("⚙️ Settings")
        st.info("Settings panel - Additional features like data export, account management, etc. would be implemented here")
        
        # Data export
        if st.button("📥 Export All Data"):
            all_expenses = get_expenses(st.session_state.user_id)
            if not all_expenses.empty:
                csv = all_expenses.to_csv(index=False)
                st.download_button(
                    label="Download All Expenses (CSV)",
                    data=csv,
                    file_name="all_expenses.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()