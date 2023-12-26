import streamlit as st
from PIL import Image
from googleapiclient.discovery import build
import pandas as pd
api_key="xxx" #Can generate from Google API
youtube=build('youtube',"v3",developerKey=api_key)
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import mysql.connector
mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="Malar", 
)
print(mydb)
mycursor = mydb.cursor(buffered=True)
import pymysql
from sqlalchemy import create_engine 
##SQL Data insertion 
Engine=create_engine("mysql+pymysql://root:Malarlocalhost/youtube")


#Primary Program
def youtubedetails(channelid):
    c=channelstats(youtube,channelid)
    v=videstats(youtube,c[1])
    p=playlistdetails(youtube,channelid)
    co=commentdetails(youtube,v[0])
    Final={"Channel_id":channelid,"Channelstats":c[0],"Videostats":v[1],"PlaylistStats":p,"Commentstats":co}
    return Final

##Channel Details
def channelstats(youtube,channelid):
    request= youtube.channels().list(
          part="snippet,contentDetails,statistics,status",
          id=channelid)

    response=request.execute()
    c=[]
    channeldata=dict(Channelname=response["items"][0]["snippet"]["title"],
                     channel_id=channelid,
                    channeldescription=response["items"][0]["snippet"]["description"],
                    channelviews=response["items"][0]["statistics"]["viewCount"],
                    channel_video_count=response["items"][0]["statistics"]["videoCount"],
                    channel_subscribers_count=response["items"][0]["statistics"]["subscriberCount"],
                    channelstatus=response["items"][0]["status"]["privacyStatus"],
                    channeltype=response["kind"])
    Playlist_id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    c.append(channeldata)
    return c,Playlist_id

##Query for videoid
def videstats(youtube,Playlist_id):
    import re
    next_page_token= None
    videoid=[]
    while 1:
        request= youtube.playlistItems().list(
              part="contentDetails",
              playlistId=Playlist_id,
              maxResults=50,
              pageToken=next_page_token)
        response=request.execute()
        videoid=videoid+response["items"]
        next_page_token=response.get("nextPageToken")
        if next_page_token is None:
            break            
    vid=[]
    for i in range(len(videoid)):
        vid.append(videoid[i]["contentDetails"]["videoId"])

    videoDetails=[]
    for i in vid:
        request=youtube.videos().list(
                 part='statistics,snippet,contentDetails',
                 id=i)
        response=request.execute()
        
        a=response["items"][0]["contentDetails"].get("duration").replace("PT","")
        li=[]
        if a.count("H")== 1:
          b=a.find("H")
          li.append(a[:b])
        else:
          li.append("00")        
        if a.count("M")== 1:
          c=a.find("M")
          if a[c-2].isdigit()==1:
            li.append(a[c-2:c])
          else:
            li.append(a[c-1])
        else:
          li.append("00")        
        if a.count("S")== 1:
          d=a.find("S")
          if a[d-2].isdigit()==1:
            li.append(a[d-2:d])
          else:
            li.append(a[d-1])
        else:
          li.append("00")
        dur=":".join(li)
        V=dict(id=response["items"][0]["id"],
               channelid=response["items"][0]["snippet"]["channelId"],
               definition=response["items"][0]["contentDetails"].get("definition"),
               duration=dur,
               dimension=response["items"][0]["contentDetails"].get("dimension"),
               Videotitle=response["items"][0]["snippet"].get("title"),
               description=response["items"][0]["snippet"].get("description"),
               Published_Date=response["items"][0]["snippet"].get("publishedAt").replace("T"," ").replace("Z",""),
               viewcount=response["items"][0]["statistics"].get("viewCount"),
               commentcount=response["items"][0]["statistics"].get("commentCount"),
               likeCount=response["items"][0]["statistics"].get("likeCount"),
               favoriteCount=response["items"][0]["statistics"].get("favoriteCount"),
               videotag=response["items"][0]["snippet"].get("tags"))
        videoDetails.append(V)
    return vid,videoDetails
