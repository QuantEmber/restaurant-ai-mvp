#!/usr/bin/env python3
"""
Restaurant AI Marketing Assistant — MVP
========================================
Streamlit app that generates social media content, marketing campaigns,
and customer engagement responses for restaurants using OpenAI GPT-4o.

Features:
  1. Photo → Instagram/Facebook captions, hashtags, CTAs
  2. Menu item → multi-platform marketing copy
  3. Event → promotional campaign ideas + audience targeting
  4. Google review → professional response suggestions
  5. Customer message → reply templates

Run:  streamlit run app.py
"""

import streamlit as st
import json
import base64
import os
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    st.error("Run: pip install openai")
    st.stop()

# ── Config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Restaurant AI Marketing Assistant",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 2rem;
    }
    .output-card {
        background: #f8f9fa;
        border-left: 4px solid #e74c3c;
        padding: 1rem 1.2rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .platform-tag {
        display: inline-block;
        background: #e74c3c;
        color: white;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .review-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 20px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ── OpenAI Client ────────────────────────────────────────────────────────

def get_client():
    """Initialize OpenAI client from sidebar key or env var."""
    api_key = st.session_state.get("openai_key") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def encode_image(uploaded_file):
    """Encode uploaded image to base64 for GPT-4o vision."""
    return base64.b64encode(uploaded_file.getvalue()).decode("utf-8")


# ── System Prompts ───────────────────────────────────────────────────────

RESTAURANT_CONTEXT = """You are a restaurant marketing expert and social media
strategist. You write engaging, appetizing, on-brand content that drives foot
traffic and online engagement. Your tone is warm, inviting, and professional —
never generic or robotic. You understand food photography, dining culture, and
what makes people want to visit a restaurant."""

CONTENT_SYSTEM = RESTAURANT_CONTEXT + """

When given information about a dish, event, or photo, generate ALL of the following:

1. **Instagram Caption** (150-200 words, storytelling style, 20-30 relevant hashtags,
   call-to-action, emoji usage that feels natural not overdone)
2. **Facebook Post** (100-150 words, more conversational, 1-2 hashtags max,
   clear CTA with link placeholder, designed for sharing)
3. **Twitter/X Post** (280 chars max, punchy, 3-5 hashtags)
4. **Promotional Campaign Idea** (2-3 sentences describing a campaign concept
   that could run for 1-2 weeks around this item/event)
5. **Audience Targeting Suggestions** (3-5 bullet points: demographics, interests,
   behaviors, lookalike audiences, geo-targeting recommendations)

Format each section with clear headers. Make content feel authentic to a
real restaurant, not like AI-generated marketing."""

REVIEW_SYSTEM = RESTAURANT_CONTEXT + """

You are responding to customer reviews on behalf of a restaurant. Your responses should:
- Always thank the reviewer by name if available
- Be warm, professional, and genuine — never defensive or robotic
- For POSITIVE reviews: express gratitude, highlight what they mentioned, invite them back
- For NEGATIVE reviews: empathize first, acknowledge the issue, offer to make it right
  (invite them to contact directly), never argue or make excuses
- For MIXED reviews: thank for positives, address concerns, show you're improving
- Keep responses 50-100 words (concise but personal)
- Include the restaurant name naturally

Generate 3 response options:
1. **Warm & Personal** — most empathetic tone
2. **Professional & Brief** — efficient but still warm
3. **Action-Oriented** — focuses on resolution/invitation"""

MESSAGE_SYSTEM = RESTAURANT_CONTEXT + """

Generate professional, friendly response templates for customer messages.
Provide 2-3 options for each message, ranging from brief to detailed.
Include personalization placeholders like [Customer Name], [Date], [Time].
Responses should feel human, not automated."""


# ── Generation Functions ─────────────────────────────────────────────────

def generate_content_from_photo(client, image_b64, context=""):
    """Generate marketing content from a food/event photo."""
    messages = [
        {"role": "system", "content": CONTENT_SYSTEM},
        {"role": "user", "content": [
            {"type": "text", "text": f"Generate restaurant marketing content for this photo. "
             f"Additional context: {context}" if context else
             "Generate restaurant marketing content for this photo."},
            {"type": "image_url", "image_url": {
                "url": f"data:image/jpeg;base64,{image_b64}",
                "detail": "high"
            }}
        ]}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1500,
        temperature=0.8,
    )
    return response.choices[0].message.content


def generate_content_from_text(client, item_name, price, description, content_type="dish"):
    """Generate marketing content from text inputs."""
    prompt = f"""Generate restaurant marketing content for this {content_type}:

Name: {item_name}
{"Price: " + price if price else ""}
Description: {description}

Make the content appetizing, engaging, and designed to drive visits/orders."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CONTENT_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.8,
    )
    return response.choices[0].message.content


def generate_event_campaign(client, event_name, date, details, special_offer=""):
    """Generate promotional campaign for an event."""
    prompt = f"""Generate a full marketing campaign for this restaurant event:

Event: {event_name}
Date: {date}
Details: {details}
{"Special Offer: " + special_offer if special_offer else ""}

Include pre-event hype posts, day-of content, and post-event follow-up ideas."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CONTENT_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        temperature=0.8,
    )
    return response.choices[0].message.content


def generate_review_response(client, review_text, reviewer_name, stars, restaurant_name):
    """Generate response options for a Google review."""
    prompt = f"""Respond to this Google review for {restaurant_name}:

Reviewer: {reviewer_name}
Rating: {stars}/5 stars
Review: "{review_text}"

Generate 3 response options as described in your instructions."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": REVIEW_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        max_tokens=800,
        temperature=0.7,
    )
    return response.choices[0].message.content


def generate_message_reply(client, customer_message, context=""):
    """Generate reply templates for customer messages."""
    prompt = f"""Generate response templates for this customer message:

Message: "{customer_message}"
{"Context: " + context if context else ""}

Provide 2-3 response options."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": MESSAGE_SYSTEM},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ── Demo Mode (no API key needed) ────────────────────────────────────────

