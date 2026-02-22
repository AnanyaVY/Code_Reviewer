"""
AI-Powered Code Review Assistant - Streamlit UI
Main application file with user interface.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json
from reviewer import CodeReviewer

# Configure Streamlit page
st.set_page_config(
    page_title="AI Code Review Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def display_pylint_results(pylint_data):
    if not pylint_data or not pylint_data.get("success"):
        st.error(f"Pylint Error: {pylint_data.get('error', 'Unknown error')}")
        return
    
    results = pylint_data.get("results", [])
    if not results:
        st.success("✅ No pylint issues found!")
        return
    
    st.subheader("Pylint Issues by Type")
    issues_by_type = {}
    for issue in results:
        issue_type = issue.get("type", "Unknown")
        if issue_type not in issues_by_type:
            issues_by_type[issue_type] = []
        issues_by_type[issue_type].append(issue)
    
    for issue_type, issues in issues_by_type.items():
        st.markdown(f"### {issue_type} ({len(issues)} issues)")
        for issue in issues:
            with st.container():
                st.markdown(f"**Line {issue.get('line', 'N/A')}:** {issue.get('message', 'No message')}")
                st.markdown(f"*Confidence: {issue.get('confidence', 'N/A')}*")
                st.markdown("---")

def display_bandit_results(bandit_data):
    if not bandit_data or not bandit_data.get("success"):
        st.error(f"Bandit Error: {bandit_data.get('error', 'Unknown error')}")
        return
    
    results = bandit_data.get("results", {})
    issues = results.get("results", [])
    
    if not issues:
        st.success("✅ No security issues found by Bandit!")
        return
    
    st.warning(f"🔒 Found {len(issues)} security issue(s)")
    
    st.subheader("Security Issues")
    for i, issue in enumerate(issues, 1):
        with st.container():
            st.markdown(f"**{i}. {issue.get('test_name', 'Unknown')} - {issue.get('severity', 'Unknown')}**")
            st.markdown(f"**Issue:** {issue.get('issue_text', 'No description')}")
            st.markdown(f"**Severity:** {issue.get('severity', 'Unknown')}")
            st.markdown(f"**Confidence:** {issue.get('confidence', 'Unknown')}")
            st.markdown(f"**Line {issue.get('line_number', 'N/A')}:** `{issue.get('code', 'N/A')}`")
            st.markdown("---")

def display_eslint_results(eslint_data):
    if not eslint_data or not eslint_data.get("success"):
        st.error(f"ESLint Error: {eslint_data.get('error', 'Unknown error')}")
        return
    
    results = eslint_data.get("results", [])
    if not results:
        st.success("✅ No ESLint issues found!")
        return
    
    for file_result in results:
        file_path = file_result.get("filePath", "Unknown file")
        messages = file_result.get("messages", [])
        
        if not messages:
            st.success(f"✅ No issues in {file_path}")
            continue
        
        st.markdown(f"### {file_path} ({len(messages)} issues)")
        for message in messages:
            with st.container():
                severity = message.get("severity", 1)
                severity_text = "Error" if severity == 2 else "Warning"
                st.markdown(f"**Line {message.get('line', 'N/A')}:** {message.get('message', 'No message')}")
                st.markdown(f"*Severity: {severity_text}*")
                if message.get("ruleId"):
                    st.markdown(f"*Rule: {message['ruleId']}*")
                st.markdown("---")

def display_ai_results(ai_data):
    if not ai_data or not ai_data.get("success"):
        st.error(f"AI Analysis Error: {ai_data.get('error', 'Unknown error')}")
        return
    
    feedback = ai_data.get("feedback", "No feedback available")
    model_used = ai_data.get("model_used", "Unknown model")
    
    st.info(f"🤖 AI Analysis powered by {model_used}")
    st.markdown(feedback)

def download_report(review_results):
    language = review_results.get('language', 'Unknown')
    
    report_content = f"""AI-Powered Code Review Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Language: {language}