#Playlist Query
def playlistdetails(youtube,channelid):
    next_page_token=None
    data1=[]
    while 1:
        request= youtube.playlists().list(
                   part="snippet",
                   channelId=channelid,
                   maxResults=50,
                   pageToken=next_page_token)
        response=request.execute()
        data1=data1+response["items"]
        next_page_token=response.get("nextPageToken")
        if next_page_token is None:
            break
            
    playlistdetails=[]

    for i in range(len(data1)):
        playlistdetails.append(dict(PlaylistId=data1[i]["id"],
                                      channelid=data1[i]["snippet"]["channelId"],
                                      PlaylistName=data1[i]["snippet"]["title"]))   
    return playlistdetails
#Comment Query
def commentdetails(youtube,vid):    
    for i in vid:
        comment=[]
        try:
            request=youtube.commentThreads().list(
            part="snippet",
            videoId=i,
            maxResults=50)
            response=request.execute()
            comment=comment+response["items"]
        except:
            pass
    commentDetails=[]
    for i in range(len(comment)):
        commentDetails.append(dict(videoid=comment[i]["snippet"]["videoId"],
                                   comment_id=comment[i]["snippet"]["topLevelComment"]["id"],
                                   Comment_Text= comment[i]['snippet']['topLevelComment']['snippet']['textDisplay'],
                                   Comment_Author= comment[i]['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                                   Comment_PublishedAt= comment[i]['snippet']['topLevelComment']['snippet']['publishedAt'].replace("T"," ").replace("Z","")))
    
    return commentDetails

##Mongodb Data Insertion
uri = "mongodb+srv://Malar:Malar@cluster0.vuk2oaz.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
client.admin.command('ping')
a=MongoClient("mongodb+srv://Malar:Malar@cluster0.vuk2oaz.mongodb.net/?retryWrites=true&w=majority")

def mongodb(Datalake):
    a.guvi.youtube.insert_one(Datalake)

def SQLinsert(channelid):
    try:
        mycursor.execute("use  youtube")
    except:
        mycursor.execute("create database youtube")
        mycursor.execute("use  youtube")
    x=a.guvi.youtube.find({"Channel_id":channelid},{"_id":False})
    for i in x:
        channeltable=i["Channelstats"]
        Videotable=i["Videostats"]
        PlaylistTable=i.get("PlaylistStats")
        CommentTable=i.get("Commentstats")
        
    cs=pd.DataFrame(channeltable)
    cs["Channelname"]=cs["Channelname"].astype(str)
    cs["channel_id"]=cs["channel_id"].astype(str)
    cs["channeldescription"]=cs["channeldescription"].astype(str)
    cs["channelviews"]=cs["channelviews"].astype(int)
    cs["channel_video_count"]=cs["channel_video_count"].astype(int)
    cs["channel_subscribers_count"]=cs["channel_subscribers_count"].astype(int)
    cs["channelstatus"]=cs["channelstatus"].astype(str)
    cs["channeltype"]=cs["channeltype"].astype(str)
    try:
        cs.to_sql("channel",Engine,if_exists="append",index=False)
    except:
        pass
    
    vs=pd.DataFrame(Videotable)
    
    for i in range(len(vs["commentcount"])):
        if (vs.iloc[i,9])==None:
            vs.iloc[i,9]=0
        
    vs["id"]=vs["id"].astype(str)
    vs["channelid"]=vs["channelid"].astype(str)
    vs["definition"]=vs["definition"].astype(str)
    vs["dimension"]=vs["dimension"].astype(str)
    vs["duration"]=vs["duration"].astype(str)
    vs["Videotitle"]=vs["Videotitle"].astype(str)
    vs["Published_Date"]=vs["Published_Date"].astype(str)
    vs["Published_Date"]=vs["Published_Date"].str.replace("Z","")
    vs["Published_Date"]=vs["Published_Date"].str.replace("T"," ")
    vs["viewcount"]=vs["viewcount"].astype(int)
    vs["commentcount"]=vs["commentcount"].astype(int)
    vs["likeCount"]=vs["likeCount"].astype(int)
    vs["favoriteCount"]=vs["favoriteCount"].astype(int)
    vs["videotag"]=vs["videotag"].astype(str)
    try:
        vs.to_sql("video",Engine,if_exists="append",index=False)
    except:
        pass
    
    ps=pd.DataFrame(PlaylistTable)
    try:
        ps["PlaylistId"]=ps["PlaylistId"].astype(str)
        ps["channelid"]=ps["channelid"].astype(str)
        ps["PlaylistName"]=ps["PlaylistName"].astype(str)
    except:
        pass
    try:
        ps.to_sql("playlist",Engine,if_exists="append",index=False)
    except:
        pass
    
    cos=pd.DataFrame(CommentTable)
    try:
        cos["comment_id"]=cos["comment_id"].astype(str)
        cos["videoid"]=cos["videoid"].astype()
        cos["Comment_Text"]=cos["Comment_Text"].astype(str)
        cos["Comment_Author"]=cos["Comment_Author"].astype(str)
        cos["Comment_PublishedAt"]=cos["Comment_PublishedAt"].astype(str) 
    except:
        pass
    try:
        cos.to_sql("comment",Engine,if_exists="append",index=False)
    except:
        pass

def databasestructure():
    try:
        mycursor.execute("USE youtube")
        #Channel column update
        mycursor.execute("alter table channel modify column channel_id varchar(255) primary key,\
        modify column channelname varchar(255), modify column channeltype varchar(255),\
        modify column channelstatus varchar(255)")
        
        #Playlist column update
        mycursor.execute("alter table playlist modify column PlaylistId varchar(255) primary key,\
        modify column channelid varchar(255),\
        modify column PlaylistName varchar(255)")
        mycursor.execute("alter table playlist add constraint FK_chID foreign key (channelid) references channel(channel_id)")
        
        #video column update
        mycursor.execute("alter table video modify column id varchar(255) primary key,\
        modify column channelid varchar(255), modify column definition varchar(255),\
        modify column duration varchar(255),\
        modify column dimension varchar(255),modify column Videotitle varchar(255),\
        modify column description text,modify column Published_Date Datetime,\
        modify column viewcount int,\
        modify column commentcount int, modify column likeCount int,\
        modify column favoriteCount int,\
        modify column videotag text")
        mycursor.execute("alter table video add constraint FK_vdID foreign key (channelid) references channel(channel_id)")
        
        #Comment column update
        mycursor.execute("alter table comment modify column comment_id varchar(255) primary key,\
        modify column Comment_Text text, modify column Comment_Author varchar(255),\
        modify column Comment_PublishedAt Datetime,\
        modify column videoid varchar(255)")
        mycursor.execute("alter table comment add constraint FK_coID foreign key (videoid) references video(id)")
        
        mycursor.execute("UPDATE video SET duration = TIME_TO_SEC(duration)")
    except:
        pass


add_selectbox = st.sidebar.selectbox(
    "",
    ("Home", "Channel Data Scraping", "Migrate to SQL", "Queries")
)


if(add_selectbox=="Home"):
    with st.container():        
        st.header("YouTube Data Harvesting and Warehousing using SQL, MongoDB and Streamlit")
        st.image(Image.open(r"C:/Users/poomalar/Downloads/OIP (2).jpeg"),width=500)
        st.subheader("A simple project helps in retrieving data from the YouTube API, \
             storing it in a MongoDB data lake, migrating it to a SQL data warehouse, \
             querying the data warehouse with SQL, and displaying the data in the Streamlit app.")
elif(add_selectbox=="Channel Data Scraping"):
    se = st.text_input("Enter the Channelid you want to scrape", "Type Here ...")
    if(st.button('Submit')):
        s=youtubedetails(se)
        st.success("{} is the name of the Youtube Channel".format(s["Channelstats"][0]["Channelname"]))
        st.info("This is a {} account".format(s["Channelstats"][0]["channelstatus"]))
        st.warning("{} is the viewcount for the particular Youtube Channel".format(s["Channelstats"][0]["channelviews"]))
        st.error("This channel has {} videos.".format(s["Channelstats"][0]["channel_video_count"]))
        st.success("This Channel has {} Subscribers".format(s["Channelstats"][0]["channel_subscribers_count"]))
        st.subheader("Click OKAY you want to move the entire data to MongoDB?")
        mongodb(s)
        st.info("Data Also was moved to MongoDB Successfully")
elif(add_selectbox=="Migrate to SQL"):
    st.subheader("With this feature, the needed data can be transefered to SQL as well")
    id=st.text_input("Enter the Channelid you want to retrieve the data from MongoDB and push to SQL")
    if(st.button("Submit")):
       SQLinsert(id)
       databasestructure()
       st.text("Cool")
elif(add_selectbox=="Queries"):
    st.subheader("This window allows you to query the database(tables) created in Workbench")
    questions=st.selectbox("Questions: ", ["Please select one",
                                       "What are the names of all the videos and their Corresponding Channels?",
                                       "Which channels have the most no of videos and how many videos?",
                                       "What are the top 10 most viewed videos & the respective channels?",
                                       "How many comments were made on each video & the respective video names?",
                                       "Which videos have the highest number of likes, and what are their corresponding channel names?",
                                       "What is the total number of likes and dislikes for each video, and what are their corresponding video names?",
                                       "What is the total number of views for each channel, and what are their corresponding channel names?",
                                       "What are the names of all the channels that have published videos in the year 2022?",
                                       "What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                                       "Which videos have the highest number of comments, and what are their corresponding channel names?"])
    if (questions=="Please select one"):
        st.text("Please Choose any one Query")
    elif(questions=="What are the names of all the videos and their Corresponding Channels?"):
        mycursor.execute("Use youtube")
        mycursor.execute("Select video.Videotitle,channel.channelname from video INNER JOIN channel on video.channelid=channel.channel_id")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="Which channels have the most no of videos and how many videos?"):
        mycursor.execute("Use youtube")
        mycursor.execute("Select video.channelid, channel.channelname, count(video.id) \
        from video INNER JOIN channel on video.channelid=channel.channel_id \
        group by video.channelid")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="What are the top 10 most viewed videos & the respective channels?"):
        mycursor.execute("Use youtube")
        mycursor.execute("select video.videotitle,video.viewcount,channel.channelname \
        from video INNER JOIN channel on video.channelid=channel.channel_id \
        order by viewcount desc \
        limit 10")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="How many comments were made on each video & the respective video names?"):
        mycursor.execute("Use youtube")
        mycursor.execute("select commentcount,videotitle \
        from video \
        order by commentcount desc")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="Which videos have the highest number of likes, and what are their corresponding channel names?"):
        mycursor.execute("Use youtube")
        mycursor.execute("select video.videotitle,video.likecount,channel.channelname \
        from video INNER JOIN channel on video.channelid=channel.channel_id \
        order by likecount desc \
        limit 10")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="What is the total number of likes and dislikes for each video, and what are their corresponding video names?"):
        mycursor.execute("Use youtube")
        mycursor.execute("select likeCount+commentcount as Total, Videotitle \
        from video")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="What is the total number of views for each channel, and what are their corresponding channel names?"):
        mycursor.execute("Use youtube")
        mycursor.execute("select channelname,channelviews \
        from channel ")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="What are the names of all the channels that have published videos in the year 2022?"):
        mycursor.execute("Use youtube")
        mycursor.execute("select video.videotitle, video.published_date, channel.channelname \
        from video INNER JOIN channel on video.channelid=channel.channel_id \
        where published_date between '2019-12-31 23:59:59' and '2021-01-01 12:00:00'")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="What is the average duration of all videos in each channel, and what are their corresponding channel names?"):
        mycursor.execute("Use youtube")
        mycursor.execute("select  channel.channelname, video.channelid, avg(video.duration) as Avg \
        from video INNER JOIN channel on video.channelid=channel.channel_id \
        group by video.channelid")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))
    elif(questions=="Which videos have the highest number of comments, and what are their corresponding channel names?"):
        mycursor.execute("Use youtube")
        mycursor.execute("select video.videotitle,video.commentcount,channel.channelname \
        from video INNER JOIN channel on video.channelid=channel.channel_id \
        order by commentcount desc \
        limit 10")
        out=mycursor.fetchall()
        from tabulate import tabulate
        a=tabulate(out,headers=[i[0] for i in mycursor.description],  tablefmt='psql')
        st.text("{}".format(a))