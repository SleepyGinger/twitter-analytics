from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting

import tweepy
import csv
import time
import re
import pandas as pd
import collections
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import requests

def index(request):
	
	html_output= '<html><head><title>Twitter Analyzer</title></head><body>'
	html_output+= '<p>&nbsp;</p>'
	html_output+= '<p>&nbsp;</p>'
	html_output+= '<p>&nbsp;</p>'
	html_output+='<center><form action="analyze/" method="request.GET">A Twitter handle please <input type="text"  size="10" name="handle">&nbsp;&nbsp;<input type="submit" value="Analyze"></form></center>'
	html_output += '</body></html>'
	return HttpResponse(html_output)

def day_graph(source):   
    date_by_years=pd.to_datetime(source, coerce=True).values.astype('datetime64[D]')
    pd.Series(date_by_years).value_counts().plot(marker='o', linestyle='-')
    plt.xticks(rotation=30)
    plt.show()
    #return(matplotlib.pyplot.savefig('d.png'))

def year_graph(source):   
    date_by_years=pd.to_datetime(source, coerce=True).values.astype('datetime64[Y]')
    pd.Series(date_by_years).value_counts().plot(marker='o', linestyle='-')
    plt.xticks(rotation=30)
    plt.show()
    #return(matplotlib.pyplot.savefig('y.png'))