=== STATIC ANALYSIS RESULTS ===
"""
    
    static_analysis = review_results.get("static_analysis", {})
    
    # Pylint section
    if static_analysis.get("pylint") and static_analysis["pylint"].get("success"):
        report_content += "\n--- PYLINT RESULTS ---\n"
        results = static_analysis["pylint"].get("results", [])
        if results:
            for issue in results:
                report_content += f"Line {issue.get('line', 'N/A')}: {issue.get('message', 'No message')}\n"
        else:
            report_content += "No pylint issues found.\n"
    
    # Bandit section  
    if static_analysis.get("bandit") and static_analysis["bandit"].get("success"):
        report_content += "\n--- BANDIT SECURITY RESULTS ---\n"
        results = static_analysis["bandit"].get("results", {})
        issues = results.get("results", [])
        if issues:
            for issue in issues:
                report_content += f"Line {issue.get('line_number', 'N/A')}: {issue.get('issue_text', 'No description')} ({issue.get('severity', 'LOW')})\n"
        else:
            report_content += "No security issues found.\n"
    
    # AI section
    ai_analysis = review_results.get("ai_analysis", {})
    if ai_analysis.get("success"):
        report_content += f"\n=== AI ANALYSIS RESULTS ===\n"
        report_content += f"Model: {ai_analysis.get('model_used', 'CodeT5')}\n\n"
        report_content += ai_analysis.get("feedback", "No AI feedback")
    
    return report_content

def main():
    st.markdown('<h1 class="main-header">🤖 AI-Powered Code Review Assistant</h1>', unsafe_allow_html=True)
    st.markdown('<h2 style="text-align: center; color: #666;">Hugging Face CodeT5 Edition</h2>', unsafe_allow_html=True)
    
    # Initialize session state
    if 'review_results' not in st.session_state:
        st.session_state.review_results = None
    if 'current_language' not in st.session_state:
        st.session_state.current_language = "Python"
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        language = st.selectbox(
            "Select Programming Language",
            ["Python", "JavaScript"],
            help="Choose the language of your code for appropriate analysis"
        )
        st.session_state.current_language = language
        
        st.markdown("---")
        st.markdown("### 🛠️ Analysis Tools")
        
        if language == "Python":
            st.markdown("**Static Analysis:**")
            st.markdown("• **Pylint** (Code quality)")
            st.markdown("• **Bandit** (Security)")
        elif language == "JavaScript":
            st.markdown("**Static Analysis:**")
            st.markdown("• **ESLint** (Code quality)")
        
        st.markdown("**🤖 AI Analysis:**")
        st.markdown("• **CodeT5** (Hugging Face)")
        st.markdown("• Code summary & suggestions")
        st.markdown("• Bug detection")
        st.markdown("• Refactoring ideas")
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<h3 class="section-header">📝 Code Input</h3>', unsafe_allow_html=True)
        
        code = st.text_area(
            "Paste your code here:",
            height=300,
            placeholder="def hello_world():\n    print('Hello, World!')\n    return True",
            help="Enter the code you want to review"
        )
        
        if st.button("🚀 Run AI Review", type="primary", use_container_width=True):
            if not code.strip():
                st.error("❌ Please enter some code to review!")
                st.session_state.review_results = None
            else:
                with st.spinner("🔄 Analyzing your code... This may take 30-60 seconds."):
                    try:
                        reviewer = CodeReviewer()
                        results = reviewer.review_code(code, language)
                        
                        st.session_state.review_results = results
                        st.session_state.current_language = language
                        st.success("✅ Code review completed!")
                        
                    except Exception as e:
                        st.error(f"❌ Error during code review: {str(e)}")
                        st.session_state.review_results = None
    
    with col2:
        st.markdown('<h3 class="section-header">📖 Instructions</h3>', unsafe_allow_html=True)
        
        st.markdown("""
        **How to use:**
        1. Select your programming language
        2. Paste your code in the text area
        3. Click "Run AI Review"
        4. View results in the sections below
        
        **What you'll get:**
        - 🤖 AI-powered code analysis
        - 🔍 Static analysis results
        - 🔒 Security scan results
        - 💡 Improvement suggestions
        """)
    
    # Display results if available
    if st.session_state.review_results:
        results = st.session_state.review_results
        language = st.session_state.current_language
        
        if "error" in results:
            st.error(results['error'])
        else:
            st.markdown("---")
            st.markdown('<h2 class="section-header">📊 Review Results</h2>', unsafe_allow_html=True)
            
            # AI Analysis Section
            with st.expander("🤖 AI Review Summary", expanded=True):
                ai_analysis = results.get("ai_analysis", {})
                display_ai_results(ai_analysis)
            
            # Static Analysis Section
            static_analysis = results.get("static_analysis", {})
            
            if language == "Python":
                with st.expander("🔍 Static Analysis (Pylint)", expanded=False):
                    display_pylint_results(static_analysis.get("pylint"))
                
                with st.expander("🔒 Security Analysis (Bandit)", expanded=False):
                    display_bandit_results(static_analysis.get("bandit"))
            
            elif language == "JavaScript":
                with st.expander("🔍 Static Analysis (ESLint)", expanded=False):
                    display_eslint_results(static_analysis.get("eslint"))
            
            # Combined Suggestions Section
            with st.expander("📋 Combined Suggestions", expanded=False):
                st.markdown("### Summary of All Findings")
                
                issue_count = 0
                
                pylint_data = static_analysis.get("pylint")
                if pylint_data and pylint_data.get("success") and pylint_data.get("results"):
                    issue_count += len(pylint_data["results"])
                
                bandit_data = static_analysis.get("bandit")
                if bandit_data and bandit_data.get("success"):
                    results_b = bandit_data.get("results", {})
                    issues = results_b.get("results", [])
                    issue_count += len(issues)
                
                eslint_data = static_analysis.get("eslint")
                if eslint_data and eslint_data.get("success") and eslint_data.get("results"):
                    for file_result in eslint_data["results"]:
                        issue_count += len(file_result.get("messages", []))
                
                if issue_count > 0:
                    st.warning(f"⚠️ Found {issue_count} total issues across all analyses")
                else:
                    st.success("🎉 No issues found in static analysis!")
                
                ai_analysis = results.get("ai_analysis", {})
                if ai_analysis.get("success"):
                    st.info("🤖 AI analysis completed - see details above")
                else:
                    st.warning("🤖 AI analysis unavailable")
            
            # Download report button
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col2:
                report_content = download_report(results)
                st.download_button(
                    label="📥 Download Full Report",
                    data=report_content,
                    file_name=f"code_review_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    # Footer
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #6c757d; font-size: 0.9rem; margin-top: 3rem;">Built with ❤️ using Hugging Face CodeT5 + Streamlit</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