DEMO_CONTENT = {
    "photo": """## 📸 Instagram Caption

Crispy on the outside, tender on the inside — our new Truffle Parmesan Fries are here and they're *everything*. Hand-cut daily, tossed in white truffle oil, and showered with aged parmesan and fresh herbs. 🍟✨

This isn't a side dish. This is the main character.

Available now for dine-in and takeout. Tag someone who needs these in their life 👇

#TruffleFries #FoodieFinds #RestaurantLife #NewMenuItem #FrenchFries #TruffleEverything #FoodPhotography #InstaFood #ChefSpecial #ComfortFood #FoodieGram #EatLocal #FoodLover #GourmetFries #Yummy #FoodPorn #Delicious #FoodBlogger #TruffleSeason #ParmesanFries #FreshAndLocal #DineLocal #FoodieLife #TastyTreats #CrispyFries

---

## 📘 Facebook Post

🍟 NEW ALERT: Truffle Parmesan Fries just dropped!

Hand-cut, tossed in white truffle oil, and loaded with aged parmesan. These aren't your average fries — they're a whole experience.

Stop by this week and try them before the secret gets out. Available for dine-in and takeout!

📍 [Restaurant Name] | 📞 [Phone] | 🔗 Order online: [link]

---

## 🐦 Twitter/X Post

Our new Truffle Parmesan Fries just hit the menu and we're not being dramatic when we say they'll change your life 🍟✨ Come try them. #TruffleFries #NewMenu #FoodieFinds #EatLocal

---

## 🎯 Campaign Idea

**"Truffle Week"** — Run a 7-day campaign featuring one truffle dish per day on social media. Day 1: Truffle Fries reveal. Day 3: Behind-the-scenes truffle prep video. Day 5: Customer taste-test reels. Day 7: Limited-time truffle flight (3 truffle dishes for $29). Creates urgency and showcases the full truffle menu.

---

## 👥 Audience Targeting

- **Demographics**: Ages 25-45, urban, household income $60k+
- **Interests**: Foodies, fine dining, cooking shows, food photography, Yelp/OpenTable users
- **Behaviors**: Frequent restaurant visitors, online food ordering, Instagram engagement with food content
- **Lookalike**: Build from existing customers who've ordered appetizers/shareables
- **Geo-targeting**: 10-mile radius, boost during lunch (11am-1pm) and dinner (5-8pm) hours""",

    "review_positive": """## 1. Warm & Personal

Thank you so much, Sarah! 😊 We're thrilled that you loved the seafood risotto — our chef puts so much heart into that dish. It means the world to hear that the service made your anniversary special. We can't wait to welcome you and your partner back. Happy anniversary again! — The [Restaurant Name] Team

## 2. Professional & Brief

Thank you for the wonderful review, Sarah! We're delighted the risotto and service exceeded your expectations. Congratulations on your anniversary — we'd love to host your next celebration. See you soon!

## 3. Action-Oriented

Sarah, thank you for choosing us for your anniversary! 🎉 Since you loved the risotto, you'll want to try our new Lobster Linguine launching next month. Follow us on Instagram for the reveal, and mention this review for a complimentary dessert on your next visit!""",

    "review_negative": """## 1. Warm & Personal

Hi Michael, thank you for taking the time to share your experience, and I'm sincerely sorry we fell short. A 45-minute wait for your entrée is not the standard we hold ourselves to, and I understand how frustrating that must have been during a busy evening. I'd love the chance to make this right — could you reach out to us at [email]? We want to ensure your next visit reflects the experience you deserve.

## 2. Professional & Brief

Michael, we apologize for the extended wait time during your visit. This doesn't reflect our standards, and we're addressing it with our kitchen team. Please contact us at [email] — we'd like to invite you back for a better experience.

## 3. Action-Oriented

Michael, thank you for this feedback — we take it seriously. We've already spoken with our kitchen team about Friday evening pacing. We'd like to offer you a complimentary meal to show you what we're really about. Please email [email] and we'll set it up at your convenience."""
}


