import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import './LanguageSwitcher.css';

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  
  // Set document direction based on language
  useEffect(() => {
    document.documentElement.dir = i18n.t('direction');
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    setIsOpen(false);
    localStorage.setItem('i18nextLng', lng);
  };

  return (
    <div className="language-switcher">
      <button 
        className="language-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Change language"
      >
        <span className="language-icon">🌐</span>
        <span className="language-code">{i18n.language.toUpperCase()}</span>
      </button>
      
      {isOpen && (
        <div className="language-dropdown">
          <button 
            className={`language-option ${i18n.language === 'en' ? 'active' : ''}`}
            onClick={() => changeLanguage('en')}
          >
            English
          </button>
          <button 
            className={`language-option ${i18n.language === 'ar' ? 'active' : ''}`}
            onClick={() => changeLanguage('ar')}
          >
            العربية
          </button>
        </div>
      )}
    </div>
  );
};

export default LanguageSwitcher;
