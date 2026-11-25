/**
 * RAI-Biz Assessment Text-to-Speech (TTS) Engine
 * ==============================================
 * Provides browser-native accessibility narration for SME assessment questions
 * with English (en-IN) and Tamil (ta-IN) dual-language voice selection.
 *
 * Privacy & Security Guarantee:
 * - 100% browser-native Web Speech API (window.speechSynthesis).
 * - Zero third-party API calls, zero audio data transmitted externally.
 * - Graceful degradation when voices or speech API are unavailable.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { QuestionDefinition } from '../api/client';

export type TTSLanguage = 'en' | 'ta';
export type TTSPlaybackState = 'idle' | 'playing' | 'paused';

export const TAMIL_CATEGORIES: Record<string, string> = {
  fairness: 'நேர்மை மற்றும் மக்கள்தொகை சமத்துவம்',
  transparency: 'வெளிப்படைத்தன்மை மற்றும் விளக்கமளிக்கும் திறன்',
  privacy: 'தரவு தனியுரிமை மற்றும் தரவு ஆளுகை',
  sustainability: 'பசுமை செயற்கை நுண்ணறிவு மற்றும் நிலைத்தன்மை'
};

export const TAMIL_STANDARD_QUESTIONS: Record<string, string> = {
  F1: 'உங்கள் நிறுவனம் இந்த AI அமைப்புக்கு பாலினம், வயது, இனம் போன்ற மக்கள்தொகை குழுக்களிடையே சார்பு மற்றும் சமத்துவ சோதனைகளை முன்கூட்டியே நடத்துகிறதா?',
  F2: 'செயல்பாட்டின் போது குழு விளைவு அளவீடுகள் (மக்கள்தொகை சமநிலை விகிதம் போன்றவை) தொடர்ந்து கண்காணிக்கப்படுகின்றனவா?',
  F3: 'வாடிக்கையாளர்கள் அல்லது ஊழியர்கள் நியாயமற்ற தானியங்கி முடிவுகள் அல்லது சார்புகளைப் புகாரளிக்க மேல்முறையீட்டு நடைமுறை உள்ளதா?',
  F4: 'பாதுகாக்கப்பட்ட பண்புகள், பதிலி காரணிகள் (அஞ்சல் குறியீடு போன்றவை) மற்றும் மாதிரி சார்பு சமரசங்கள் ஆவணப்படுத்தப்பட்டுள்ளனவா?',
  F5: 'அல்காரித சார்பு அனுமதிக்கப்பட்ட வரம்பை மீறும் போது தானியங்கி செயல்பாட்டை நிறுத்த அல்லது மறுபயிற்சி செய்ய முறையான திட்டம் உள்ளதா?',

  T1: 'ஒரு குறிப்பிட்ட தானியங்கி முடிவுக்கு என்ன காரணங்கள் என்பதை உங்கள் AI அமைப்பு உள்ளூர் மற்றும் உலகளாவிய விளக்கங்களாக வழங்க முடியுமா?',
  T2: 'முடிவுகளில் AI அமைப்பு முக்கிய பங்கு வகிக்கும் போது பாதிக்கப்பட்ட நபர்களுக்கு அது வெளிப்படையாக தெரிவிக்கப்படுகிறதா?',
  T3: 'ஒவ்வொரு தானியங்கி கணிப்புக்கும் உள்ளீடு, மாதிரி பதிப்பு, நேரம் ஆகியவற்றுடன் மாற்ற முடியாத தணிக்கை பதிவுகள் பராமரிக்கப்படுகின்றனவா?',
  T4: 'மாதிரியின் துல்லியம் மற்றும் தரவு சறுக்கல் ஆகியவை குறிப்பிட்ட கால இடைவெளியில் உண்மையான பின்னூட்டங்களுடன் ஒப்பிடப்படுகிறதா?',
  T5: 'அதிக தாக்கத்தை ஏற்படுத்தும் தானியங்கி பரிந்துரைகளை சரிபார்க்க அல்லது மாற்ற தகுதியான மனித மேற்பார்வை அதிகாரம் உள்ளதா?',

  P1: 'உங்கள் தரவு அமைப்பில் தேவையற்ற தனிப்பட்ட அடையாள தகவல்கள் மாதிரி செயலாக்கத்திற்கு முன் நீக்கப்படுகின்றனவா?',
  P2: 'AI பயிற்சி தரவு மற்றும் மாதிரிகளுக்கான அணுகல் முறையான பாத்திர அடிப்படையிலான அனுமதிகள் மற்றும் பல காரணி அங்கீகாரம் மூலம் கட்டுப்படுத்தப்படுகிறதா?',
  P3: 'சேகரிக்கப்பட்ட தரவுகளுக்கு தானியங்கி தரவு தக்கவைப்பு மற்றும் பாதுகாப்பான அழிப்பு கால அட்டவணை உள்ளதா?',
  P4: 'அனைத்து முக்கியமான தரவுகளும் பரிமாற்றத்தின் போதும் சேமிப்பகத்திலும் வலுவான மறைகுறியாக்கத்துடன் பாதுகாக்கப்படுகின்றனவா?',
  P5: 'வெளிப்புற AI கருவிகள் மற்றும் சேவை வழங்குநர்களுக்கு ஆவணப்படுத்தப்பட்ட தரவு தனியுரிமை தாக்க மதிப்பீடுகள் மேற்கொள்ளப்படுகிறதா?',

  S1: 'மாதிரி பயிற்சி மற்றும் பயன்பாட்டிற்கான கணினி நேரம், மின்சார பயன்பாடு மற்றும் மதிப்பிடப்பட்ட ஆற்றல் நுகர்வு கண்காணிக்கப்படுகிறதா?',
  S2: 'பயன்பாடற்ற நேரங்களில் கிளவுட் வளங்களை தானாக சுருக்குவது போன்ற உகந்தமைப்புகள் செய்யப்பட்டுள்ளனவா?',
  S3: 'ஒரே மாதிரியான வினவல்களுக்கு கேச்சிங் பயன்படுத்தி தேவையற்ற மறு கணக்கீடுகள் மற்றும் ஆற்றல் வீணாவது தவிர்க்கப்படுகிறதா?',
  S4: 'அதிக ஆற்றல் தேவைப்படும் பெரிய மாதிரிகளுக்குப் பதிலாக இலகுரக, ஆற்றல் திறன் கொண்ட மாதிரிகள் மதிப்பீடு செய்யப்பட்டுள்ளனவா?',
  S5: 'AI அமைப்பை இயக்கும் கிளவுட் டேட்டா சென்டர்களின் கார்பன் உமிழ்வு மற்றும் புதுப்பிக்கத்தக்க ஆற்றல் காரணி மதிப்பிடப்படுகிறதா?'
};

export const TAMIL_OPTIONS_TEXT =
  'பதிலளிப்பதற்கான விருப்பங்கள்: விருப்பம் ஒன்று: ஆம். விருப்பம் இரண்டு: பகுதியளவு. விருப்பம் மூன்று: இல்லை. விருப்பம் நான்கு: பொருந்தாது.';

export const ENGLISH_OPTIONS_TEXT =
  'Available answer options: Option 1: Yes. Option 2: Partially. Option 3: No. Option 4: Not applicable.';

export const MISSING_TAMIL_VOICE_MESSAGE =
  'Tamil voice is not available on this device. Please install or enable a Tamil speech voice, or select English.';

/**
 * Checks whether the browser runtime supports Web Speech API synthesis.
 */
