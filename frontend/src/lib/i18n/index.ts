export {
  DICTIONARY,
  common,
  student,
  auth,
  teacher,
  type TranslationKey,
  type TranslationEntry,
  type DictShape,
} from "./dictionary";
export {
  DEFAULT_LOCALE,
  LOCALES,
  LOCALE_LABELS,
  LOCALE_STORAGE_KEY,
  applyDocumentLang,
  getLocaleServerSnapshot,
  getLocaleSnapshot,
  isLocale,
  readStoredLocale,
  resetLocaleStore,
  setStoredLocale,
  subscribeLocale,
  writeStoredLocale,
  type Locale,
} from "./locale";
export {
  LocaleProvider,
  useLocale,
  useTranslation,
} from "./locale-context";
