from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting

import tweepy
import pandas as pd
import re
import matplotlib.pyplot as plt

import requests


def index(request):
	
	html_output=  '<html><head><title>Twitter Analyzer</title>'
	html_output+= "<script>"
	html_output+= "(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){"
	html_output+= "(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),"
	html_output+= "m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)"
	html_output+= "})(window,document,'script','//www.google-analytics.com/analytics.js','ga');"
	html_output+= "ga('create', 'UA-56466801-1', 'auto');"
	html_output+= "ga('send', 'pageview');</script></head>"
	html_output+= '<body><p>&nbsp;</p>'
	html_output+= '<p>&nbsp;</p>'
	html_output+= '<p>&nbsp;</p>'
	html_output+='<center><form action="analyze/" method="request.GET">A Twitter handle please <input type="text"  size="10" name="screen_name">&nbsp;&nbsp;<input type="submit" value="Analyze"></form></center>'
	html_output += '</body></html>'
	return HttpResponse(html_output)	

def analyze(request):
	screen_name = request.GET["screen_name"].replace('@','')

	#Twitter only allows access to a users most recent 3240 tweets with this method	
	#authorize twitter, initialize tweepy
	auth = tweepy.OAuthHandler('aOtAWCqvw99r9mDkP5TtpQ','1Qs97JNZpzx0XoInBH1ikmFHseZo511Ts4PxrwJss')
	auth.set_access_token('588385097-TZXoE2FP55l2ZLdxbrN8iC784YoNBelrgLaJRTJE','wvj8OCfEzt27IEVo36nBEMWL37K8HBl8s5zDz9yjnVc')
	api = tweepy.API(auth)
	
	data = api.get_user(screen_name)

	
	#initialize a list to hold all the tweepy Tweets
	alltweets = []	
	
	#make initial request for most recent tweets (200 is the maximum allowed count)
	new_tweets = api.user_timeline(screen_name = screen_name ,count=200)
	
	#save most recent tweets
	alltweets.extend(new_tweets)
	
	#save the id of the oldest tweet less one
	oldest = alltweets[-1].id - 1
	
	#keep grabbing tweets until there are no tweets left to grab
	while len(new_tweets) > 0:
		print "Getting tweets before tweet id: %s" % (oldest)
		
		#all subsiquent requests use the max_id param to prevent duplicates
		new_tweets = api.user_timeline(screen_name = screen_name ,count=200,max_id=oldest)
		
		#save most recent tweets
		alltweets.extend(new_tweets)
		
		#update the id of the oldest tweet less one
		oldest = alltweets[-1].id - 1
		
		print "%s tweets downloaded so far..." % (len(alltweets))
	    
	print "Finished Collecting"
	
	#transform the tweepy tweets into a 2D array that will populate the csv	
	outtweets = [[tweet.text.encode("utf-8").replace('&amp;','&'), tweet.created_at, tweet.retweet_count, tweet.favorite_count, tweet.in_reply_to_status_id_str, tweet.in_reply_to_user_id_str, tweet.in_reply_to_screen_name] for tweet in alltweets]
	
	#creates DataFrame with selected fields
	df=pd.DataFrame(outtweets).fillna(False)
	df.columns = ['Tweet', 'Date', 'RT_count', 'Favorited_count', 'Reply_id', 'At_message_id',  'At_message_user']
	
	#creates new columns from the Date
	url=str(data.url)
	created=re.search("([0-9]{4}-[0-9]{2}\-[0-9]{2})", str(data.created_at))
	created=created.group()
	start_date=re.search("([0-9]{4}-[0-9]{2}\-[0-9]{2})", str(alltweets[-1].created_at))
	start_date=start_date.group()
	df['short_date']=pd.to_datetime(df['Date'], coerce=True).values.astype('datetime64[D]')
	df['month']=pd.DatetimeIndex(df['Date']).month
	df['year']=pd.DatetimeIndex(df['Date']).year
	df['hour']=pd.DatetimeIndex(df['Date']).hour
	RT_df=df[df['Tweet'].str.startswith("RT ")]
	RT_count=len(df[df['Tweet'].str.startswith("RT ")])
	status_count=str(len(df))
	at=df[(~df['Tweet'].str.startswith("@"))]
	original_df=at[(~at['Tweet'].str.startswith("RT"))]
	original_df=original_df[original_df['At_message_id']==False]
	original_count=len(original_df)
	original_RT_df=original_df[original_df['RT_count']>0]
	original_RT_count=len(original_RT_df)
	origianl_RT_sum=sum(original_RT_df['RT_count'])
	favorite_df=original_df[original_df['Favorited_count']>0]
	favorite_count=len(favorite_df['Favorited_count'])
	favorite_sum=sum(favorite_df['Favorited_count'])
	all_at_user_df=df[df['At_message_id']>0]
	reply_df=all_at_user_df[all_at_user_df['Reply_id']>0]
	reply_count=len(all_at_user_df[all_at_user_df['Reply_id']>0])
	at_df=all_at_user_df[all_at_user_df['Reply_id']==False]
	at_count=len(all_at_user_df[all_at_user_df['Reply_id']==False])

	if 'profile_banner_url' in data._json:
		profile_banner=str(data._json['profile_banner_url'])
	else:
		profile_banner = 'none'

	f_df=favorite_df[['Tweet','Favorited_count','short_date']][:10]
	at_df=all_at_user_df[['Tweet','At_message_user','short_date']][:10]
	att=str(at_df.values)
	att=att.replace("Timestamp('",'')
	att=att.replace("[ '",'')
	att=att.replace(" 00:00:00', tz=None)]",'')
	att=att.replace("'\n  '",'<br>')

	show_at_df=at_df['At_message_user'].value_counts()[:5]
	show_at_df=str(show_at_df)
	show_at_df=show_at_df.replace('\n','<br>')
	show_at_df=show_at_df.replace('dtype: int64','')
	
	html_output=  '<html><head><title>Twitter Analyzer</title>'
	html_output+= "<script>"
	html_output+= "(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){"
	html_output+= "(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),"
	html_output+= "m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)"
	html_output+= "})(window,document,'script','//www.google-analytics.com/analytics.js','ga');"
	html_output+= "ga('create', 'UA-56466801-1', 'auto');"
	html_output+= "ga('send', 'pageview');"
	html_output+= "</script></head>"
	html_output+= '<body style="background-image: url('+profile_banner+'); background-position: right top; background-repeat: no-repeat; background-attachment: fixed; background-position: 3% 2%;  background-size: 250px 90px; ">'
	html_output+= '<img src='+str(data.profile_image_url_https)+' alt=Profile_Pic background-position: 3% 2%; background-repeat: no-repeat; background-attachment: fixed;>'
	html_output+= '<center><font size="11">'+ str(data.name)+ "'s Twitter Overview </font>"
	html_output+= '<br>'
	html_output+= '<br> Followers: ' + str(data.followers_count)
	html_output+= '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Following: ' + str(data.friends_count)
	html_output+= '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Member of ' + str(data.listed_count) + ' lists'  + "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Location: " + str(data.location.encode('ascii', 'ignore'))
	html_output+= '<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tweeting since ' + created + '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Total tweets: ' + str(data.statuses_count)
	html_output+= '<br>description:'+ str(data.description.encode('ascii', 'ignore'))
	html_output+= '<br><br>'
	html_output+= '<font size="8"> Activity</font> <br><br> Analyzing '+str(percentage(status_count,str(data.statuses_count)))+' of tweets, startering from '+start_date
	html_output+= '<br> <br>' +str(percentage(original_count,status_count)) +" (" + str(original_count) + " tweets)  of @" +str(data.screen_name)+ "'s activity are original tweets (no RTs or replies)"
	html_output+= '<br>' +str(percentage(RT_count,status_count)) +" (" + str(RT_count) + " tweets)  of @" +str(data.screen_name)+ "'s tweets were RTs"
	html_output+= '<br>' +str(percentage(reply_count,status_count)) +" (" + str(reply_count) + " tweets)  of @" +str(data.screen_name)+ "'s tweets were replies to a user"
	html_output+= '<br>' +str(percentage(at_count,status_count)) +" (" + str(at_count) + " tweets)  of @" +str(data.screen_name)+ "'s tweets were directed at a user"
	html_output+= '<br><br>'
	html_output+= '<font size="8"> In-depth</font>'
	html_output+= '<br>'+screen_name+' favorited ' + str(data.favourites_count) + " tweets"
	html_output+= '<br>' + str(percentage(original_RT_count,original_count)) +" (" + str(original_RT_count)+ " tweets) of @" +screen_name+ "'s original tweets were retweeted " + str(origianl_RT_sum) + " times"
	html_output+= '<br>' + str(percentage(favorite_count,original_count)) +" (" + str(favorite_count)+ " tweets) of @" +screen_name+ "'s original tweets were favorited " + str(favorite_sum) + " times"
	html_output+= '<br><br>Top 5 user interactions with frequencies<br>'
	html_output+=  ' '+show_at_df+'<br><br><br>'
	html_output+= "<br> <img src=/date_graph/?screen_name="+screen_name+"><br><br><br>"
	html_output+= "<br> <img src=/hour_graph/?screen_name="+screen_name+"><br><br><br>"
	html_output+= "<br> <img src=/week_day/?screen_name="+screen_name+"><br><br><br>"

	html_output += '</center></body></html>'


	return HttpResponse(html_output)

