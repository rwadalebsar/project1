import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button, ButtonGroup } from '@mui/material';

const LanguageSwitcher = () => {
  const { i18n } = useTranslation();

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    // Store the language preference in localStorage
    localStorage.setItem('language', lng);
    // Set the document direction based on language
    document.documentElement.dir = lng === 'ar' ? 'rtl' : 'ltr';
  };

  return (
    <ButtonGroup size="small" aria-label="language switcher">
      <Button 
        onClick={() => changeLanguage('en')}
        variant={i18n.language === 'en' ? 'contained' : 'outlined'}
      >
        EN
      </Button>
      <Button 
        onClick={() => changeLanguage('ar')}
        variant={i18n.language === 'ar' ? 'contained' : 'outlined'}
      >
        عربي
      </Button>
    </ButtonGroup>
  );
};

export default LanguageSwitcher;