export function isSpeechSynthesisSupported(): boolean {
  return typeof window !== 'undefined' && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
}

/**
 * Searches available browser voices for the best matching Tamil voice.
 * Matches: ta-IN, ta_IN, any ta-* prefix, or voice name containing "tamil".
 */
export function findTamilVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (!voices || voices.length === 0) return null;
  const exact = voices.find((v) => v.lang === 'ta-IN' || v.lang === 'ta_IN');
  if (exact) return exact;

  const prefix = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith('ta'));
  if (prefix) return prefix;

  const nameMatch = voices.find((v) => v.name && v.name.toLowerCase().includes('tamil'));
  return nameMatch || null;
}

/**
 * Searches available browser voices for the best matching English voice.
 * Priority: en-IN (Indian English) -> en-US / en-GB -> any English voice -> first available voice.
 */
export function findEnglishVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (!voices || voices.length === 0) return null;
  const indianEnglish = voices.find((v) => v.lang === 'en-IN' || v.lang === 'en_IN');
  if (indianEnglish) return indianEnglish;

  const standardEn = voices.find((v) => v.lang === 'en-US' || v.lang === 'en-GB');
  if (standardEn) return standardEn;

  const anyEn = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith('en'));
  if (anyEn) return anyEn;

  return voices[0] || null;
}