def percentage(part, whole):
    if whole==0:
        return "0%"
    else:
        ans = 100 * float(part)/float(whole)
        rnd = '%.0f' % round(ans, 1)
        return str(rnd) + "%"

def date_graph(request):

	screen_name = request.GET["screen_name"].replace('@','')

	#Twitter only allows access to a users most recent 3240 tweets with this method	
	#authorize twitter, initialize tweepy
	auth = tweepy.OAuthHandler('aOtAWCqvw99r9mDkP5TtpQ','1Qs97JNZpzx0XoInBH1ikmFHseZo511Ts4PxrwJss')
	auth.set_access_token('588385097-TZXoE2FP55l2ZLdxbrN8iC784YoNBelrgLaJRTJE','wvj8OCfEzt27IEVo36nBEMWL37K8HBl8s5zDz9yjnVc')
	api = tweepy.API(auth)
	
	data = api.get_user(screen_name)

	
	#initialize a list to hold all the tweepy Tweets
	alltweets = []	
	
	#make initial request for most recent tweets (200 is the maximum allowed count)
	new_tweets = api.user_timeline(screen_name = screen_name ,count=200)
	
	#save most recent tweets
	alltweets.extend(new_tweets)
	
	#save the id of the oldest tweet less one
	oldest = alltweets[-1].id - 1
	
	#keep grabbing tweets until there are no tweets left to grab
	while len(new_tweets) > 0:
		print "Getting tweets before tweet id: %s" % (oldest)
		
		#all subsiquent requests use the max_id param to prevent duplicates
		new_tweets = api.user_timeline(screen_name = screen_name ,count=200,max_id=oldest)
		
		#save most recent tweets
		alltweets.extend(new_tweets)
		
		#update the id of the oldest tweet less one
		oldest = alltweets[-1].id - 1
		
		print "%s tweets downloaded so far..." % (len(alltweets))
	    
	print "Finished Collecting"
	
	#transform the tweepy tweets into a 2D array that will populate the csv	
	outtweets = [[tweet.text.encode("utf-8").replace('&amp;','&'), tweet.created_at, tweet.retweet_count, tweet.favorite_count, tweet.in_reply_to_status_id_str, tweet.in_reply_to_user_id_str, tweet.in_reply_to_screen_name] for tweet in alltweets]
	
	#creates DataFrame with selected fields
	df=pd.DataFrame(outtweets).fillna(False)
	df.columns = ['Tweet', 'Date', 'RT_count', 'Favorited_count', 'Reply_id', 'At_message_id',  'At_message_user']
	
	#creates new columns from the Date
	df['short_date']=pd.to_datetime(df['Date'], coerce=True).values.astype('datetime64[D]')
	
	response = HttpResponse(mimetype="image/png")
	
	ds=pd.Series(df['short_date'])
	date_span = pd.date_range(df['short_date'].min(), df['short_date'].max())
	pds=ds.value_counts()
	pds.index = pd.DatetimeIndex(pds.index)
	pds = pds.reindex(date_span, fill_value=0)
	plt.plot(date_span.to_pydatetime(), pds, color='green')
	plt.xticks(rotation=30)
	plt.ylabel('Frequency')
	plt.xlabel('Date')
	plt.savefig(response, format="png")
	plt.close()

	return response

