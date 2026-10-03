"""
rag_service.py - 100% Offline PostgreSQL Knowledge Base & Retrieval Service for NidhiVani AI.
Provides fast keyword, semantic tag, and full-text retrieval across English, Hindi, and Marathi.
Zero external downloads, zero third-party mirrors, and zero external API dependencies.
"""

import re
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from sqlalchemy import text
from models import BankKnowledgeChunk
from database import engine

# 18 Curated Multilingual Knowledge Chunks derived from data/knowledge_base/
KNOWLEDGE_CHUNKS = [
    # --- Interest Rates & Charges ---
    {
        "doc_id": "interest_rates_and_charges",
        "category": "rates",
        "title": "Savings Account Interest Rates",
        "content_en": "NidhiVani AI savings accounts earn 3.00% p.a. for balances up to ₹1 Lakh, 3.50% for ₹1 Lakh to ₹10 Lakhs, and 4.00% for balances above ₹10 Lakhs. Interest is calculated on daily closing balance and credited quarterly.",
        "content_hi": "निधिवानी एआई बचत खाते पर ₹1 लाख तक के बैलेंस पर 3.00% वार्षिक, ₹1 लाख से ₹10 लाख पर 3.50% और ₹10 लाख से अधिक पर 4.00% ब्याज मिलता है। ब्याज की गणना दैनिक आधार पर होती है और हर तिमाही खाते में जमा की जाती है।",
        "content_mr": "निधिवानी एआय बचत खात्यावर ₹1 लाखांपर्यंतच्या शिल्लकीवर 3.00% वार्षिक, ₹1 लाख ते ₹10 लाखांवर 3.50% आणि ₹10 लाखांपेक्षा जास्त रकमेवर 4.00% व्याज मिळते. व्याज तिमाही आधारावर खात्यात जमा केले जाते.",
        "keywords": "savings interest rate balance quarterly interest rates बचत बचत खाते ब्याज दर व्याज शिल्लक सेविंग्स"
    },
    {
        "doc_id": "interest_rates_and_charges",
        "category": "rates",
        "title": "Fixed Deposit (FD) Slabs & Senior Citizen Bonus",
        "content_en": "Our Fixed Deposit rates are: 1 Year yields 6.80% p.a., 3 Years yields 7.10% (our highest standard rate), and 5 Years Tax Saver yields 6.50%. Senior citizens (aged 60+) receive an additional 0.50% bonus across all slabs, giving 7.30% for 1 year.",
        "content_hi": "हमारी फिक्स्ड डिपॉजिट (FD) दरें: 1 साल के लिए 6.80%, 3 साल के लिए 7.10% (सर्वोच्च दर), और 5 साल के टैक्स सेवर पर 6.50% है। 60 वर्ष से अधिक के वरिष्ठ नागरिकों को सभी अवधियों पर 0.50% अतिरिक्त ब्याज मिलता है, जैसे 1 साल पर 7.30%।",
        "content_mr": "आमचे मुदत ठेव (FD) व्याजदर: 1 वर्षासाठी 6.80%, 3 वर्षांसाठी 7.10% (सर्वोच्च दर), आणि 5 वर्षांच्या टॅक्स सेव्हरवर 6.50% आहे. 60 वर्षांवरील ज्येष्ठ नागरिकांना सर्व कालावधींवर 0.50% अतिरिक्त व्याज मिळते, म्हणजेच 1 वर्षासाठी 7.30%.",
        "keywords": "fd fds fixed deposit rates rate interest interest rate senior citizen bonus tenure सावधि सावधि जमा मुदत मुदत ठेव एफडी फिक्स्ड डिपॉजिट डिपॉझिट ब्याज व्याज दर ब्याज दर वरिष्ठ नागरिक ज्येष्ठ नागरिक नवीन नई return returns"
    },
    {
        "doc_id": "interest_rates_and_charges",
        "category": "rates",
        "title": "Recurring Deposit (RD) Rates",
        "content_en": "Recurring Deposits start from ₹500 monthly for tenures from 6 months to 10 years. Interest rates match our Fixed Deposit rates for the same tenure, including the 0.50% senior citizen bonus.",
        "content_hi": "आवर्ती जमा (RD) ₹500 प्रति माह से शुरू होती है, जिसकी अवधि 6 महीने से 10 साल तक है। इस पर ब्याज दरें समान अवधि की FD दरों के बराबर हैं, साथ ही वरिष्ठ नागरिकों को 0.50% अतिरिक्त छूट मिलती है।",
        "content_mr": "आवर्ती ठेव (RD) दरमहा ₹500 पासून 6 महिने ते 10 वर्षांच्या कालावधीसाठी सुरू होते. यावर मुदत ठेवीप्रमाणेच (FD) व्याजदर लागू होतात, तसेच ज्येष्ठ नागरिकांना 0.50% अतिरिक्त लाभ मिळतो.",
        "keywords": "rd rds recurring deposit monthly tenure rate आवर्ती आवर्ती जमा रिकरिंग डिपॉझिट हप्ता आरडी व्याज ब्याज दर"
    },
    {
        "doc_id": "interest_rates_and_charges",
        "category": "rates",
        "title": "Retail Loan Interest Rates",
        "content_en": "Our loan interest rates: Home loans start at 8.40% p.a., Car loans are fixed at 8.75% p.a., Personal loans start from 10.50% (minimum CIBIL 720 required), and Gold loans start at 8.25% p.a.",
        "content_hi": "हमारे ऋण (लोन) की ब्याज दरें: होम लोन 8.40% से शुरू, कार लोन 8.75% फिक्स्ड, पर्सनल लोन 10.50% से (न्यूनतम सिबिल 720 आवश्यक), और गोल्ड लोन 8.25% से शुरू हैं।",
        "content_mr": "आमचे कर्ज (लोन) व्याजदर: गृहकर्ज (Home Loan) 8.40% पासून, कार लोन 8.75% फिक्स, वैयक्तिक कर्ज (Personal Loan) 10.50% पासून (किमान CIBIL 720 आवश्यक), आणि सुवर्ण कर्ज 8.25% पासून सुरू आहे.",
        "keywords": "loan home loan car loan personal loan gold loan interest rate emi cibil ऋण लोन कर्ज गृहकर्ज गाडी कर्ज पर्सनल लोन व्याज दर सिबिल"
    },
    {
        "doc_id": "interest_rates_and_charges",
        "category": "rates",
        "title": "Service Charges & Non-Maintenance Penalties",
        "content_en": "All digital transfers (NEFT, RTGS, IMPS) via voice and web are completely free (₹0). If your account drops below the minimum balance, non-maintenance penalty is ₹150 per quarter. Cheque return fee is ₹350.",
        "content_hi": "आवाज और वेब के जरिए सभी डिजिटल ट्रांसफर (NEFT, RTGS, IMPS) पूरी तरह निःशुल्क (₹0) हैं। न्यूनतम बैलेंस न रखने पर ₹150 प्रति तिमाही शुल्क लगता है। चेक बाउंस होने पर ₹350 पेनल्टी है।",
        "content_mr": "व्हॉइस आणि वेबद्वारे सर्व डिजिटल ट्रान्सफर (NEFT, RTGS, IMPS) पूर्णपणे मोफत (₹0) आहेत. खात्यात किमान शिल्लक न ठेवल्यास दर तिमाहीला ₹150 दंड आकारला जातो. धनादेश (Cheque) परत आल्यास ₹350 शुल्क आहे.",
        "keywords": "charges penalty fee minimum balance bounce neft rtgs imps charge शुल्क दंड पेनल्टी किमान शिल्लक किमान बॅलन्स फी"
    },

    # --- Banking Operations & Limits ---
    {
        "doc_id": "banking_operations_and_limits",
        "category": "limits",
        "title": "Fund Transfer Limits & Operating Timings",
        "content_en": "IMPS transfers run 24x7 up to ₹2,00,000 per transaction and ₹5,00,000 daily. NEFT is available 24x7 with batches every 30 minutes up to ₹10,00,000 daily. RTGS operates 24x7 for transactions starting at a minimum of ₹2,00,000.",
        "content_hi": "IMPS ट्रांसफर 24x7 उपलब्ध है, जिसकी सीमा ₹2,00,000 प्रति लेनदेन और ₹5,00,000 दैनिक है। NEFT 24x7 उपलब्ध है (दैनिक सीमा ₹10,00,000)। RTGS 24x7 उपलब्ध है और यह न्यूनतम ₹2,00,000 के लेनदेन के लिए है।",
        "content_mr": "IMPS ट्रान्सफर 24x7 सुरू असते, ज्याची मर्यादा प्रति व्यवहार ₹2,00,000 आणि दररोज ₹5,00,000 आहे. NEFT 24x7 उपलब्ध आहे (दैनिक मर्यादा ₹10,00,000). RTGS 24x7 उपलब्ध असून किमान ₹2,00,000 पासून सुरू होते.",
        "keywords": "limit transfer limit imps neft rtgs daily limit timings मर्यादा दैनिक मर्यादा पैसे पाठवणे ट्रान्सफर लिमिट आयएमपीएस एनईएफटी आरटीजीएस वेळ"
    },
    {
        "doc_id": "banking_operations_and_limits",
        "category": "limits",
        "title": "Voice Banking Transfer Security Cap",
        "content_en": "For customer security against acoustic eavesdropping and duress, voice-initiated transfers are strictly capped at ₹10,000 per transaction and ₹25,000 daily. All voice transfers require mandatory 4-digit MPIN validation.",
        "content_hi": "ग्राहक सुरक्षा और धोखाधड़ी से बचाव के लिए, आवाज द्वारा पैसे भेजने की अधिकतम सीमा ₹10,000 प्रति लेनदेन और ₹25,000 दैनिक तय की गई है। सभी वॉयस ट्रांसफर के लिए 4-अंकीय MPIN अनिवार्य है।",
        "content_mr": "ग्राहकांच्या सुरक्षिततेसाठी, आवाजाद्वारे (Voice) पैसे पाठवण्याची कमाल मर्यादा प्रति व्यवहार ₹10,000 आणि दररोज ₹25,000 निश्चित केली आहे. सर्व व्हॉइस ट्रान्सफरसाठी 4-अंकी MPIN अनिवार्य आहे.",
        "keywords": "voice transfer limit cap security mpin voice banking ₹10000 वॉयस व्हॉइस ट्रान्सफर मर्यादा बोलून पैसे वॉयस लिमिट वॉयस से पैसे सुरक्षितता सुरक्षा एमपीआयएन"
    },
    {
        "doc_id": "banking_operations_and_limits",
        "category": "limits",
        "title": "Minimum Average Balance (MAB) Requirements",
        "content_en": "Minimum Average Quarterly Balance requirements: ₹3,000 for Metro and Urban branches, ₹1,500 for Semi-Urban branches, and ₹1,000 for Rural branches. Basic (Jan Dhan / BSBDA) accounts have zero minimum balance requirements.",
        "content_hi": "न्यूनतम औसत तिमाही बैलेंस की आवश्यकता: मेट्रो और शहरी शाखाओं के लिए ₹3,000, अर्ध-शहरी के लिए ₹1,500, और ग्रामीण शाखाओं के लिए ₹1,000 है। जन धन और बुनियादी खातों में शून्य (Zero) बैलेंस की सुविधा है।",
        "content_mr": "किमान सरासरी तिमाही शिल्लक: मेट्रो आणि शहरी शाखांसाठी ₹3,000, निम-शहरी शाखांसाठी ₹1,500 आणि ग्रामीण शाखांसाठी ₹1,000 आहे. जन धन खात्यांसाठी शून्य (Zero) बॅलन्स सुविधा उपलब्ध आहे.",
        "keywords": "minimum balance mab aqb metro urban rural zero balance jan dhan न्यूनतम बैलेंस न्यूनतम शेष किमान शिल्लक किमान बॅलन्स जन धन"
    },
    {
        "doc_id": "banking_operations_and_limits",
        "category": "limits",
        "title": "Account Statements & Records",
        "content_en": "You can request account statements for the last 1, 3, or 6 months by voice or online. PDF statements are sent instantly to your registered email address free of charge.",
        "content_hi": "आप आवाज या ऑनलाइन पोर्टल के माध्यम से पिछले 1, 3 या 6 महीनों के बैंक स्टेटमेंट का अनुरोध कर सकते हैं। पीडीएफ स्टेटमेंट आपके पंजीकृत ईमेल पर तुरंत निःशुल्क भेजा जाता है।",
        "content_mr": "तुम्ही आवाजाद्वारे किंवा ऑनलाइन पोर्टलवरून मागील 1, 3 किंवा 6 महिन्यांचे बँक स्टेटमेंट मागवू शकता. पीडीएफ स्टेटमेंट तुमच्या नोंदणीकृत ईमेलवर त्वरित मोफत पाठवले जाते.",
        "keywords": "statement pdf statement email passbook transaction history स्टेटमेंट पासबुक ईमेल खात्याचा तपशील विवरण"
    },

    # --- KYC & Fraud Protection ---
    {
        "doc_id": "kyc_and_fraud_protection",
        "category": "compliance",
        "title": "KYC Verification & Re-KYC Documents",
        "content_en": "Officially Valid Documents (OVD) accepted for KYC and Re-KYC are: Passport, Driving Licence, Aadhaar Card (masked), Voter ID, and NREGA job card. PAN card or Form 60 is mandatory for transactions above ₹50,000.",
        "content_hi": "केवाईसी (KYC) और री-केवाईसी के लिए मान्य दस्तावेज हैं: पासपोर्ट, ड्राइविंग लाइसेंस, आधार कार्ड (मास्क्ड), वोटर आईडी, और नरेगा जॉब कार्ड। ₹50,000 से अधिक के लेनदेन के लिए पैन कार्ड या फॉर्म 60 अनिवार्य है।",
        "content_mr": "केवायसी (KYC) आणि री-केवायसीसाठी अधिकृत वैध कागदपत्रे: पासपोर्ट, ड्रायव्हिंग लायसन्स, आधार कार्ड, मतदान ओळखपत्र (Voter ID), आणि नरेगा जॉब कार्ड. ₹50,000 वरील व्यवहारांसाठी पॅन कार्ड आवश्यक आहे.",
        "keywords": "kyc re-kyc documents aadhaar pan passport voter id ovd केवायसी कागदपत्रे दस्तऐवज आधार पॅन पासपोर्ट ओळखपत्र"
    },
    {
        "doc_id": "kyc_and_fraud_protection",
        "category": "compliance",
        "title": "Cyber Fraud Reporting & 1930 Helpline",
        "content_en": "In case of any unauthorized transaction, report immediately to the National Cyber Crime Helpline at 1930 or visit cybercrime.gov.in. Under RBI rules, reporting unauthorized fraud within 72 hours (3 working days) grants zero customer liability.",
        "content_hi": "किसी भी अनधिकृत या धोखाधड़ी लेनदेन के मामले में, तुरंत राष्ट्रीय साइबर क्राइम हेल्पलाइन 1930 पर कॉल करें या cybercrime.gov.in पर जाएं। आरबीआई नियमों के अनुसार, 72 घंटों (3 कार्यदिवसों) के भीतर सूचना देने पर ग्राहक की देनदारी शून्य (Zero Liability) होती है।",
        "content_mr": "कोणत्याही अनधिकृत किंवा संशयास्पद व्यवहाराची तक्रार त्वरित राष्ट्रीय सायबर हेल्पलाइन 1930 वर किंवा cybercrime.gov.in वर नोंदवा. आरबीआय नियमांनुसार, 72 तासांच्या आत तक्रार केल्यास ग्राहकाचे कोणतेही नुकसान होत नाही (Zero Liability).",
        "keywords": "fraud cyber fraud scam unauthorized 1930 helpline liability zero liability सायबर गुन्हे फसवणूक तक्रार हेल्पलाइन 1930 अनधिकृत फसवणूक धोखाधड़ी देनदारी जीरो देनदारी शून्य देनदारी रिपोर्ट फ्रॉड फ्राड ट्रांजैक्शन"
    },
    {
        "doc_id": "kyc_and_fraud_protection",
        "category": "compliance",
        "title": "Physical Cards & Credential Safety",
        "content_en": "NidhiVani AI is a digital-first voice branch and does not issue physical plastic debit or credit cards. Bank officials will NEVER ask for your 4-digit MPIN, password, or OTP. Never share your MPIN with anyone.",
        "content_hi": "निधिवानी एआई एक आधुनिक डिजिटल शाखा है और यह कोई भौतिक प्लास्टिक डेबिट या क्रेडिट कार्ड जारी नहीं करती है। बैंक कर्मचारी आपसे कभी भी आपका 4-अंकीय MPIN या पासवर्ड नहीं पूछेंगे। अपना MPIN किसी के साथ साझा न करें।",
        "content_mr": "निधिवानी एआय ही डिजिटल-प्रथम शाखा असून ती कोणतेही प्लास्टिक डेबिट किंवा क्रेडिट कार्ड देत नाही. बँकेचे अधिकारी कधीही तुमचा 4-अंकी MPIN किंवा पासवर्ड विचारत नाहीत. तुमचा MPIN कोणालाही सांगू नका.",
        "keywords": "debit card credit card atm card plastic card mpin safety डेबिट कार्ड क्रेडिट कार्ड एटीएम कार्ड प्लास्टिक कार्ड पिन सुरक्षितता"
    },

    # --- Branches & Contacts (Granular Chunks) ---
    {
        "doc_id": "branches_and_contacts",
        "category": "branches",
        "title": "Pune IT Park Branch & Address",
        "content_en": "Pune Branch Address: Plot 18, Fergusson College Road (FC Road), Deccan Gymkhana, Shivajinagar, Pune, Maharashtra 411004. IFSC Code: NIDH0002001. MICR: 411892003. Services: Voice biometric kiosks, SME & Startup lending desk, NRI banking.",
        "content_hi": "पुणे शाखा पता: प्लॉट 18, फर्ग्यूसन कॉलेज रोड (FC Road), डेक्कन जिमखाना, शिवाजीनगर, पुणे, महाराष्ट्र 411004। IFSC कोड: NIDH0002001। सुविधाएं: वॉयस बायोमेट्रिक कियोस्क, एसएमई एवं स्टार्टअप डेस्क, एनआरआई बैंकिंग।",
        "content_mr": "पुणे शाखा पत्ता: प्लॉट 18, फर्ग्युसन कॉलेज रोड (FC Road), डेक्कन जिमखाना, शिवाजीनगर, पुणे, महाराष्ट्र 411004. IFSC कोड: NIDH0002001. सेवा: व्हॉइस बायोमेट्रिक किऑस्क, एसएमई आणि स्टार्टअप डेस्क, अनिवासी भारतीय (NRI) बँकिंग.",
        "keywords": "pune branch address ifsc fc road deccan gymkhana shivajinagar pune branch location pune pune शाखा पत्ता आयएफएससी एफसी रोड डेक्कन जिमखाना शिवाजीनगर पुणे शाखा पुण्याची शाखा पुण्यात"
    },
    {
        "doc_id": "branches_and_contacts",
        "category": "branches",
        "title": "Mumbai Flagship Branch & Address",
        "content_en": "Mumbai Flagship Branch Address: Suite 402, Maker Chambers V, Nariman Point, Mumbai, Maharashtra 400021. IFSC Code: NIDH0001001. MICR: 400892002. Services: Full branch services, Safe Deposit Lockers, High Net Worth Wealth Desk, 24x7 Cash Recyclers.",
        "content_hi": "मुंबई मुख्य शाखा पता: सूट 402, मेकर चेंबर्स V, नरीमन पॉइंट, मुंबई, महाराष्ट्र 400021। IFSC कोड: NIDH0001001। सुविधाएं: लॉकर सुविधा, वेल्थ डेस्क, 24x7 कैश रीसाइक्लर।",
        "content_mr": "मुंबई मुख्य शाखा पत्ता: सूट 402, मेकर चेंबर्स V, नरिमन पॉईंट, मुंबई, महाराष्ट्र 400021. IFSC कोड: NIDH0001001. सेवा: सेफ डिपॉझिट लॉकर्स, वेल्थ डेस्क, 24x7 कॅश रिसायकलर्स.",
        "keywords": "mumbai branch address ifsc nariman point maker chambers mumbai location mumbai mumbai शाखा पत्ता आयएफएससी नरिमन पॉईंट मुंबई शाखा मुंबईची शाखा मुंबईत"
    },
    {
        "doc_id": "branches_and_contacts",
        "category": "branches",
        "title": "New Delhi Central Branch & Address",
        "content_en": "New Delhi Central Branch Address: Inner Circle, Block L, Connaught Place, New Delhi, Delhi 110001. IFSC Code: NIDH0003001. MICR: 110892004. Services: Senior citizen priority counter, Government treasury bonds, FOREX exchange.",
        "content_hi": "नई दिल्ली शाखा पता: इनर सर्कल, ब्लॉक एल, कनॉट प्लेस, नई दिल्ली, दिल्ली 110001। IFSC कोड: NIDH0003001। सुविधाएं: वरिष्ठ नागरिक प्राथमिकता काउंटर, सरकारी ट्रेजरी बांड, फॉरेक्स।",
        "content_mr": "नवी दिल्ली मध्यवर्ती शाखा पत्ता: इनर सर्कल, ब्लॉक एल, कॅनॉट प्लेस, नवी दिल्ली 110001. IFSC कोड: NIDH0003001. सेवा: ज्येष्ठ नागरिक विशेष काउंटर, सरकारी ट्रेझरी बाँड्स, फॉरेक्स.",
        "keywords": "delhi new delhi branch address ifsc connaught place inner circle delhi location delhi delhi नई दिल्ली नवी दिल्ली शाखा पत्ता आयएफएससी कनॉट प्लेस दिल्ली शाखा"
    },
    {
        "doc_id": "branches_and_contacts",
        "category": "branches",
        "title": "All Physical Branch Directory & Locations",
        "content_en": "NidhiVani AI operates 3 physical branches: 1) Mumbai (Nariman Point, IFSC: NIDH0001001), 2) Pune (FC Road, Deccan Gymkhana, IFSC: NIDH0002001), and 3) New Delhi (Connaught Place, IFSC: NIDH0003001). Digital voice banking is available 24x7 nationwide.",
        "content_hi": "निधिवानी एआई की 3 प्रमुख भौतिक शाखाएं हैं: 1) मुंबई (नरीमन पॉइंट, IFSC: NIDH0001001), 2) पुणे (एफसी रोड, IFSC: NIDH0002001), और 3) नई दिल्ली (कनॉट प्लेस, IFSC: NIDH0003001)। डिजिटल वॉयस बैंकिंग पूरे देश में 24x7 उपलब्ध है।",
        "content_mr": "निधिवानी एआईच्या ३ प्रमुख भौतिक शाखा आहेत: १) मुंबई (नरिमन पॉईंट, IFSC: NIDH0001001), २) पुणे (एफसी रोड, IFSC: NIDH0002001), आणि ३) नवी दिल्ली (कॅनॉट प्लेस, IFSC: NIDH0003001). डिजिटल व्हॉइस बँकिंग संपूर्ण देशभरात 24x7 उपलब्ध आहे.",
        "keywords": "branches all branches directory how many branches total branches branch list सर्व शाखा सर्व शाखांचा पत्ता किती शाखा शाखांची यादी एकूण शाखा सभी शाखाएं कितनी शाखाएं"
    },
    {
        "doc_id": "branches_and_contacts",
        "category": "branches",
        "title": "Working Hours & Saturday Holiday Schedule",
        "content_en": "Branch operational hours are Monday to Friday: 10:00 AM to 4:00 PM. Branches are open on the 1st, 3rd, and 5th Saturdays (10:00 AM to 2:00 PM), and closed on the 2nd and 4th Saturdays and Sundays. Digital voice banking operates 24x7.",
        "content_hi": "शाखा का समय सोमवार से शुक्रवार सुबह 10:00 बजे से शाम 4:00 बजे तक है। पहले, तीसरे और पांचवें शनिवार को शाखा खुली रहती है (सुबह 10 से दोपहर 2 बजे)। दूसरे और चौथे शनिवार तथा रविवार को अवकाश रहता है।",
        "content_mr": "शाखेची वेळ सोमवार ते शुक्रवार सकाळी 10:00 ते दुपारी 4:00 आहे. पहिल्या, तिसऱ्या आणि पाचव्या शनिवारी शाखा सुरू असते (सकाळी 10 ते 2). दुसऱ्या व चौथ्या शनिवारी आणि रविवारी सुट्टी असते. डिजिटल बँकिंग 24x7 सुरू असते.",
        "keywords": "timings working hours open close saturday holiday sunday वेळ वेळा कामाची वेळ कामकाज कामकाजाची वेळ बँक शाखा समय शनिवार सुट्टी उघडण्याची वेळ बंद वेळ"
    },
    {
        "doc_id": "branches_and_contacts",
        "category": "branches",
        "title": "Customer Support Toll-Free & Contacts",
        "content_en": "You can reach NidhiVani AI customer care 24x7 on our toll-free number 1800-123-NIDHI (1800-123-64344) or via email at support@nidhivani.in. For unresolved grievances, contact our Principal Nodal Officer at grievance@nidhivani.in.",
        "content_hi": "आप निधिवानी एआई कस्टमर केयर से हमारे टोल-फ्री नंबर 1800-123-NIDHI (1800-123-64344) पर 24x7 संपर्क कर सकते हैं, या support@nidhivani.in पर ईमेल कर सकते हैं।",
        "content_mr": "तुम्ही निधिवानी एआय ग्राहक सेवेशी आमच्या टोल-फ्री क्रमांक 1800-123-NIDHI (1800-123-64344) वर 24x7 संपर्क करू शकता किंवा support@nidhivani.in वर ईमेल करू शकता.",
        "keywords": "customer care toll free phone number helpline contact email grievance ग्राहक सेवा टोल फ्री फोन नंबर संपर्क ईमेल तक्रार"
    }
]

