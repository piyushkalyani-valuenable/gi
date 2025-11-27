"""
API Testing Script - Tests all bill + bond combinations
"""
import os
import json
import requests
import random
from pathlib import Path
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
DATA_DIR = Path("Data")
BILLS_DIR = DATA_DIR / "Bills"
BONDS_DIR = DATA_DIR / "realtimebond"
OUTPUT_DIR = Path("testing")

# Testing Configuration
TEST_PERCENTAGE = 5  # Set percentage of combinations to test (1-100)
                      # 100 = test all combinations
                      # 10 = test 10% of combinations randomly
                      # 1 = test 1% of combinations randomly

# Create output directory
OUTPUT_DIR.mkdir(exist_ok=True)


def test_bill_with_bond(bill_path: Path, bond_path: Path) -> Dict[str, Any]:
    """
    Test a single bill + bond combination
    
    Returns the calculation result
    """
    print(f"\n{'='*80}")
    print(f"Testing: {bond_path.name} + {bill_path.name}")
    print(f"{'='*80}")
    
    try:
        # Step 1: Create session and upload bond
        print("📄 Uploading policy bond...")
        with open(bond_path, 'rb') as f:
            response = requests.post(
                f"{API_BASE_URL}/api/chat",
                files={'file': (bond_path.name, f, 'application/pdf')},
                data={'user_input': ''}
            )
        
        if response.status_code != 200:
            return {"error": f"Bond upload failed: {response.status_code}", "response": response.text}
        
        result = response.json()
        session_id = result.get('session_id')
        print(f"✅ Session created: {session_id}")
        
        # Step 2: Choose "bill" option
        print("📋 Selecting bill option...")
        response = requests.post(
            f"{API_BASE_URL}/api/chat",
            data={
                'session_id': session_id,
                'user_input': 'bill'
            }
        )
        
        if response.status_code != 200:
            return {"error": f"Bill option failed: {response.status_code}", "response": response.text}
        
        # Step 3: Upload bill
        print("🧾 Uploading bill...")
        with open(bill_path, 'rb') as f:
            # Determine mime type
            ext = bill_path.suffix.lower()
            mime_types = {
                '.pdf': 'application/pdf',
                '.png': 'image/png',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.webp': 'image/webp',
                '.avif': 'image/avif'
            }
            mime_type = mime_types.get(ext, 'application/octet-stream')
            
            response = requests.post(
                f"{API_BASE_URL}/api/chat",
                files={'file': (bill_path.name, f, mime_type)},
                data={
                    'session_id': session_id,
                    'user_input': ''
                }
            )
        
        if response.status_code != 200:
            return {"error": f"Bill upload failed: {response.status_code}", "response": response.text}
        
        result = response.json()
        print("✅ Calculation complete!")
        
        # Extract the calculation result from the reply
        reply = result.get('reply', '')
        if 'Claim Calculation Result:' in reply:
            # Parse the JSON from the reply
            json_str = reply.split('Claim Calculation Result:')[1].strip()
            calculation = json.loads(json_str)
            return {
                "success": True,
                "session_id": session_id,
                "bond_file": bond_path.name,
                "bill_file": bill_path.name,
                "calculation": calculation
            }
        else:
            return {
                "success": False,
                "session_id": session_id,
                "bond_file": bond_path.name,
                "bill_file": bill_path.name,
                "error": "No calculation result in response",
                "response": result
            }
    
    except Exception as e:
        return {
            "success": False,
            "bond_file": bond_path.name,
            "bill_file": bill_path.name,
            "error": str(e)
        }


def main():
    """Run all bill + bond combinations"""
    
    # Get all bills and bonds
    bills = sorted([f for f in BILLS_DIR.iterdir() if f.is_file()])
    bonds = sorted([f for f in BONDS_DIR.iterdir() if f.is_file() and f.suffix.lower() == '.pdf'])
    
    # Generate all combinations
    all_combinations = [(bond, bill) for bond in bonds for bill in bills]
    total_possible = len(all_combinations)
    
    # Calculate how many to test based on percentage
    num_to_test = max(1, int(total_possible * TEST_PERCENTAGE / 100))
    
    # Randomly sample combinations if not testing 100%
    if TEST_PERCENTAGE < 100:
        random.shuffle(all_combinations)
        combinations_to_test = all_combinations[:num_to_test]
        print(f"🎲 Random sampling enabled: Testing {TEST_PERCENTAGE}% of combinations")
    else:
        combinations_to_test = all_combinations
        print(f"📋 Testing all combinations")
    
    print(f"Found {len(bills)} bills and {len(bonds)} bonds")
    print(f"Total possible combinations: {total_possible}")
    print(f"Combinations to test: {num_to_test}")
    print(f"\nStarting tests...\n")
    
    # Test selected combinations
    results = []
    
    for idx, (bond_path, bill_path) in enumerate(combinations_to_test, 1):
        print(f"\n[{idx}/{num_to_test}] Testing combination...")
        
        # Run test
        result = test_bill_with_bond(bill_path, bond_path)
        results.append(result)
        
        # Save individual result
        bond_name = bond_path.stem.replace(' ', '_')
        bill_name = bill_path.stem.replace(' ', '_')
        output_file = OUTPUT_DIR / f"{bond_name}_{bill_name}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved to: {output_file}")
        
        # Show summary
        if result.get('success'):
            calc = result.get('calculation', {})
            insurer = calc.get('insurer_pays', 0)
            patient = calc.get('patient_pays', 0)
            total_bill = calc.get('total_bill_amount', 0)
            print(f"✅ SUCCESS - Bill: Rs.{total_bill:.2f} | Insurer: Rs.{insurer:.2f} | Patient: Rs.{patient:.2f}")
        else:
            error = result.get('error', 'Unknown error')
            print(f"❌ FAILED - {error}")
    
    # Save summary
    summary = {
        "test_percentage": TEST_PERCENTAGE,
        "total_possible_combinations": total_possible,
        "total_tests": num_to_test,
        "successful": sum(1 for r in results if r.get('success')),
        "failed": sum(1 for r in results if not r.get('success')),
        "results": results
    }
    
    summary_file = OUTPUT_DIR / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*80}")
    print(f"TESTING COMPLETE")
    print(f"{'='*80}")
    print(f"Test percentage: {TEST_PERCENTAGE}%")
    print(f"Total possible combinations: {summary['total_possible_combinations']}")
    print(f"Tests run: {summary['total_tests']}")
    print(f"Successful: {summary['successful']}")
    print(f"Failed: {summary['failed']}")
    print(f"Success rate: {summary['successful']/summary['total_tests']*100:.1f}%")
    print(f"\nResults saved to: {OUTPUT_DIR}/")
    print(f"Summary saved to: {summary_file}")


if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️ Server responded but not healthy")
    except requests.exceptions.RequestException:
        print("❌ ERROR: Server is not running!")
        print(f"Please start the server first: cd server && python main.py")
        exit(1)
    
    main()
