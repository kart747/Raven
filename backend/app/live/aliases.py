"""
How headlines name parties, MPs and states, in English and Indian languages.

Each phrase maps to a Raven party id, an MP's exact name in the Lok Sabha record, or a canonical state; the
tagger only uses an alias when that party, MP or state exists. `None` means "recognise this phrase but tag
nothing", for names that contain another party's name (e.g. Nationalist Congress Party contains "Congress").

A phrase ending in `*` is a stem: it may be followed by a case ending in the same word (भाजपने, பாஜகவின்,
കോൺഗ്രസിന്റെ), as Marathi, Gujarati, Bengali and the Dravidian languages attach them. Stems are written without a
final virama so the inflected forms match, and are at least four characters long. Short words that are also
ordinary words are listed without `*` (असम, "Assam", would otherwise match असमान, "unequal").
"""

PARTY_ALIASES = {
    # English
    "bjp": "BJP", "bharatiya janata party": "BJP",
    "congress": "INC", "indian national congress": "INC",
    "aap": "AAP", "aam aadmi party": "AAP",
    "tmc": "AITC", "trinamool": "AITC", "trinamool congress": "AITC",
    "samajwadi party": "SP", "akhilesh yadav's sp": "SP",
    "dmk": "DMK", "aiadmk": "AIADMK", "mdmk": "MDMK", "dmdk": "DMDK", "vck": "VCK",
    "tdp": "TDP", "telugu desam": "TDP",
    "jdu": "JDU", "jd u": "JDU", "janata dal united": "JDU",
    "jd s": "JDS", "janata dal secular": "JDS",
    "rjd": "RJD", "rashtriya janata dal": "RJD",
    "bjd": "BJD", "biju janata dal": "BJD",
    "ysrcp": "YSRCP", "ysr congress": "YSRCP",
    "brs": "BRS", "bharat rashtra samithi": "BRS",
    "bsp": "BSP", "bahujan samaj party": "BSP",
    "jmm": "JMM", "jharkhand mukti morcha": "JMM",
    "aimim": "AIMIM", "shiromani akali dal": "SAD", "akali dal": "SAD",
    "shiv sena ubt": "SS(UBT)", "sena ubt": "SS(UBT)",
    "ncp sp": "NCP(SP)", "ncp sharadchandra pawar": "NCP(SP)",
    "nationalist congress party sharadchandra pawar": "NCP(SP)",
    "nationalist congress party": None, "nationalist congress": None,   # two parties since the 2023 split
    "kerala congress": "KC", "tamil maanila congress": None,
    "cpi m": "CPI(M)", "cpm": "CPI(M)",
    "iuml": "IUML", "indian union muslim league": "IUML",
    "jana sena": "JSP", "janasena": "JSP",
    "inld": "INLD",

    # Hindi and Marathi (Devanagari)
    "भाजप*": "BJP", "बीजेपी*": "BJP", "भारतीय जनता पार्टी*": "BJP", "भारतीय जनता पक्ष*": "BJP",
    "कांग्रेस*": "INC",                                   # also काँग्रेस (chandrabindu is folded)
    "तृणमूल*": "AITC", "तृणमूल कांग्रेस*": "AITC", "टीएमसी*": "AITC",
    "वाईएसआर कांग्रेस*": "YSRCP", "वाईएसआरसीपी": "YSRCP",
    "राष्ट्रवादी कांग्रेस*": None, "केरल कांग्रेस*": "KC",
    "आम आदमी पार्टी*": "AAP",
    "सपा": "SP", "समाजवादी पार्टी*": "SP",
    "बसपा": "BSP", "बहुजन समाज पार्टी*": "BSP",
    "राजद": "RJD", "राष्ट्रीय जनता दल": "RJD",
    "जदयू": "JDU", "जेडीयू": "JDU",
    "द्रमुक": "DMK", "अन्नाद्रमुक": "AIADMK",
    "तेदेपा": "TDP", "टीडीपी": "TDP",
    "माकपा": "CPI(M)", "झामुमो": "JMM", "बीजद": "BJD", "बीजेडी": "BJD", "बीआरएस": "BRS",
    "अकाली दल": "SAD", "शिरोमणि अकाली दल": "SAD", "एआईएमआईएम": "AIMIM",
    "शिवसेना यूबीटी": "SS(UBT)",

    # Gujarati
    "ભાજપ*": "BJP", "કોંગ્રેસ*": "INC", "આમ આદમી પાર્ટી*": "AAP",
    # Punjabi (Gurmukhi)
    "ਭਾਜਪਾ*": "BJP", "ਕਾਂਗਰਸ*": "INC", "ਆਮ ਆਦਮੀ ਪਾਰਟੀ*": "AAP", "ਅਕਾਲੀ ਦਲ*": "SAD", "ਸ਼੍ਰੋਮਣੀ ਅਕਾਲੀ ਦਲ*": "SAD",
    # Bengali
    "বিজেপি*": "BJP", "কংগ্রেস*": "INC", "তৃণমূল*": "AITC", "তৃণমূল কংগ্রেস*": "AITC", "সিপিএম*": "CPI(M)",
    # Tamil
    "பாஜக*": "BJP", "பா ஜ க": "BJP", "காங்கிரஸ*": "INC",
    "திமுக*": "DMK", "தி மு க": "DMK", "அதிமுக*": "AIADMK", "அ தி மு க": "AIADMK",
    "மதிமுக*": "MDMK", "தேமுதிக*": "DMDK", "விசிக*": "VCK",
    # Telugu
    "బీజేపీ*": "BJP", "భాజపా*": "BJP", "కాంగ్రెస*": "INC", "టీడీపీ*": "TDP", "తెలుగుదేశ*": "TDP",
    "వైఎస్సార్సీపీ*": "YSRCP", "వైసీపీ*": "YSRCP", "బీఆర్ఎస*": "BRS", "జనసేన*": "JSP",
    # Kannada
    "ಬಿಜೆಪಿ*": "BJP", "ಕಾಂಗ್ರೆಸ*": "INC", "ಜೆಡಿಎಸ*": "JDS",
    # Malayalam
    "ബിജെപി*": "BJP", "കോൺഗ്രസ*": "INC", "കേരള കോൺഗ്രസ*": "KC",
    "സിപിഎം*": "CPI(M)", "സിപിഐഎം*": "CPI(M)", "സിപിഐ എം*": "CPI(M)", "സിപിഐ*": "CPI", "മുസ്ലിം ലീഗ*": "IUML",
}