/**
 * Generates spoken text for an assessment question in English.
 */
export function formatEnglishSpeechText(question: QuestionDefinition): string {
  const category = question.category_title || question.category || 'Governance Criteria';
  return `Question ${question.id}. Category: ${category}. ${question.question_text}. ${ENGLISH_OPTIONS_TEXT}`;
}

/**
 * Generates spoken text for an assessment question in Tamil.
 */
export function formatTamilSpeechText(question: QuestionDefinition): string {
  const catKey = (question.category || '').toLowerCase();
  const category = TAMIL_CATEGORIES[catKey] || question.category_title || 'பொது ஆளுகை';
  const qText = TAMIL_STANDARD_QUESTIONS[question.id] || question.question_text;
  return `கேள்வி ${question.id}. பிரிவு: ${category}. ${qText}. ${TAMIL_OPTIONS_TEXT}`;
}

/**
 * React hook managing Assessment Text-to-Speech lifecycle and controls.
 */
export function useAssessmentTTS() {
  const [selectedLanguage, setSelectedLanguage] = useState<TTSLanguage>('en');
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null);
  const [playbackState, setPlaybackState] = useState<TTSPlaybackState>('idle');
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [missingVoiceNotice, setMissingVoiceNotice] = useState<string | null>(null);
  const [isSupported, setIsSupported] = useState<boolean>(true);

  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  // Load and update voices
  const refreshVoices = useCallback(() => {
    if (!isSpeechSynthesisSupported()) {
      setIsSupported(false);
      return;
    }
    try {
      const vList = window.speechSynthesis.getVoices();
      if (vList && vList.length > 0) {
        setVoices(vList);
      }
    } catch (err) {
      console.warn('Could not retrieve speech voices:', err);
    }
  }, []);

  useEffect(() => {
    const supported = isSpeechSynthesisSupported();
    setIsSupported(supported);
    if (!supported) return;

    refreshVoices();
    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = refreshVoices;
    }
    if (typeof window.speechSynthesis.addEventListener === 'function') {
      window.speechSynthesis.addEventListener('voiceschanged', refreshVoices);
    }

    // Safety cleanup on unmount
    return () => {
      try {
        if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
          if (typeof window.speechSynthesis.removeEventListener === 'function') {
            window.speechSynthesis.removeEventListener('voiceschanged', refreshVoices);
          }
          window.speechSynthesis.cancel();
        }
      } catch (e) {
        // Ignore unmount cancel errors
      }
    };
  }, [refreshVoices]);

  const tamilVoice = findTamilVoice(voices);
  const englishVoice = findEnglishVoice(voices);
  const isTamilVoiceAvailable = Boolean(tamilVoice);
  const isEnglishVoiceAvailable = Boolean(englishVoice);

  const stop = useCallback(() => {
    if (!isSpeechSynthesisSupported()) return;
    try {
      window.speechSynthesis.cancel();
    } catch (e) {
      console.warn('Speech cancellation error:', e);
    }
    utteranceRef.current = null;
    setActiveQuestionId(null);
    setPlaybackState('idle');
  }, []);

  const pause = useCallback(() => {
    if (!isSpeechSynthesisSupported()) return;
    try {
      window.speechSynthesis.pause();
      setPlaybackState('paused');
    } catch (e) {
      console.warn('Speech pause error:', e);
    }
  }, []);

  const resume = useCallback(() => {
    if (!isSpeechSynthesisSupported()) return;
    try {
      window.speechSynthesis.resume();
      setPlaybackState('playing');
    } catch (e) {
      console.warn('Speech resume error:', e);
    }
  }, []);

  const play = useCallback(
    (question: QuestionDefinition) => {
      if (!isSpeechSynthesisSupported()) {
        setMissingVoiceNotice('Text-to-speech is not supported on this browser or device.');
        return;
      }

      // Check Tamil voice availability
      if (selectedLanguage === 'ta') {
        const availableTa = findTamilVoice(window.speechSynthesis.getVoices());
        if (!availableTa) {
          stop();
          setMissingVoiceNotice(MISSING_TAMIL_VOICE_MESSAGE);
          return;
        }
      }

      setMissingVoiceNotice(null);

      // Stop any existing speech before starting a new question
      stop();

      const text =
        selectedLanguage === 'ta'
          ? formatTamilSpeechText(question)
          : formatEnglishSpeechText(question);

      const utterance = new SpeechSynthesisUtterance(text);

      if (selectedLanguage === 'ta') {
        const taVoice = findTamilVoice(window.speechSynthesis.getVoices());
        if (taVoice) {
          utterance.voice = taVoice;
        }
        utterance.lang = 'ta-IN';
        utterance.rate = 0.9; // Slightly slower for crisp Tamil diction
      } else {
        const enVoice = findEnglishVoice(window.speechSynthesis.getVoices());
        if (enVoice) {
          utterance.voice = enVoice;
        }
        utterance.lang = 'en-IN';
        utterance.rate = 0.95;
      }

      utterance.onstart = () => {
        setActiveQuestionId(question.id);
        setPlaybackState('playing');
      };

      utterance.onpause = () => {
        setPlaybackState('paused');
      };

      utterance.onresume = () => {
        setPlaybackState('playing');
      };

      utterance.onend = () => {
        setActiveQuestionId(null);
        setPlaybackState('idle');
        utteranceRef.current = null;
      };

      utterance.onerror = (e) => {
        // Cancelled errors are expected when user stops or switches questions
        if (e.error !== 'canceled' && e.error !== 'interrupted') {
          console.warn('TTS playback error:', e);
        }
        setActiveQuestionId(null);
        setPlaybackState('idle');
        utteranceRef.current = null;
      };

      utteranceRef.current = utterance;
      setActiveQuestionId(question.id);
      setPlaybackState('playing');

      try {
        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.error('Failed to trigger speech synthesis:', err);
        setPlaybackState('idle');
        setActiveQuestionId(null);
      }
    },
    [selectedLanguage, stop]
  );

  const replay = useCallback(
    (question: QuestionDefinition) => {
      play(question);
    },
    [play]
  );

  const handleLanguageChange = useCallback(
    (newLang: TTSLanguage) => {
      setSelectedLanguage(newLang);
      setMissingVoiceNotice(null);
      // Stop current playback when language is changed
      if (playbackState !== 'idle') {
        stop();
      }
      // If switching to Tamil and no voice exists, advise immediately
      if (newLang === 'ta') {
        const ta = findTamilVoice(window.speechSynthesis.getVoices());
        if (!ta) {
          setMissingVoiceNotice(MISSING_TAMIL_VOICE_MESSAGE);
        }
      }
    },
    [playbackState, stop]
  );

  const dismissNotice = useCallback(() => {
    setMissingVoiceNotice(null);
  }, []);

  return {
    isSupported,
    selectedLanguage,
    setLanguage: handleLanguageChange,
    activeQuestionId,
    playbackState,
    isTamilVoiceAvailable,
    isEnglishVoiceAvailable,
    missingVoiceNotice,
    dismissNotice,
    play,
    pause,
    resume,
    stop,
    replay
  };
}
