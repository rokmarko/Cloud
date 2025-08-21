#!/usr/bin/env python3
"""
Create a test checklist to demonstrate the printable checklist feature.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models import db, Checklist, User
from src.app import create_app
import json

def create_demo_checklist():
    """Create a demo checklist for testing the printable feature."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Find the first active user (or create if needed)
            user = User.query.filter_by(is_active=True).first()
            
            if not user:
                print("❌ No active user found in database")
                return False
            
            print(f"📝 Creating demo checklist for user: {user.email}")
            
            # Create a comprehensive demo checklist
            demo_data = {
                "Language": "en-gb",
                "Voice": "Harry",
                "Root": {
                    "Type": 0,
                    "Name": "Root",
                    "Children": [
                        {
                            "Type": 0,
                            "Name": "Pre-flight",
                            "Children": [
                                {
                                    "Type": 1,
                                    "Name": "Aircraft Exterior Inspection",
                                    "Items": [
                                        {
                                            "Title": "Pitot tube cover",
                                            "Action": "REMOVE",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Wing inspection",
                                            "Action": "CHECK for damage, fuel leaks, control surface freedom",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Propeller",
                                            "Action": "CHECK for nicks, cracks, security",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                },
                                {
                                    "Type": 1,
                                    "Name": "Cockpit Preparation",
                                    "Items": [
                                        {
                                            "Title": "Seat belts and harnesses",
                                            "Action": "FASTEN and ADJUST",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Flight controls",
                                            "Action": "CHECK free and correct movement",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Avionics master switch",
                                            "Action": "ON",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "Type": 0,
                            "Name": "Engine Start",
                            "Children": [
                                {
                                    "Type": 1,
                                    "Name": "Before Engine Start",
                                    "Items": [
                                        {
                                            "Title": "Fuel selector",
                                            "Action": "BOTH or ON position",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Mixture",
                                            "Action": "RICH",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Propeller area",
                                            "Action": "CLEAR",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                },
                                {
                                    "Type": 1,
                                    "Name": "Engine Start Sequence",
                                    "Items": [
                                        {
                                            "Title": "Master switch",
                                            "Action": "ON",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Beacon light",
                                            "Action": "ON",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Start engine",
                                            "Action": "ENGAGE starter, monitor oil pressure",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "Type": 0,
                            "Name": "In-flight",
                            "Children": [
                                {
                                    "Type": 1,
                                    "Name": "Takeoff",
                                    "Items": [
                                        {
                                            "Title": "Engine parameters",
                                            "Action": "CHECK green ranges",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Flight controls",
                                            "Action": "FINAL check",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Transponder",
                                            "Action": "SET to assigned squawk code",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "Type": 0,
                            "Name": "Post-flight",
                            "Children": [
                                {
                                    "Type": 1,
                                    "Name": "Engine Shutdown",
                                    "Items": [
                                        {
                                            "Title": "Mixture",
                                            "Action": "IDLE CUT-OFF",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Ignition switch",
                                            "Action": "OFF",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Master switch",
                                            "Action": "OFF",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                },
                                {
                                    "Type": 1,
                                    "Name": "Securing Aircraft",
                                    "Items": [
                                        {
                                            "Title": "Control lock",
                                            "Action": "INSTALL",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Pitot tube cover",
                                            "Action": "INSTALL",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Tie-down or hangar",
                                            "Action": "SECURE aircraft",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "Type": 0,
                            "Name": "Emergency",
                            "Children": [
                                {
                                    "Type": 1,
                                    "Name": "Engine Fire During Start",
                                    "Items": [
                                        {
                                            "Title": "Starter",
                                            "Action": "CONTINUE cranking to suck flames into engine",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Mixture",
                                            "Action": "IDLE CUT-OFF",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Fuel selector",
                                            "Action": "OFF",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                },
                                {
                                    "Type": 1,
                                    "Name": "Emergency Landing",
                                    "Items": [
                                        {
                                            "Title": "Airspeed",
                                            "Action": "MAINTAIN best glide speed",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Emergency frequency",
                                            "Action": "121.5 MHz - MAYDAY call",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        },
                                        {
                                            "Title": "Transponder",
                                            "Action": "7700 (emergency)",
                                            "VoiceText": "",
                                            "VoiceBin": ""
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
            
            # Create the checklist
            checklist = Checklist(
                title="Demo Aircraft Checklist",
                description="A comprehensive demonstration checklist showing pre-flight, engine start, in-flight, post-flight, and emergency procedures.",
                json_content=json.dumps(demo_data),
                items=json.dumps([]),  # Legacy field, keep for compatibility
                user_id=user.id
            )
            
            db.session.add(checklist)
            db.session.commit()
            
            print(f"✅ Created demo checklist with ID: {checklist.id}")
            print(f"   Title: {checklist.title}")
            print(f"   Sections: 5 (Pre-flight, Engine Start, In-flight, Post-flight, Emergency)")
            print(f"   Total checklists: 7")
            print(f"   Total items: 19")
            print(f"\n🖨️  You can now test the printable version at:")
            print(f"   http://localhost:5000/dashboard/checklists/{checklist.id}/print")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating demo checklist: {e}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = create_demo_checklist()
    if success:
        print("\n✅ Demo checklist created successfully!")
    else:
        print("\n❌ Failed to create demo checklist!")
    
    sys.exit(0 if success else 1)