def hour_graph(request):

	screen_name = request.GET["screen_name"].replace('@','')

	#Twitter only allows access to a users most recent 3240 tweets with this method	
	#authorize twitter, initialize tweepy
	auth = tweepy.OAuthHandler('aOtAWCqvw99r9mDkP5TtpQ','1Qs97JNZpzx0XoInBH1ikmFHseZo511Ts4PxrwJss')
	auth.set_access_token('588385097-TZXoE2FP55l2ZLdxbrN8iC784YoNBelrgLaJRTJE','wvj8OCfEzt27IEVo36nBEMWL37K8HBl8s5zDz9yjnVc')
	api = tweepy.API(auth)
	
	data = api.get_user(screen_name)

	
	#initialize a list to hold all the tweepy Tweets
	alltweets = []	
	
	#make initial request for most recent tweets (200 is the maximum allowed count)
	new_tweets = api.user_timeline(screen_name = screen_name ,count=200)
	
	#save most recent tweets
	alltweets.extend(new_tweets)
	
	#save the id of the oldest tweet less one
	oldest = alltweets[-1].id - 1
	
	#keep grabbing tweets until there are no tweets left to grab
	while len(new_tweets) > 0:
		print "Getting tweets before tweet id: %s" % (oldest)
		
		#all subsiquent requests use the max_id param to prevent duplicates
		new_tweets = api.user_timeline(screen_name = screen_name ,count=200,max_id=oldest)
		
		#save most recent tweets
		alltweets.extend(new_tweets)
		
		#update the id of the oldest tweet less one
		oldest = alltweets[-1].id - 1
		
		print "%s tweets downloaded so far..." % (len(alltweets))
	    
	print "Finished Collecting"
	
	#transform the tweepy tweets into a 2D array that will populate the csv	
	outtweets = [[tweet.text.encode("utf-8").replace('&amp;','&'), tweet.created_at, tweet.retweet_count, tweet.favorite_count, tweet.in_reply_to_status_id_str, tweet.in_reply_to_user_id_str, tweet.in_reply_to_screen_name] for tweet in alltweets]
	
	#creates DataFrame with selected fields
	df=pd.DataFrame(outtweets).fillna(False)
	df.columns = ['Tweet', 'Date', 'RT_count', 'Favorited_count', 'Reply_id', 'At_message_id',  'At_message_user']
	
	#creates new columns from the Date
	df['hour']=pd.DatetimeIndex(df['Date']).hour
	
	response = HttpResponse(mimetype="image/png")
	
	days_hours=range(23)
	h = pd.Series(df['hour'])
	ph = h.value_counts()
	ph = ph.reindex(days_hours, fill_value=0)
	plt.plot(ph)
	plt.axis([0, 23, 0, max(ph)+5])
	plt.ylabel('Number of Tweets')
	plt.xlabel('Hour of the day')
	plt.savefig(response, format="png")
	plt.close()

	return response

