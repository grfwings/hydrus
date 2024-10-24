---
title: Changelog
---

# changelog

!!! note
    This is the new changelog, only the most recent builds. For all versions, see the [old changelog](old_changelog.html).

## [Version 595](https://github.com/hydrusnetwork/hydrus/releases/tag/v595)

### ugoiras

* thanks to a user who put in a lot of work, we finally have Ugoira rendering! all ugoiras will now animate using the hydrus native animation player. if the ugoira has json timing data in its zip (those downloaded with PixivUtil and gallery-dl will!), we will use that, but if it is just a zip of images (which is most older ugoiras you'll see in the wild), it'll check a couple of note names for the timing data, and, failing that, will assign a default 125ms per frame fallback. ugoiras without internal timing data will currently get no 'duration' metadata property, but right-clicking on them will show their note-based or simulated duration on the file info line
* all existing ugoiras will be metadata rescanned and thumbnail regenned on update
* technical info here: https://hydrusnetwork.github.io/hydrus/filetypes.html#ugoira
* ugoira metadata and thumbnail generation is cleaner
* a bug in ugoira thumbnail selection, when the file contains non-image files, is fixed
* a future step will be to write a special hook into the hydrus downloader engine to recognise ugoiras (typically on Pixiv) and splice the timing data into the zip on download, at which point we'll finally be able to turn on Ugoira downloading on Pixiv on our end. for now, please check out PixivUtil or gallery-dl to get rich Ugoiras
* I'd like to bake the simulated or note-based durations into the database somehow, as I don't like the underlying media object thinking these things have no duration, but it'll need more thought

### misc

* all multi-column lists now sort string columns in a caseless manner. a subscription called 'Tents' will now slot between 'sandwiches' and 'umbrellas'
* in 'favourite searches', the 'folder' name now has hacky nested folder support. just put '/' in the folder name and it'll make nested submenus. in future this will be implemented with a nicer tree widget
* file logs now load faster in a couple of ways, which should speed up UI session and subscriptions dialog load. previously, there were two rounds of URL normalisation on URL file import object load, one wasteful and one fixable with a cache; these are now dealt with. thanks to the users who sent in profiles of the subscriptions dialog opening; let me know how things seem now (hopefully this fixes/relieves #1612)
* added 'Swap in common resolution labels' to `options->media viewer`. this lets you turn off the '1080p' and '4k'-style label swap-ins for common resolutions on file descriptor strings
* the 'are you sure you want to exit the client? 3 pages say "I am still importing"' popup now says the page names, and in a pretty way, and it shows multiple messages nicer
* the primary 'sort these tags in a human way m8' routine now uses unicode tech to sort things like ß better
* the String Converter can decode 'hex' and 'base64' again (so you can now do '68656c6c6f20776f726c64' or 'aGVsbG8gd29ybGQ=' to 'hello world'). these functions were a holdover from hash parsing in the python 2 times, but I've brushed them off and cleared out the 'what if we put raw bytes in the parsing system bro' nonsense we used to have to deal with. these types are now explictly UTF-8. I also added a couple unit tests for them
* fixed an options initialisation bug where setting two files in the duplicate filter as 'not related' was updating the A file to have the B file's file modified time if that was earlier!! if you have files in this category, you will be asked on update if you want to reset their file modified date back to what is actually on disk (the duplicate merge would not have overwritten this; this only happens if you edit the time in the times dialog by hand). a unit test now checks this situation. sorry for the trouble, and thank you to the user who noticed and reported this
* the hydrus Docker package now sets the 'hydrus' process to `autorestart=unexpected`. I understand this makes `file->exit` stick without an automatic restart. it seems like commanding the whole Docker image to shut down still causes a near-instant unclean exit (some SIGTERM thing isn't being caught right, I think), but `file->exit` should now be doable beforehand. we will keep working here

### more OR preds

* the new 'replace selected with their OR' and the original 'add an OR of the selected' are now mutually exclusive, depending on whether the current selection is entirely in the active search list
* added 'start an OR with selected', which opens the 'edit OR predicate' panel on the current selection. this works if you only select one item, too
* added 'dissolve selected into single predicates', when you select only OR predicates. it does the opposite of the 'replace'
* the new OR menu gubbins is now in its own separated menu section on the tag right-click
* the indent for OR sub preds is moved up from two spaces to four

### urls

* wrote some help about the 'force page refetch' checkboxes in 'tag import options' here: https://hydrusnetwork.github.io/hydrus/getting_started_downloading.html#force_page_fetch
* added a new submenu `urls->force metadata refetch` that lets you quickly and automatically create a new urls downloader page with the selected files' 'x URL Class' urls with the tag import options set to the respective URLs' default but with these checkboxes all set for you. we finally have a simple answer to 'I messed up my tag parse, I need to redownload these files to get the tags'!
* the urls menu offers the 'for x url class' even when only one file is selected now. crazy files with fifty of the same url class can now be handled

### duplicates auto-resolution

* wrote some placeholder UI for the new system. anyone who happens to be in advanced mode will see another tab on duplicate filter pages. you can poke around if you like, but it is mostly just blank lists that aren't plugged into anything
* wrote some placeholder help too. same deal, just a placeholder that you have to look for to find that I'll keep working on
* I still feel good about the duplicates auto-resolution system. there is much more work to do, but I'll keep iterating and fleshing things out

### client api

* the new `/get_files/file_path` command now returns the `filetype` and `size` of the file
* updated the Client API help and unit tests for this
* client api version is now 73

### new build stuff

* the library updates we've been testing the past few weeks have gone well, so I am rolling them into the normal builds for everyone. the libraries that do 'fetch stuff from the internet' and 'help python manage its packages' are being updated because of some security problems that I don't think matter for us at all (there's some persistent https verification thing in requests that I know we don't care about, and a malicious URL exploit in setuptools that only matters if you are using it to download packages, which, as I understand, we don't), but we are going to be good and update anyway
* `requests` is updated from `2.31.0` to `2.32.3`
* `setuptools` is updated from `69.1.1` to `70.3.0`
* `PyInstaller` is updated from `6.2` to `6.7` for Windows and Linux to handle the new `setuptools`
* there do not appear to be any update conflicts with dlls or anything, so just update like you normally do. I don't think the new pyinstaller will have problems with older/weirder Windows, but let me know if you run into anything
* users who run from source may like to reinstall their venvs after pulling to get the new libraries too

### boring cleanup

* refactored `ClientGUIDuplicates` to a new `duplicates` gui module and renamed it to `ClientGUIDuplicateActions`
* harmonised some duplicates auto-resolution terminology across the client to exactly that form. not auto-duplicates or duplicate auto resolution, but 'duplicates auto-resolution'
* fixed some bad help link anchors
* clarified a couple things in the 'help my db is broke.txt' document
* updated the new x.svg to a black version; it looks a bit better in light & dark styles

## [Version 594](https://github.com/hydrusnetwork/hydrus/releases/tag/v594)

### misc

* fixed an error that was stopping files from being removed sometimes (it also messed up thumbnail selection). it could even cause crashes! the stupid logical problem was in my new list code; it was causing the thumbnail grid backing list to get pseudorandomly poisoned with bad indices when a previous remove event removed the last item in the list
* the tag `right-click->search` menu, on a multiple selection of non-OR predicates that exists in its entirely in the current search context, now has `replace selected with their OR`, which removes the selection and replaces it with an OR of them all!
* the system predicate parser no longer removes all underscores from to-be-parsed text. this fixes parsing for namespaces, URLs, service names, etc.. with underscores in (issue #1610)
* fixed some bad layout in the edit predicates dialog for system:hash (issue #1590)
* fixed some content update logic for the advanced delete choices of 'delete from all local file domains' and 'physically delete now', where the UI-side thumbnail logic was not removing the file from the 'all my files' or 'all local files' domains respectively, which caused some funny thumbnail display and hide/show rules until a restart rebuilt the media object from the (correct) db source
* if you physically delete a file, I no longer force-remove it from view so enthusiastically. if you are looking at 'all known files', it should generally still display after the delete (and now it will properly recognise it is now non-local)
* I may have fixed an issue with page tab bar clicks on the very new Qt 6.8, which has been rolling out this week
* wrote out my two rules for tagging (don't be perfect, only tag what you search) to the 'getting started - more tags' help page: https://hydrusnetwork.github.io/hydrus/getting_started_more_tags.html#tags_are_for_searching_not_describing

### shutdown improvements

* I cleaned up and think I fixed some SIGTERM and related 'woah, we have to shut down right now' shutdown handling. if a non-UI thread calls for the program to exit, the main 'save data now' calls are now all done by or blocked on that thread, with improved thread safety for when it does tell Qt to hide and save the UI and so on (issue #1601, but not sure I totally fixed it)
* added some SIGTERM test calls to `help->debug->tests` so we can explore this more in future
* on the client, the managers for db maintenance, quick downloads, file maintanence, and import folders now shut down more gracefully, with overall program shutdown waiting for them to exit their loops and reporting what it is still waiting on in the exit splash (like it already does for subscriptions and tag display). as a side thing, these managers also start faster on program boot if you nudge their systems to do something

### boring cleanup

* wrote some unit tests to test my unique list and better catch stupid errors like I made last week
* added default values for the 'select from list of things' dialogs for: edit duplicate merge rating action; edit duplicate merge tag action; and edit url/parser link
* moved `FastIndexUniqueList` from `HydrusData` to `HydrusLists`
* fixed an error in the main import object if it parses (and desires to skip associating) a domain-modified 'post time' that's in the first week of 1970
* reworked the text for the 'focus the text input when you change pages' checkbox under `options->gui pages` and added a tooltip
* reworded and changed tone of the boot error message on missing database tables if the tables are all caches and completely recoverable
* updated the twitter link and icon in `help->links` to X

## [Version 593](https://github.com/hydrusnetwork/hydrus/releases/tag/v593)

### misc

* in a normal search page tag autocomplete input, search results will recognise exact-text-matches of their worse siblings for 'put at the top of the list' purposes. so, if you type 'lotr', and it was siblinged to 'series:lord of the rings', then 'series:lord of the rings' is now promoted to the top of the list, regardless of count, as if you had typed in that full ideal tag
* OR predicates are now multi-line. the top line is OR:, and then each sub-tag is now listed indented below. if you construct an OR pred using shift+enter in the tag autocomplete, this new OR does start to eat up some space, but if you are making crazy 17-part OR preds, maybe you'll want to use the OR button dialog input anyway
* when you right-click an OR predicate, the 'copy' menu now recognises this as '3 selected tags' etc.. and will copy all the involved tags and handle subtags correctly
* the 'remove/reset for all selected' file relationship menu is no longer hidden behind advanced mode. it being buried five layers deep is enough
* to save a button press, the manage tag siblings dialog now has a paste button for the right-side tag autocomplete input. if you paste multiple lines of content, it just takes the first
* updated the file maintenance job descriptions for the 'try to redownload' jobs to talk about how to deal with URL downloads that 404 or produce a duplicate and brushed up a bit of that language in general
* the new 'if a db job took more than 15 seconds, log it' thing now tests if the program was non-idle at the start or end of the db job, rather than just the end. this will catch some 'it took so long that some "wake up" stuff had time to kick in' instances
* fixed a typo where if the 'other' hashes were unknown, the 'sha512 (unknown)' label was saying 'md5 (unknown)'
* file import logs get a new 'advanced' menu option, tucked away a little, to 'renormalise' their contents. this is a maintenance job to clear out duplicate chaff on an existing list after the respective URL Class rules have changed to remove something in normalisation (e.g. setting a parameter to be ephemeral). I added a unit test for this also, but let me know how it works in the wild

### default downloaders

* fixed the source time parsing for the gelbooru 0.2.0 (rule34.xxx and others) and gelbooru 0.2.5 (gelbooru proper) page parsers

### client api

* fixed the 'permits everything' API Permissions update from a couple weeks ago. it was supposed to set 'permits everything' when the existing permissions structure was 'mostly full', but the logic was bad and it was setting it when the permissions were sparse. if you were hit by this and did not un-set the 'permits everything' yourself in _review services_, you will get a yes/no prompt on update asking if you want to re-run the fixed update. if the update only missed out setting "permits everything" where it should have, you'll just get a popup saying it did them. sorry for missing this, my too-brief dev machine test happened to be exactly on the case of a coin flip landing three times on its edge--I've improved my API permission tests for future

### duplicate auto-resolution progress

* I got started on the db module that will handle duplicates auto-resolution. this started out feeling daunting, and I wasn't totally sure how I'd do some things, but I gave it a couple iterations and managed to figure out a simple design I am very happy with. I think it is about 25-33% complete (while object design is ~50-75% and UI is 0%), so there is a decent bit to go here, but the way is coming into focus

### boring code cleanup

* updated my `SortedList`, which does some fast index lookup stuff, to handle more situations, optimised some remove actions, made it more compatible as a list drop-in replacement, moved it to `HydrusData`, and renamed it to `FastIndexUniqueList`
* the autocomplete results system uses the new `FastIndexUniqueList` a bit for some cached matches and results reordering stuff
* expanded my `TemporerIntegerTable` system, which I use to do some beardy 'executemany' SELECT statements, to support an arbitrary number of integer columns. the duplicate auto-resolution system is going to be doing mass potential pair set intersections, and this makes it simple
* thanks to a user, the core `Globals` files get some linter magic that lets an IDE do good type checking on the core controller classes without running into circular import issues. this reduced project-wide PyCharm linter warnings from like 4,500 to 2,200 wew
* I pulled the `ServerController` and `TestController` gubbins out of `HydrusGlobals` into their own 'Globals' files in their respective modules to ensure other module-crawlers (e.g. perhaps PyInstaller) do not get confused about what they are importing here, and to generally clean this up a bit
* improved a daemon unit test that would sometimes fail because it was not waiting long enough for the daemon to finish. I cut some other fat and it is now four or five seconds faster too

## [Version 592](https://github.com/hydrusnetwork/hydrus/releases/tag/v592)

### misc

* the 'read' autocomplete dropdown has a new one-click 'clear search' button, just beside the favourites 'star' menu button. the 'empty page' favourite is removed from new users' defaults
* in an alteration to the recent Autocomplete key processing, Ctrl+c/Ctrl+Insert _will_ now propagate to the results list if you currently have none of the text input selected (i.e. if it would have been a no-op on the text input, we assume you wanted whatever is selected in the list)
* in the normal thumbnail/viewer menu and _review services_, the 'files' entry is renamed to 'locations'. this continues work in the left hand button of the autocomplete dropdown where you set the 'location', which can be all sorts of complicated things these days, rather than just 'file service key selector'. I don't think I'll rename 'my files' or anything, but I will try to emphasise this 'locations' idea more when I am talking about local file domains etc.. in other places going forward; what I often think of as 'oh yeah the files bit' isn't actually referring to the files themselves, but where they are located, so let's be precise
* last week's tag pair filtering in _tags-&gt;migrate tags_ now has 'if either the left or right of the pair have count', and when you hit 'Go' with any of the new count filter checkboxes hit, the preview summary on the yes/no confirmation dialog talks about it
* any time a watcher subject is parsed, if the text contains non-decoded html entities (like `&gt;`), they are now auto-converted to normal chars. these strings are often ripped from odd places and are only used for user display, so this just makes that simpler
* if you are set to remove trashed files from view, this now works when the files are in multpile local file domains, and you choose 'delete from all local file services', and you are looking at 'all my files' or a subset of your local file domains
* we now log any time (when the client is non-idle) that a database job's work inside the transaction wrapper takes more than 15 seconds to complete
* fixed an issue caused by the sibling or parents system doing some regen work at an unlucky time

### default downloaders

* thanks to user help, the derpibooru post parser now additionally grabs the raw markdown of a description as a second note. this catches links and images better than the html string parse. if you strictly only want one of these notes, please feel free to dive into _network-&gt;downloaders-&gt;defailt import options_ for your derpi downloader and try to navigate the 'note import options' hell I designed and let me know how it could be more user friendly

### parsing system

* added a new NESTED formula type. this guy holds two formulae of any type internally, parsing the document with the first and passing those results on to the second. it is designed to solve the problem of 'how do I parse this JSON tucked inside HTML' and _vice versa_. various encoding stuff all seems to be handled, no extra work needed
* added Nested formula stuff to the 'how to make a downloader' help
* made all the screenshot in the parsing formula help clickable
* renamed the COMPOUND formula to ZIPPER formula
* all the 'String Processor' buttons across the program now have copy and paste buttons, so it is now easy to duplicate some rules you set up
* in the parsing system, sidecar importer, and clipboard watcher, all strings are now cleansed of errant 'surrogate' characters caused by the source incorrectly providing utf-16 garbage in a utf-8 stream. fingers crossed, the cleansing here will actually _fix_ problem characters by converting them to utf-8, but we'll see
* thanks to a user, the JSON parsing system has a new 'de-minify json' parsing rule, which decompresses a particular sort of minified JSON that expresses multiply-referenced values using list positions. as it happened that I added NESTED formulae this week, I wonder if we will migrate this capability to the string processing system, but let's give it time to breathe

### client api

* fixed the permission check on the new 'get file/thumbnail local path' commands--due to me copy/pasting stupidly, they were still just checking 'search files' perm
* added `/get_files/local_file_storage_locations`, which spits out the stuff in _database-&gt;move media files_ and lets you do local file access _en masse_
* added help and a unit test for this new command
* the client api version is now 72

### some security/library updates

* the 'old' OpenCV version in the `(a)dvanced` setup, which pointed to version 4.5.3.56, which had the webp vulnerability, is no longer an option. I believe this means that the program will no longer run on python 3.7. I understad Win 7 can run python 3.8 at the latest, so we are nearing the end of the line on that front
* the old/new Pillow choice in `(a)dvanced` setup, which offered support for python 3.7, is removed
* I have added a new question to the `(a)dvanced` venv setup to handle misc 'future' tests better, and I added a new future test for two security patches for `setuptools` and `requests`: 
* A) `setuptools` is updated to 70.3.0 (from 69.1.1) to resolve a security issue related to downloading packages from bad places (don't think this would ever affect us, but we'll be good)
* B) `requests` is updated to 2.32.3 (from 2.31.0) to resolve a security issue with verify=False (the specific problem doesn't matter for us, but we'll be good)
* if you run from source and want to help me test, you might like to rebuild your venv this week and choose the new future choice. these version increments do not appear to be a big deal, so assuming no problems I will roll these new libraries into a 'future' test build next week, and then into the normal builds a week after

### boring code cleanup

* did a bunch more `super()` refactoring. I think all `__init__` is now converted across the program, and I cleared all the normal calls in the canvas and media results panel code too
* refactored `ClientGUIResults` into four files for the core class, the loading, the thumbnails, and some menu gubbins. also unified the mish-mash of `Results` and `MediaPanel` nomenclature to `MediaResultsPanel`

## [Version 591](https://github.com/hydrusnetwork/hydrus/releases/tag/v591)

### misc

* fixed a stupid oversight with last week's "move page focus left/right after closing tab" thing where it was firing even when the page closed was not the current tab!! it now correctly only moves your focus if you close the _current_ tab, not if you just middle click some other one
* fixed the _share-&gt;export files_ menu command not showing if you right-clicked on just one file
* cleaned some of the broader thumbnail menu code, separating the 'stuff to show if we have a focus' and 'stuff to show if we have a selection'; the various 'manage' commands now generally show even if there is no current 'focus' in the preview (which happens if you select with ctrl+click or ctrl+a and then right-click in whitespace)
* the 'migrate tags' dialog now allows you to filter the sibling or parent pairs by whether the child/worse or parent/ideal tag has actual mapping counts on an arbitrary tag service. some new unit tests ensure this capability
* fixed an error in the duplicate metadata merge system where if files were exchanging known URLs, and one of those URLs was not actually an URL (e.g. it was garbage data, or human-entered 'location' info), a secondary system that tried to merge correlated domain-based timestamps was throwing an exception
* to reduce comma-confusion, the template for 'show num files and import status' on page names is now "name - (num_files - import_status)"
* the option that governs whether page names have the file count after them (under _options-&gt;gui pages_) has a new choice--'show for all pages, but only if greater than zero'--which is now the default for new users

### some boring code cleanup

* broke up the over-coupled 'migrate tags' unit tests into separate content types and the new count-filtering stuff
* cleaned up the 'share' menu construction code--it was messy after some recent rewrites
* added some better error handling around some of the file/thumbnail path fetching/regen routines

### client api

* the client api gets a new permissions state this week: the permissions structure you edit for an access key can now be (and, as a convenient default, starts as) a simple 'permits everything' state. if the permissions are set to 'permit everything', then this overrules all the specific rules and tag search filter gubbins. nice and simple, and a permissions set this way will automatically inherit new permissions in the future. any api access keys that have all the permissions up to 'edit ratings' will be auto-updated to 'permits everything' and you will get an update saying this happened--check your permissions in _review services_ if you need finer control
* added a new permission, `13`, for 'see local paths'
* added `/get_files/file_path`, which fetches the local path of a file. it needs the new permission
* added `/get_files/thumbnail_path`, which fetches the local path of a thumbnail and optionally the filetype of the actual thumb (jpeg or png). it needs the new permission
* the `/request_new_permissions` command now accepts a `permits_everything` bool as a selective alternate to the `basic_permissions` list
* the `/verify_access_key` command now responds with the name of the access key and the new `permits_everything` value
* the API help is updated for the above
* new unit tests test all the above
* the Client API version is now 71

### client api refactoring

* the main `ClientLocalServerResources` file has been getting too huge (5,000 lines), so I've moved it and `ClientLocalServer` to their own `api` module and broken the Resources file up into core functions, the superclass, and the main verbs
* fixed permissions check for `/manage_popups/update_popup`, which was checking for pages permission rather than popup permission
* did a general linting pass of these easier-to-handle files; cleaned up some silly stuff

## [Version 590](https://github.com/hydrusnetwork/hydrus/releases/tag/v590)

### misc

* the 'check now' button in manage subscriptions is generally more intelligent and now offers questions around paused status: if _all_ the selected queries are DEAD, it now asks you if you want to resurrect them with a yes/no variant of the DEAD/ALIVE question (previously it just did it); if you are in _edit subscriptions_ and any of the selected subs are paused, it now asks you if you want to include them (and unpause) in the check now, and if not it reduces the queries examined for the DEAD/ALIVE question appropriately (previously it just did their queries, and did not unpause); in either _edit subscriptions_ or _edit subscription_, if any queries in the selection after any 'paused subs' or 'DEAD/ALIVE' filtering are paused, it asks you if you want to include (and unpause) them in the check now (previously it just did and unpaused them all)
* if you shrink the search page's preview window down to 0 size (which it will suddenly snap to, and which is a silghtly different hide state to the one caused by double-left-clicking the splitter sash), the preview canvas will now recognise it is hidden and no longer load media as you click on thumbs. previously this thing was loading noisy videos in the background etc..
* the `StringMatch` 'character set' match type now has 'hexadecimal characters' (`^[\da-fA-F]+$`) and 'base-64 characters' (`^[a-zA-Z\d+/]+={0,2}$`) in its dropdown choice
* the 'gui pages' options panel now has 'when closing tabs, move focus (left/right)', so if you'd rather move left when middle-clicking tabs etc.., you can now set it, and if your style's default behaviour is whack and never moved to the right before despite you wanting it, now you can force it; it is now explicit either way. let me know if any crazy edge-case focus logic happens in this mode with nested page of pages or whatever
* when you right-click a file, in the _share-&gt;copy hash_ menu, the md5, sha1, and sha512 hashes are now loaded from the database, usually in the milliseconds after the menu is opened, and shown in the menu labels for quick human reference. if your client does not have these hashes for the file, it says so
* the 'share' thumbnail menu is now visible on non-local files. it is severely truncated, basically just shows copy hash/file_id stuff
* wrote a 'Current Deleted Pending Petitioned' section for the Developer API to discuss how the states in the content storage system overlap and change in relation to various commands in the content update pipeline https://hydrusnetwork.github.io/hydrus/developer_api.html#CDPP It may be of interest to non-API-devs who are generally interested in what exactly the 'pending' state etc.. is
* if the file import options in a hard drive import page currently imports to an empty location context (e.g. you deleted the local file service it wanted to import to), the import page now pauses and presents an appropriate error text. the URL importers already did this, so this is the hdd import joining them
* this 'check we are good to do file work' test in the importer pages now in all cases pursues a 'default' file import options to the actual real one that will be used, so if your importer file import options are borked, this is now detected too and the importer will pause rather than fail everything in its file log
* thanks to a user, fixed a typo bug in the new multi-column list work that was causing problems when looking at gallery logs that included mis-linked log entries. in general, the main 'turn this integer into something human' function will now handle errors better

### default downloaders

* _advanced/technical, tl;dr: x.com URLs save better now._ since a better fix will take more work, the 'x post' URL class is for now set to associate URLs. this fixes the association of x.com URLs when those are explicitly referred to as source URLs in a booru post. previously, some hydrus network engine magic related to how x URLs are converted to twitter URLs (and then fx/vxtwitter URLs) to get parsed by the twitter parser was causing some problems. a full 'render this URL as this URL' system will roll out in future to better handle this situation where two non-API URLs can mean the same thing. this will result in some twitter/x post URL duplication--we'll figure out a nice merge later!

### duplicate auto-resolution tech

* I have written the first skeleton of the `MetadataConditional` object. it has a rule based on a system predicate (like 'width &gt; 400px') and returns True/False when you give it a media object. this lego-brick will plug into a variety of different systems in future, including the duplicate auto-resolution system, with a unified UI
* system predicates cannot yet do this arbitrarily, so it will be future work to fill out this code. to start with, I've just got system:filetype working to ultimately effect the first duplicate auto-resolution job of 'if pixel duplicates and one is jpeg, one png, then keep the jpeg'
* add some unit tests to test this capability

### boring search object code decoupling

* refactored the main `Predicate` object and friends to the new `ClientSearchPredicate`
* refactored the main `NumberTest` object and friends to the new `ClientNumberTest`
* refactored the main `TagContext` object and friends to the new `ClientTagContext`
* refactored the main `FileSearchContext` object and friends to the new `ClientSearchFileSearchContext`
* moved some other `ClientSearch` stuff to other places and renamed the original file to `ClientSearchFavourites`; it now just contains the favourite searches manager
* some misc cleanup around here. some enums had bad names, that sort of thing

## [Version 589](https://github.com/hydrusnetwork/hydrus/releases/tag/v589)

### misc

* the similar-files search maintenance code has an important update that corrects tree rebalancing for a variety of clients that initialised with an unlucky first import file. in the database update, I will check if you were affected here and immediately optimise your tree if so. it might take a couple minutes if you have millions of files
* tag parent and sibling changes now calculate faster at the database level. a cache that maintains the structure of which pairs need to be synced is now adjusted with every parent/sibling content change, rather than regenerated. for the PTR, I believe this will save about a second of deferred CPU time on an arbitrary parent/sibling change for the price of about 2MB of memory, hooray. fingers crossed, looking at the _tags-&gt;sibling/parent sync-&gt;review_ panel while repository processing is going on will now be a smooth-updating affair, rather than repeated 'refreshing...' wait-flicker
* the 'the pairs you mean to add seem to connect to some loops' auto-loop-resolution popup in the manage siblings/parents dialogs will now only show when it is relevent to pairs to be added. previously, this thing was spamming during the pre-check of the process of the user actually breaking up loops by removing pairs
* added an item, 'sync now', to the _tags-&gt;sibling/parent sync_ menu. this is a nice easy way to force 'work hard' on all services that need work. it tells you if there was no work to do
* reworked the 'new page chooser' mini-dialog and better fixed-in-place the intended static 3x3 button layout
* showing 'all my files' and 'local files' in the 'new page chooser' mini-dialog is now configurable in _options-&gt;pages_. previously 'local files' was hidden behind advanced mode. 'all my files' will only ever show if you have more than one local files domain
* when a login script fails with 401 or 403, or indeed any other network error, it now presents a simpler error in UI (previously it could spam the raw html of the response up to UI)
* generally speaking, the network job status widget will now only show the first line of any status text it is given. if some crazy html document or other long error ends up spammed to this thing, it should now show a better summary
* the 'filename' and 'first/second/etc.. directory' checkbox-and-text-input controls in the filename tagging panel now auto-check when you type something in
* the 'review sibling/parent sync' and 'manage where tag siblings and parents apply' dialogs are now plugged into the 'default tag service' system. they open to this tab, and if you are set to update it to the last seen, they save over the value on changes

### default downloaders

* fixed the default safebooru file page parser to stop reading undesired '?' tags for every namespace (they changed their html recently I think)
* catbox 'collection' pages are now parseable by default

### boring list stuff

* fixed an issue with showing the 'manage export folders' dialog. sorry for the trouble--in my list rewrite, I didn't account for one thing that is special for this list and it somehow slipped through testing. as a side benefit, we are better prepped for a future update that will support column hiding and rearranging
* optimised about half of the new multi-column lists, as discussed last week. particularly included are file log, gallery log, watcher page, gallery page, and filename tagging panel, which all see a bunch of regular display/sort updates. the calls to get display data or sort data for a row are now separate, so if the display code is CPU expensive, it won't slow a sort
* in a couple places, url type column is now sorted by actual text, i.e. file url-gallery url-post url-watchable url, rather than the previous conveniently ordered enum. not sure if this is going to be annoying, so we'll see
* the filename tagging list no longer sorts the tag column by tag contents, instead it just does '#''. this makes this list sort superfast, so let's see if it is super annoying, but since this guy often has 10,000+ items, we may prefer the fast sort/updates for now

### client api

* the `/add_files/add_file` command now has a `delete_after_successful_import` parameter, default false, that does the same as the manual file import's similar checkbox. it only works on commands with a `path` parameter, obviously
* updated client api help and unit tests to test this
* client api version is now 70

### more boring cleanup

* I cleaned up a mash of ancient shortcut-processing jank in the tag autocomplete input and fixed some logic. everything is now processed through one event filter, the result flags are no longer topsy-turvy, and the question of which key events are passed from the text input to the results list is now a simple strict whitelist--basically now only up/down/page up/page down/home/end/enter (sometimes)/escape (sometimes) and ctrl+p/n (for legacy reasons) are passed to the results list. this fixes some unhelpful behaviour where you couldn't select text and ctrl+c it _unless_ the results list was empty (since the list was jumping in, after recent updates, and saying 'hey, I can do ctrl+c, bro' and copying the currently selected results)
* the key event processing in multi-column lists is also cleaned up from the old wx bridge to native Qt handling
* and some crazy delete handling in the manage urls dialog is cleaned up too
* the old `EVT_KEY_DOWN` wx bridge is finally cleared out of the program. I also cleared out some other old wx event definitions that have long been replaced. mostly we just have some mouse handling and window state changes to deal with now
* replaced many of my ancient static inheritance references with python's `super()` gubbins. I disentangled all the program's multiple inheritance into super() and did I think about half of the rest. still like 360 `__init__` lines to do in future
* a couple of the 'noneable text' widgets that I recently set to have a default text, in the subscription dialogs, now use that text as placeholder rather than actual default. having 'my subscription' or whatever is ok as a guide, but when the user actually wants to edit, having it be real text is IRL a pain
* refactored the repair file locations dialog and manage options dialog and new page picker mini-dialog to their own python files

## [Version 588](https://github.com/hydrusnetwork/hydrus/releases/tag/v588)

### fast new lists

* tl;dr: big lists faster now. you do not need to do anything
* every multi-column list in the program (there's about 75 of them) now works on a more sophisticated model (specifically, we are updating from QTreeWidget to QTreeView). instead of the list storing and regenerating display labels for every single row of a table, only the rows that are currently in view are generally consulted. sort events are similarly extremely fast, with off-screen updates virtualised and deferred
* in my tests, a list with 170,000 rows now sorts in about four seconds. my code is still connected to a non-optimised part of the old system, so I hope to improve gains with background cleanup work in coming months. I believe I can make it work at least twice as fast in places, particularly in initialisation
* multi-column lists are much better about initialising/migrating the selection 'focus' (the little, usually dotted-line-border box that says where keyboard focus is) through programmatic insertions and deletes and sorts
* column headers now show the up/down 'sort' arrows using native style. everything is a bit more Qt-native and closer to C++ instead of my old custom garbage
* none of this changes anything to do with single-column lists across the program, which are still using somewhat jank old code. my taglist in particular is an entirely custom object that is neat in some ways but stuck in place by my brittle design. the above rewrite was tricky in a couple of annoying ways but overall very worth doing, so I expect to replicate it elsewhere. another open choice is rewriting the similarly entirely custom thumbnail canvas to a proper Qt widget with a QLayout and such. we'll see how future work goes

### misc

* fixed the 'show' part of 'pages-&gt;sidebar and preview panels-&gt;show/hide sidebar and preview panel', which was busted last week in the page relayout cleanup
* I think I fixed the frame of flicker (usually a moment of page-wide autocomplete input) you would sometimes get when clicking a 'show these files' popup message files button
* fixed the new shimmie parser (by adding a simpler dupe and wangling the example urls around) to correctly parse r34h tags
* I think I may have fixed some deadlocks and/or mega-pauses in the manage tag parents/siblings dialogs when entering pairs causes a dialog (a yes/no confirmation, or the 'enter a reason' input) to pop up
* I think I have fixed the 'switch between fullscreen borderless and regular framed window' command when set to the 'media_viewer' shortcut set. some command-processing stuff wasn't wired up fully after I cleared out some old hacks a while ago
* the manage tag parents dialog has some less janky layout as it is expanded/shrunk
* if similar files search tree maintenance fails to regenerate a branch, the user is now told to try running the full regen
* the full similar files search tree regen now filters out nodes with invalid phashes (i.e. due to database damage), deleting those nodes fully and printing all pertinent info to the log, and tells the user what to do next
* you can now regen the similar files search tree on an empty database without error, lol
* while I was poking around lists, I fixed a bit of bad error handling when you try to import a broken serialised data png to a multi-column list

### client api

* the `/get_files/search_files` command now supports `include_current_tags` and `include_pending_tags`, mirroring the buttons on the normal search interface (issue #1577)
* updated the help and unit tests to check these new params
* client api version is now 69

## [Version 587](https://github.com/hydrusnetwork/hydrus/releases/tag/v587)

### all misc this week

* I made a second stupid typo last week. it raised an error when trying to open the 'manage tag display and search' dialog! it was fixed thanks to a user
* the current local file domains of a file (e.g. 'my files') are now simply listed in the top-right hover window, above any remote locations or URLs. I think I'm going to make these checkboxes or something in future so we can have one-click file migrations
* if you set up a _share-&gt;export files_ job and one of the internal files is actually missing, the error message now tells you to go check for missing files using the database file maintenance stuff
* if an export files job that is set to delete internal files breaks half way through, the routine now makes sure only to delete what was actually successful
* subscriptions now catch program shutdown signals better. previously, this was being handled as an unknown error and delay times and error texts were being set. it now just closes cleanly, no worries
* the command palette should now match case-insensitively
* I _may_ have fixed a false-positive delete-lock report ('could not delete files xyz because of delete lock') that can happen in the duplicate filter. also, the 'unable to delete file' popup that happens in this case now quietly prints the current stack to log, which I would be interested in seeing
* I believe I have fixed several of the false-positive 'hey it looks like you edited this parser, are you sure you want to cancel?' confirmations in the edit parser dialog
* the automatic datestring parsing routine should now be more resilient against english datestrings when the locale differs significantly (it seems if the locale requires a 24-hour clock, it may be a problem for AM/PM time strings)
* cleaned up some ancient-and-terrible sash-sizing code that manages the three resizable panels of each media results page. hopefully I fixed an issue in Docker and other places where the media page could spawn with a 0-pixel-wide thumbnail panel
* fixed a weird/stupid bug with the new scanbar that would sometimes start giving errors on media transitions because it couldn't find its media parent
* improved how a core UI job waits on the database to be free. it now uses just a little less CPU/fewer thread switches
* improved how that same UI job waits on the pubsub system to be free, same deal
* since they reversed the API click-through requirement, removed the 8chan TOS click-through login script from the defaults. existing users will see it set to non-active. 8chan thread watching should work out the box again

### new list stuff

* I worked on a new multi-column list class that uses a more intelligent data model. I basically finished it, but I will not launch it yet--it needs a bunch more testing and debugging
* as a side thing, a variety of list display update calls, even on the old list, are now a little faster

## [Version 586](https://github.com/hydrusnetwork/hydrus/releases/tag/v586)

### faster sibling/parent fetching

* for a while, some users have had extremely slow selective sibling/parent fetching, usually manifesting in sibling/parent display calculation or autocomplete results decoration. with last week's new sibling/parent async dialogs, the problem was suddenly exposed further. thankfully, this situation was a useful testbed, and I have made multiple updates that I believe should remove much if not all of the unreasonable megalag. if you saw 30 second delays in the new sibling/parent dialogs, let me know how this all works for you. the ideal is that simple stuff takes 50ms, and something that behind the scenes might have 14,000 rows (stuff like 'gender:female' in parents can sprawl like this), should be no more than a couple of seconds on first fetch, and much faster thereafter
* fixed up a bad preload routine in the new sibling/parents dialogs that was doing busy wait and eating up bunch of extra CPU
* simplified the main sibling/parent chain-following search
* removed all the UNION queries from the sibling and parent modules; maybe I'll reintroduce it one day, but it doesn't really save much time and can limit search cleverness by making the query planner go bananas
* further optimised the recursive loop of this search, particularly for parents which has to do some additional sibling ideal lookup stuff to join chains coupled by sibling relations
* overhauled the tag parents/siblings storage tables from the old two-table combined format to dynamic sub-tables separated by both service_id and status. this makes parent and sibling storage a little more spammy but also significantly smaller and more simple, and it ensures search code is always working on clean, efficient, and fast indices, which means no more crazy search variability no matter how we work with these things. as a side benefit, I relaxed the logic so the siblings storage is now capable of storing more 'conflicting' pairs, no longer enforcing an old overly optimistic 1-&gt;n rule (which was probably the cause of some 'I see a different loop to you, how do we debug this?' frustration amongst PTR users comparing siblings). **if you sync with the PTR, the database update to v586 will take a few seconds this week**
* there may still be a single slow-the-first-time query for parents in a PTR-syncing client, simply because certain joiner tags like 'gender:female' merge many groups together. I am considering what to do here, so let's see how it goes
* plugged a hole in the 'fetch relevant sibling/parent pairs' routine where if you triggered two searches at the same time with overlapping tags (e.g. let's say things were working super slow), the second routine was not waiting correctly for the results and the main EnterPairs method was raising a 'hey, this should not have happened' message

### misc

* fixed an issue in the media scanbar where if you had it set to hide completely when the mouse is not over it, then if the media was paused while the scanbar was hidden, the scanbar would unhide in a blank state until you clicked it. further, the anti-show/hide-flicker tech is improved here
* when you open up a tag search page from the media viewer's tag list (e.g. by middle-clicking a tag), the original context's file domain is now preserved. if you open a media viewer on 'my files', then new search pages from the taglist will now be in 'my files' (it was previously defaulting to the safe backstop of 'all my files')
* the client now forces a full tag presentation refresh when deleting a service or resetting a tag respository's processing. this should clear up some ghost tags we were seeing here without having to restart
* the master decoding call used by the parsing system (which does 'convert this raw I/O input to nice unicode text') will now implicitly trust encoding provided by the network engine if that encoding is exlpcitly set in the response (previously it would defer to `chardet` if that was more confident), and if the given document is encoded incorrectly, it will replace bad characters with special question marks
* when an import options button handles only one options type (e.g. the tag import options button in edit subscription query panel, where it also only does 'additional tags' stuff, or the file import buttons in _options-&gt;importing_), the button now previews what it does in its label. the way these summary statements is produced (and, more generally, used in the button's tooltips) is also tightened up--there is less newline spam, and smaller changes will collect into a single line
* because of some remaining display bugs, if your Qt's default style would be the new 'windows11' (which is true for Win Qt 6.7.x), I am saying 'no' and switching it back to 'windowsvista'
* I removed a 'do not allow an import folder to run for more than an hour' timer. this was an undocumented backstop hack and was messing with 'do not run regularly' import folders that operate on 100,000+ file mega folders. if you want a gigantic import job, you got it
* silenced some spammy network reporting--the main file and gallery import objects were printing tracebacks to the log on many failure states, which in some unusual SSL/Connection errors was resulting in a whole lot of html garbage being dumped to the log
* improved the error message when an audio file's duration cannot be determined
* tweaked the 'help my db is broke.txt' document
* fixed up some weird tag application logic: the client db and the tags manager object now agree that you can, through programmatic means, petition content that does not yet exist (e.g. to insert deleted rows from an external source), and thus if you wish to _pend_ content, we need to check for conflicting pre-existing _petitioned_ content, and _vice versa_. the manage tags dialog similarly understands this, but it won't offer the 'petition' action when things do not yet exist because this is a bit technical and best left to programmatic editing like the Client API or migrate tags window. it was previously possible to create a situation where a file had both pending and petitioned data that did not yet exist (`tag (+1) (-1)`, lol)--this should no longer be possible. if you got into this situation and want to clean it up, try doing a search for 'system:has tags' on just 'include pending tags', and then ctrl+a-&gt;F3 your results and then ctrl+a the taglist and hit enter on it--you should be given an option to 'undo petition on x tags' and clear it all up in one go

### noneable defaults

* all of the 'noneable' (nullable) integer widgets (where you have an editable number with a 'no limit' checkbox beside it) now initialise with an appropriate default value in the integer box, even if they otherwise initialise in the 'None' state. previously, these would usually sit at '1' on the number side, when starting at None, meaning you'd have to guess an appropriate number when switching from None to something concrete. all the noneable integers in the options dialog now initialise with their respective options default
* similarly, most of the noneable text input boxes now initialise with a suggested value in the text box even if the initial value for that dialog or whatever is the 'None' checkbox ticked
* and all of the nullable bytes widgets (a number-of-bytes value and then 'no limit' checkbox) similarly now initialise with a default value. they kind of already did, but it is better formalised now
* dejanked some nullable int widget code design. the ones that have two dimensions are now their own class

### client api

* thanks to a user, `/get_files/render` has new parameters that let you now ask for a png/jpeg/webp rather than just png, at a certain quality, and a certain resolution
* added the 'sort by pixel hash hex and blurhash' sort_type definitions to the help for `/get_files/search_files` and noted that you can asc/desc these too
* `/add_files/add_file` now accepts a 'file domain' to set a custom import destination (just like in file import options). obviously you can only set local file domains here
* `/add_urls/add_url` also now accepts a 'file domain', same deal. it will select/create a new url downloader page with non-default file import options set with that import destination
* updated the help and unit tests to reflect the above
* added `/add_urls/migrate_files` to copy files to new local file domains (essentially doing _files-&gt;add to_ from the thumbnail menu)
* with (I think) all multiple local file service capabilities added to the Client API, issue #251 is finally ticked off
* client api version is now 68
