We are an online game band which plays midi (band name is "吃得好好，睡得饱饱") and would like share midi among the group only. There are about 120 midis in total, which are attributed to one of the members.

Build a flask app to do the following.

## Features
1. The user can view the list of songs. And also download/edit it.
2. The user can upload a midi. 
	- It should have a unique ID (hidden from user)	
	- it should record who (the role selected) uploaded it, and when. The current role can be chosen of these three: "D", "M", "J", using a simple combobox. 
	- It should contain a song name (required, non-blank), artist(optional), version(text consisting of numerics and dots), and freeform text notes.
	- It should parse the track names of the midi file using mido library.
- Optionally, it should be able to accept a source file (in mscz format only), and also a lyric (lrc) file. All files should have max size 1MB.
3. The user can delete any song upon confirmation.
4. The user can edit the midi. Which is the same as uploading. But if in edit the user does not upload a new midi or source file or lyric file, the old one should not be overwritten.
5. The user should be able to click a button and download all midi in a zip file. The file name must be "{face_id:03}{role} - {songname}[- v{version}].mid"
If lyric is present, use the same name, but replace mid with lrc. bracket part is there only if version is non-empty. Note here face_id is not the hidden ID. It must be ordered in the time it was uploaded, ascending.


## Notes
1. No security/login is needed. Use HTTP basic authentication if you must.
2. All pages should have minimal dependencies. (best if no dependency at all)
It is okay if the page is ugly. You may use basic CSS though. The tooltips etc should be in Simplified Chinese.
3. You do not need to consider performance. It has very low traffic, and need not scale. Use simple and low resource implementation, e.g., sqlite.