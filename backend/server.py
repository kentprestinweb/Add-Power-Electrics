from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============== MODELS ==============

class Lead(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    phone: str
    suburb: str
    job_description: str
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "new"  # new, contacted, booked, completed
    sms_sent: bool = False
    email_sent: bool = False
    quote_sent: bool = False
    review_requested: bool = False

class LeadCreate(BaseModel):
    name: str
    phone: str
    suburb: str
    job_description: str

class EmailLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    lead_id: str
    email_type: str  # "confirmation", "quote"
    recipient_name: str
    recipient_phone: str
    subject: str
    body: str
    sent_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: str = "sent"  # In real implementation: "sent", "delivered", "failed"

class ChatMessage(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    action: Optional[str] = None  # None, "collect_name", "collect_phone", "collect_suburb", "collect_job", "lead_saved"
    lead_data: Optional[dict] = None
    quick_replies: Optional[List[str]] = None  # Dynamic quick reply suggestions

# Quick reply sets for different contexts
QUICK_REPLIES = {
    "greeting": ["Get a free quote", "What areas do you service?", "Emergency help"],
    "faq_followup": ["Yes, book now", "No thanks", "Tell me more"],
    "diy_warning": ["Yes, get a quote", "No thanks"],
    "after_booking_offer": ["Yes please", "Maybe later", "Just browsing"],
    "collect_name": [],  # No quick replies during data collection
    "collect_phone": [],
    "collect_suburb": ["Clyde North", "Cranbourne", "Berwick", "Pakenham", "Other"],
    "collect_job": ["Powerpoint installation", "Switchboard upgrade", "Lighting", "EV charger", "Other"],
    "lead_saved": ["Ask another question", "That's all, thanks"],
    "negative": ["Actually, yes book me in", "Ask another question"],
    "services_menu": ["Powerpoints", "Switchboards", "Lighting", "EV Chargers", "Smoke Alarms", "Other"],
}

class ConversationState(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    state: str = "greeting"  # greeting, faq, collect_name, collect_phone, collect_suburb, collect_job, completed
    collected_data: dict = Field(default_factory=dict)
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ============== FAQ DATABASE ==============

BUSINESS_INFO = {
    "name": "Add Power Electrics",
    "owner": "The team at Add Power Electrics",
    "phone": "0448 195 614",
    "rating": "5.0 stars (37 reviews)",
    "areas": "Greater Melbourne - all suburbs from CBD to outer areas",
    "hours": "9 AM - 5 PM, Monday to Friday",
    "emergency": "Yes, we offer emergency electrical services"
}

# Order matters - more specific patterns first
FAQ_PATTERNS = [
    # EV Chargers - specific pattern first
    (["ev", "electric vehicle", "ev charger", "tesla charger", "car charger", "charging station"],
     "EV charger installation is one of our growing specialties! We install home charging stations for Tesla, BYD, Hyundai, and all other electric vehicles. We can set up 7kW single-phase or 22kW three-phase chargers. What type of EV do you have, and do you know if you have single or three-phase power?"),
    
    # Powerpoints
    (["powerpoint", "power point", "outlet", "socket", "gpo"],
     "Yes, we install powerpoints! Whether you need additional outlets, USB powerpoints, or outdoor weatherproof GPOs, we've got you covered. Where do you need them installed?"),
    
    # Switchboard
    (["switchboard", "fuse box", "safety switch", "rcd", "circuit breaker"],
     "Switchboard upgrades are one of our specialties! We can upgrade old fuse boxes to modern safety switch boards, add circuits, or install new RCDs. Is your switchboard giving you trouble?"),
    
    # Lights & Downlights
    (["light", "lights", "downlight", "led", "lighting", "lamp"],
     "We're experts in lighting! LED downlights, pendant lights, outdoor security lighting, sensor lights - you name it. Looking to upgrade to energy-efficient LEDs?"),
    
    # Ceiling Fans
    (["ceiling fan", "fan", "cooling"],
     "Ceiling fan installation is a popular service! We can install new fans or replace existing ones. Do you have existing wiring or need new cabling run?"),
    
    # Smoke Alarms
    (["smoke alarm", "smoke detector", "fire alarm"],
     "Smoke alarm installation and testing is essential for safety! We install interconnected smoke alarms that comply with Australian regulations. Need your alarms checked?"),
    
    # TV & Data
    (["tv", "television", "antenna", "data", "network", "internet"],
     "Yes! We do TV wall mounting and antenna installation with attention to detail - clean cable management included. Where would you like your TV mounted?"),
    
    # Power Issues
    (["tripping", "trip", "power out", "no power", "blackout", "fault"],
     "Power tripping can be caused by faulty appliances, overloaded circuits, or safety switch issues. This needs attention! Can I grab your details so we can help diagnose the issue?"),
    
    # Hot Water
    (["hot water", "water heater"],
     "We can help with hot water system electrical connections and troubleshooting. Is your hot water system electric or do you need electrical work for a new installation?"),
    
    # Service areas
    (["area", "areas", "suburb", "location", "where", "clyde", "melbourne", "service area"],
     "We service the entire Greater Melbourne area! From the CBD to all outer suburbs - Clyde North, Cranbourne, Berwick, Pakenham, Werribee, you name it. Wherever you are in Melbourne, we can help. Are you in Greater Melbourne?"),
    
    # Availability
    (["available", "today", "urgent", "emergency", "asap", "quick"],
     "We try to accommodate urgent jobs where possible! For emergencies, we prioritise safety issues. Let me grab your details and we'll get back to you ASAP with availability."),
    
    # Quotes - more general
    (["quote", "cost", "price", "how much", "pricing", "rates", "charge"],
     "We offer free quotes for most jobs! Pricing depends on the scope of work. Would you like us to come out and provide a no-obligation quote?"),
    
    # License & Insurance
    (["license", "licensed", "insured", "insurance", "qualified", "certified"],
     "Absolutely! Add Power Electrics is fully licensed and insured. All our work meets Australian electrical standards and we provide certificates of compliance."),
    
    # DIY / How to do it myself questions - SAFETY REDIRECT
    (["how to", "how do i", "how can i", "diy", "myself", "manually", "tutorial", "guide", "steps to", "can i do"],
     "⚠️ For your safety, we strongly recommend NOT doing electrical work yourself. In Australia, DIY electrical work is actually illegal and can void your insurance, cause fires, or serious injury.\n\nWe offer affordable rates and can usually come out within 24-48 hours. Want me to grab your details for a free quote?"),
    
    # General inquiry - last resort
    (["help", "service", "work", "job", "need", "looking", "install"],
     "We offer a full range of residential and commercial electrical services! This includes powerpoints, lighting, switchboards, smoke alarms, ceiling fans, EV chargers, and more. What can we help you with today?"),
]

# Helper function to check if message looks like a question
def is_question(message: str) -> bool:
    """Check if a message looks like a question rather than an answer"""
    message_lower = message.lower().strip()
    question_indicators = [
        "how much", "how to", "how do", "how can", "how long",
        "what is", "what's", "what are", "what do",
        "when", "where", "why", "which",
        "can you", "can i", "do you", "is it", "are you",
        "cost", "price", "charge", "rate",
        "?"
    ]
    return any(q in message_lower for q in question_indicators)

# Helper function to validate name
def is_valid_name(message: str) -> bool:
    """Check if message looks like a valid name"""
    message = message.strip()
    # Name should be 2-50 chars, mostly letters/spaces, not a question
    if len(message) < 2 or len(message) > 50:
        return False
    if is_question(message):
        return False
    # Should contain mostly letters
    letter_count = sum(1 for c in message if c.isalpha() or c.isspace())
    return letter_count >= len(message) * 0.7

# ============== CHATBOT LOGIC ==============

def detect_intent(message: str) -> tuple:
    """Detect user intent from message and return (intent_type, response)"""
    message_lower = message.lower().strip()
    
    # Check for greetings
    greetings = ["hi", "hello", "hey", "g'day", "gday", "good morning", "good afternoon"]
    if any(g in message_lower for g in greetings):
        return ("greeting", f"G'day! 👋 Welcome to Add Power Electrics - your trusted local sparky in Greater Melbourne with a 5-star rating! How can I help you today? I can answer questions about our services or help you book a job.")
    
    # Check for DIY/how-to questions FIRST (safety concern)
    diy_patterns = ["how to", "how do i", "how can i", "diy", "myself", "manually", "tutorial", "guide", "steps to", "can i do it myself"]
    if any(diy in message_lower for diy in diy_patterns):
        return ("diy_warning", "⚠️ For your safety, we strongly recommend NOT doing electrical work yourself. In Australia, DIY electrical work is actually illegal and can void your insurance, cause fires, or serious injury.\n\nWe offer affordable rates and can usually come out within 24-48 hours. Want me to grab your details for a free quote?")
    
    # Check for booking/quote intent
    booking_words = ["book", "appointment", "schedule", "come out", "visit", "call me", "contact"]
    if any(b in message_lower for b in booking_words):
        return ("start_lead", "Great! I'd love to help you book a service. Let me grab a few details so we can get back to you quickly. What's your name?")
    
    # Check FAQ patterns (ordered list - more specific first)
    for keywords, response in FAQ_PATTERNS:
        if any(kw in message_lower for kw in keywords):
            return ("faq", response + "\n\nWould you like to book a job or get a free quote? I can grab your details!")
    
    # Check for yes/affirmative responses
    yes_words = ["yes", "yeah", "yep", "sure", "ok", "okay", "please", "definitely", "absolutely"]
    if any(y == message_lower or message_lower.startswith(y + " ") or message_lower.endswith(" " + y) for y in yes_words):
        return ("affirmative", None)  # Will be handled based on context
    
    # Check for no/negative responses
    no_words = ["no", "nah", "not", "don't", "nope"]
    if any(n == message_lower for n in no_words):
        return ("negative", "No worries! Is there anything else I can help you with today?")
    
    # Check for "tell me more" or similar exploratory responses
    explore_words = ["tell me more", "more info", "what else", "other services", "what do you do", "services"]
    if any(e in message_lower for e in explore_words):
        return ("explore_services", "We offer a wide range of electrical services! Here are some of our most popular ones - tap to learn more, or type your own question:")
    
    # Default response
    return ("unknown", "I'm here to help with electrical questions! What would you like to know about? Tap a service below or type your question:")

async def get_or_create_conversation(session_id: str) -> dict:
    """Get or create a conversation state"""
    conv = await db.conversations.find_one({"session_id": session_id}, {"_id": 0})
    if not conv:
        conv = ConversationState(session_id=session_id).model_dump()
        await db.conversations.insert_one(conv)
    return conv

async def update_conversation(session_id: str, state: str, collected_data: dict):
    """Update conversation state"""
    await db.conversations.update_one(
        {"session_id": session_id},
        {"$set": {
            "state": state,
            "collected_data": collected_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )

def validate_phone(phone: str) -> bool:
    """Validate Australian phone number"""
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    return bool(re.match(r'^(\+?61|0)?4\d{8}$', cleaned) or re.match(r'^(\+?61|0)?[2-9]\d{7,8}$', cleaned))

# ============== API ROUTES ==============

@api_router.get("/")
async def root():
    return {"message": "Add Power Electrics Chatbot API", "status": "online"}

@api_router.post("/chat", response_model=ChatResponse)
async def chat(chat_message: ChatMessage):
    """Process chat message and return response"""
    session_id = chat_message.session_id
    message = chat_message.message.strip()
    
    # Get conversation state
    conv = await get_or_create_conversation(session_id)
    state = conv.get("state", "greeting")
    collected_data = conv.get("collected_data", {})
    
    intent, intent_response = detect_intent(message)
    
    # IMPORTANT: During lead collection, check if user is asking a question instead of answering
    if state in ["collect_name", "collect_phone", "collect_suburb", "collect_job"]:
        # If user asks a question during lead capture, answer it and remind them
        if is_question(message):
            # Handle common questions during lead capture
            if intent == "faq" or intent == "diy_warning":
                field_name = 'name' if state == 'collect_name' else 'phone number' if state == 'collect_phone' else 'suburb' if state == 'collect_suburb' else 'job description'
                return ChatResponse(
                    response=f"{intent_response}\n\n---\n\n📝 By the way, I was just collecting your details for a quote. Would you like to continue? Just tell me your **{field_name}**.",
                    quick_replies=["Continue booking", "Cancel"]
                )
            elif any(word in message.lower() for word in ["how much", "cost", "price", "charge"]):
                field_name = "name" if state == "collect_name" else "phone number" if state == "collect_phone" else "suburb" if state == "collect_suburb" else "job description"
                return ChatResponse(
                    response=f"Great question! Pricing depends on the specific job - that's why we offer free quotes. Once I have your details, we can give you an accurate price.\n\n📝 What's your **{field_name}**?",
                    quick_replies=["Continue booking", "Cancel"]
                )
    
    # State machine for lead collection
    if state == "collect_name":
        # Validate it looks like a name
        if not is_valid_name(message):
            return ChatResponse(
                response="I didn't quite catch that. Could you please tell me your name?",
                action="collect_name",
                quick_replies=[]
            )
        collected_data["name"] = message
        await update_conversation(session_id, "collect_phone", collected_data)
        return ChatResponse(
            response=f"Thanks {message}! 📱 What's the best phone number to reach you on?",
            action="collect_phone",
            quick_replies=[]
        )
    
    elif state == "collect_phone":
        if validate_phone(message):
            collected_data["phone"] = message
            await update_conversation(session_id, "collect_suburb", collected_data)
            return ChatResponse(
                response="Perfect! 📍 What suburb are you located in?",
                action="collect_suburb",
                quick_replies=QUICK_REPLIES["collect_suburb"]
            )
        else:
            return ChatResponse(
                response="Hmm, that doesn't look like a valid phone number. Could you please enter your Australian mobile or landline number? (e.g., 0412 345 678)",
                action="collect_phone",
                quick_replies=[]
            )
    
    elif state == "collect_suburb":
        collected_data["suburb"] = message
        await update_conversation(session_id, "collect_job", collected_data)
        return ChatResponse(
            response="Great! 🔧 Now, briefly describe the electrical work you need done:",
            action="collect_job",
            quick_replies=QUICK_REPLIES["collect_job"]
        )
    
    elif state == "collect_job":
        collected_data["job_description"] = message
        
        # Save the lead
        lead = Lead(
            name=collected_data.get("name", ""),
            phone=collected_data.get("phone", ""),
            suburb=collected_data.get("suburb", ""),
            job_description=collected_data.get("job_description", "")
        )
        lead_dict = lead.model_dump()
        await db.leads.insert_one(lead_dict.copy())  # Use copy to avoid _id mutation
        
        # Auto-send confirmation email
        await send_confirmation_email(lead_dict)
        
        # Reset conversation
        await update_conversation(session_id, "completed", {})
        
        # Return clean lead data without potential _id
        clean_lead_data = {
            "id": lead_dict["id"],
            "name": lead_dict["name"],
            "phone": lead_dict["phone"],
            "suburb": lead_dict["suburb"],
            "job_description": lead_dict["job_description"],
            "status": lead_dict["status"],
            "created_at": lead_dict["created_at"]
        }
        
        return ChatResponse(
            response=f"Awesome! ✅ Thanks {collected_data.get('name', '')}! I've passed your details to the team at Add Power Electrics and sent you a confirmation.\n\n📋 **Your Request:**\n• Name: {collected_data.get('name')}\n• Phone: {collected_data.get('phone')}\n• Suburb: {collected_data.get('suburb')}\n• Job: {collected_data.get('job_description')}\n\n📧 A confirmation has been sent to you!\n\nWe'll be in touch shortly! Is there anything else I can help with?",
            action="lead_saved",
            lead_data=clean_lead_data,
            quick_replies=QUICK_REPLIES["lead_saved"]
        )
    
    # Handle intents based on current state
    if intent == "greeting":
        await update_conversation(session_id, "greeting", {})
        return ChatResponse(response=intent_response, quick_replies=QUICK_REPLIES["greeting"])
    
    elif intent == "diy_warning":
        await update_conversation(session_id, "faq", {})
        return ChatResponse(response=intent_response, quick_replies=QUICK_REPLIES["diy_warning"])
    
    elif intent == "start_lead" or (intent == "affirmative" and state in ["greeting", "faq", "completed", "diy_warning"]):
        await update_conversation(session_id, "collect_name", {})
        return ChatResponse(
            response="Great! I'd love to help you book a service. Let me grab a few details so we can get back to you quickly. 👤 What's your name?",
            action="collect_name",
            quick_replies=[]
        )
    
    elif intent == "faq":
        await update_conversation(session_id, "faq", {})
        return ChatResponse(response=intent_response, quick_replies=QUICK_REPLIES["faq_followup"])
    
    elif intent == "negative":
        return ChatResponse(response=intent_response, quick_replies=QUICK_REPLIES["negative"])
    
    else:
        return ChatResponse(response=intent_response, quick_replies=QUICK_REPLIES["greeting"])

@api_router.post("/leads", response_model=Lead)
async def create_lead(lead_data: LeadCreate):
    """Manually create a lead"""
    lead = Lead(**lead_data.model_dump())
    lead_dict = lead.model_dump()
    await db.leads.insert_one(lead_dict)
    return lead

@api_router.get("/leads", response_model=List[Lead])
async def get_leads():
    """Get all leads"""
    leads = await db.leads.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return leads

@api_router.patch("/leads/{lead_id}/status")
async def update_lead_status(lead_id: str, status: str):
    """Update lead status"""
    valid_statuses = ["new", "contacted", "booked", "completed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid_statuses}")
    
    result = await db.leads.update_one(
        {"id": lead_id},
        {"$set": {"status": status}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Status updated", "status": status}

@api_router.delete("/leads/{lead_id}")
async def delete_lead(lead_id: str):
    """Delete a lead"""
    result = await db.leads.delete_one({"id": lead_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}

@api_router.get("/stats")
async def get_stats():
    """Get dashboard statistics"""
    total_leads = await db.leads.count_documents({})
    new_leads = await db.leads.count_documents({"status": "new"})
    contacted = await db.leads.count_documents({"status": "contacted"})
    booked = await db.leads.count_documents({"status": "booked"})
    completed = await db.leads.count_documents({"status": "completed"})
    
    return {
        "total_leads": total_leads,
        "new_leads": new_leads,
        "contacted": contacted,
        "booked": booked,
        "completed": completed
    }

# ============== EMAIL FUNCTIONS ==============

def generate_confirmation_email(lead: dict) -> dict:
    """Generate confirmation email content for customer"""
    subject = "Thanks for contacting Add Power Electrics! ⚡"
    body = f"""Hi {lead['name']},

Thanks for reaching out to Add Power Electrics! We've received your enquiry and a member of our team will be in touch shortly.

📋 YOUR REQUEST DETAILS:
━━━━━━━━━━━━━━━━━━━━━━
• Name: {lead['name']}
• Phone: {lead['phone']}
• Location: {lead['suburb']}
• Job Description: {lead['job_description']}
━━━━━━━━━━━━━━━━━━━━━━

We typically respond within 2-4 business hours. For urgent electrical emergencies, please call us directly at 0448 195 614.

What happens next?
1. Our team reviews your request
2. We'll call you to discuss the job and arrange a time
3. We provide a free, no-obligation quote on-site

⭐ Add Power Electrics
Licensed & Insured | 5.0 Stars (37 Reviews)
Servicing Clyde North & Melbourne's South-East

This is an automated confirmation email."""
    
    return {"subject": subject, "body": body}

def generate_quote_email(lead: dict) -> dict:
    """Generate quote request email content"""
    subject = f"Your Free Quote Request - Add Power Electrics ⚡"
    body = f"""Hi {lead['name']},

Great news! We're ready to provide you with a FREE quote for your electrical work.

📋 JOB SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━
{lead['job_description']}
━━━━━━━━━━━━━━━━━━━━━━

📍 Location: {lead['suburb']}

WHAT'S INCLUDED IN OUR QUOTE:
✓ Detailed breakdown of work required
✓ Transparent pricing - no hidden fees
✓ Expected timeframe
✓ All materials and labour

We'd love to arrange a time to come out and assess the job. This visit is completely FREE with no obligation.

To confirm your quote appointment, simply:
📞 Call us: 0448 195 614
💬 Reply to this message

We look forward to helping you!

⭐ Add Power Electrics
Licensed & Insured | 5.0 Stars (37 Reviews)
Servicing Clyde North & Melbourne's South-East"""
    
    return {"subject": subject, "body": body}

async def send_confirmation_email(lead: dict) -> dict:
    """Send confirmation email when lead is captured (MOCKED)"""
    email_content = generate_confirmation_email(lead)
    
    # Create email log
    email_log = EmailLog(
        lead_id=lead['id'],
        email_type="confirmation",
        recipient_name=lead['name'],
        recipient_phone=lead['phone'],
        subject=email_content['subject'],
        body=email_content['body']
    )
    
    # Store email log in database
    await db.email_logs.insert_one(email_log.model_dump())
    
    # Update lead
    await db.leads.update_one({"id": lead['id']}, {"$set": {"email_sent": True}})
    
    logger.info(f"[MOCKED EMAIL] Confirmation sent to {lead['name']} ({lead['phone']})")
    
    return email_log.model_dump()

# ============== EMAIL API ROUTES ==============

@api_router.post("/email/send-quote")
async def send_quote_email(lead_id: str):
    """Send quote email to customer (MOCKED)"""
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    email_content = generate_quote_email(lead)
    
    # Create email log
    email_log = EmailLog(
        lead_id=lead_id,
        email_type="quote",
        recipient_name=lead['name'],
        recipient_phone=lead['phone'],
        subject=email_content['subject'],
        body=email_content['body']
    )
    
    # Store email log
    await db.email_logs.insert_one(email_log.model_dump())
    
    # Update lead
    await db.leads.update_one({"id": lead_id}, {"$set": {"quote_sent": True}})
    
    logger.info(f"[MOCKED EMAIL] Quote sent to {lead['name']} ({lead['phone']})")
    
    return {
        "message": "Quote email simulated (Email integration ready)",
        "lead_id": lead_id,
        "email": email_log.model_dump(),
        "note": "To enable real emails, add SendGrid/Resend credentials to .env"
    }

@api_router.get("/email/logs")
async def get_email_logs(lead_id: Optional[str] = None):
    """Get email logs, optionally filtered by lead_id"""
    query = {"lead_id": lead_id} if lead_id else {}
    logs = await db.email_logs.find(query, {"_id": 0}).sort("sent_at", -1).to_list(100)
    return logs

@api_router.get("/email/preview/{lead_id}")
async def preview_emails(lead_id: str):
    """Preview what emails would be sent for a lead"""
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return {
        "confirmation": generate_confirmation_email(lead),
        "quote": generate_quote_email(lead),
        "review_request": generate_review_request_email(lead)
    }

def generate_review_request_email(lead: dict) -> dict:
    """Generate review request email for completed jobs"""
    subject = "How did we do? ⭐ - Add Power Electrics"
    body = f"""Hi {lead['name']},

Thanks for choosing Add Power Electrics for your recent electrical work!

We hope everything went smoothly. If you were happy with our service, we'd really appreciate a quick Google review - it only takes 30 seconds and helps other Melburnians find a sparky they can trust.

⭐ LEAVE A REVIEW:
https://g.page/r/YOUR-GOOGLE-REVIEW-LINK/review

Your feedback helps us:
✓ Improve our service
✓ Help other customers find reliable electricians
✓ Keep delivering 5-star work

Already left a review? Thank you so much! 🙏

If anything wasn't quite right, please reply to this email or call us on 0448 195 614 - we want to make it right.

Thanks again for your business!

⚡ Add Power Electrics
5.0 Stars | 37+ Reviews | Greater Melbourne
Licensed & Insured"""
    
    return {"subject": subject, "body": body}

@api_router.post("/email/send-review-request")
async def send_review_request_email(lead_id: str):
    """Send review request email to customer after job completion (MOCKED)"""
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    if lead.get('status') != 'completed':
        raise HTTPException(status_code=400, detail="Can only request reviews for completed jobs")
    
    email_content = generate_review_request_email(lead)
    
    # Create email log
    email_log = EmailLog(
        lead_id=lead_id,
        email_type="review_request",
        recipient_name=lead['name'],
        recipient_phone=lead['phone'],
        subject=email_content['subject'],
        body=email_content['body']
    )
    
    # Store email log
    await db.email_logs.insert_one(email_log.model_dump())
    
    # Update lead
    await db.leads.update_one({"id": lead_id}, {"$set": {"review_requested": True}})
    
    logger.info(f"[MOCKED EMAIL] Review request sent to {lead['name']} ({lead['phone']})")
    
    return {
        "message": "Review request email simulated (Email integration ready)",
        "lead_id": lead_id,
        "email": email_log.model_dump(),
        "note": "To enable real emails, add SendGrid/Resend credentials to .env"
    }

# SMS placeholder endpoint (ready for Twilio integration)
@api_router.post("/sms/send")
async def send_sms_notification(lead_id: str):
    """Placeholder for SMS notification - ready for Twilio integration"""
    lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # TODO: Integrate Twilio here
    # message = f"New lead from {lead['name']}! Phone: {lead['phone']}, Suburb: {lead['suburb']}, Job: {lead['job_description']}"
    # client.messages.create(body=message, from_=TWILIO_NUMBER, to=BUSINESS_PHONE)
    
    await db.leads.update_one({"id": lead_id}, {"$set": {"sms_sent": True}})
    
    return {
        "message": "SMS notification simulated (Twilio integration ready)",
        "lead_id": lead_id,
        "sms_sent": True,
        "note": "To enable real SMS, add Twilio credentials to .env"
    }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
