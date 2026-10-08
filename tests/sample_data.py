"""Deterministic fixtures for the five assessment samples; production never imports these."""

SAMPLE_CASES = [
    {
        "input": "Paid ₹ 1,250 to AWS India Pvt Ltd on 12 March 2024. Invoice #INV-2024-0312. Services: cloud compute.",
        "draft": {
            "vendor_name": {"value": "AWS India Pvt Ltd", "confidence": 0.99},
            "amount": {"value": 1250, "confidence": 0.99},
            "currency": {"value": "INR", "confidence": 0.99},
            "date": {"value": "2024-03-12", "confidence": 0.99},
            "category": {"value": "software", "confidence": 0.91},
            "description": {"value": "Cloud compute services", "confidence": 0.91},
            "invoice_id": {"value": "INV-2024-0312", "confidence": 0.99},
        },
    },
    {
        "input": "Hi team, please find attached the invoice from Zoho Corp for ₹ 4,800 (software subscription, April 2024). Reference: ZHO-88821.",
        "draft": {
            "vendor_name": {"value": "Zoho Corp", "confidence": 0.97},
            "amount": {"value": 4800, "confidence": 0.99},
            "currency": {"value": "INR", "confidence": 0.98},
            "date": {"value": None, "confidence": 0.13},
            "category": {"value": "software", "confidence": 0.95},
            "description": {"value": "Software subscription for April 2024", "confidence": 0.92},
            "invoice_id": {"value": "ZHO-88821", "confidence": 0.98},
        },
    },
    {
        "input": "hey can someone reimburse me for the uber last tuesday? it was like 340 rupees, went to the airport for the client meeting",
        "draft": {
            "vendor_name": {"value": "Uber", "confidence": 0.83},
            "amount": {"value": 340, "confidence": 0.61},
            "currency": {"value": "INR", "confidence": 0.88},
            "date": {"value": None, "confidence": 0.38},
            "category": {"value": "travel", "confidence": 0.97},
            "description": {"value": "Ride to the airport for a client meeting", "confidence": 0.92},
            "invoice_id": {"value": None, "confidence": 0.08},
        },
    },
    {
        "input": "DELHI METRO RAIL CORP Token: 0042 Fare: INR 30 Date: 29-04-2024 From: Rajiv Chowk To: Hauz Khas",
        "draft": {
            "vendor_name": {"value": "DELHI METRO RAIL CORP", "confidence": 0.98},
            "amount": {"value": 30, "confidence": 0.98},
            "currency": {"value": "INR", "confidence": 0.99},
            "date": {"value": "29-04-2024", "confidence": 0.96},
            "category": {"value": "travel", "confidence": 0.94},
            "description": {"value": "Delhi Metro fare from Rajiv Chowk to Hauz Khas", "confidence": 0.95},
            "invoice_id": {"value": None, "confidence": 0.12},
        },
    },
    {
        "input": "meeting notes: discussed q2 targets, revenue up 12%, john to follow up with vendors next week",
        "draft": {
            "vendor_name": {"value": None, "confidence": 0.05},
            "amount": {"value": None, "confidence": 0.04},
            "currency": {"value": None, "confidence": 0.03},
            "date": {"value": None, "confidence": 0.05},
            "category": {"value": None, "confidence": 0.05},
            "description": {"value": None, "confidence": 0.10},
            "invoice_id": {"value": None, "confidence": 0.03},
        },
    },
]
