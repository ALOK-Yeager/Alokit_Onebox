import type { EmailResult } from '../types/email';

export const demoEmails: EmailResult[] = [
  {
    id: 'demo_001',
    subject: 'Q4 Project Timeline Update - Critical Deadlines',
    sender: 'project-manager@techcorp.com',
    snippet:
      "We've moved the API integration milestone to next week while the database migration stays on track for October 15th.",
    category: 'More Information',
    timestamp: '2024-10-05T14:30:00Z'
  },
  {
    id: 'demo_002',
    subject: 'Stripe Account Verification Required - Action Needed',
    sender: 'support@stripe.com',
    snippet:
      'Please upload a government-issued ID and proof of address within 48 hours to keep payouts enabled on acct_1234567890.',
    category: 'Interested',
    timestamp: '2024-10-04T10:15:00Z'
  },
  {
    id: 'demo_003',
    subject: 'Security Alert: New SSH Key Added to Your Account',
    sender: 'noreply@github.com',
    snippet:
      'A new SSH key was added to your GitHub account. Review account security if this was not you. Fingerprint: SHA256:abcd1234.',
    category: 'Interested',
    timestamp: '2024-10-03T16:45:00Z'
  },
  {
    id: 'demo_004',
    subject: 'Annual Performance Review Process - Schedule Your 1:1',
    sender: 'hr@company.com',
    snippet:
      "Schedule your 1:1 by October 15th and submit the self-assessment before meeting with your manager for next year's goals.",
    category: 'More Information',
    timestamp: '2024-10-02T09:00:00Z'
  },
  {
    id: 'demo_005',
    subject: 'Weekly Tech Newsletter - AI Breakthroughs This Week',
    sender: 'marketing@newsletter.com',
    snippet:
      'OpenAI launches new multimodal tools, Google ships Gemini updates, and Azure expands AI services in this weekly roundup.',
    category: 'Not Interested',
    timestamp: '2024-10-01T12:00:00Z'
  },
  {
    id: 'demo_006',
    subject: 'Series A Funding Announcement - We Did It!',
    sender: 'ceo@startup.com',
    snippet:
      "We closed our $15M Series A round, doubling the engineering team and expanding go-to-market. Celebration Friday at 5 PM!",
    category: 'Interested',
    timestamp: '2024-09-30T17:30:00Z'
  },
  {
    id: 'demo_007',
    subject: 'Contract Renewal Discussion - Pricing Questions',
    sender: 'client@bigcorp.com',
    snippet:
      'Client wants to renew in November but needs to review pricing for the expanded scope. Schedule a call this week.',
    category: 'Interested',
    timestamp: '2024-09-29T14:20:00Z'
  },
  {
    id: 'demo_008',
    subject: 'Suspicious Login Attempt Detected',
    sender: 'security@bank.com',
    snippet:
      'A login attempt from an unrecognized device was blocked. Verify activity or reset your password and enable MFA.',
    category: 'Interested',
    timestamp: '2024-09-28T08:45:00Z'
  },
  {
    id: 'demo_009',
    subject: 'New Development Environment Setup Guide',
    sender: 'devtools@company.com',
    snippet:
      'Docker-based dev environment cuts onboarding from 2 days to 2 hours. Follow the guide and migrate by next Friday.',
    category: 'More Information',
    timestamp: '2024-09-27T11:15:00Z'
  },
  {
    id: 'demo_010',
    subject: 'Updated Terms of Service - Review Required',
    sender: 'legal@vendor.com',
    snippet:
      'Data privacy updates affect sections 4.2 and 7.1. Continued service use means you accept the new ToS.',
    category: 'More Information',
    timestamp: '2024-09-26T15:00:00Z'
  }
];
