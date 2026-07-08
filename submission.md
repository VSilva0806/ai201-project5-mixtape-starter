### Codebase Map
models.py defines 5 SQLAlchemy models: User, Tag, Song, ListeningEvent, Rating, Playlist, and Notification. The ListeningEvent model logs a single play of a song by a user

Data Flow - A user requests activity feed from friends. A GET /feed/<user_id>/activity requrest hits activity() in routes/feed.py, which calls the get_activity_feed(user_id) in services/feed_service.py. That function loads the user, gets their friends from the friendships table, queries the most recent ListeningEvent rows from those friends, and for each event fetches the friend's User and the Song to build a dict. 

### Root Cause Analysis
Issue #1: My listening streak keeps resetting{
    Reproduction: I asked Claude AI to generate a user object with an arbitrary listening streak value and setting the current day as Monday. For each consecutive day I tested, I made sure to increment the streak to make sure the streak was not resetting due to a gap. After repeatedly testing the update_listening_streak function in streak_service.py, I identified the bug to occur when the current day was Sunday. The streak resetting when clearly it was not supposed to. 
    
    Root Cause: The bug was located in that specific function. I then asked Claude AI to look at that the update_listening_streak function and diagnose it. It claimed the error occured due to this specific comparison: today.weekday() != 6, where today.weekday() returns Sunday. The spec specifies that streaks only increment when a user listens yesterday and today, and resets when a user does not maintain that consecutive flow. More importantly, it does not specify a day-of-week condition, so that condition should not have existed at all. I was then confident that I found the right place for it.

    Fix: I simply removed the condition and retested the function using the same methods during the reproduction step. I verified that user streak updated Sundays now by testing test_streaks.py and confirming streaks were being updated on that day. This change ensured that no comparison was being made based on a specific day, and only restricted a comparison to determine if the user had a gap in their streak, which is what the spec is looking for. To ensure, I did not break any further functions, I also tested the get_streak() function and it worked flawlessly.
}