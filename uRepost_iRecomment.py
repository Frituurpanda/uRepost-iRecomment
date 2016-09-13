import praw
from oauth import OAuth2Util
from oauth import OAuthTokenRequest
from urlparse import urlparse
from pymongo import MongoClient
import datetime
import time
import kdapi
import traceback
import random

def CallKdapi(SearchUrl):
    itemDict = kdapi.check(SearchUrl)
    itemList = itemDict['output']
    itemTime = itemDict['time']
    length = len(itemList)
    if length == 0:
        return {'ID': 'Empty'}
    if length == 1:
        if itemList[0].similarity == None:
            return {'ID': 'Empty'}
    score = 0
    url = None
    for item in itemList:
        if item.similarity != None:
            if item.similarity > 98:
                if score < item.score:
                    score = item.score
                    url = item.link
    if url == None:
        return {'ID': 'Empty'}
    if score < 30:
        return {'ID': 'Empty'}

    FirstSplitUrl = url.split("/comments/")
    SecondSplitUrl = FirstSplitUrl[1].split("/")
    SubmissionID = SecondSplitUrl[0]
    return {'ID': SubmissionID}

def Main():
    print("-------------------------------------------------------------------------------------------------")
    print(time.strftime('%X')+": Started Main(): " + OAuthTokenRequest.printdebuglines())
    print("-------------------------------------------------------------------------------------------------")
    user_agent = 'Post Smart Comments see uri for the source'
    r = praw.Reddit(user_agent)
    o = OAuth2Util.OAuth2Util(r)
    mongoUrl = "mongodb://localhost:27017/"
    client = MongoClient(mongoUrl)
    db = client.CheckList

    # Removing all posts that are downvoted below 1point
    removeDownvotedPosts(r)
    # checking the checkDB in MongoDB. Refreshing when needed.
    lastidlist, lastids = initialLastidSetup(db)
    # returns random subreddit from the allowedSubreddits.txt
    myline, subreddit = grabRandomSubreddit(r)

    print('uRepost_iRecomment going to filter in: /r/' + myline)
    for post in subreddit.get_hot(limit=100):
        for allTimeStamps in db.RobotTimeStamp.find():
            minutes = 60
            BeforeTimeTuple = time.mktime(allTimeStamps['value'].timetuple())
            CurrentTime = datetime.datetime.now()
            CurrentTimeTuple = time.mktime(CurrentTime.timetuple())
            TimeDiffrence = int(CurrentTimeTuple - BeforeTimeTuple) / minutes
            if TimeDiffrence >= 40:
                db.RobotTimeStamp.delete_one(allTimeStamps)
                o.refresh()
                CurrentTimeNow = {"value": datetime.datetime.now()}
                db.RobotTimeStamp.insert_one(CurrentTimeNow)
        postkey = str(vars(post)['id']) + str(vars(post)['created'])
        if postkey in lastids:
            continue
        lastids.append(postkey)

        url = urlparse(vars(post)['url'])
        imgurl = ''
        if url.netloc == 'imgur.com':
            if url.path.split('/')[1] == 'a':
                continue
            else:
                imgurl = url.geturl()

        elif url.netloc == 'i.imgur.com':
            imgurl = url.geturl()
        if imgurl == '':
            continue

        value = CallKdapi(imgurl)
        SubmissionID = value['ID']
        if SubmissionID == "Empty":
            print time.strftime('%X') + ": Checking " + vars(post)['id'] + " on KarmaDecay"
            continue

        nextlastid = vars(post)['id']
        duplicate = 0
        submission = r.get_submission(submission_id=SubmissionID)
        submissionPoster = submission.author
        CommentList = submission.comments
        print ("Using top comment from submission: " +
               "https://reddit.com/r/funny/"+ SubmissionID+
               "Posted by redditor: " + "/u/"+str(CommentList[0].author))

        TopComment = CommentList[0].body
        TopComment += '\n'
        TopComment += '\n'
        TopComment += "~ ["+str(CommentList[0].author) + "]("+CommentList[0].permalink+")"

        # Should make something with this to filter out submissions that are older than 6hours
        submission2 = r.get_submission(submission_id=nextlastid)
        submission2.replace_more_comments(limit=16, threshold=10)
        flat_comments = praw.helpers.flatten_tree(submission2.comments)

        print("---------------------------------------------------------------------------------------")
        print(TopComment)
        print("---------------------------------------------------------------------------------------")

        # Simple function to filter out bad phrases before posting the comment.
        lines = open('illegalPhrases.txt').read().splitlines()
        for word in lines:
            if word in TopComment:
                print "Found the word " + word
                duplicate = 2

        for comment in flat_comments:
            if comment.body == TopComment:
                duplicate = 1
        if duplicate == 1:
            continue
        if duplicate == 2:
            print "Discarded comment: phrase found in illegalPhrases.txt"
            break
        try:
            post.add_comment(TopComment)
            post.upvote()
        except praw.errors.APIException as PrawError:
            lastids.remove(postkey)
            print PrawError
            break
        break

    db.LastIdList.delete_one(lastidlist)
    nextIdItem = {"value": lastids}
    db.LastIdList.insert_one(nextIdItem)
    InUseValue = {"value": 1}
    db.InUse.delete_one(InUseValue)
    NotInUseValue = {"value": 0}
    db.InUse.insert_one(NotInUseValue)

    # Sleep to keep it posting evey every 5secs
    delayAfterPost(300,500)


def grabRandomSubreddit(r):
    lines = open('allowedSubreddits.txt').read().splitlines()
    myline = random.choice(lines)
    subreddit = r.get_subreddit(myline)
    return myline, subreddit


def initialLastidSetup(db):
    lastids = []
    lastidlist = None
    if "LastIdList" not in db.collection_names():
        lastids = []
        lastidlist = {"value": lastids}
        db.LastIdList.insert_one(lastidlist)
    else:
        lastidCollection = db.LastIdList
        for listofids in lastidCollection.find():
            lastidlist = listofids
            lastids = lastidlist['value']
    if "RobotTimeStamp" not in db.collection_names():
        CurrentTime = {"value": datetime.datetime.now()}
        db.RobotTimeStamp.insert_one(CurrentTime)
        print("O.refresh()")
        # o.refresh()
    return lastidlist, lastids

def delayAfterPost(low, high):
    sleepValue = random.randint(low, high)
    print 'DELAY: ', sleepValue, 'seconds'
    time.sleep(sleepValue)

def removeDownvotedPosts(r):
    user = r.get_redditor("uRepost_iRecomment")
    gen = user.get_comments()
    for thing in gen:
        if thing.score < 1:
            thing.delete()

def finalDbCheckup():
    global db, RunCollection, RunElem
    mongoUrl = "mongodb://localhost:27017/"
    client = MongoClient(mongoUrl)
    db = client.CheckList
    if "Zrunning" not in db.collection_names():
        RunningValue = {"value": 1}
        db.Zrunning.insert_one(RunningValue)
    else:
        RunCollection = db.Zrunning
        for RunElem in RunCollection.find():
            if RunElem['value'] == 1:
                print "Can't run"
                exit()

finalDbCheckup()

try:
    Main()
except:
    RunCollection = db.Zrunning
    for RunElem in RunCollection.find():
        db.Zrunning.delete_one(RunElem)
        NewRunElem = {"value": 0}
        db.Zrunning.insert_one(NewRunElem)
    traceback.print_exc()
    exit()
