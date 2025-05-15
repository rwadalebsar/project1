import { useTranslation } from 'react-i18next';
import './ModernLanguageSwitcher.css';

const ModernLanguageSwitcher = () => {
  const { i18n } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    // Store the language preference in localStorage
    localStorage.setItem('language', lng);
    // Set the document direction based on language
    document.documentElement.dir = lng === 'ar' ? 'rtl' : 'ltr';
  };

  return (
    <div className="modern-language-switcher">
      <button 
        className={`language-button ${i18n.language === 'en' ? 'active' : ''}`}
        onClick={() => changeLanguage('en')}
      >
        EN
      </button>
      <button 
        className={`language-button ${i18n.language === 'ar' ? 'active' : ''}`}
        onClick={() => changeLanguage('ar')}
      >
        عربي
      </button>
    </div>
  );
};

export default ModernLanguageSwitcher;