# How headlines refer to particular MPs -> the MP's exact name in the Lok Sabha record (never guessed)
MP_ALIASES = {
    "pm modi": "Narendra Modi", "prime minister modi": "Narendra Modi", "prime minister narendra modi": "Narendra Modi",
    # Hindi / Marathi
    "नरेंद्र मोदी*": "Narendra Modi", "प्रधानमंत्री मोदी*": "Narendra Modi", "पीएम मोदी*": "Narendra Modi",
    "पंतप्रधान मोदी*": "Narendra Modi",
    "राहुल गांधी*": "Rahul Gandhi", "प्रियंका गांधी*": "Priyanka Gandhi Vadra",
    "अमित शाह*": "Amit Shah", "राजनाथ सिंह*": "Rajnath Singh", "अखिलेश यादव*": "Akhilesh Yadav",
    "डिंपल यादव*": "Dimple Yadav", "नितिन गडकरी*": "Nitin Jairam Gadkari",
    "शिवराज सिंह चौहान*": "Shivraj Singh Chouhan", "ओम बिरला*": "Om Birla", "किरेन रिजिजू*": "Kiren Rijiju",
    "पीयूष गोयल*": "Piyush Vedprakash Goyal", "असदुद्दीन ओवैसी*": "Asaduddin Owaisi", "शशि थरूर*": "Shashi Tharoor",
    "धर्मेंद्र प्रधान*": "Dharmendra Pradhan", "मनोहर लाल खट्टर*": "Manohar Lal",
    "सुप्रिया सुले*": "Supriya Sule", "सुप्रिया सुळे*": "Supriya Sule",
    "अभिषेक बनर्जी*": "Abhishek Banerjee", "चिराग पासवान*": "Chirag Paswan", "जीतन राम मांझी*": "Jitan Ram Manjhi",
    "अनुराग ठाकुर*": "Anurag Singh Thakur", "गिरिराज सिंह*": "Giriraj Singh",
    "ज्योतिरादित्य सिंधिया*": "Jyotiraditya M Scindia", "भूपेंद्र यादव*": "Bhupender Yadav",
    "मनसुख मांडविया*": "Mansukh Mandaviya", "गजेंद्र सिंह शेखावत*": "Gajendra Singh Shekhawat",
    "अर्जुन राम मेघवाल*": "Arjun Ram Meghwal",
    # Gujarati
    "નરેન્દ્ર મોદી*": "Narendra Modi", "વડાપ્રધાન મોદી*": "Narendra Modi", "રાહુલ ગાંધી*": "Rahul Gandhi",
    "અમિત શાહ*": "Amit Shah",
    # Punjabi
    "ਨਰਿੰਦਰ ਮੋਦੀ*": "Narendra Modi", "ਰਾਹੁਲ ਗਾਂਧੀ*": "Rahul Gandhi", "ਅਮਿਤ ਸ਼ਾਹ*": "Amit Shah",
    # Bengali
    "নরেন্দ্র মোদী*": "Narendra Modi", "নরেন্দ্র মোদি*": "Narendra Modi", "প্রধানমন্ত্রী মোদী*": "Narendra Modi",
    "প্রধানমন্ত্রী মোদি*": "Narendra Modi", "রাহুল গান্ধী*": "Rahul Gandhi", "রাহুল গান্ধি*": "Rahul Gandhi",
    "অমিত শাহ*": "Amit Shah", "অভিষেক বন্দ্যোপাধ্যায়*": "Abhishek Banerjee",
    # Tamil
    "நரேந்திர மோடி*": "Narendra Modi", "பிரதமர் மோடி*": "Narendra Modi", "ராகுல் காந்தி*": "Rahul Gandhi",
    "அமித் ஷா*": "Amit Shah",
    # Telugu
    "నరేంద్ర మోదీ*": "Narendra Modi", "ప్రధాని మోదీ*": "Narendra Modi", "రాహుల్ గాంధీ*": "Rahul Gandhi",
    "అమిత్ షా*": "Amit Shah", "అసదుద్దీన్ ఒవైసీ*": "Asaduddin Owaisi",
    # Kannada
    "ನರೇಂದ್ರ ಮೋದಿ*": "Narendra Modi", "ಪ್ರಧಾನಿ ಮೋದಿ*": "Narendra Modi", "ರಾಹುಲ್ ಗಾಂಧಿ*": "Rahul Gandhi",
    "ಅಮಿತ್ ಶಾ*": "Amit Shah",
    # Malayalam
    "നരേന്ദ്ര മോദി*": "Narendra Modi", "പ്രധാനമന്ത്രി മോദി*": "Narendra Modi", "രാഹുൽ ഗാന്ധി*": "Rahul Gandhi",
    "അമിത് ഷാ*": "Amit Shah", "ശശി തരൂർ*": "Shashi Tharoor", "പ്രിയങ്ക ഗാന്ധി*": "Priyanka Gandhi Vadra",
}