def detect_query_language(query: str, requested_lang: str = "en-in") -> str:
    """
    Intelligently detects whether the query is in Marathi, Hindi, or English.
    If the user types/speaks in Devanagari script, analyzes distinctive lexical markers
    to differentiate Marathi from Hindi. If no Devanagari is found, honors requested_lang.
    """
    if not query:
        return (requested_lang or "en-in").lower().strip()
    
    query_str = query.strip()
    
    # Check if text contains Devanagari Unicode characters (U+0900 to U+097F)
    if re.search(r"[\u0900-\u097F]", query_str):
        # Distinctive Marathi lexical markers and inflections
        marathi_markers = [
            "आहे", "आहेत", "नाही", "नाहीत", "काय", "कसे", "कुठे", "कधी", "किती", 
            "सांगा", "पत्ता", "शाखा", "शाखेचा", "शाखेची", "शाखेचे", "वेळ", "वेळा", 
            "शिल्लक", "बँकेचा", "बँकेची", "बँकेचे", "खाते", "खात्याचा", "खात्यातील", 
            "पाहिजे", "करा", "करावे", "करावी", "मिळेल", "होईल", "हवे", "माझा", "माझी", 
            "माझे", "तुमचा", "तुमची", "तुमचे", "च्या", "ची", "चे", "वरून", "कडून", 
            "मध्ये", "मुदत", "ठेव", "कर्ज", "गृहकर्ज", "पुण्यात", "पुण्याची", "मुंबईत"
        ]
        
        # Distinctive Hindi lexical markers and inflections
        hindi_markers = [
            "है", "हैं", "हूँ", "था", "थी", "थे", "क्या", "कहाँ", "कहा", "कैसे", 
            "कितना", "कितने", "बताओ", "बताइए", "पता", "समय", "बैलेंस", "खाता", 
            "खाते", "चाहिए", "मिलेगा", "होगा", "सकता", "सकते", "सकती", "मेरा", 
            "मेरी", "मेरे", "आपका", "आपकी", "आपके", "के", "की", "का", "में", 
            "पर", "से", "जमा"
        ]
        
        mr_matches = sum(1 for m in marathi_markers if m in query_str)
        hi_matches = sum(1 for m in hindi_markers if m in query_str)
        
        if mr_matches > hi_matches:
            return "mr-in"
        elif hi_matches > mr_matches:
            return "hi-in"
        elif mr_matches > 0:
            return "mr-in"
        elif "mr" in (requested_lang or "").lower():
            return "mr-in"
        elif "hi" in (requested_lang or "").lower():
            return "hi-in"
        else:
            return "mr-in" if any(w in query_str for w in ["शाखा", "पत्ता", "शिल्लक", "वेळ"]) else "hi-in"

    # 2. Check for Romanized Hindi (Hinglish) and Romanized Marathi (Marathlish)
    # when input is written in Latin/English characters
    words = set(re.findall(r"\b[a-zA-Z]+\b", query_str.lower()))
    
    # Distinctive Romanized Hindi (Hinglish) markers (avoiding ambiguous English words)
    hinglish_markers = {
        "kya", "kyu", "kyun", "kaise", "kaisa", "kaisi", "kitna", "kitne", "kitni",
        "kab", "kaha", "kahan", "hain", "hote", "hoti", "hota", "hoga", "hogi", "hoge",
        "chahiye", "batao", "bataiye", "bhejo", "bhejna", "paisa", "paise", "rupaye",
        "mujhe", "mera", "meri", "mere", "aapka", "aapki", "aapke", "tumhara", "humara",
        "nahi", "nahin", "liye", "milta", "milti", "milte", "milega", "milegi",
        "khata", "khate", "byaj", "biyaj", "dena", "lena", "jama", "nayi", "naya", "naye",
        "walon", "wali", "wale", "karna", "kare", "karo", "karta", "karti", "hai"
    }
    
    # Distinctive Romanized Marathi (Marathlish) markers
    marathlish_markers = {
        "kay", "kiti", "kuthe", "kadhi", "kasa", "kashi", "kase",
        "ahe", "aahe", "ahet", "aahet", "nahit", "mahit", "mahiti",
        "karaycha", "karayche", "karaychi", "pathva", "pathvayche", "pathvaycha",
        "shillak", "sang", "sanga", "mala", "majha", "majhi", "majhe", "maza", "mazi", "maze",
        "tumcha", "tumchi", "tumche", "aamcha", "aamchi", "aamche", "chya",
        "madhye", "varun", "kadun", "bhetel", "pahije", "havi", "hava", "have", "shakha",
        "vel", "vela", "sakali", "sandhyakali"
    }
    
    hi_matches = len(words.intersection(hinglish_markers))
    mr_matches = len(words.intersection(marathlish_markers))
    
    if mr_matches > hi_matches and mr_matches >= 1:
        return "mr-in"
    elif hi_matches > mr_matches and hi_matches >= 1:
        return "hi-in"
    elif mr_matches >= 1:
        return "mr-in"

    return (requested_lang or "en-in").lower().strip()

