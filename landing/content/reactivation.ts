/**
 * Copy for the player-facing reactivation landing page /r/[campaign_id].
 * Separate from the marketing landing copy (en.ts / ru.ts).
 *
 * Language selection: prefer campaign preferred_language; fall back to ?lang= param; default EN.
 * Russian text uses normal letter-spacing — never negative / tracking-tight.
 */

export interface ReactivationCopy {
  pageTitle: string;
  welcomeBack: (name: string) => string;
  yourOffer: string;
  watchVideo: string;
  videoUnavailableAlt: string;
  ctaLabel: string;
  thankYouHeadline: string;
  thankYouBody: string;
  depositHeadline: string;
  depositAmountLabel: string;
  depositAmountPlaceholder: string;
  depositSubmit: string;
  depositSuccess: string;
  depositMin: string;
  preparingHeadline: string;
  preparingBody: string;
  failedHeadline: string;
  failedBody: string;
  notFoundHeadline: string;
  notFoundBody: string;
  errorHeadline: string;
  errorBody: string;
  termsNote: string;
  poweredBy: string;
  backToHome: string;
}

export const reactivationEn: ReactivationCopy = {
  pageTitle: 'Your exclusive offer — Recall',
  welcomeBack: (name: string) => `Welcome back, ${name}`,
  yourOffer: 'Your exclusive offer',
  watchVideo: 'Watch your personal message',
  videoUnavailableAlt: 'Your personalized video postcard',
  ctaLabel: 'Claim my bonus',
  thankYouHeadline: 'Your bonus is on its way!',
  thankYouBody: 'Make a deposit below to activate your offer.',
  depositHeadline: 'Activate your bonus',
  depositAmountLabel: 'Deposit amount',
  depositAmountPlaceholder: 'e.g. 100',
  depositSubmit: 'Deposit & activate',
  depositSuccess: 'Bonus activated — enjoy your game!',
  depositMin: 'Minimum deposit: 10',
  preparingHeadline: 'Your personal video is being prepared',
  preparingBody: 'Please check back in a few minutes.',
  failedHeadline: 'Video temporarily unavailable',
  failedBody: 'Please contact our support team.',
  notFoundHeadline: 'This offer link has expired',
  notFoundBody: 'Please contact us to receive a new personalised offer.',
  errorHeadline: 'Something went wrong',
  errorBody: 'Please try again or contact our support team.',
  termsNote: 'Personalised promotional offer. Terms and conditions apply. Please play responsibly.',
  poweredBy: 'Powered by Recall AI',
  backToHome: '← Recall',
};

export const reactivationRu: ReactivationCopy = {
  pageTitle: 'Ваше персональное предложение — Recall',
  welcomeBack: (name: string) => `С возвращением, ${name}`,
  yourOffer: 'Ваше персональное предложение',
  watchVideo: 'Посмотрите ваше персональное видео',
  videoUnavailableAlt: 'Ваша персональная видеооткрытка',
  ctaLabel: 'Получить бонус',
  thankYouHeadline: 'Ваш бонус уже ждёт!',
  thankYouBody: 'Сделайте депозит ниже, чтобы активировать предложение.',
  depositHeadline: 'Активировать бонус',
  depositAmountLabel: 'Сумма депозита',
  depositAmountPlaceholder: 'напр. 1000',
  depositSubmit: 'Внести и активировать',
  depositSuccess: 'Бонус активирован — приятной игры!',
  depositMin: 'Минимальный депозит: 10',
  preparingHeadline: 'Ваше персональное видео готовится',
  preparingBody: 'Пожалуйста, зайдите снова через несколько минут.',
  failedHeadline: 'Видео временно недоступно',
  failedBody: 'Обратитесь в нашу службу поддержки.',
  notFoundHeadline: 'Срок действия этой ссылки истёк',
  notFoundBody: 'Свяжитесь с нами, чтобы получить новое персональное предложение.',
  errorHeadline: 'Что-то пошло не так',
  errorBody: 'Попробуйте ещё раз или обратитесь в службу поддержки.',
  termsNote: 'Персонализированное рекламное предложение. Применяются условия и положения. Играйте ответственно.',
  poweredBy: 'Powered by Recall AI',
  backToHome: '← Recall',
};

export function pickCopy(preferredLanguage: string, langParam?: string): ReactivationCopy {
  const lang = langParam ?? preferredLanguage;
  return lang === 'ru' ? reactivationRu : reactivationEn;
}