# States in Indian languages (English names come from the canonical list)
STATE_ALIASES = {
    # Hindi / Marathi
    "उत्तर प्रदेश*": "Uttar Pradesh", "यूपी": "Uttar Pradesh", "महाराष्ट्र*": "Maharashtra", "बिहार*": "Bihar",
    "पश्चिम बंगाल*": "West Bengal", "मध्य प्रदेश*": "Madhya Pradesh", "मध्यप्रदेश*": "Madhya Pradesh",
    "तमिलनाडु*": "Tamil Nadu", "तमिलनाडू*": "Tamil Nadu", "राजस्थान*": "Rajasthan", "कर्नाटक*": "Karnataka",
    "गुजरात*": "Gujarat", "आंध्र प्रदेश*": "Andhra Pradesh", "ओडिशा*": "Odisha", "उड़ीसा*": "Odisha",
    "तेलंगाना*": "Telangana", "तेलंगणा*": "Telangana", "केरल*": "Kerala", "केरळ*": "Kerala", "झारखंड*": "Jharkhand",
    "असम": "Assam", "आसाम*": "Assam", "पंजाब*": "Punjab", "छत्तीसगढ़*": "Chhattisgarh", "हरियाणा*": "Haryana",
    "दिल्ली*": "Delhi", "जम्मू कश्मीर*": "Jammu and Kashmir", "जम्मू और कश्मीर*": "Jammu and Kashmir",
    "जम्मू आणि काश्मीर*": "Jammu and Kashmir", "उत्तराखंड*": "Uttarakhand", "हिमाचल*": "Himachal Pradesh",
    "त्रिपुरा*": "Tripura", "मेघालय*": "Meghalaya", "मणिपुर*": "Manipur", "नगालैंड*": "Nagaland",
    "नागालैंड*": "Nagaland", "गोवा*": "Goa", "अरुणाचल प्रदेश*": "Arunachal Pradesh", "पुडुचेरी*": "Puducherry",
    "मिज़ोरम*": "Mizoram", "सिक्किम*": "Sikkim", "लद्दाख*": "Ladakh", "चंडीगढ़*": "Chandigarh",
    "लक्षद्वीप*": "Lakshadweep", "अंडमान और निकोबार*": "Andaman and Nicobar Islands",
    # Gujarati
    "ગુજરાત*": "Gujarat", "મહારાષ્ટ્ર*": "Maharashtra", "રાજસ્થાન*": "Rajasthan", "દિલ્હી*": "Delhi",
    "ઉત્તર પ્રદેશ*": "Uttar Pradesh", "મધ્ય પ્રદેશ*": "Madhya Pradesh", "બિહાર*": "Bihar", "પંજાબ*": "Punjab",
    # Punjabi
    "ਪੰਜਾਬ*": "Punjab", "ਹਰਿਆਣਾ*": "Haryana", "ਦਿੱਲੀ*": "Delhi", "ਚੰਡੀਗੜ੍ਹ*": "Chandigarh",
    "ਹਿਮਾਚਲ*": "Himachal Pradesh", "ਜੰਮੂ ਕਸ਼ਮੀਰ*": "Jammu and Kashmir", "ਰਾਜਸਥਾਨ*": "Rajasthan",
    # Bengali (বিহার is also "monastery", so Bihar is left out)
    "পশ্চিমবঙ্গ*": "West Bengal", "ত্রিপুরা*": "Tripura", "আসাম*": "Assam", "ঝাড়খণ্ড*": "Jharkhand",
    "ওড়িশা*": "Odisha", "দিল্লি*": "Delhi", "দিল্লী*": "Delhi",
    # Tamil
    "தமிழ்நா*": "Tamil Nadu", "தமிழக*": "Tamil Nadu", "கேரள*": "Kerala", "கர்நாடக*": "Karnataka",
    "ஆந்திர*": "Andhra Pradesh", "தெலங்கானா*": "Telangana", "தெலுங்கானா*": "Telangana",
    "புதுச்சேரி*": "Puducherry", "புதுவை*": "Puducherry", "தில்லி*": "Delhi", "டெல்லி*": "Delhi",
    "மகாராஷ்டிர*": "Maharashtra", "பிகார*": "Bihar", "பீகார*": "Bihar", "குஜராத*": "Gujarat",
    "பஞ்சாப*": "Punjab", "ஒடிசா*": "Odisha", "அஸ்ஸாம*": "Assam", "ராஜஸ்தான*": "Rajasthan",
    "உத்தரப் பிரதேச*": "Uttar Pradesh", "உத்தர பிரதேச*": "Uttar Pradesh", "மேற்கு வங்க*": "West Bengal",
    # Telugu
    "తెలంగాణ*": "Telangana", "ఆంధ్రప్రదేశ*": "Andhra Pradesh", "ఆంధ్ర ప్రదేశ*": "Andhra Pradesh", "ఏపీ": "Andhra Pradesh",
    "కర్ణాటక*": "Karnataka", "తమిళనాడు*": "Tamil Nadu", "ఢిల్లీ*": "Delhi", "మహారాష్ట్ర*": "Maharashtra",
    "ఒడిశా*": "Odisha",
    # Kannada
    "ಕರ್ನಾಟಕ*": "Karnataka", "ಕೇರಳ*": "Kerala", "ತಮಿಳುನಾಡ*": "Tamil Nadu", "ಮಹಾರಾಷ್ಟ್ರ*": "Maharashtra",
    "ದೆಹಲಿ*": "Delhi", "ಆಂಧ್ರ ಪ್ರದೇಶ*": "Andhra Pradesh", "ತೆಲಂಗಾಣ*": "Telangana", "ಗೋವಾ*": "Goa",
    # Malayalam
    "കേരള*": "Kerala", "തമിഴ്നാട*": "Tamil Nadu", "കർണാടക*": "Karnataka", "ഡൽഹി*": "Delhi",
    "ലക്ഷദ്വീപ*": "Lakshadweep",
}

# A state name followed by an i/ii vowel sign is a demonym or adjective (गुजराती, ગુજરાતીઓ, ਪੰਜਾਬੀ, বিহারী,
# महाराष्ट्रीय): "a person or thing from there", not the state itself
STATE_DEMONYM_VOWELS = set("\u093f\u0940\u09bf\u09c0\u0a3f\u0a40\u0abf\u0ac0")
