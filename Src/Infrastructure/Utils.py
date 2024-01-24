# utils.py

from Src.Models.Models import Centre, CentreUpload, Night


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
    


def GetRecordingIdentifierForUpload(upload:CentreUpload, centre:Centre):
    # ar = AuthenticationRepository()
    upload.Centre = centre
    returningFlag = "-F" if upload.IsFollowup else ""
    return f"{upload.Centre.Prefix}{str(upload.Centre.MemberNumber).zfill(2)}-{str(upload.RecordingNumber).zfill(3)}{returningFlag}"

def GetRecordingIdentifierForNight(night: Night, centre:Centre, upload:CentreUpload):
    # ar = AuthenticationRepository()
    night.Upload.Centre = centre #upload.Centre #ar.GetCentreById(upload.CentreId)
    night.Upload = upload#ar.GetUploadById(night.UploadId) #self.GetUploadById(night.UploadId)
    returingFlag = "-F-" if night.IsFollowup else "-" 
    return f"{night.Upload.Centre.Prefix}{str(night.Upload.Centre.MemberNumber).zfill(2)}-{str(night.Upload.RecordingNumber).zfill(3)}{returingFlag}{str(night.NightNumber).zfill(2)}"
