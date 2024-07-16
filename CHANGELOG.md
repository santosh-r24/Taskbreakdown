# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

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
