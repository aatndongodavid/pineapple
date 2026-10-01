import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import fr from './locales/fr.json';
import en from './locales/en.json';

const SAVED_LANG_KEY = 'pineapple_language';
const savedLanguage = typeof window !== 'undefined' ? localStorage.getItem(SAVED_LANG_KEY) || 'fr' : 'fr';

i18n
  .use(initReactI18next)
  .init({
    resources: {
      fr: { translation: fr },
      en: { translation: en },
    },
    lng: savedLanguage,
    fallbackLng: 'fr',
    interpolation: {
      escapeValue: false, // React already escapes values
    },
  });

i18n.on('languageChanged', (lng) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem(SAVED_LANG_KEY, lng);
  }
});

export default i18n;
