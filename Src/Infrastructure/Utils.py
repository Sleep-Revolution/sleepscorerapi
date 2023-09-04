# utils.py

def format_last_logged_in(last_login, request_time):
    if last_login:
        last_login = last_login.replace(tzinfo=request_time.tzinfo)
        now = request_time
        time_difference = now - last_login
        days = time_difference.days
        years = days // 365
        days = days % 365
        hours = time_difference.seconds // 3600
        minutes = (time_difference.seconds % 3600) // 60
        time_ago = []

        if years > 0:
            time_ago.append(f"{years} year{'s' if years > 1 else ''}")
        if days > 0:
            time_ago.append(f"{days} day{'s' if days > 1 else ''}")
        if hours > 0:
            time_ago.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes > 0:
            time_ago.append(f"{minutes} minute{'s' if minutes > 1 else ''}")

        if time_ago:
            time_ago.append("ago.")
        
        formatted_time_ago = ' '.join(time_ago)
        formatted_last_login = f"{last_login.strftime('%Y-%m-%d %H:%M')} - {formatted_time_ago}"
        return formatted_last_login
    else:
        return "Never logged in."