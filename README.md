# ToDoListAgent

This is a PoC for a todolist agent, which breaks down big goals into smaller tasks. This is a very simple PoC. Integrated memory into conversations now.

### Features:-
1. Gets input from user, and ensures it follows the SMART framework.
2. Uses Gemini Flash 1.5 to answer the prompt(if it adheres to the SMART framework).
3. Uses postgres as database to store chat 
4. Uses streamlit as an interface. 
5. Older chats are summarised, model has exact past 5 chat context.
6. Plans can be synced to calendar. 
7. Plans can be synced to Google Tasks via chat.

#### Instructions

1. The Agent follows the [SMART framework](https://www.atlassian.com/blog/productivity/how-to-write-smart-goals) to help define goals.
2. Being specific and giving supporting details will help to curate a personalised plan.
3. Set Timeline dates, and schedule time to help create a more accurate timeline. 
4. Timelines **must** be set in order to generate plans, and to sync to calendar. 
5. The agent generates a summary of older messages every so often (after every 5000 Tokens), and preserves newer messages for precise context.
6. You can see if a summary has been generated, by toggling the summary button.
7. If a summary hasn't been generated, the agent uses all previous messages as context. 
8. Currently the summary can't be edited.
10. The agent only *remembers* the latest summary (if present) and the messages post it.
11. Delete chat in the side bar can be used to delete all chat interactions with the agent.
12. Delete summary in the side bar, deletes all summaries.