def analyze(request):
	screen_name = request.GET["handle"].replace('@','')


	# this should all work just fine with Twitter
	auth = tweepy.OAuthHandler('aOtAWCqvw99r9mDkP5TtpQ','1Qs97JNZpzx0XoInBH1ikmFHseZo511Ts4PxrwJss')
	auth.set_access_token('588385097-TZXoE2FP55l2ZLdxbrN8iC784YoNBelrgLaJRTJE','wvj8OCfEzt27IEVo36nBEMWL37K8HBl8s5zDz9yjnVc')
	api = tweepy.API(auth)
	data = api.get_user(screen_name)
	profile_img=data._json['profile_image_url_https']
	name=data._json['name']
	background=data._json["profile_banner_url"]
	description=data._json["description"].encode("utf-8")
	description= re.sub('\W', ' ', description)
	#displayed_url=data._json['entities']['url']['urls'][0]['display_url']
	created=str(data._json['created_at'])
	created=created[4:10]+', '+created[25:30]

	################################################################################

	#initialize a list to hold all the tweepy Tweets
	alltweets = []	
	
	#make initial request for most recent tweets (200 is the maximum allowed count)
	new_tweets = api.user_timeline(screen_name = screen_name, count=200)
	
	#save most recent tweets
	alltweets.extend(new_tweets)
	
	#save the id of the oldest tweet less one
	oldest = alltweets[-1].id - 1
	
	#keep grabbing tweets until there are no tweets left to grab
	while len(new_tweets) > 0:
		
		#all subsiquent requests use the max_id param to prevent duplicates
		new_tweets = api.user_timeline(screen_name = screen_name,count=200,max_id=oldest)
		
		#save most recent tweets
		alltweets.extend(new_tweets)
		
		#update the id of the oldest tweet less one
		oldest = alltweets[-1].id - 1
		
	
	#transform the tweepy tweets into a 2D array that will populate the csv	
	outtweets = [[tweet.retweet_count, tweet.in_reply_to_status_id_str, tweet.text.encode("utf-8").replace('&amp;','&'), tweet.in_reply_to_user_id_str, tweet.created_at, tweet.in_reply_to_screen_name, tweet.favorite_count] for tweet in alltweets]
	
	#write the csv	
	with open('/tmp/%s.csv' % screen_name, 'wb') as f:
		writer = csv.writer(f)
		writer.writerow(["Times_RTd", 'status_id', 'Tweet', 'conversation_id', 'Date', 'user', 'Times_Favorited'])
		writer.writerows(outtweets)
	pass

	################################################################################
	dd = pd.DataFrame(outtweets)
	dd.columns = ['RT_count', 'reply_id', 'Tweet', 'at_message_id', 'date', 'at_message_user', 'favorited_count' ]
	year_graph(dd['date'])
	btop_messaged_user=str(dd['at_message_user'].value_counts()[:5])
	top_messaged_user=btop_messaged_user.replace("\n", "'<br>'").replace("dtype: int64","").replace("'","")

	columns = collections.defaultdict(list)
	text=[]
	total=0
	with open('/tmp/%s.csv' % screen_name, 'rU') as f:
	    reader = csv.reader(f)
	    reader.next()
	    for row in reader:
	        text.extend(row)
	        total +=1
	        for (i,v) in enumerate(row):
	            columns[i].append(v)

	tRT = columns[0]	            
	tconvo = columns[1]
	ttext = columns[2]
	tdirect = columns[3]
	tdate= columns[4]
	tuser = columns[5]

	tuser=[]

	#adds +1 to oringinal if finds empty space in tconvo
	original=0
	for each in tconvo:
	    if re.match(r'^\s*$',each):
	        original += 1

	#finds any digit in tconvo
	convo=0
	for each in tconvo:
	    if re.findall(r"\d", each):
	        convo += 1

	#looks for retweets by finding 'RT' in ttext
	RT=0
	for each in ttext:
	    if re.match(r"RT ",each):
	        RT += 1

	direct=0
	for each in tdirect:
	    if re.findall(r"\d",each):
	        direct += 1
	RTd=0
	for each in tRT:
	    if each=='0':
	        RTd += 1
	        
	originaltweets=total-direct-RT
	convostarter = direct-convo

	df = pd.read_csv('/tmp/%s.csv' % screen_name).reset_index()

	interesting_df = df[(df.conversation_id.isnull()) &
	                    (df.Times_RTd > 0) &
	                    (-df.Tweet.str.match(r"RT "))]

	headers = ["Date", "Times_RTd", "Tweet"]
	head=["Date", "Times_Favorited", "Tweet"]

	tweetsRTd = len(interesting_df)
	interesting_df.to_csv('%s_RTS.csv' % screen_name, cols=headers)

	################################################################################

	activity = total-originaltweets
	PtweetsRTd = percentage(tweetsRTd, originaltweets)
	Poriginaltweets = percentage(originaltweets, total)
	PRT = percentage(RT, total)
	Pconvo = percentage(convo, total)
	Pconvostarter = percentage(convostarter, total)
	users = df['user'].value_counts()[:10]
	fav = df.sort(['Times_Favorited'], ascending=[0])[:10][['Tweet','Times_Favorited']]
	totalfavorited = df['Times_Favorited'].sum()
	num_RT = interesting_df["Times_RTd"].sum()

	
	html_output=  '<html><head><title>Twitter Analyzer</title></head><body style="background-image: url('+background+'); background-position: right top; background-repeat: no-repeat; background-attachment: fixed; background-position: 3% 2%;  background-size: 250px 90px; ">'
	html_output+= '<center><font size="11"><img src='+profile_img+' alt=Profile_Pic>'
	html_output+= ' '+ name+ "'s Twitter Overview </font>"
	html_output+= '<br>'
	html_output+= '<br> Followers: ' + str(data.followers_count)
	html_output+= '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Following: ' + str(data.friends_count)
	html_output+= '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Member of ' + str(data.listed_count) + ' lists'  + "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Total tweets: " + str(total)
	html_output+= '<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tweeting since ' + str(created) + '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;URL:'
	html_output+= '<br>'+ str(description)
	html_output+= '<br><br>'
	html_output+= '<font size="8"> Activity</font>' 
	html_output+= '<br>' +Poriginaltweets +" (" + str(originaltweets) + " tweets)  of @" +screen_name+ "'s activity are original tweets (no RT or replies)"
	html_output+= '<br>' +PRT +" (" + str(RT) + " tweets)  of @" +screen_name+ "'s tweets were RTs"
	html_output+= '<br>' +Pconvo +" (" + str(convo) + " tweets)  of @" +screen_name+ "'s tweets were replies to a user"
	html_output+= '<br>' +Pconvostarter +" (" + str(convostarter) + " tweets)  of @" +screen_name+ "'s tweets were directed at a user"
	html_output+= '<br><br>'
	html_output+= '<font size="8"> In-depth</font>'
	html_output+= '<br>Favorited ' + str(data.favourites_count) + " tweets"
	html_output+= '<br>' + PtweetsRTd +" (" + str(tweetsRTd)+ " tweets) of @" +screen_name+ "'s tweets were retweeted " + str(num_RT) + " times"
	html_output+= '<br>' + "@" +screen_name+ " received " + str(totalfavorited)+  " favorites"
	html_output+= '<br><br>Top 5 direct messaged users with frequencies<br>'
	html_output+= top_messaged_user
	html_output+= '<br> <img src=/tmp/y.png>'
	html_output+='</center>'
	#html_output+= 'Top Favorited tweets'
	#html_output+= fav

	html_output += '</center></body></html>'

	return HttpResponse(html_output)

def percentage(part, whole):
    if whole==0:
        return "0%"
    else:
        ans = 100 * float(part)/float(whole)
        rnd = '%.0f' % round(ans, 1)
        return str(rnd) + "%"



#def db(request):

 #   greeting = Greeting()
  #  greeting.save()

 	#greetings = Greeting.objects.all()

    r#eturn render(request, 'db.html', {'greetings': greetings})
