# Taskbreakdown

## Table of Contents
- [Overview](#Overview)
- [Features](#features)
- [Instructions](#instructions)
- [How to Use](#how-to-use)
- [Future Enhancements](#future-enhancements)
### Overview
This is a Todolist agent, it breaks down big goals into smaller tasks following the [SMART](https://www.atlassian.com/blog/productivity/how-to-write-smart-goals) framework. It integrates with google suite to sync plans and tasks to Google Calendar, and Google tasks respectively.

#### Usefulness
Taskbreakdown is designed for individuals who struggle with managing large, complex goals. Whether they are professionals, students, or anyone with significant projects, the agent simplifies the process of goal setting and tracking by breaking down objectives into actionable tasks. This tool is particularly helpful for those who need a structured approach to achieve their goals but may be overwhelmed by the scale or complexity of the tasks involved.

By utilizing the SMART framework, the agent ensures that goals are Specific, Measurable, Achievable, Relevant, and Time-bound, making it easier for users to define and pursue their objectives effectively. The integration with Google Suite allows users to sync their plans and tasks, ensuring that they are reminded of their responsibilities and deadlines, leading to improved productivity and a better ability to manage time.

#### Impactfulness
Taskbreakdown positively impacts users by enhancing their ability to achieve personal and professional goals. By providing a clear and structured plan, it reduces the mental burden associated with planning and task management. The tool promotes better time management and goal achievement, contributing to users' overall well-being and success.

In addition, Taskbreakdown’s integration with widely-used tools like Google Calendar and Google Tasks means it can seamlessly fit into users’ existing workflows, making it easier to adopt and more likely to be used consistently. This ease of integration and use makes the agent a valuable tool for improving productivity and reducing stress related to goal management.

### Features
1. Gets input from user, and ensures it follows the SMART framework.
2. Uses Gemini Flash 1.5 to answer the prompt(if it adheres to the SMART framework).
3. Uses postgres to store conversations. 
4. streamlit is used as the web interface. 
5. Older chats are summarised, model has exact past 5 chat context.
6. Plans can be synced to Google Calendar. 
7. Tasks can be synced to Google Tasks.

### Instructions

1. The Agent follows the [SMART](https://www.atlassian.com/blog/productivity/how-to-write-smart-goals) framework to help define goals.
2. Being specific and giving supporting details will help to curate a personalised plan.
3. Set Timeline dates, and schedule time to help create a more accurate timeline. 
4. Timelines **must** be set in order to generate plans, and to sync to calendar. 
5. The agent generates a summary of older messages every so often (after every 5000 Tokens), and preserves newer messages for precise context.
6. You can see if a summary has been generated, by toggling the summary button.
7. If a summary hasn't been generated, the agent uses all previous messages as context. 
8. Currently the summary can't be edited.
9. The agent only *remembers* the latest summary (if present) and the messages post it.
10. Delete chat in the side bar can be used to delete all chat interactions with the agent.
11. Delete summary in the side bar, deletes all summaries.

### How to Use
1. You can view the live app by going to https://taskbreakdown.streamlit.app/, and follow the instructions on How to begin.

#### Getting Started in local

To run this project in local, follow these steps:

1. **Clone the repository:**
   ```
   git clone https://github.com/yourusername/ToDoListAgent.git
   ```
2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
3. **Set up Google API integration:**
   - Obtain your [Google API credentials](https://aistudio.google.com/app/apikey) and copy it.
4. **Set up streamlit secrets:**
Setup google console project details, database url, and google api in streamlit `secrets.toml` file following the [Streamlit](https://docs.streamlit.io/develop/api-reference/connections/secrets.toml) in folder structure and use the following template.
    ```
    message_rate_limit = 10 
    timeframe_in_mins = 60
    database_url = 'postgres://xxxx.us-east-1.rds.amazonaws.com:5432/xxxx'
    [google_oauth] # Setup console project and details here
        redirect_uris =["http://localhost:8501"]
        client_id = ""
        project_id = ""
        auth_uri = ""
        token_uri = ""
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_secret = ""
    [api_keys]
    key_1 = '' #Paste the key from the previous step
    ```

5. **Run the app:**
   ```
   streamlit run Home.py
   ```

### Future Enhancements
- Add more granular control over task breakdowns.
- Improve the natural language processing capabilities.
- Conisder adding multimodality and Zero shot audio detection for feedback using https://github.com/coqui-ai/TTS
- Add dynamic planning to the tool based on user completing the tasks set

