### Codebase Map
models.py defines 5 SQLAlchemy models: User, Tag, Song, ListeningEvent, Rating, Playlist, and Notification. The ListeningEvent model logs a single play of a song by a user

Data Flow - A user requests activity feed from friends. A GET /feed/<user_id>/activity requrest hits activity() in routes/feed.py, which calls the get_activity_feed(user_id) in services/feed_service.py. That function loads the user, gets their friends from the friendships table, queries the most recent ListeningEvent rows from those friends, and for each event fetches the friend's User and the Song to build a dict. 

### Root Cause Analysis
Issue #1: My listening streak keeps resetting{
    Reproduction: I asked Claude AI to generate a user object with an arbitrary listening streak value and setting the current day as Monday. For each consecutive day I tested, I made sure to increment the streak to make sure the streak was not resetting due to a gap. After repeatedly testing the update_listening_streak function in streak_service.py, I identified the bug to occur when the current day was Sunday. The streak resetting when clearly it was not supposed to. 
    
    Root Cause: The bug was located in that specific function. I then asked Claude AI to look at that the update_listening_streak function and diagnose it. It claimed the error occured due to this specific comparison: today.weekday() != 6, where today.weekday() returns Sunday. The spec specifies that streaks only increment when a user listens yesterday and today, and resets when a user does not maintain that consecutive flow. More importantly, it does not specify a day-of-week condition, so that condition should not have existed at all. I was then confident that I found the right place for it.

    Fix: I simply removed the condition and retested the function using the same methods during the reproduction step. I verified that user streak updated Sundays now by testing test_streaks.py and confirming streaks were being updated on that day. This change ensured that no comparison was being made based on a specific day, and only restricted a comparison to determine if the user had a gap in their streak, which is what the spec is looking for. To ensure, I did not break any further functions, I also tested the get_streak() function and it worked flawlessly.
}

Issue #2: Friends Listening Now shows people from yesterday{
    Reproduction: I asked Claude AI to generate two user objects, both friends, with user 2 having a playlist. I asked it to set user 2's listened_at variable under ListeningEvent to 24 hours ago to an arbitrary song from playlist. I ran the get_friends_listening_now function located in feed_service.py for user 1 and received user 2's most recent song and the time it was listened to (24 hours ago). 

    Root Cause: After testing get_friends_listening_now, I hypothesized that the bug was present in there. I opened the file and noticed the recent_events object where ListeningEvent was queried from user 2 as well listed_at being filtered based on a cutoff. The line: cutoff = datetime.now(timezone.utc) - RECENT_THRESHOLD implied that the cutoff is a 24 hour window: now - 24h. The function only generates outputs based on the last 24 hours, and not a calendar day boundary, so it did not strictly mean "today". The cutoff needs to be modified. 

    Fix: To fix the issue, I needed to alter cutoff such that the boundary is midnight (12:00 AM) of the current day. Changing the line that was causing the issue to: cutoff = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time(), tzinfo=timezone.utc) which sets the cutoff to midnight of current day, so the condittion listened_at >= cutoff only picks up events from today, and anything from yesterday, no matter how recent is excluded. Additionlly, we remove the line: RECENT_THRESHOLD = timedelta(hours=24) and import timedelta as it is not used anywhere in the new line of code. To ensure the big was fixed, I asked Claude to create another user object that was friends with user 1 and had its listened_at variable set to today. I ran the function again with user 1 and it successfully ouputed only user 3's song and recent time listened. Furthermore, I tested get_activity_feed to ensure the function would not be affected, and thankfully it was not.


}