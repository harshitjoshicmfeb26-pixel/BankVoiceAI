def get_translated_message(key: str, lang: str, **kwargs) -> str:
    lang = (lang or "en-in").lower().strip()
    
    translations = {
        "cancel_success": {
            "en-in": "Transfer cancelled successfully.",
            "hi-in": "स्थानांतरण सफलतापूर्वक रद्द कर दिया गया।",
            "mr-in": "हस्तांतरण यशस्वीरित्या रद्द केले गेले."
        },
        "transfer_success": {
            "en-in": "MPIN verified successfully. Sent ₹{amount:.2f} to {recipient_name} from your {source} account. Your new {source} balance is ₹{new_balance:.2f}.",
            "hi-in": "एमपीआईएन सफलतापूर्वक सत्यापित किया गया। आपके {source} खाते से {recipient_name} को ₹{amount:.2f} भेज दिए गए हैं। आपका नया {source} बैलेंस ₹{new_balance:.2f} है।",
            "mr-in": "एमपीायन यशस्वीरित्या सत्यापित केले गेले. आपल्या {source} खात्यातून {recipient_name} ला ₹{amount:.2f} पाठवले गेले आहेत. आपले नवीन {source} शिल्लक ₹{new_balance:.2f} आहे."
        },
        "transfer_failed": {
            "en-in": "Failed to execute transfer: {error}",
            "hi-in": "स्थानांतरण निष्पादित करने में विफल: {error}",
            "mr-in": "हस्तांतरण करण्यात अयशस्वी: {error}"
        },
        "too_many_attempts": {
            "en-in": "Too many incorrect MPIN attempts. The transfer has been cancelled, and you are being logged out for security.",
            "hi-in": "अमान्य एमपीआईएन के बहुत अधिक प्रयास। स्थानांतरण रद्द कर दिया गया है, और सुरक्षा के लिए आपको लॉग आउट किया जा रहा है।",
            "mr-in": "अनेक अमान्य एमपीआयएनचे प्रयत्न. हस्तांतरण रद्द केले गेले आहे, आणि सुरक्षेसाठी आपल्याला लॉग आउट केले जात आहे."
        },
        "incorrect_mpin": {
            "en-in": "Incorrect MPIN. You have {remaining_attempts} {attempt_word} remaining. Please try again, or say 'cancel' to abort the transfer.",
            "hi-in": "गलत एमपीआईएन। आपके पास {remaining_attempts} {attempt_word} शेष हैं। कृपया पुन: प्रयास करें, या रद्द करने के लिए 'cancel' कहें।",
            "mr-in": "चुकीचा एमपीआयएन. आपल्याकडे {remaining_attempts} {attempt_word} शिल्लक आहेत. कृपया पुन्हा प्रयत्न करा, किंवा रद्द करण्यासाठी 'cancel' म्हणा."
        },
        "pending_transfer_prompt": {
            "en-in": "You have a pending transfer of ₹{amount:.2f} to {recipient_name}. Please enter or state your 4-digit MPIN to confirm, or say 'cancel' to abort.",
            "hi-in": "आपका {recipient_name} को ₹{amount:.2f} का स्थानांतरण लंबित है। पुष्टि करने के लिए कृपया अपना 4-अंकीय एमपीआईएन दर्ज करें या बोलें, या रद्द करने के लिए 'cancel' कहें।",
            "mr-in": "आपले {recipient_name} ला ₹{amount:.2f} चे हस्तांतरण प्रलंबित आहे. पुष्टी करण्यासाठी कृपया आपला 4-अंकी एमपीआयएन टाका किंवा बोला, किंवा रद्द करण्यासाठी 'cancel' म्हणा."
        }
    }
    
    lang_key = lang if lang in ["hi-in", "mr-in"] else "en-in"
    msg_template = translations.get(key, {}).get(lang_key, translations.get(key, {}).get("en-in", ""))
    
    return msg_template.format(**kwargs)