def init_knowledge_base(force: bool = False):
    """Ensure the bank_knowledge_chunk table is created and seeded with the 18 authoritative multilingual chunks."""
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        existing = session.exec(select(BankKnowledgeChunk)).first()
        count = len(session.exec(select(BankKnowledgeChunk)).all())
        # Re-seed if forced or if chunk count has changed
        if not existing or count != len(KNOWLEDGE_CHUNKS) or force:
            for c in session.exec(select(BankKnowledgeChunk)).all():
                session.delete(c)
            session.commit()
            print(f"[RAG] Seeding {len(KNOWLEDGE_CHUNKS)} authoritative multilingual policy chunks into PostgreSQL...")
            for chunk_data in KNOWLEDGE_CHUNKS:
                chunk = BankKnowledgeChunk(
                    doc_id=chunk_data["doc_id"],
                    category=chunk_data["category"],
                    title=chunk_data["title"],
                    content_en=chunk_data["content_en"],
                    content_hi=chunk_data["content_hi"],
                    content_mr=chunk_data["content_mr"],
                    keywords=chunk_data["keywords"]
                )
                session.add(chunk)
            session.commit()
            print(f"[RAG] Seeded {len(KNOWLEDGE_CHUNKS)} chunks into bank_knowledge_chunk successfully.")

