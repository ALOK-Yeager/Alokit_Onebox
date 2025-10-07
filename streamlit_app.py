import streamlit as st
import requests
import pandas as pd
import time
import os
from typing import List, Dict, Any, Optional

# Set environment variables for cleaner output
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

# --- Configuration ---
st.set_page_config(
    page_title="📧 Onebox Aggregator",
    page_icon="📧",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = "http://localhost:3000/api/emails"
EMAIL_CATEGORIES = ["Interested", "Not Interested", "More Information", "Unclassified"]

# Try to import hybrid search for direct access
try:
    from search_service import HybridSearch
    USE_HYBRID_SEARCH = True
except ImportError:
    USE_HYBRID_SEARCH = False
    st.sidebar.warning("⚠️ Hybrid search not available. Using API only.")

# --- Styling ---
st.markdown("""
<style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    /* Search result styling */
    .search-result {
        border: 1px solid #e1e4e8;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
        transition: box-shadow 0.3s;
    }
    .search-result:hover {
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .search-result h3 {
        margin-top: 0;
        font-size: 1.2rem;
    }
    .search-result p {
        margin-bottom: 0.5rem;
    }
    .relevance-indicator {
        font-size: 0.9rem;
        font-weight: bold;
    }
    .keyword-match {
        color: #2a7de1; /* Blue for keyword */
    }
    .semantic-match {
        color: #28a745; /* Green for semantic */
    }
    /* Responsive design */
    @media (max-width: 600px) {
        .block-container {
            padding: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- API Functions ---
def get_email_by_id(email_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch email details from the API by email ID.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/{email_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching email {email_id}: {e}")
        return None

def perform_hybrid_search_direct(query: str, n_results: int = 5) -> List[str]:
    """
    Perform hybrid search using the local search service.
    """
    if USE_HYBRID_SEARCH:
        try:
            searcher = HybridSearch()
            return searcher.search(query, n_results=n_results)
        except Exception as e:
            st.error(f"Hybrid search error: {e}")
            return []
    return []

def perform_search(query: str, search_type: str = "hybrid", category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Calls the backend API to perform a search.
    """
    endpoint = f"{API_BASE_URL}/search"
    params = {
        "q": query,
        "type": search_type,
    }
    if category_filter and category_filter != "All":
        params["category"] = category_filter

    try:
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the search API: {e}")
        return []

# --- UI Components ---
def display_search_result(result: Dict[str, Any]):
    """
    Renders a single search result in a formatted block.
    """
    match_type = result.get("match_type", "keyword")
    relevance_score = result.get("score", 0.0)

    with st.container():
        st.markdown(f'<div class="search-result">', unsafe_allow_html=True)
        st.subheader(result.get("subject", "No Subject"))

        # Relevance indicator
        if match_type == "semantic":
            relevance_html = f'<span class="relevance-indicator semantic-match">Semantic Match (Score: {relevance_score:.2f})</span>'
        else:
            relevance_html = f'<span class="relevance-indicator keyword-match">Keyword Match (Score: {relevance_score:.2f})</span>'
        st.markdown(relevance_html, unsafe_allow_html=True)

        # Email details
        st.text(f"From: {result.get('from', 'N/A')}")
        date_val = result.get('date')
        if date_val:
            try:
                formatted_date = pd.to_datetime(date_val).strftime('%Y-%m-%d %H:%M')
            except:
                formatted_date = str(date_val)
            st.text(f"Date: {formatted_date}")
        else:
            st.text("Date: N/A")
        st.text(f"Category: {result.get('aiCategory', 'N/A')}")

        # Email body snippet
        with st.expander("Show Snippet"):
            st.text_area("", result.get("body_snippet", "No content available."), height=150, disabled=True)

        st.markdown('</div>', unsafe_allow_html=True)


# --- Main Application ---
def main():
    st.title("📧 Onebox Aggregator")
    st.write("🔍 Hybrid search combining keyword and semantic search across your indexed emails.")

    # --- Search Controls ---
    with st.sidebar:
        st.header("🔍 Search Options")
        search_mode = st.radio(
            "Search Mode",
            ["API Search", "Direct Hybrid Search"] if USE_HYBRID_SEARCH else ["API Search"],
            help="API Search uses the backend endpoint. Direct Hybrid Search uses local VectorDB."
        )
        
        st.divider()
        
        search_query = st.text_input(
            "Search Query",
            placeholder="Try: 'Show me emails about project deadlines'"
        )
        
        # Initialize variables
        category_filter = "All"
        n_results = 5
        
        if search_mode == "API Search":
            category_filter = st.selectbox("Filter by Category", ["All"] + EMAIL_CATEGORIES)
        else:
            n_results = st.slider("Number of Results", min_value=1, max_value=20, value=5)
        
        search_button = st.button("🔍 Search", use_container_width=True, type="primary")
        
        st.divider()
        st.caption("💡 **Tips:**")
        st.caption("• Use natural language queries")
        st.caption("• Try specific keywords")
        st.caption("• Filter by category for better results")

    # --- Search Results ---
    if search_button and search_query:
        with st.spinner("Searching your emails..."):
            if search_mode == "Direct Hybrid Search" and USE_HYBRID_SEARCH:
                # Use direct hybrid search
                email_ids = perform_hybrid_search_direct(search_query, n_results=n_results)
                
                st.header(f"📬 Search Results for '{search_query}'")
                
                if not email_ids:
                    st.info("🔍 No results found. Try a different query or check your VectorDB.")
                else:
                    st.success(f"✅ Found {len(email_ids)} results")
                    
                    # Fetch email details for each ID
                    for i, email_id in enumerate(email_ids, 1):
                        email = get_email_by_id(email_id)
                        if email:
                            with st.expander(f"{i}. {email.get('subject', 'No Subject')}", expanded=(i==1)):
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.write(f"**From:** {email.get('from', 'N/A')}")
                                    st.write(f"**To:** {email.get('to', 'N/A')}")
                                with col2:
                                    date_val = email.get('date')
                                    if date_val:
                                        try:
                                            formatted_date = pd.to_datetime(date_val).strftime('%Y-%m-%d %H:%M')
                                        except:
                                            formatted_date = str(date_val)
                                        st.write(f"**Date:** {formatted_date}")
                                    st.write(f"**Category:** {email.get('aiCategory', 'N/A')}")
                                
                                st.divider()
                                content = email.get('body', email.get('content', 'No content available'))
                                st.text_area("Preview", content[:500] + "..." if len(content) > 500 else content, height=150, disabled=True, key=f"content_{i}")
                        else:
                            st.warning(f"⚠️ Could not fetch email: {email_id}")
            else:
                # Use API search
                search_results = perform_search(
                    search_query,
                    category_filter=category_filter if search_mode == "API Search" else None
                )

                st.header(f"📬 Search Results for '{search_query}'")

                if not search_results:
                    st.info("🔍 No results found. Try a different query or broaden your filters.")
                else:
                    st.success(f"✅ Found {len(search_results)} results")
                    for result in search_results:
                        display_search_result(result)

    elif not search_query:
        st.info("👈 Enter a query in the sidebar to begin searching your emails.")


if __name__ == "__main__":
    main()
