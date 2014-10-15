from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting

import tweepy
import csv
import time
import re
import pandas as pd
import collections

import requests

# Create your views here.
def index(request):
	screen_name = request.GET["handle"]
	handle=screen_name

	# this should all work just fine with Twitter
	auth = tweepy.OAuthHandler('aOtAWCqvw99r9mDkP5TtpQ','1Qs97JNZpzx0XoInBH1ikmFHseZo511Ts4PxrwJss')
	auth.set_access_token('588385097-TZXoE2FP55l2ZLdxbrN8iC784YoNBelrgLaJRTJE','wvj8OCfEzt27IEVo36nBEMWL37K8HBl8s5zDz9yjnVc')
	api = tweepy.API(auth)
	data = api.get_user(screen_name)

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
	            
	ttext = columns[2]
	tconvo = columns[1]
	tRT = columns[0]
	tdirect = columns[3]
	tfollowers = columns[5]

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
	PRT = percentage(RT, activity)
	Pconvo = percentage(convo, activity)
	Pconvostarter = percentage(convostarter, activity)
	users = df['user'].value_counts()[:10]
	fav = df.sort(['Times_Favorited'], ascending=[0])[:10][['Tweet','Times_Favorited']]
	totalfavorited = df['Times_Favorited'].sum()
	num_RT = interesting_df["Times_RTd"].sum()
	
	html_output = '<html><head><title>Twitter Analyzer</title</head><body>'

	html_output = ''
	html_output+= '@'+ handle +" " + str(total) + " Statistics:"
	html_output+= 'Followers: ' + str(data.followers_count)
	html_output+= 'Following: ' + str(data.friends_count)
	html_output+= 'Member of ' + str(data.listed_count) + ' lists'
	html_output+= ' '
	html_output+= 'Activity: '
	html_output+= Poriginaltweets +" (" + str(originaltweets) + " tweets)  of @" +handle+ " activity are original tweets (no RT or replies)"
	html_output+= PtweetsRTd +" (" + str(tweetsRTd)+ " tweets) of @" +handle+ " original tweets were retweeted " + str(num_RT) + " times"
	html_output+= "@" +handle+ " received " + str(totalfavorited)+  " favorites"
	html_output+= ' '
	html_output+= 'In-depth:'
	html_output+= '@'+ handle + " RTd " + str(RT) + " times"
	html_output+= 'Favorited ' + str(data.favourites_count) + " tweets"
	html_output+= "Replied to " + str(convo) + " tweets"
	html_output+= str(convostarter) + " tweets were directed at a user"
	html_output+= ''
	html_output+= 'Top 10 user interactions and number of replies to that user:'
	#html_output+= '<br />'.join(users)
	html_output+= ' '
	html_output+= 'Top Favorited tweets'
	#html_output+= '<br />'.join(fav)

	html_output += '</body></html>'

	return HttpResponse(html_output)


def percentage(part, whole):
    if whole==0:
        return "0%"
    else:
        ans = 100 * float(part)/float(whole)
        rnd = '%.0f' % round(ans, 1)
        return str(rnd) + "%"








def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, 'db.html', {'greetings': greetings})