# ── UI Layout ────────────────────────────────────────────────────────────

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/restaurant.png", width=60)
    st.markdown("### Settings")

    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-...",
        help="Enter your OpenAI API key. Get one at platform.openai.com",
        key="openai_key",
    )

    demo_mode = not bool(api_key)
    if demo_mode:
        st.info("**Demo Mode** — showing sample outputs. Add your API key for live generation.")

    st.markdown("---")

    restaurant_name = st.text_input(
        "Restaurant Name",
        value="The Golden Fork",
        help="Used in review responses and branding",
    )

    brand_tone = st.selectbox(
        "Brand Tone",
        ["Warm & Inviting", "Modern & Trendy", "Classic & Elegant", "Casual & Fun"],
        help="Influences the style of generated content",
    )

    st.markdown("---")
    st.markdown("""
    **Built by [QuantEmber](https://quantember.github.io/portfolio)**

    *AI-powered marketing for restaurants*
    """)


# Main content
st.markdown('<p class="main-header">🍽️ Restaurant AI Marketing Assistant</p>',
            unsafe_allow_html=True)
st.markdown('<p class="sub-header">Generate social media content, campaigns, '
            'and customer responses in seconds</p>', unsafe_allow_html=True)

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📸 Photo Content",
    "📝 Menu Item",
    "🎉 Event Campaign",
    "⭐ Review Responder",
    "💬 Message Templates",
])


# ── Tab 1: Photo Content ────────────────────────────────────────────────

with tab1:
    st.markdown("### Upload a food photo to generate marketing content")

    col1, col2 = st.columns([1, 1])

    with col1:
        uploaded_photo = st.file_uploader(
            "Upload food/drink/event photo",
            type=["jpg", "jpeg", "png", "webp"],
            help="Best results with well-lit, appetizing food photography",
        )

        photo_context = st.text_area(
            "Additional context (optional)",
            placeholder="e.g., 'New summer menu item, $16, available weekends only'",
            height=100,
        )

        if uploaded_photo:
            st.image(uploaded_photo, caption="Uploaded photo", use_container_width=True)

    with col2:
        generate_photo_btn = st.button("🚀 Generate Content", key="photo_btn",
                                       type="primary", use_container_width=True)

        if generate_photo_btn:
            if demo_mode:
                st.markdown(DEMO_CONTENT["photo"])
            else:
                client = get_client()
                if client:
                    with st.spinner("Analyzing photo and generating content..."):
                        if uploaded_photo:
                            img_b64 = encode_image(uploaded_photo)
                            result = generate_content_from_photo(
                                client, img_b64, photo_context)
                        else:
                            st.warning("Please upload a photo first.")
                            result = None
                        if result:
                            st.markdown(result)


