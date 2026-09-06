"""Curated discovery records, not a substitute for the current BIS catalogue.
Sources reviewed 2026-09-06. Archived manuals establish identity, not current validity.
Add published full text before adding any clause-level requirements.
"""
REVIEWED = '2026-09-06'
CATALOGUE = 'https://standards.bis.gov.in/'
MANUALS = 'https://www.bis.gov.in/product-manual-archive/?lang=en'
LINKS = {
    'catalogue': ('Search Indian Standards', CATALOGUE),
    'apply': ('Manakonline / e-BIS', 'https://www.manakonline.in/'),
    'crs': ('CRS application guidance', 'https://crsbis.in/BIS/app_srv/tdc/gl/jsp/instappform.jsp'),
    'fmcs': ('BIS foreign manufacturers guidance', 'https://www.bis.gov.in/fmcs/certification-process/aboutfmcs/?lang=en'),
    'scheme_iv': ('Scheme IV product-specific guidance', 'https://www.bis.gov.in/specific-guidelines-for-scheme-iv-certificate-of-conformity/?lang=en'),
    'hallmark': ('BIS hallmarking FAQ', 'https://www.bis.gov.in/hallmarking-overview/hallmarking-faqs/hallmarking-faq/?lang=en'),
    'labs': ('BIS laboratory search (LIMS)', 'https://lims.bis.gov.in/'),
    'lrs': ('BIS laboratory recognition FAQ', 'https://www.bis.gov.in/laboratorys/laboratory-services-overview/laboratory-faq/?lang=en'),
    'crs_labs': ('Recognized CRS laboratories', 'https://crsbis.in/BIS/bis_lab.do'),
    'complaint': ('BIS consumer protection', 'https://bis.gov.in/other/consumer_affairs.htm'),
    'eco': ('Ecomark Rules 2024 announcement', 'https://www.pib.gov.in/PressReleasePage.aspx?PRID=2061878'),
    'cpcb': ('CPCB Ecomark rules', 'https://cpcb.nic.in/rules-7/'),
}
# Candidate IDs deliberately omit edition years where the latest revision is unverified.
STANDARDS = [
    dict(id='kettle', aliases=['kettle', 'liquid heating'], codes=['IS 302 (Part 1)', 'IS 302-2-15'], title='Household electrical safety; appliances for heating liquids', detail='For a smart electric kettle, confirm household use, voltage, heating design and wireless features. Smart connectivity alone does not establish CRS applicability.', source='https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=367'),
    dict(id='mask', aliases=['n95', 'respirator', 'filter half mask'], codes=['IS 9473'], title='Particle-filtering half masks', detail='N95 is not itself an Indian classification. Confirm intended use and the required Indian performance class; do not assume equivalence.', source=MANUALS),
    dict(id='helmet', aliases=['helmet', 'two wheeler'], codes=['IS 4151'], title='Protective helmets for two-wheeler riders', detail='Confirm that this is a motorcycle/two-wheeler helmet. Bicycle and industrial helmets require separate scope checks.', source=MANUALS),
    dict(id='gold', aliases=['gold', 'jewelry', 'jewellery'], codes=['IS 1417'], title='Gold jewellery and artefacts — fineness and marking', detail='Confirm the article type and fineness. Hallmarking is a separate certification route from an ISI product licence.', source=LINKS['hallmark'][1]),
    dict(id='silver', aliases=['silver'], codes=['IS 2112'], title='Silver jewellery and artefacts — fineness and marking', detail='Check the revised silver standard and current HUID guidance; older silver hallmark formats may differ.', source=LINKS['hallmark'][1]),
    dict(id='toys', aliases=['toy', 'toys'], codes=['IS 9873 (applicable parts)', 'IS 15644 (electric toys)'], title='Safety of toys', detail='Specify age group, materials, intended play and whether electrically powered. Select the applicable mechanical, flammability, chemical and electrical requirements.', source=MANUALS),
    dict(id='rebar', aliases=['rebar', 'tmt', 'reinforcement', 'steel bar'], codes=['IS 1786'], title='High-strength deformed steel bars and wires for concrete reinforcement', detail='Confirm steel grade, diameter and intended use before selecting test requirements.', source=MANUALS),
    dict(id='steel', aliases=['structural steel', 'steel plate', 'steel'], codes=['IS 2062 (Part 1):2025'], title='Hot-rolled medium and high-tensile structural steel', detail='Structural steel is one possible category; specify form, grade and application. Reinforcement bars use a different standard.', source='https://lims.bis.gov.in/home/search_is_number/?is_number__doc_no=2062'),
    dict(id='cement', aliases=['cement', 'opc'], codes=['IS 269'], title='Ordinary Portland cement', detail='Confirm whether the cement is OPC, Portland pozzolana or another type; the appropriate standard depends on that distinction.', source=MANUALS),
    dict(id='formula', aliases=['infant milk', 'infant formula', 'baby formula'], codes=['IS 14433'], title='Infant milk substitutes', detail='Distinguish infant milk substitutes from milk powder and follow-up formula. The BIS compulsory-certification list marks infant milk substitutes as de-notified. Check the current BIS scope and food-regulatory requirements separately.', source='https://www.bis.gov.in/product-certification/products-under-compulsory-certification/scheme-i-mark-scheme/?lang=en'),
    dict(id='water', aliases=['packaged drinking water', 'bottled water'], codes=['IS 14543'], title='Packaged drinking water other than packaged natural mineral water', detail='Natural mineral water has a different scope. This record does not establish a current mandatory certification obligation.', source=MANUALS),
    dict(id='it', aliases=['laptop', 'computer', 'it equipment'], codes=['IS 13252 (Part 1)'], title='Information technology equipment — safety (legacy catalogue candidate)', detail='Check the live CRS product list for the currently notified standard and any migration to newer safety standards before applying.', source=LINKS['crs'][1]),
    dict(id='battery', aliases=['lithium', 'battery', 'batteries'], codes=['IS 16046 (Part 2)'], title='Safety of portable sealed secondary lithium cells and batteries', detail='Chemistry, portability and end use determine scope; do not apply this candidate automatically to traction or industrial batteries.', source=LINKS['crs'][1]),
]
SCHEMES = {
    'isi': dict(title='Scheme I — ISI Mark', links=['apply', 'catalogue'], steps=[
        'Identify the applicable published IS, product manual and current Quality Control Order, including effective dates and exemptions.',
        'Prepare factory, manufacturing process, quality-control, test-equipment and product-scope information; review the product-specific application checklist.',
        'Apply through Manakonline and pay the applicable fees shown by BIS.',
        'Complete the applicable factory assessment, sample testing and corrective actions requested by BIS.',
        'After grant, use the mark only within the licensed scope and follow surveillance, testing, marking and renewal conditions.']),
    'crs': dict(title='Scheme II — Compulsory Registration Scheme (CRS)', links=['crs', 'crs_labs'], steps=[
        'Check the current notified product list and applicable IS; electronics are not automatically all covered by CRS.',
        'Define manufacturer, factory, brand and model coverage, and obtain testing from a BIS-recognized CRS laboratory for the applicable standard.',
        'Prepare the test report and required application documents; overseas applicants must check Authorized Indian Representative requirements.',
        'Submit the registration application through the official CRS portal and address BIS queries.',
        'After registration, follow applicable marking, model-inclusion, surveillance and renewal requirements.']),
    'fmcs': dict(title='Foreign Manufacturers Certification Scheme (FMCS)', links=['fmcs', 'apply'], steps=[
        'FMCS is not Scheme IV. Determine the product certification route; foreign manufacturers of CRS products must follow the CRS route.',
        'Identify the applicable IS and product-specific requirements and nominate an Authorized Indian Representative as required.',
        'Prepare factory, process, testing and quality-control documentation and submit the prescribed FMCS application.',
        'Arrange BIS factory inspection, sampling and testing; resolve nonconformities and complete the applicable agreement, fees and guarantee requirements.',
        'Use the Standard Mark only after licence grant and within its scope; maintain surveillance and renewal compliance.']),
    'scheme_iv': dict(title='Scheme IV — Certificate of Conformity', links=['scheme_iv'], steps=[
        'Scheme IV concerns a Certificate of Conformity; it is not the name of FMCS.',
        'Check whether the product is covered by the relevant order and product-specific Scheme IV guidelines.',
        'Prepare and submit the prescribed application with the required scope and conformity evidence.',
        'Complete the assessment and testing specified by BIS, resolve queries, and follow certificate and surveillance conditions after grant.']),
    'eco': dict(title='Ecomark — environmental criteria', links=['eco', 'cpcb'], steps=[
        'Consult the Ecomark Rules 2024 and current category criteria. CPCB implements the scheme in partnership with BIS.',
        'Check product eligibility, environmental criteria and the applicable underlying quality certification or conformity requirements.',
        'Prepare evidence against the category criteria and follow the application and verification process prescribed by CPCB.',
        'After grant, maintain the prescribed reporting and compliance records. Do not assume an ISI licence alone grants Ecomark.']),
}
LANGUAGES = {'en':'English','hi':'Hindi','ta':'Tamil','te':'Telugu','bn':'Bengali','mr':'Marathi','gu':'Gujarati','kn':'Kannada','ml':'Malayalam','pa':'Punjabi','or':'Odia','ur':'Urdu'}
# Deterministic alias expansion is intentionally small; full translation uses the API.
ALIASES = {
    'kettle':['केतली','केटल','கெட்டில்','கெட்டில்','కెటిల్','কেটলি'],
    'gold':['सोना','सोने','தங்க','బంగారం','সোনা'],
    'silver':['चांदी','வெள்ளி','వెండి','রূপা'],
    'hallmark':['हॉलमार्क','ஹால்மார்க்','హాల్‌మార్క్','হলমার্ক'],
    'complaint':['शिकायत','புகார்','ఫిర్యాదు','অভিযোগ'],
    'laboratory':['प्रयोगशाला','ஆய்வகம்','ஆய்வக','ప్రయోగశాల','গবেষণাগার','ল্যাব'],
    'certification':['प्रमाणन','लाइसेंस','சான்றிதழ்','சான்று','ధృవీకరణ','শংসাপত্র'],
    'toy':['खिलौ','பொம்மை','బొమ్మ','খেলনা'],
    'helmet':['हेलमेट','தலைக்கவச','హెల్మెట్','হেলমেট'],
    'infant formula':['शिशु दूध','குழந்தை பால்','శిశు పాలు','শিশুর দুধ'],
    'surgical instruments':['सर्जिकल उपकरण','शल्य उपकरण','அறுவை சிகிச்சை கருவி'],
}
OFFLINE_NOTICE = {
    'hi':'ऑफ़लाइन मोड: नीचे स्रोतों पर आधारित अंग्रेज़ी जानकारी है। पूर्ण हिन्दी अनुवाद के लिए OpenAI कनेक्शन आवश्यक है।',
    'ta':'ஆஃப்லைன் முறை: கீழே ஆதாரங்களுடன் ஆங்கிலத் தகவல் உள்ளது. முழு தமிழ் மொழிபெயர்ப்புக்கு OpenAI இணைப்பு தேவை.',
    'te':'ఆఫ్‌లైన్ మోడ్: కింద ఆధారాలతో ఆంగ్ల సమాచారం ఉంది. పూర్తి తెలుగు అనువాదానికి OpenAI అనుసంధానం అవసరం.',
    'bn':'অফলাইন মোড: নিচে সূত্রসহ ইংরেজি তথ্য রয়েছে। সম্পূর্ণ বাংলা অনুবাদের জন্য OpenAI সংযোগ প্রয়োজন।',
}
