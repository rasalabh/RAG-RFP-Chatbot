"""
RAG Evaluation API Test Script

This script demonstrates the RAG evaluation feature by:
1. Sending test queries to the chatbot
2. Requesting evaluation metrics
3. Displaying results in a formatted way
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/chat"

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Test queries
TEST_QUERIES = [
    "What are the supported SBC models with Avaya Infinity?",
    "How is the 911 service priced with Avaya Infinity?",
    "How does Advanced bundle compare to Essentials Voice bundle?",
    "What languages are supported by Avaya Infinity modules?",
]

def print_separator():
    """Print a visual separator"""
    print("\n" + "="*80 + "\n")

def print_header(text: str):
    """Print a formatted header"""
    print(f"{Colors.BOLD}{Colors.HEADER}{text}{Colors.ENDC}")

def print_metric(name: str, score: float, verdict: str):
    """Print a formatted metric"""
    # Color based on score
    if score >= 0.7:
        color = Colors.OKGREEN
    elif score >= 0.5:
        color = Colors.WARNING
    else:
        color = Colors.FAIL
    
    # Create progress bar
    bar_length = 40
    filled_length = int(bar_length * score)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    
    # Verdict color
    verdict_color = Colors.OKGREEN if 'PASS' in verdict or 'FAITHFUL' in verdict or 'RELEVANT' in verdict else Colors.FAIL
    
    print(f"  {Colors.BOLD}{name}:{Colors.ENDC}")
    print(f"  {color}{bar}{Colors.ENDC} {color}{score*100:.1f}%{Colors.ENDC} {verdict_color}[{verdict}]{Colors.ENDC}")

def send_chat_request(query: str, evaluate: bool = True, top_k: int = 5, temperature: float = 0.7) -> Dict[str, Any]:
    """
    Send a chat request to the API
    
    Args:
        query: The question to ask
        evaluate: Whether to enable RAG evaluation
        top_k: Number of chunks to retrieve
        temperature: LLM temperature
    
    Returns:
        API response as dictionary
    """
    payload = {
        "message": query,
        "top_k": top_k,
        "temperature": temperature,
        "evaluate": evaluate
    }
    
    try:
        response = requests.post(CHAT_ENDPOINT, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        return None

def display_response(query: str, data: Dict[str, Any]):
    """Display the API response in a formatted way"""
    print_separator()
    print_header(f"QUERY: {query}")
    
    # Display answer
    print(f"\n{Colors.BOLD}{Colors.OKCYAN}ANSWER:{Colors.ENDC}")
    print(f"{data.get('response', 'No response')}\n")
    
    # Display sources
    sources = data.get('sources', [])
    if sources:
        print(f"{Colors.BOLD}{Colors.OKBLUE}SOURCES:{Colors.ENDC}")
        for source in sources:
            file_name = source['file'].split('\\')[-1].split('/')[-1]
            print(f"  📄 {file_name} - Page {source['page']}")
        print()
    
    # Display evaluation metrics
    evaluation = data.get('evaluation')
    if evaluation:
        print(f"{Colors.BOLD}{Colors.HEADER}EVALUATION METRICS:{Colors.ENDC}\n")
        
        # Overall score
        overall_score = evaluation.get('overall_score', 0)
        overall_verdict = evaluation.get('overall_verdict', 'UNKNOWN')
        
        verdict_color = Colors.OKGREEN if overall_verdict == 'PASS' else Colors.FAIL
        print(f"  {Colors.BOLD}Overall Score: {Colors.ENDC}{verdict_color}{overall_score*100:.1f}%{Colors.ENDC} {verdict_color}[{overall_verdict}]{Colors.ENDC}\n")
        
        # Individual metrics
        metrics = evaluation.get('metrics', {})
        
        if 'context_relevance' in metrics:
            metric = metrics['context_relevance']
            print_metric('Context Relevance', metric['score'], metric['verdict'])
            print()
        
        if 'faithfulness' in metrics:
            metric = metrics['faithfulness']
            print_metric('Faithfulness', metric['score'], metric['verdict'])
            print()
        
        if 'answer_relevance' in metrics:
            metric = metrics['answer_relevance']
            print_metric('Answer Relevance', metric['score'], metric['verdict'])
            print()
        
        # Recommendations
        recommendations = evaluation.get('recommendations', [])
        if recommendations:
            print(f"{Colors.BOLD}RECOMMENDATIONS:{Colors.ENDC}")
            for rec in recommendations:
                print(f"  {rec}")

def run_evaluation_demo():
    """Run the evaluation demonstration"""
    print_header("RAG EVALUATION API DEMO")
    print("\nThis script demonstrates the RAG evaluation feature.")
    print("It sends test queries and displays evaluation metrics.\n")
    
    print(f"{Colors.WARNING}Note: Make sure the server is running at {API_BASE_URL}{Colors.ENDC}")
    print(f"{Colors.WARNING}      and you have documents uploaded and processed.{Colors.ENDC}\n")
    
    input("Press Enter to start the demo...")
    
    # Test each query
    for i, query in enumerate(TEST_QUERIES, 1):
        print_separator()
        print(f"{Colors.BOLD}Test {i}/{len(TEST_QUERIES)}{Colors.ENDC}")
        
        # Send request with evaluation enabled
        data = send_chat_request(query, evaluate=True)
        
        if data:
            display_response(query, data)
        else:
            print(f"{Colors.FAIL}Failed to get response for query: {query}{Colors.ENDC}")
        
        # Pause between queries
        if i < len(TEST_QUERIES):
            input(f"\n{Colors.OKCYAN}Press Enter for next query...{Colors.ENDC}")
    
    print_separator()
    print_header("DEMO COMPLETE!")
    print("\nYou can now:")
    print("  1. Try the UI at http://localhost:8000")
    print("  2. Enable the 'Enable Evaluation' checkbox")
    print("  3. Ask your own questions and see metrics in real-time")

def run_single_query_test(query: str = None):
    """Test a single query with detailed output"""
    if query is None:
        query = input(f"{Colors.OKCYAN}Enter your query: {Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}Sending query with evaluation enabled...{Colors.ENDC}")
    data = send_chat_request(query, evaluate=True)
    
    if data:
        display_response(query, data)
        
        # Also show raw JSON for debugging
        print_separator()
        print_header("RAW JSON RESPONSE")
        print(json.dumps(data, indent=2))
    else:
        print(f"{Colors.FAIL}Failed to get response{Colors.ENDC}")

def main():
    """Main function"""
    print("\n" + "="*80)
    print(f"{Colors.BOLD}{Colors.HEADER}RAG EVALUATION TEST SCRIPT{Colors.ENDC}")
    print("="*80 + "\n")
    
    print("Choose an option:")
    print("  1. Run full demo with test queries")
    print("  2. Test a single query")
    print("  3. Exit")
    
    choice = input(f"\n{Colors.OKCYAN}Enter choice (1-3): {Colors.ENDC}")
    
    if choice == '1':
        run_evaluation_demo()
    elif choice == '2':
        run_single_query_test()
    elif choice == '3':
        print("Goodbye!")
    else:
        print(f"{Colors.WARNING}Invalid choice{Colors.ENDC}")

if __name__ == "__main__":
    main()
