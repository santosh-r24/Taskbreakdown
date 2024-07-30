# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [1.0.0] - 2024-07-30
 
Updates pushed in this commit.
 
### Added
- Now the agent can generate and sync plans to google calander.
- Added a tab in Todolist page to schedule time.
- Added another model for json responses for calander. 
- Added st.spinner to show that the agent is responding.
- Added instructions popover in Todolist Tab.
### Changed
- Refactored the code further. llm function calls, calendar, and helper utils are abstracted from main streamlit code.
- There's a separate tab to see the plan generated so far, which would be sent to calendar.
- Added appropriate streamlit status messages instead of st write.  
- Added login button instead of login url.
- Changed the How to use Tool function in the markdown in Home page.
- Changed the order the tabs appear on sidebar.
- Changed st.experimental_dialog to st.dialog decorator.
- Moved database_functions along with utils, llm_utils inside helpers.
- Modified .gitignore file.
### Fixed

## [Unreleased] - 2024-07-22
 
Updates pushed in this commit.
 
### Added
- The model now retrieves previous chats as context. older chats are summarised, while newer chat is used as is for better precision.
- Toggle button to update Gemini Key
### Changed
- Completely removed obsolete code 
- Used st.cache to limit the number of database calls (for messages and summary)
- cleaned the code, by fucntionising. All variables are stored in st.session_state.
- Updated README.md
- The image now is fetched from your google account in user
### Fixed
- Bug fix for updating API key

## [Unreleased] - 2024-07-16
 
Updates pushed in this commit.
 
### Added
 
### Changed
- changed database to heroku postgres, now saves chat to postgres 
### Fixed

## [Unreleased] - 2024-07-08
 
Updates pushed in this commit.
 
### Added
- Added input to get and use gemini key
 
### Changed
- Added instructions on how to use the tool
- Using streamlit secrets instead of config to store secrets
### Fixed
- pyscopg library fix in requirements.txt

## [Unreleased] - 2024-07-06
 
Updates pushed in this commit.
 
### Added
- Added Chat interface.
- Added memory
- Saves the conversation and reloads it in database
- added login via google oauth
 
### Changed
- Removed audio input
- Added a limit of 4000 tokens, so that responses can be quicker. Post which old conversations will be summarised
 
### Fixed

## [Unreleased] - 2024-06-23

Updates pushed in this commit - 

### Added
- Defined System behavior, the agent now respons to only questions pertaining to taskbreakdown
 
### Changed
 
### Fixed
- If token length moves over 4000 tokens, the previous conversations will be summarised.
## [Unreleased] - 2024-06-17

Updates pushed in this commit.

### Added
- Directly added both voice and text input 
- These inputs are directly fed into the model to generate a response
 
### Changed
 
### Fixed


## [Unreleased] - 2024-06-11
 
Updates pushed in this commit.
 
### Added
- Added PoC functionalities
- Added streamlit as interface
- Added 1st draft of readme
 
### Changed
 
### Fixed