def week_day(request):

	screen_name = request.GET["screen_name"].replace('@','')

	#Twitter only allows access to a users most recent 3240 tweets with this method	
	#authorize twitter, initialize tweepy
	auth = tweepy.OAuthHandler('aOtAWCqvw99r9mDkP5TtpQ','1Qs97JNZpzx0XoInBH1ikmFHseZo511Ts4PxrwJss')
	auth.set_access_token('588385097-TZXoE2FP55l2ZLdxbrN8iC784YoNBelrgLaJRTJE','wvj8OCfEzt27IEVo36nBEMWL37K8HBl8s5zDz9yjnVc')
	api = tweepy.API(auth)
	
	data = api.get_user(screen_name)

	
	#initialize a list to hold all the tweepy Tweets
	alltweets = []	
	
	#make initial request for most recent tweets (200 is the maximum allowed count)
	new_tweets = api.user_timeline(screen_name = screen_name ,count=200)
	
	#save most recent tweets
	alltweets.extend(new_tweets)
	
	#save the id of the oldest tweet less one
	oldest = alltweets[-1].id - 1
	
	#keep grabbing tweets until there are no tweets left to grab
	while len(new_tweets) > 0:
		print "Getting tweets before tweet id: %s" % (oldest)
		
		#all subsiquent requests use the max_id param to prevent duplicates
		new_tweets = api.user_timeline(screen_name = screen_name ,count=200,max_id=oldest)
		
		#save most recent tweets
		alltweets.extend(new_tweets)
		
		#update the id of the oldest tweet less one
		oldest = alltweets[-1].id - 1
		
		print "%s tweets downloaded so far..." % (len(alltweets))
	    
	print "Finished Collecting"
	
	#transform the tweepy tweets into a 2D array that will populate the csv	
	outtweets = [[tweet.text.encode("utf-8").replace('&amp;','&'), tweet.created_at, tweet.retweet_count, tweet.favorite_count, tweet.in_reply_to_status_id_str, tweet.in_reply_to_user_id_str, tweet.in_reply_to_screen_name] for tweet in alltweets]
	
	#creates DataFrame with selected fields
	df=pd.DataFrame(outtweets).fillna(False)
	df.columns = ['Tweet', 'Date', 'RT_count', 'Favorited_count', 'Reply_id', 'At_message_id',  'At_message_user']
	
	#creates new columns from the Date
	df['short_date']=pd.to_datetime(df['Date'], coerce=True).values.astype('datetime64[D]')
	
	response = HttpResponse(mimetype="image/png")
	
	df['weekday'] = df['short_date'].apply(lambda x: x.weekday())
	weekday=range(7)
	w = pd.Series(df['weekday'])
	wk = w.value_counts()
	wk = wk.reindex(weekday, fill_value=0)
	wk.index=['Mon', 'Tues', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun']
	wk.plot(color='red')
	plt.grid(False)
	plt.ylabel('Number of Tweets')
	plt.xlabel('Day of the week')
	plt.savefig(response, format="png")
	plt.close()

	return response

#def db(request):

 #   greeting = Greeting()
  #  greeting.save()

 	#greetings = Greeting.objects.all()

    #return render(request, 'db.html', {'greetings': greetings})