# ── Tab 2: Menu Item ────────────────────────────────────────────────────

with tab2:
    st.markdown("### Generate marketing copy for a menu item")

    col1, col2 = st.columns([1, 1])

    with col1:
        item_name = st.text_input("Item Name", placeholder="e.g., Truffle Mushroom Risotto")
        item_price = st.text_input("Price (optional)", placeholder="e.g., $24")
        item_desc = st.text_area(
            "Description",
            placeholder="e.g., Arborio rice, wild mushroom medley, white truffle oil, "
                        "aged parmesan, fresh thyme. Vegetarian. Gluten-free.",
            height=120,
        )
        item_type = st.selectbox("Content type", ["New dish", "Daily special",
                                                    "Seasonal menu", "Drink/cocktail",
                                                    "Dessert", "Brunch item"])

    with col2:
        generate_item_btn = st.button("🚀 Generate Content", key="item_btn",
                                      type="primary", use_container_width=True)

        if generate_item_btn:
            if not item_name:
                st.warning("Please enter an item name.")
            elif demo_mode:
                st.markdown(DEMO_CONTENT["photo"])  # Reuse demo
            else:
                client = get_client()
                if client:
                    with st.spinner("Crafting your marketing content..."):
                        result = generate_content_from_text(
                            client, item_name, item_price, item_desc, item_type)
                        st.markdown(result)


# ── Tab 3: Event Campaign ───────────────────────────────────────────────

with tab3:
    st.markdown("### Create a promotional campaign for your event")

    col1, col2 = st.columns([1, 1])

    with col1:
        event_name = st.text_input("Event Name",
                                    placeholder="e.g., Live Jazz & Wine Night")
        event_date = st.date_input("Event Date")
        event_details = st.text_area(
            "Event Details",
            placeholder="e.g., Live jazz trio, curated wine flight ($35), "
                        "small plates menu, 7-10pm, reservations recommended",
            height=120,
        )
        event_offer = st.text_input("Special Offer (optional)",
                                     placeholder="e.g., 15% off wine bottles, "
                                                 "free appetizer with reservation")

    with col2:
        generate_event_btn = st.button("🚀 Generate Campaign", key="event_btn",
                                        type="primary", use_container_width=True)

        if generate_event_btn:
            if not event_name:
                st.warning("Please enter an event name.")
            elif demo_mode:
                st.info("**Demo mode** — add your OpenAI API key to generate live campaign content.")
                st.markdown("""### Sample Campaign: Live Jazz & Wine Night

**📸 Pre-Event Hype (1 week before)**
> The countdown is ON. Next Friday, the lights go low, the jazz goes live, and the wine flows free(ish). 🎷🍷 Reserve your table now — last month sold out.

**📘 Day-Of Post**
> TONIGHT! Live Jazz & Wine Night starts at 7pm. Walk-ins welcome but tables are filling fast. See you there! 📍 [Address]

**🎯 Post-Event Follow-Up**
> What a night! 🎶 Thank you to everyone who joined us. Missed it? Don't worry — we're doing it again [date]. Early bird reservations open now.

**👥 Targeting**: Jazz lovers, wine enthusiasts, date night planners, 25-55, 15-mile radius, Friday evening boost
""")
            else:
                client = get_client()
                if client:
                    with st.spinner("Building your campaign strategy..."):
                        result = generate_event_campaign(
                            client, event_name, str(event_date),
                            event_details, event_offer)
                        st.markdown(result)


