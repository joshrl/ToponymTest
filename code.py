#!/usr/bin/env python

import web
from web import webapi

import dateutil.parser
from dateutil.tz import *
import urllib2
from xml.dom import minidom
import simplegeo
import json
import keys

urls = (
  #Product site.
  '/','Index',
  
  #place lookup...
  '/place/(.*),(.*)/(.*)', 'ToponymLookup',
)
app = web.application(urls, globals(), autoreload=True)
application = app.wsgifunc()

render = web.template.render('templates/')

class Index:
  def GET(self):
    return render.index()

class ToponymLookup:
  
  lat=0
  lng=0
  
  services=['flickr','yelp','simplegeo','geoplaces','nytimes']
  
  def GET(self,lat_str,lng_str,service='geoplaces'):
    
    self.lat = float(lat_str)
    self.lng = float(lng_str)
    
    if service in self.services:
      result = getattr(self,service)()
      return json.dumps(result)
    else:
      return ""
  
  
  def flickr(self):
    #flickr
    name1=None
    name2=None
    try:
      url = "http://api.flickr.com/services/rest/?method=flickr.places.findByLatLon&api_key=%s&lat=%f&lon=%f" % (keys.FLICKR_API_KEY,self.lat,self.lng)
      dom = minidom.parse(urllib2.urlopen(url))
      
      s = dom.getElementsByTagName('place')[0].getAttribute('name')
      place_type = dom.getElementsByTagName('place')[0].getAttribute('place_type')
      
      names = s.split(',')
      if place_type == 'neighbourhood':
        name1 = names[0]
        if len(names) > 1:
          name2 = names[1]
      else:
        name2 = names[0]
    except Exception, e:
      return (0,str(e))
    return (1,name1,name2)

  def simplegeo(self):
    name1=None
    name2=None
    try:
      client = simplegeo.Client(keys.SIMPLEGEO_API_KEY,keys.SIMPLEGEO_API_SECRET)
      results =  client.get_contains(self.lat,self.lng)
      for result in results:
        if result['type'] == 'Neighborhood':
          name1 = result['name']
        elif result['type'] == 'City':
          name2 = result['name']
    except Exception, e:
      return (0,str(e))
    return (1,name1,name2)
  
  def yelp(self):
    name1=None
    name2=None
    
    try:
      url = "http://api.yelp.com/neighborhood_search?lat=%f&long=%f&ywsid=%s" % (self.lat,self.lng,keys.YELP_API_KEY)
      response = urllib2.urlopen(url).read()
      obj = json.loads(response)
      if obj['message']['code'] == 0:
        neighborhoods = obj['neighborhoods']
        for hood in neighborhoods:
          if name1:
            name1 += ","
          name1 = hood['name']
          name2 = hood['city']
    except Exception, e:
      return (0,str(e))
    return (1,name1,name2)
  
  def geoplaces(self):
    name1=None
    name2=None
    try:
      url = "http://ws.geonames.org/findNearbyJSON?featureCode=PPL&maxRows=1&lat=%s&lng=%s" % (self.lat,self.lng)
      response = urllib2.urlopen(url).read()
      obj = json.loads(response)
      name1 = obj['geonames'][0]['name']
      name2 = obj['geonames'][0]['adminCode1']
    except Exception, e:
      return (0,str(e))
    return (1,name1,name2)

  def nytimes(self):
    name1=None
    name2=None
    try:
      url = "http://api.nytimes.com/svc/politics/v2/districts.json?&lat=%s&lng=%s&api-key=%s" % (self.lat,self.lng,keys.NYTIMES_KEY)
      response = urllib2.urlopen(url).read()
      obj = json.loads(response)
      for value in obj['results']:
        if value['level'] == 'Neighborhood':
          name1=value['district']
        if value['level'] == 'Borough':
          name2=value['district']
    
    except urllib2.HTTPError, httpErr:
      if httpErr.code != 404:
        return (0,str(e))
    except Exception, e:
      return (0,str(e))
    return (1,name1,name2)




if __name__ == "__main__": app.run()