def search_knowledge_base(query: str, language: str = "en-in") -> Dict[str, Any]:
    """
    100% Offline Retrieval Tool for NidhiVani AI.
    Searches PostgreSQL bank_knowledge_chunk table using multilingual token matching and relevance scoring.
    Automatically detects user's input language (Devanagari Marathi/Hindi) and returns the native response.
    """
    if not query or not query.strip():
        return {
            "found": False,
            "answer": "Please ask a question about interest rates, loans, branch timings, KYC, or banking policies.",
            "title": None,
            "category": None
        }

    # Auto-detect language from query text if input is in Devanagari script
    detected_lang = detect_query_language(query, language)
    lang_clean = detected_lang.lower().strip()
    
    # Clean query into tokens (handling alphanumeric + Devanagari range \u0900-\u097F)
    cleaned_query = re.sub(r"[^\w\s\u0900-\u097F]", " ", query.lower())

    # --- GUARDRAIL 1: Prompt Injection / System Override / Exploit Detection ---
    injection_patterns = [
        "ignore all rules", "secret keys", "system prompt", "drop table", 
        "admin password", "passwords", "database secret"
    ]
    if any(inj in cleaned_query for inj in injection_patterns):
        return {
            "found": False,
            "answer": "Security Alert: Unauthorized command detected. I am a secure banking assistant and cannot process system override or credential requests.",
            "title": "Security Guardrail",
            "category": "security_guardrail",
            "score": 0
        }

    # --- GUARDRAIL 2: Privacy Boundary (User Balance & Personal Account Inquiries) ---
    balance_patterns = [
        r"\b(alice|bob|charlie|david|emma|user|my|whose|\w+)\s+(s\s+)?balance\b",
        r"\bcheck\s+balance\b", r"\baccount\s+balance\b",
        r"मेरा बैलेंस", r"माझी शिल्लक", r"खाते का बैलेंस", r"खात्यातील शिल्लक"
    ]
    is_policy_balance_query = any(w in cleaned_query for w in ["minimum", "mab", "aqb", "rate", "interest", "slab", "न्यूनतम", "किमान", "ब्याज", "व्याज", "दर"])
    if not is_policy_balance_query and any(re.search(pat, cleaned_query) for pat in balance_patterns):
        return {
            "found": False,
            "answer": "For security and privacy, individual account balances cannot be retrieved through general support. Please ask our Account Specialist by saying 'Check my balance'.",
            "title": "Account Privacy Boundary",
            "category": "privacy_guardrail",
            "score": 0
        }

    tokens = [t.strip() for t in cleaned_query.split() if len(t.strip()) >= 2]
    
    # Common stop words to ignore in scoring
    stop_words = {
        "what", "is", "your", "the", "are", "tell", "me", "about", "how", "much", "many", "can", "you", "i", "do",
        "in", "on", "at", "to", "for", "from", "today", "now", "it", "this", "that", "there", "here", "a", "an",
        "and", "or", "of", "with", "by", "as", "be", "was", "were", "please", "give", "right", "want", "know", "new",
        "क्या", "है", "आपका", "मुझे", "बताओ", "की", "का", "के", "में", "पर", "होता", "होती", "होते", "से", "तो",
        "काय", "आहे", "तुमचे", "मला", "सांगा", "चे", "ची", "च्या", "मध्ये", "वर", "आहेत", "होते", "ना",
        "kya", "hai", "hain", "ho", "ka", "ki", "ke", "ko", "se", "mein", "main", "par", "batao", "bataiye",
        "wali", "waali", "wala", "wale",
        "kay", "ahe", "aahe", "ahet", "cha", "chi", "che", "chya", "la", "sang", "sanga"
    }
    meaningful_tokens = [t for t in tokens if t not in stop_words]
    if not meaningful_tokens:
        meaningful_tokens = tokens

    # Map Romanized Hindi/Marathi terms to Devanagari equivalents for cross-script retrieval
    ROMAN_PHONETIC_BANKING_MAP = {
        "bachat": "बचत", "byaj": "ब्याज", "vyaj": "व्याज", "biyaj": "ब्याज", "dar": "दर",
        "khata": "खाता", "khate": "खाते", "khatyavar": "खात्यावर", "khatyat": "खात्यात",
        "thev": "ठेव", "mudat": "मुदत", "savdhi": "सावधि", "karz": "कर्ज", "rin": "ऋण",
        "shakha": "शाखा", "shakhecha": "शाखेचा", "shakhechi": "शाखेची", "pata": "पता", "patta": "पत्ता",
        "shillak": "शिल्लक", "rok": "रोकड", "jama": "जमा", "nikasi": "निकासी", "shulka": "शुल्क",
        "dand": "दंड", "sahayata": "सहायता", "madat": "मदत", "suraksha": "सुरक्षा",
        "bhetel": "मिळेल", "milega": "मिलेगा", "milta": "मिलता", "milte": "मिळते",
        "kagadpatra": "कागदपत्रे", "dakhla": "दाखला", "karyalay": "कार्यालय", "vel": "वेळ"
    }
    expanded_tokens = list(meaningful_tokens)
    for t in meaningful_tokens:
        if t in ROMAN_PHONETIC_BANKING_MAP:
            expanded_tokens.append(ROMAN_PHONETIC_BANKING_MAP[t])
    meaningful_tokens = expanded_tokens

    # Intent analysis for disambiguating compound queries (e.g., branch mentions vs. product rates)
    has_policy_intent = any(w in cleaned_query.split() for w in [
        "fd", "fds", "fixed", "interest", "rate", "rates", "loan", "loans", "savings", "saving", 
        "rd", "charges", "penalty", "mab", "aqb", "kyc", "fraud", "ब्याज", "व्याज", "दर", "ऋण", 
        "कर्ज", "मुदत", "सावधि", "बचत", "शिल्लक", "बैलेंस"
    ])
    has_location_intent = any(w in cleaned_query.split() for w in [
        "address", "location", "pata", "patta", "ifsc", "timing", "timings", "hours", "open", "close",
        "कहाँ", "कुठे", "पत्ता", "पता", "आयएफएससी", "वेळ", "समय"
    ])

    # Specific product anchors
    is_fd_query = any(w in cleaned_query.split() for w in ["fd", "fds", "fixed", "मुदत", "सावधि", "एफडी"])
    is_savings_query = any(w in cleaned_query.split() for w in ["savings", "saving", "बचत", "सेविंग्स"])
    is_loan_query = any(w in cleaned_query.split() for w in ["loan", "loans", "emi", "कर्ज", "ऋण", "लोन", "गृहकर्ज"])
    is_rd_query = any(w in cleaned_query.split() for w in ["rd", "rds", "recurring", "आवर्ती", "आरडी"])

    with Session(engine) as session:
        all_chunks = session.exec(select(BankKnowledgeChunk)).all()
        if not all_chunks or len(all_chunks) != len(KNOWLEDGE_CHUNKS):
            init_knowledge_base(force=True)
            all_chunks = session.exec(select(BankKnowledgeChunk)).all()

        best_chunk = None
        highest_score = 0

        for chunk in all_chunks:
            kw_set = set(re.findall(r"[\w\u0900-\u097F]+", chunk.keywords.lower()))
            title_set = set(re.findall(r"[\w\u0900-\u097F]+", chunk.title.lower()))
            content_set = set(re.findall(r"[\w\u0900-\u097F]+", f"{chunk.content_en} {chunk.content_hi} {chunk.content_mr}".lower()))
            
            score = 0
            for token in meaningful_tokens:
                if token in kw_set:
                    score += 4  # Direct keyword hit
                elif token in title_set:
                    score += 3  # Direct title hit
                elif token in content_set:
                    score += 1  # Content hit
                else:
                    # Root / prefix stem match (e.g. inflections like "बँकेची" -> "बँक" or "कामकाजाची" -> "कामकाज")
                    for kw in kw_set:
                        if len(token) >= 3 and len(kw) >= 3:
                            if token.startswith(kw) or kw.startswith(token):
                                score += 3
                                break

            # Boost exact multi-word key phrases and specific branch city names
            for phrase in [
                "senior citizen", "वरिष्ठ नागरिक", "ज्येष्ठ नागरिक", "fixed deposit", "मुदत ठेव", 
                "सावधि जमा", "1930", "toll free", "टोल फ्री", "ifsc", "ifsc code", "आयएफएससी", "working hours", 
                "कामाची वेळ", "कामकाज", "voice transfer", "वॉयस ट्रांसफर", "व्हॉइस ट्रान्सफर", "वॉयस से पैसे",
                "धोखाधड़ी", "cyber fraud", "साइबर", "देनदारी", "zero liability", "जीरो देनदारी",
                "interest rate", "interest rates", "ब्याज दर", "व्याज दर", "branch address", "शाखा पत्ता",
                "pune", "पुणे", "mumbai", "मुंबई", "delhi", "दिल्ली", "शाखा", "शाखेचा", "शाखेची", "पत्ता", "पता"
            ]:
                if phrase in cleaned_query and phrase in f"{chunk.keywords} {chunk.title} {chunk.content_en} {chunk.content_hi} {chunk.content_mr}".lower():
                    score += 6

            # Specific product anchor boosts
            if is_fd_query and chunk.title.startswith("Fixed Deposit"):
                score += 8
            elif is_savings_query and chunk.title.startswith("Savings"):
                score += 8
            elif is_loan_query and chunk.title.startswith("Retail Loan"):
                score += 8
            elif is_rd_query and chunk.title.startswith("Recurring Deposit"):
                score += 8

            # Intent hierarchy: rates/policies priority over branch locators when no location intent is present
            if has_policy_intent and not has_location_intent:
                if chunk.category in ["rates", "limits", "compliance"] and any(t in kw_set for t in meaningful_tokens):
                    score += 4

            if score > highest_score:
                highest_score = score
                best_chunk = chunk

        # Confidence threshold: score must be at least 4 (requires at least 1 keyword match or title+content hit)
        if best_chunk and highest_score >= 4:
            if "hi" in lang_clean:
                content = best_chunk.content_hi
            elif "mr" in lang_clean:
                content = best_chunk.content_mr
            else:
                content = best_chunk.content_en

            return {
                "found": True,
                "answer": content,
                "title": best_chunk.title,
                "category": best_chunk.category,
                "score": highest_score,
                "detected_language": lang_clean
            }
        else:
            if "hi" in lang_clean:
                fallback = "मुझे इस विषय पर बैंक की आधिकारिक नीति की सटीक जानकारी नहीं मिली। कृपया हमारे टोल-फ्री नंबर 1800-123-64344 पर संपर्क करें या नजदीकी शाखा में जाएं।"
            elif "mr" in lang_clean:
                fallback = "मला या विषयावर बँकेच्या अधिकृत धोरणाची अचूक माहिती मिळाली नाही. कृपया आमच्या 1800-123-64344 या टोल-फ्री क्रमांकावर संपर्क साधा किंवा जवळच्या शाखेला भेट द्या."
            else:
                fallback = "I could not find an official bank policy record matching your inquiry. Please call our 24x7 customer care at 1800-123-NIDHI or visit your nearest branch."

            return {
                "found": False,
                "answer": fallback,
                "title": None,
                "category": None,
                "score": highest_score,
                "detected_language": lang_clean
            }