# ── Tab 4: Review Responder ─────────────────────────────────────────────

with tab4:
    st.markdown("### Generate professional responses to Google reviews")

    col1, col2 = st.columns([1, 1])

    with col1:
        reviewer_name = st.text_input("Reviewer Name", placeholder="e.g., Sarah M.")
        review_stars = st.slider("Star Rating", 1, 5, 3)
        review_text = st.text_area(
            "Review Text",
            placeholder="Paste the customer's Google review here...",
            height=150,
        )

        # Quick presets
        st.markdown("**Quick test presets:**")
        preset_col1, preset_col2 = st.columns(2)
        with preset_col1:
            if st.button("⭐ Positive Review", key="preset_pos"):
                st.session_state["_preset"] = "positive"
        with preset_col2:
            if st.button("😤 Negative Review", key="preset_neg"):
                st.session_state["_preset"] = "negative"

    with col2:
        generate_review_btn = st.button("🚀 Generate Responses", key="review_btn",
                                         type="primary", use_container_width=True)

        # Handle presets
        preset = st.session_state.get("_preset", "")

        if preset == "positive" or (generate_review_btn and review_stars >= 4 and demo_mode):
            st.session_state.pop("_preset", None)
            st.markdown(DEMO_CONTENT["review_positive"])
        elif preset == "negative" or (generate_review_btn and review_stars < 4 and demo_mode):
            st.session_state.pop("_preset", None)
            st.markdown(DEMO_CONTENT["review_negative"])
        elif generate_review_btn and not demo_mode:
            if not review_text:
                st.warning("Please paste a review.")
            else:
                client = get_client()
                if client:
                    with st.spinner("Crafting responses..."):
                        result = generate_review_response(
                            client, review_text, reviewer_name,
                            review_stars, restaurant_name)
                        st.markdown(result)


# ── Tab 5: Message Templates ────────────────────────────────────────────

with tab5:
    st.markdown("### Generate reply templates for customer messages")

    col1, col2 = st.columns([1, 1])

    with col1:
        msg_type = st.selectbox("Message Type", [
            "Reservation inquiry",
            "Hours / location question",
            "Complaint or issue",
            "Catering request",
            "Private event inquiry",
            "Menu question (allergies/dietary)",
            "General compliment",
            "Other",
        ])

        customer_msg = st.text_area(
            "Customer Message",
            placeholder="Paste or type the customer's message...",
            height=150,
        )

    with col2:
        generate_msg_btn = st.button("🚀 Generate Replies", key="msg_btn",
                                      type="primary", use_container_width=True)

        if generate_msg_btn:
            if not customer_msg:
                st.warning("Please enter a customer message.")
            elif demo_mode:
                st.markdown("""### Response Options

**Option 1 — Brief & Friendly**
> Hi [Customer Name]! Thanks for reaching out 😊 We'd love to host your party! We accommodate groups of up to 40 in our private dining room. Could you share the date, headcount, and any dietary needs? I'll put together some options for you! — [Your Name], The Golden Fork

**Option 2 — Detailed & Professional**
> Dear [Customer Name],
>
> Thank you for considering The Golden Fork for your celebration! Our private dining room seats up to 40 guests and includes:
> - Customizable prix fixe menu ($45-65/person)
> - Dedicated server and bartender
> - A/V setup for toasts and slideshows
> - Complimentary cake cutting
>
> I'd love to schedule a quick call or walkthrough. What date works best for you?
>
> Warm regards,
> [Your Name], Events Coordinator
""")
            else:
                client = get_client()
                if client:
                    with st.spinner("Generating reply templates..."):
                        result = generate_message_reply(
                            client, customer_msg,
                            f"Message type: {msg_type}. Restaurant: {restaurant_name}")
                        st.markdown(result)


# ── Footer ───────────────────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    '<p style="text-align:center; color:#888; font-size:0.85rem;">'
    'Restaurant AI Marketing Assistant — Built by QuantEmber<br>'
    'Powered by OpenAI GPT-4o | Streamlit</p>',
    unsafe_allow_html=True
)
