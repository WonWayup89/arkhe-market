Arkhe Market Phase 6 patch

This patch begins the upgrade sequence with:
1. automatic test mode until a wallet or broker is connected
2. separate test and live balance stores
3. a shared balance resolver
4. command center seed and reset actions
5. command center cards using resolved balances instead of hardcoded amounts

Assumptions:
- your current project uses views/ rather than pages/
- your current app already has crypto, stocks, futures, promotion, and settings tabs
