# Nabu AI Language Tutor - TODO List

## Completed Tasks ✅

### UI and Branding
- [x] **UI Reverted**: Changed to a clean, simple design with title, language selector, welcome message, and stats cards
- [x] **Nabu Branding**: Updated all references from "Logo" to "Nabu" in the UI 
- [x] **Start Conversation Button**: Made the button more prominent with better styling and visibility
- [x] **Language Silo**: Vocabulary is now filtered by the selected target language
- [x] **Conversation Stats**: Added "Times Seen" and "Times Used" columns to vocabulary tab
- [x] **Home Tab**: The Home tab is now the main landing page with the other tabs live

### Database and Schema
- [x] **Vocabulary Schema Fix**: Fixed column name mismatch (`mastery_score` → `mastery_level`) in vocabulary queries
- [x] **Database Integration**: All tabs now use a shared database manager instance

## Pending Tasks 🔄

### UI Improvements
- [ ] **Remove Watermark**: Check for and remove any watermark in the bottom corner (no watermark found in code)
- [ ] **Test UI Visibility**: Verify the "Start Conversation" button is visible and functional
- [ ] **Dashboard Styling**: Ensure the dashboard matches the original design requirements

### Functionality
- [ ] **Maintain Functionality**: Ensure all existing functionality is preserved after UI changes
- [ ] **Language Switching**: Test that language changes properly update vocabulary and other components
- [ ] **Conversation Navigation**: Verify the "Start Conversation" button properly navigates to conversation mode

### Vocabulary System
- [ ] **Stats Implementation**: Ensure conversation statistics (times seen, times used) are properly tracked
- [ ] **Language Filtering**: Verify vocabulary filtering works correctly for different languages
- [ ] **Database Population**: Add sample vocabulary data for testing

## Next Steps
1. Test the application to verify the UI changes are working correctly
2. Check if the "Start Conversation" button is visible and functional
3. Verify vocabulary filtering by language works properly
4. Test conversation functionality and navigation
5. Add sample data if needed for testing

## Notes
- The vocabulary table schema has been fixed to use `mastery_level` instead of `mastery_score`
- The dashboard UI has been updated with a more prominent "Start Conversation" button
- No watermark was found in the codebase
- All tabs are now live and functional