def get_simulation_message(key: str, lang: str, **kwargs) -> str:
    lang = (lang or "en-in").lower().strip()
    
    sim_translations = {
        "no_other_users": {
            "en-in": "[Simulation Mode] No other users found in database to transfer money to.",
            "hi-in": "[सिमुलेशन मोड] पैसे ट्रांसफर करने के लिए डेटाबेस में कोई अन्य उपयोगकर्ता नहीं मिला।",
            "mr-in": "[सिम्युलेशन मोड] पैसे पाठवण्यासाठी डेटाबेसमध्ये इतर कोणताही वापरकर्ता आढळला नाही."
        },
        "transfer_pending": {
            "en-in": "[Simulation Mode] You requested a transfer of ₹{amount:.2f} to {recipient_name} from your {source} account. To confirm and execute this transfer, please state or enter your 4-digit MPIN.",
            "hi-in": "[सिमुलेशन मोड] आपने अपने {source} खाते से {recipient_name} को ₹{amount:.2f} ट्रांसफर करने का अनुरोध किया है। इस ट्रांसफर की पुष्टि करने और निष्पादित करने के लिए, कृपया अपना 4-अंकीय एमपीआईएन बोलें या दर्ज करें।",
            "mr-in": "[सिम्युलेशन मोड] आपण आपल्या {source} खात्यातून {recipient_name} ला ₹{amount:.2f} हस्तांतरित करण्याची विनंती केली आहे. या हस्तांतरणाची पुष्टी करण्यासाठी आणि अंमलात आणण्यासाठी, कृपया आपला 4-अंकी एमपीआयएन बोला किंवा टाका."
        },
        "no_txs": {
            "en-in": "[Simulation Mode] No transactions found in your history.",
            "hi-in": "[सिमुलेशन मोड] आपके इतिहास में कोई लेन-देन नहीं मिला।",
            "mr-in": "[सिम्युलेशन मोड] तुमच्या इतिहासामध्ये कोणतेही व्यवहार आढळले नाहीत."
        },
        "tx_header": {
            "en-in": "[Simulation Mode] Here are your last {count} transactions:\n\n| Date | Description | Category | Type | Amount |\n| :--- | :--- | :--- | :--- | :--- |\n",
            "hi-in": "[सिमुलेशन मोड] आपके पिछले {count} लेन-देन यहाँ हैं:\n\n| दिनांक | विवरण | श्रेणी | प्रकार | राशि |\n| :--- | :--- | :--- | :--- | :--- |\n",
            "mr-in": "[सिम्युलेशन मोड] तुमचे शेवटचे {count} व्यवहार येथे आहेत:\n\n| तारीख | तपशील | श्रेणी | प्रकार | रक्कम |\n| :--- | :--- | :--- | :--- | :--- |\n"
        },
        "fd_details": {
            "en-in": "[Simulation Mode] Your fixed deposit {id} has a tenure of {tenure} and matures on {maturity_date}.",
            "hi-in": "[सिमुलेशन मोड] आपकी सावधि जमा (FD) {id} की अवधि {tenure} है और यह {maturity_date} को परिपक्व होगी।",
            "mr-in": "[सिम्युलेशन मोड] तुमच्या मुदत ठेवीचा (FD) {id} कालावधी {tenure} आहे आणि ती {maturity_date} रोजी परिपक्व होईल."
        },
        "no_fds": {
            "en-in": "[Simulation Mode] You do not have any active Fixed Deposits in database. Configure GEMINI_API_KEY to create one.",
            "hi-in": "[सिमुलेशन मोड] डेटाबेस में आपका कोई सक्रिय सावधि जमा (FD) नहीं है। संवादात्मक नियंत्रण सक्षम करने के लिए GEMINI_API_KEY कॉन्फ़िगर करें।",
            "mr-in": "[सिम्युलेशन मोड] डेटाबेसमध्ये तुमची कोणतीही सक्रिय मुदत ठेव (FD) नाही. संभाषणात्मक आवाज नियंत्रणे सक्षम करण्यासाठी GEMINI_API_KEY कॉन्गर करा."
        },
        "default_welcome": {
            "en-in": "Welcome {name}! [Simulation Mode] Configure GEMINI_API_KEY to enable conversational voice controls.",
            "hi-in": "स्वागत है {name}! [सिमुलेशन मोड] संवादात्मक आवाज नियंत्रण सक्षम करने के लिए GEMINI_API_KEY कॉन्फ़िगर करें।",
            "mr-in": "स्वागत आहे {name}! [सिम्युलेशन मोड] संभाषणात्मक आवाज नियंत्रणे सक्षम करण्यासाठी GEMINI_API_KEY कॉन्गर करा."
        },
        "balance_details": {
            "en-in": "[Simulation Mode] Your account balances are:\n- Savings Account: ₹{savings_balance:.2f}\n- Checking Account: ₹{checking_balance:.2f}",
            "hi-in": "[सिमुलेशन मोड] आपके खाते की शेष राशि है:\n- बचत खाता: ₹{savings_balance:.2f}\n- चालू खाता: ₹{checking_balance:.2f}",
            "mr-in": "[सिम्युलेशन मोड] तुमच्या खात्यातील शिल्लक खालीलप्रमाणे आहे:\n- बचत खाते: ₹{savings_balance:.2f}\n- चालू खाते: ₹{checking_balance:.2f}"
        }
    }
    
    lang_key = lang if lang in ["hi-in", "mr-in"] else "en-in"
    msg_template = sim_translations.get(key, {}).get(lang_key, sim_translations.get(key, {}).get("en-in", ""))
    
    return msg_template.format(**kwargs)
