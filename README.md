# ToDoListAgent

This is a proof of concept Todolist agent, it breaks down big goals into smaller tasks following the SMART framework. It integrates with google suite to sync plans and tasks to Google Calendar, and Google tasks respectively. 

### Features:-
1. Gets input from user, and ensures it follows the SMART framework.
2. Uses Gemini Flash 1.5 to answer the prompt(if it adheres to the SMART framework).
3. Uses postgres to store conversations. 
4. streamlit is used as the web interface. 
5. Older chats are summarised, model has exact past 5 chat context.
6. Plans can be synced to Google Calendar. 
7. Tasks can be synced to Google Tasks.

#### Instructions

1. The Agent follows the [SMART framework](https://www.atlassian.com/blog/productivity/how-to-write-smart-goals) to help define goals.
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

#### How to Use
1. You can view the live app by going to https://taskbreakdown.streamlit.app/, and follow the instructions on How to begin.