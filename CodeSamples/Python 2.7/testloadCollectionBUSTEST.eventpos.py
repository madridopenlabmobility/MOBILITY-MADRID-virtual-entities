'''
Created on 1 de jun. de 2016

@author: anrecio
This example shows how do seekings time arrive to a EMT stop (stopfindBusTest) using EMT Opendata API.
Once this, each buses that will arrive at stop are asking about their position and data using EMT myBus API.
Finally, each data collected are storaged into MobilityLabs system using AMPQ.
(Data it is possible monitoring using RB data portal http://rbmobility.emtmadrid.es:3333 with same credentials)
'''
import urllib
import urllib2
from VEUtils.pysimplesoap import client
from VEUtils.pysimplesoap.client import SoapClient
from VEUtils import xmltodict
from VEUtils.geo import geoconversion

import  VEUtils.simplejson as json
import datetime


import time
import pika
import json

  
      
stopFindBusTest=72
urlGetFindBusTest="https://openbus.emtmadrid.es:9443/emt-proxy-server/last/geo/GetArriveStop.php"

useragent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
#params = {'idClient' : 'EMT.SERVICIOS.OPENBUS','passKey' : 'A2C983E5-5BA3-41F3-B47C-428F467041DC','idStop' : stopFindBusTest}
params = {'idClient' : 'mobilitylabs.usertest','passKey' : 'usertest','idStop' : stopFindBusTest}
headers = { 'User-Agent' : useragent,'Content-type':'application/x-www-form-urlencoded' }

