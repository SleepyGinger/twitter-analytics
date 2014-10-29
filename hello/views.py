from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting

import tweepy
import pandas as pd
import re

import requests

def index(request):
	
	html_output= '<html><head><title>Twitter Analyzer</title></head><body>'
	html_output+= '<p>&nbsp;</p>'
	html_output+= '<p>&nbsp;</p>'
	html_output+= '<p>&nbsp;</p>'
	html_output+='<center><form action="analyze/" method="request.GET">A Twitter handle please <input type="text"  size="10" name="screen_name">&nbsp;&nbsp;<input type="submit" value="Analyze"></form></center>'
	html_output += '</body></html>'
	return HttpResponse(html_output)

#def day_graph(source):   
#    date_by_years=pd.to_datetime(source, coerce=True).values.astype('datetime64[D]')
#    pd.Series(date_by_years).value_counts().plot(marker='o', linestyle='-')
#    plt.xticks(rotation=30)
#    plt.show()
#    return(matplotlib.pyplot.savefig('d.png'))
#
#def year_graph(source):   
#    date_by_years=pd.to_datetime(source, coerce=True).values.astype('datetime64[Y]')
#    pd.Series(date_by_years).value_counts().plot(marker='o', linestyle='-')
#    plt.xticks(rotation=30)
#    plt.show()
#    return(matplotlib.pyplot.savefig('y.png'))

def analyze(request):
	screen_name = request.GET["screen_name"].replace('@','')

	#Twitter only allows access to a users most recent 3240 tweets with this method	
	#authorize twitter, initialize tweepy
	auth = tweepy.OAuthHandler('aOtAWCqvw99r9mDkP5TtpQ','1Qs97JNZpzx0XoInBH1ikmFHseZo511Ts4PxrwJss')
	auth.set_access_token('588385097-TZXoE2FP55l2ZLdxbrN8iC784YoNBelrgLaJRTJE','wvj8OCfEzt27IEVo36nBEMWL37K8HBl8s5zDz9yjnVc')
	api = tweepy.API(auth)
	
	data = api.get_user(screen_name)
	#profile_img=data._json['profile_image_url_https']
	created=str(data._json['created_at'])
	created=created[4:10]+','+created[25:30]
	name=data._json['name']
	#background=data._json["profile_banner_url"]
	description=data._json["description"].encode("utf-8")
	description= re.sub('\W', ' ', description)
	#displayed_url=data._json['entities']['url']['urls'][0]['display_url']
	
	
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
		#print "Getting tweets before tweet id: %s" % (oldest)
		
		#all subsiquent requests use the max_id param to prevent duplicates
		new_tweets = api.user_timeline(screen_name = screen_name ,count=200,max_id=oldest)
		
		#save most recent tweets
		alltweets.extend(new_tweets)
		
		#update the id of the oldest tweet less one
		oldest = alltweets[-1].id - 1
		
		#print "%s tweets downloaded so far..." % (len(alltweets))
	    
	#print "Finished Collecting"
	
	#transform the tweepy tweets into a 2D array that will populate the csv	
	outtweets = [[tweet.text.encode("utf-8").replace('&amp;','&'), tweet.created_at, tweet.retweet_count, tweet.favorite_count, tweet.in_reply_to_status_id_str, tweet.in_reply_to_user_id_str, tweet.in_reply_to_screen_name] for tweet in alltweets]
	
	#creates DataFrame with selected fields
	df=pd.DataFrame(outtweets).fillna(False)
	df.columns = ['Tweet', 'Date', 'RT_count', 'Favorited_count', 'Reply_id', 'At_message_id',  'At_message_user']
	
	#creates new columns from the Date
	df['short_date']=pd.to_datetime(df['Date'], coerce=True).values.astype('datetime64[D]')
	df['month']=pd.DatetimeIndex(df['Date']).month
	df['year']=pd.DatetimeIndex(df['Date']).year
	df['hour']=pd.DatetimeIndex(df['Date']).hour
	RT_df=df[df['Tweet'].str.startswith("RT ")]
	RT_count=len(df[df['Tweet'].str.startswith("RT ")])
	status_count=str(data.statuses_count)
	at=df[(~df['Tweet'].str.startswith("@"))]
	original_df=at[(~at['Tweet'].str.startswith("RT"))]
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

	
	html_output=  '<html><head><title>Twitter Analyzer</title></head><body style="background-image: url('+str(data.profile_banner_url)+'); background-position: right top; background-repeat: no-repeat; background-attachment: fixed; background-position: 3% 2%;  background-size: 250px 90px; ">'
	html_output+= '<center><font size="11"><img src='+str(data.profile_image_url_https)+' alt=Profile_Pic>'
	html_output+= ' '+ str(data.name)+ "'s Twitter Overview </font>"
	html_output+= '<br>'
	html_output+= '<br> Followers: ' + str(data.followers_count)
	html_output+= '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Following: ' + str(data.friends_count)
	html_output+= '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Member of ' + str(data.listed_count) + ' lists'  + "&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;Total tweets: " + str(data.statuses_count)
	html_output+= '<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Tweeting since ' + str(data.created_at) + '&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;URL:'
	html_output+= '<br>'+ str(data.description)
	html_output+= '<br><br>'
	html_output+= '<font size="8"> Activity</font>' 
	html_output+= '<br>' +str(percentage(original_count,status_count)) +" (" + str(original_count) + " tweets)  of @" +str(data.screen_name)+ "'s activity are original tweets (no RT or replies)"
	html_output+= '<br>' +str(percentage(RT_count,status_count)) +" (" + str(RT_count) + " tweets)  of @" +str(data.screen_name)+ "'s tweets were RTs"
	html_output+= '<br>' +str(percentage(reply_count,status_count)) +" (" + str(reply_count) + " tweets)  of @" +str(data.screen_name)+ "'s tweets were replies to a user"
	html_output+= '<br>' +str(percentage(at_count,status_count)) +" (" + str(at_count) + " tweets)  of @" +str(data.screen_name)+ "'s tweets were directed at a user"
	html_output+= '<br><br>'
	html_output+= '<font size="8"> In-depth</font>'
	html_output+= '<br>Favorited ' + str(data.favourites_count) + " tweets"
	html_output+= '<br>' + str(percentage(original_RT_count,status_count)) +" (" + str(original_RT_count)+ " tweets) of @" +screen_name+ "'s original tweets were retweeted " + str(origianl_RT_sum) + " times"
	html_output+= '<br>' + str(percentage(favorite_count,status_count)) +" (" + str(favorite_count)+ " tweets) of @" +screen_name+ "'s original tweets were favorited " + str(favorite_sum) + " times"
	html_output+= '<br><br>Top 5 direct messaged users with frequencies<br>'
	html_output+= "<br> <img src='test.png'>"
	html_output+= '</center>'


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
