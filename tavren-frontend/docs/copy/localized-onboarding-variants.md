# Localized Onboarding Copy Variants

This document contains localized onboarding copy variants for different regulatory and cultural contexts based on the existing Empowerment and Reward versions.

## 🇪🇺 EU GDPR-Sensitive Region (France, Germany, etc.)

### Headline
**Your Data Rights, Protected**

### Subhead
Tavren empowers you with full control over your personal information. Exercise your privacy rights while choosing exactly what data you share and with whom.

### CTA
**Manage My Data Rights**

### Tone Note
This variant emphasizes legal rights and control rather than financial incentives. "Protected" and "empowers" signal GDPR compliance, while "exercise your privacy rights" directly references the regulatory framework Europeans are familiar with. The CTA focuses on rights management rather than control or earnings to align with the EU's strong data protection culture.

## 🌍 Global South Mobile-First Region (e.g., India, Brazil)

### Headline
**Fair Value for Your Data**

### Subhead
Tavren ensures you're treated fairly in the digital economy. Simple controls let you share data safely and get rewarded instantly.

### CTA
**Start Earning Now**

### Tone Note
This version uses shorter, simpler sentences optimized for mobile screens and varied literacy levels. It emphasizes fairness and immediate rewards, addressing common concerns about exploitation in digital ecosystems. "Simple controls" acknowledges potential technical barriers while "safely" builds trust. The direct CTA focuses on immediate benefit rather than abstract concepts of control or rights.

## Implementation Notes

To implement these variants in code:

```typescript
// Add to VARIANT_CONTENT in CopyVariantSwitcher.tsx
const VARIANT_CONTENT = {
  // Existing variants
  A: { ... },
  B: { ... },
  
  // New localized variants
  EU: {
    headline: 'Your Data Rights, Protected',
    subhead: 'Tavren empowers you with full control over your personal information. Exercise your privacy rights while choosing exactly what data you share and with whom.',
    cta: 'Manage My Data Rights',
    altHeadline: 'Privacy By Design'
  },
  GLOBAL_SOUTH: {
    headline: 'Fair Value for Your Data',
    subhead: 'Tavren ensures you\'re treated fairly in the digital economy. Simple controls let you share data safely and get rewarded instantly.',
    cta: 'Start Earning Now',
    altHeadline: 'Your Data, Your Earnings'
  }
};
```

To activate these variants, update the component to detect appropriate locale and region, or manually test with URL parameters like `?variant=EU` or `?variant=GLOBAL_SOUTH`.