data = urllib.urlencode(params)
req = urllib2.Request(urlGetFindBusTest, data, headers)
response = urllib2.urlopen(req)
results = response.read()
resultJson = json.loads(results)
vep_data=[]
if resultJson.has_key('arrives'):
    resultJsonbus = resultJson['arrives']
    bucles=0
    myBusTest = 0
    while bucles < 50:
        
        for results in resultJsonbus:
            print results
            datagram = {}
            datagramHeader={}
            #if myBusTest == 0:
            myBusTest = results['busId']
            print "accesing to bus Id..."+myBusTest
            urlbus = "https://mybus.emtmadrid.es:8073/rests"
            params="?srv=DatosCoche&Paradas=99&bus="+myBusTest
            aut_h = urllib2.HTTPPasswordMgrWithDefaultRealm()  
            aut_h.add_password(None, urlbus,  "EMT.SERVICIOS.OPENBUS",  "A2C983E5-5BA3-41F3-B47C-428F467041DC")  
            handler = urllib2.HTTPBasicAuthHandler(aut_h)
            opener = urllib2.build_opener(handler)  
            urllib2.install_opener(opener)  
            
            response = urllib2.urlopen(urlbus+params)
            results = response.read()
            print results
            
            valueDict = xmltodict.parse(results)
                        
            myCoordinates = [0,0]
            idBus = "0000".encode("utf-8")
            idLine = '000'.encode("utf-8")
            idTrip = "0000".encode("utf-8")
            direction = "0".encode("utf-8")
            status = "0".encode("utf-8")
            delay = "0".encode("utf-8")
            idStop = "0".encode("utf-8")
            estado = "0".encode("utf-8")
            textStop = "####".encode("utf-8")
            offSet = "0".encode("utf-8")
            Z="0".encode("utf-8")
            dataPos = ["0","0"]
            driver =   "0".encode("utf-8") 
    
            if valueDict.has_key('DatosCoche'):
    
                busValue = valueDict['DatosCoche']
                if busValue.has_key('vehiculo'):
                    idBus = str(busValue['vehiculo']).encode("utf-8")
                if busValue.has_key('linea'):
                    idLine = str(busValue['linea']).encode("utf-8")
                if busValue.has_key('viaje'):
                    idTrip = str(busValue['viaje']).encode("utf-8")
                if busValue.has_key('sentido'):
                    direction = str(busValue['sentido']).encode("utf-8")
                if busValue.has_key('estado'):
                    status = str(busValue['estado']).encode("utf-8")
                if busValue.has_key('desfase'):
                    delay = str(busValue['desfase']).encode("utf-8")
                if busValue.has_key('posicion'):
                    offSet = str(busValue['posicion']).encode("utf-8")
                X=0
                Y=0
                if busValue.has_key('gps'):
                    busGps = busValue['gps']
                    if busGps.has_key('@est'):
                        X=busGps['@est']
                    else:
                        X=0
                    if busGps.has_key('@nor'):
                        Y=busGps['@nor']
                    else:
                        Y=0
                    if busGps.has_key('@zone'):
                        zone=busGps['@zone']
                    else:
                        zone=0
                    
                    if X > 0 and Y > 0:
                        dataPos = geoconversion.to_latlon(float(X), float(Y), int(zone), "S") 
                    else:
                        dataPos = [X,Y]
                    
                    if busGps.has_key('@alt'):
                        Z=str(busGps['@alt']).encode("utf-8")
                    else:
                        Z="0".encode("utf-8")
                    if busValue.has_key('enParada'):
                        dataStop = busValue['enParada']
                        idStop = str(dataStop['@codigo']).encode("utf-8")
                        textStop = str(dataStop['#text']).encode("utf-8")
                        
                        
                    msgLog = " coorx"+str(dataPos[1])+"coort"+str(dataPos[0])
            
                    print msgLog 
            
                    myCoordinates = [str(dataPos[1]),str(dataPos[0])]
            
                pointData =   {'type':'Point','coordinates':myCoordinates}
    
    
                extraposition={'bus':idBus,"line":idLine,"trip":idTrip,"direction":direction,"status":status,"delay":delay,"stop":idStop,"name":textStop,"offSet":offSet,"altitude":Z,'geometry':pointData}
                datagramHeader["layerData"]={}
                datagramHeader["layerData"]["_id"]=idBus
                datagramHeader["layerData"]["system"]= "LAYERS"
                datagramHeader["layerData"]["subsystem"]="PUTDATA"
                datagramHeader["layerData"]["function"]="REPLACE"
                datagramHeader["layerData"]["layer"]={}
                datagramHeader["layerData"]["layer"]["owner"]="mobilitylabs.usertest"
                datagramHeader["layerData"]["layer"]["type"]="SHARED"
                datagramHeader["layerData"]["layer"]["name"]="BUSTEST.eventpos"
                datagramHeader["layerData"]["geometry"]=pointData
                datagramHeader["layerData"]["shape"]={}
                datagramHeader["layerData"]["shape"]["type"]="marker"
                datagramHeader["layerData"]["shape"]["options"]={}
                datagramHeader["layerData"]["shape"]["options"]["shape"]="circle"
                datagramHeader["layerData"]["shape"]["options"]["markerColor"]="blue"
                datagramHeader["layerData"]["shape"]["options"]["prefix"]="fa"
                datagramHeader["layerData"]["shape"]["options"]["icon"]="fa-car"
                datagramHeader["layerData"]["instant"]=str(datetime.datetime.utcnow())
                datagramHeader["layerData"]["busState"]={}
                datagramHeader["layerData"]["busState"]["idLine"]=idLine
                datagramHeader["layerData"]["busState"]["trip"]=idTrip
                datagramHeader["layerData"]["busState"]["direction"]=direction
                datagramHeader["layerData"]["busState"]["status"]=status 
                datagramHeader["layerData"]["busState"]["delay"]=delay 
                datagramHeader["layerData"]["busState"]["offset"]=offSet
                textStatus = "<b><p>Bus Number:"+idBus+"</p><p>Line Number:"+idLine+"</p></b>"
                datagramHeader["layerData"]["state"]={}           
                datagramHeader["layerData"]["state"]["description"]=textStatus
                datagramHeader["layerData"]["state"]["format"]  = "text"
                vep_data.append(datagramHeader)

                         
                datagram["target"]="datagramServer"
                datagram["vep_data"]=vep_data
                user = "mobilitylabs.usertest"
                credentSend = pika.PlainCredentials(user, "usertest")
                #hostSend = '192.168.14.200'
                hostSend = "amqp.emtmadrid.es"
                portSend = 5672
              
        
                connection = pika.BlockingConnection(pika.ConnectionParameters(hostSend, portSend, '/', credentSend))
        
                channel = connection.channel()
                strdatagram=str(datagram).replace("'", '"')
                channel.basic_publish(exchange='',
                                      routing_key='messages',
                                      body= strdatagram,
                                      properties=pika.BasicProperties(delivery_mode = 2, user_id = user))
        
                connection.close()
        time.sleep(5)
        bucles +=1
        
        
        
