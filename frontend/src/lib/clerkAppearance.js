/**
 * Clerk appearance configuration that matches the QueryTalk AI
 * dark cinematic SaaS theme — deep-navy foundation + single teal accent.
 * Colors sourced from tailwind.config.js design tokens.
 */
export const clerkAppearance = {
  variables: {
    // Core colors
    colorPrimary:          '#40CCB7',         // Teal accent
    colorBackground:       '#101321',         // Page background
    colorInputBackground:  '#0C0E1A',         // Surface-container-lowest
    colorInputText:        '#FFFFFF',
    colorText:             '#FFFFFF',
    colorTextSecondary:    '#9CA3AF',         // Muted foreground / label
    colorDanger:           '#EF4444',
    colorSuccess:          '#40CCB7',
    colorNeutral:          '#6B7280',
    colorShimmer:          'rgba(64, 204, 183, 0.05)',

    // Typography
    fontFamily:        "'Space Grotesk', system-ui, sans-serif",
    fontFamilyButtons: "'Space Grotesk', system-ui, sans-serif",
    fontSize:          '14px',
    fontWeight: {
      normal: 400,
      medium: 500,
      bold:   600,
    },

    // Border radius
    borderRadius: '0.5rem',

    // Spacing
    spacingUnit: '4px',
  },

  elements: {
    // Root card — surface panel
    card: {
      background:          'rgba(28, 30, 45, 0.75)',
      backdropFilter:      'blur(24px)',
      WebkitBackdropFilter:'blur(24px)',
      border:              '1px solid #2A2D3D',
      boxShadow:           '0 24px 80px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(64, 204, 183, 0.05)',
      borderRadius:        '1rem',
    },

    // Page / root wrapper
    rootBox: {
      width: '100%',
    },

    // Header title
    headerTitle: {
      color:          '#40CCB7',
      fontSize:       '22px',
      fontWeight:     '700',
      letterSpacing:  '-0.01em',
      fontFamily:     "'Space Grotesk', system-ui, sans-serif",
    },

    headerSubtitle: {
      color:    '#6B7280',
      fontSize: '13px',
    },

    // Form field labels
    formFieldLabel: {
      color:          '#9CA3AF',
      fontSize:       '12px',
      fontWeight:     '500',
      textTransform:  'uppercase',
      letterSpacing:  '0.05em',
      fontFamily:     "'JetBrains Mono', monospace",
    },

    // Form field inputs
    formFieldInput: {
      background:   'rgba(0, 0, 0, 0.25)',
      border:       '1px solid #2A2D3D',
      color:        '#FFFFFF',
      borderRadius: '0.5rem',
      fontSize:     '14px',
      transition:   'all 0.2s ease',
      '&:focus': {
        borderColor: 'rgba(64, 204, 183, 0.7)',
        boxShadow:   '0 0 0 2px rgba(64, 204, 183, 0.2)',
        outline:     'none',
      },
    },

    // Primary action button — teal glow
    formButtonPrimary: {
      background:   'rgba(64, 204, 183, 0.6)',
      border:       '1px solid #40CCB7',
      color:        '#FFFFFF',
      fontWeight:   '600',
      fontSize:     '14px',
      fontFamily:   "'Space Grotesk', system-ui, sans-serif",
      borderRadius: '0.5rem',
      transition:   'all 0.2s ease',
      boxShadow:    '0 0 20px rgba(64, 204, 183, 0.2)',
      '&:hover': {
        background: 'rgba(64, 204, 183, 0.8)',
        boxShadow:  '0 0 28px rgba(64, 204, 183, 0.35)',
        transform:  'translateY(-1px)',
      },
      '&:active': {
        transform: 'scale(0.98)',
      },
    },

    // Social OAuth buttons
    socialButtonsIconButton: {
      background:   'rgba(255, 255, 255, 0.03)',
      border:       '1px solid #2A2D3D',
      borderRadius: '0.5rem',
      color:        '#FFFFFF',
      '&:hover': {
        background:   'rgba(64, 204, 183, 0.06)',
        borderColor:  'rgba(64, 204, 183, 0.3)',
      },
    },

    socialButtonsBlockButton: {
      background:   'rgba(255, 255, 255, 0.03)',
      border:       '1px solid #2A2D3D',
      borderRadius: '0.5rem',
      color:        '#FFFFFF',
      fontSize:     '14px',
      '&:hover': {
        background:  'rgba(64, 204, 183, 0.06)',
        borderColor: 'rgba(64, 204, 183, 0.3)',
      },
    },

    // Divider
    dividerLine: {
      background: '#2A2D3D',
    },
    dividerText: {
      color:          '#6B7280',
      fontSize:       '12px',
      fontFamily:     "'JetBrains Mono', monospace",
      textTransform:  'uppercase',
      letterSpacing:  '0.05em',
    },

    // Footer links
    footerActionText: {
      color:    '#6B7280',
      fontSize: '13px',
    },
    footerActionLink: {
      color:      '#40CCB7',
      fontWeight: '500',
      '&:hover': {
        color: '#2EAA97',
      },
    },
    footer: {
      background: 'transparent',
      '& + div': {
        display: 'none',
      },
    },

    // "Secured by Clerk" badge — hidden
    footerPages: {
      display: 'none',
    },

    // Internal links (Forgot password)
    formFieldAction: {
      color:    '#40CCB7',
      fontSize: '13px',
      '&:hover': {
        color: '#2EAA97',
      },
    },

    // Error messages
    formFieldErrorText: {
      color:    '#EF4444',
      fontSize: '12px',
    },
    alert: {
      background:   'rgba(239, 68, 68, 0.08)',
      border:       '1px solid rgba(239, 68, 68, 0.25)',
      borderRadius: '0.5rem',
      color:        '#FECACA',
      fontSize:     '13px',
    },
    alertText: {
      color: '#FECACA',
    },

    // OTP / verification code inputs
    otpCodeFieldInput: {
      background:   'rgba(0, 0, 0, 0.3)',
      border:       '1px solid #2A2D3D',
      color:        '#FFFFFF',
      borderRadius: '0.5rem',
      fontSize:     '20px',
      fontFamily:   "'JetBrains Mono', monospace",
      '&:focus': {
        borderColor: '#40CCB7',
        boxShadow:   '0 0 0 2px rgba(64, 204, 183, 0.2)',
      },
    },

    // Identity preview
    identityPreviewText: {
      color:    '#FFFFFF',
      fontSize: '14px',
    },
    identityPreviewEditButton: {
      color:     '#40CCB7',
      '&:hover': { color: '#2EAA97' },
    },

    // Avatar
    avatarBox: {
      borderRadius: '0.5rem',
      border:       '1px solid rgba(64, 204, 183, 0.25)',
    },

    // Back button
    backLink: {
      color:     '#6B7280',
      '&:hover': { color: '#40CCB7' },
    },

    // Clerk logo — hidden
    internal: {
      display: 'none',
    },
  },
};
