import { createContext, useContext } from 'react';

// Interface text only. Data (names, parties, figures, source titles) is shown as published.
const STRINGS = {
  en: {
    'nav.dashboard': 'Dashboard',
    'nav.live': 'Live',
    'nav.parties': 'Parties',
    'nav.donations': 'Electoral Bonds',
    'nav.candidates': 'Candidates',
    'nav.ngos': 'NGO Funding',
    'nav.legislative': 'Parliament',
    'nav.brief': 'AI Brief',
    'nav.sources': 'Sources',
    'app.tagline': 'OSINT Transparency Portal',
    'app.search': 'Search',
    'notice.title': 'About this data:',
    'notice.body': 'every figure comes from a public source (SBI/ECI electoral bond disclosure, MyNeta affidavits, FCRA returns, Lok Sabha records, PIB) and links back to it. Coverage gaps are listed under Sources & Data Quality.',
    'facts.title': 'Key facts',
    'facts.note': 'Computed from the data on this site · click for the records',
    'facts.view': 'View records',
    'map.title': 'India map',
    'map.allIndia': 'All India',
    'map.click': 'Click a state for details.',
    'map.noData': 'No data',
    'map.credit': 'Boundaries as per the Survey of India map, from',
    'state.profile': 'State profile',
    'state.select': 'Select a state',
    'state.tab.ls': 'Lok Sabha',
    'state.tab.mla': 'MLAs',
    'state.tab.ngo': 'NGO Foreign Funding',
    'state.tab.parl': 'Parliament',
    'state.tab.news': 'News',
    'state.empty.title': 'Click a state on the map',
    'state.empty.body': "Shows that state's Lok Sabha candidates, sitting MLAs, NGO foreign contributions, and MPs' parliamentary activity.",
    'search.placeholder': 'Search parties, companies, candidates, MLAs, NGOs, MPs, questions...',
    'search.hint': 'Type at least two letters. Purchasers also match the raw SBI spellings.',
    'footer.data': 'Data: SBI/ECI, ADR/MyNeta, MHA FCRA returns, Lok Sabha (via Vonter), PIB',
    'footer.code': 'Source code (AGPL-3.0)',
    'footer.report': 'Report an error',
  },
  hi: {
    'nav.dashboard': 'डैशबोर्ड',
    'nav.live': 'लाइव',
    'nav.parties': 'राजनीतिक दल',
    'nav.donations': 'चुनावी बॉन्ड',
    'nav.candidates': 'उम्मीदवार',
    'nav.ngos': 'एनजीओ अंशदान',
    'nav.legislative': 'संसद',
    'nav.brief': 'एआई सारांश',
    'nav.sources': 'स्रोत',
    'app.tagline': 'ओपन-सोर्स पारदर्शिता पोर्टल',
    'app.search': 'खोजें',
    'notice.title': 'इस डेटा के बारे में:',
    'notice.body': 'हर आंकड़ा एक सार्वजनिक स्रोत से लिया गया है (SBI/ECI चुनावी बॉन्ड प्रकटीकरण, MyNeta शपथपत्र, FCRA रिटर्न, लोकसभा रिकॉर्ड, PIB) और उसी स्रोत से जुड़ा है। जो डेटा उपलब्ध नहीं है, उसकी सूची "स्रोत और डेटा गुणवत्ता" में दी गई है।',
    'facts.title': 'मुख्य तथ्य',
    'facts.note': 'इसी साइट के डेटा से गणना · रिकॉर्ड देखने के लिए क्लिक करें',
    'facts.view': 'रिकॉर्ड देखें',
    'map.title': 'भारत का नक्शा',
    'map.allIndia': 'पूरा भारत',
    'map.click': 'विवरण के लिए किसी राज्य पर क्लिक करें।',
    'map.noData': 'डेटा नहीं',
    'map.credit': 'सीमाएँ भारतीय सर्वेक्षण विभाग (Survey of India) के नक्शे के अनुसार, स्रोत:',
    'state.profile': 'राज्य प्रोफ़ाइल',
    'state.select': 'कोई राज्य चुनें',
    'state.tab.ls': 'लोकसभा',
    'state.tab.mla': 'विधायक',
    'state.tab.ngo': 'एनजीओ विदेशी अंशदान',
    'state.tab.parl': 'संसद',
    'state.tab.news': 'समाचार',
    'state.empty.title': 'नक्शे पर किसी राज्य पर क्लिक करें',
    'state.empty.body': 'उस राज्य के लोकसभा उम्मीदवार, वर्तमान विधायक, एनजीओ को मिला विदेशी अंशदान और सांसदों की संसदीय गतिविधि दिखाई जाएगी।',
    'search.placeholder': 'दल, कंपनियाँ, उम्मीदवार, विधायक, एनजीओ, सांसद, प्रश्न खोजें...',
    'search.hint': 'कम से कम दो अक्षर लिखें। बॉन्ड खरीदारों के नाम SBI की मूल वर्तनी से भी मिलाए जाते हैं।',
    'footer.data': 'डेटा: SBI/ECI, ADR/MyNeta, गृह मंत्रालय FCRA रिटर्न, लोकसभा (Vonter के माध्यम से), PIB',
    'footer.code': 'सोर्स कोड (AGPL-3.0)',
    'footer.report': 'त्रुटि की सूचना दें',
  },
};

export const LANGS = [{ id: 'en', label: 'EN' }, { id: 'hi', label: 'हिंदी' }];

export const LangContext = createContext('en');

export const translate = (lang, key) => STRINGS[lang]?.[key] ?? STRINGS.en[key] ?? key;

/** t('key') in the current language, falling back to English. */
export function useT() {
  const lang = useContext(LangContext);
  return (key) => translate(lang, key);
}
