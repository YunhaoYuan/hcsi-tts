# -*- coding: UTF-8 -*-
# Version：2020.7.18
# 使用说明：
# （1）修改合成参数，目前暂只支持修改文本text、发音人voice
# （2）可设置音频存放文件名，默认路径在同目录下
# （3）使用POST或GET方式访问API得到合成结果，正常运行显示：
# Response status and response reason:
# 200 OK
# The POST/GET request succeed!
#
import http.client
import urllib.parse
import requests
import json
def processGETRequest(appKey, token, text, audioSaveFile, format, sampleRate, voice, volume, speech_rate, pitch_rate) :
    host = 'hcclspeech.se.cuhk.edu.hk'
    url =  'https://'+host+'/TTS_API/'
    # 设置URL请求参数
    url = url + '?appkey=' + appKey
    url = url + '&token=' + token
    url = url + '&text=' + text
    url = url + '&format=' + format
    url = url + '&sample_rate=' + str(sampleRate)
    url = url + '&voice=' + voice
    url = url + '&volume=' + str(volume)
    url = url + '&speech_rate=' + str(speech_rate)
    url = url + '&pitch_rate=' + str(pitch_rate)
    print(url)
    conn = http.client.HTTPSConnection(host)
    conn.request(method='GET', url=url)
    # 处理服务端返回的响应
    response = conn.getresponse()
    print('Response status and response reason:')
    print(response.status ,response.reason)
    contentType = response.getheader('Content-Type')
    body = response.read()
    if 'audio/wav' == contentType :
        with open(audioSaveFile, mode='wb') as f:
            f.write(body)
        print('The GET request succeed!')
    else :
        print('The GET request failed: ' + str(body))
    conn.close()

def processPOSTRequest(appKey, token, text, audioSaveFile, format, sampleRate, voice, volume, speech_rate, pitch_rate) :
    host = 'hcclspeech.se.cuhk.edu.hk'
    url = 'https://' + host + '/TTS_API/'
    # 设置HTTPS Headers
    httpHeaders = {
        'Content-Type': 'application/json'
        }
    # 设置HTTPS Body
    body = {'appkey': appKey, 'token': token, 'text': text, 'format': format, 'sample_rate': sampleRate, 'voice': voice,
            'volume': volume, 'speech_rate': speech_rate, 'pitch_rate': pitch_rate}
    body = json.dumps(body)
    print('The POST request body content: ' + body)
    conn = http.client.HTTPSConnection(host)
    conn.request(method='POST', url=url, body=body, headers=httpHeaders)
    # 处理服务端返回的响应
    response = conn.getresponse()
    print('Response status and response reason:')
    print(response.status ,response.reason)
    contentType = response.getheader('Content-Type')
    body = response.read()
    if 'audio/wav' == contentType :
        with open(audioSaveFile, mode='wb') as f:
            f.write(body)
        print('The POST request succeed!')
    else :
        print('The POST request failed: ' + str(body))
    conn.close()

##调用API代码段：
#应用appkey
appKey = 'your_appkey'
#服务鉴权Token
token = 'your_token'
#待合成文本
text = '7月18日，深圳多云。'
#音频编码格式，可选wav，mp3，pcm，默认wav
format = 'wav'
#音频采样率，支持16000Hz、8000Hz，默认是16000Hz
sampleRate = 16000
# voice 发音人，可选0-9
#LJSpeech-1.1                       说话人0 英语     女
#DataBaker                          说话人1 普通话   女
#TTS.HUawei.zhcmn.F.Deng            说话人2 普通话   女
#TTS.Huawei.enus.F.XuYue   		    说话人3 英语     女
#TTS.THCoSS.zhcmn.F.M 03FR00 		说话人4 普通话   男
#TTS.THCoSS.zhcmn.F.M 03MR00  	    说话人5 普通话   女
#TTS.Pachira.zhcmn            		说话人6 普通话   女
#TTS.DataBaker.enus.M.DB1     	    说话人7 英语     男
#TTS.DataBaker.enus.F.DB1			说话人8 英语     女
#TTS.DataBaker.enus.F.DB2		    说话人9 英语     女
voice = '1'
# volume 音量，范围是0~100，可选，默认50
volume=50
# speech_rate 语速，范围是-500~500，可选，默认是0
speech_rate=0
# pitch_rate 语调，范围是-500~500，可选，默认是0
pitch_rate=0
#音频存放文件
audioSaveFile = 'syAudio.wav'
textUrlencode = text
textUrlencode = urllib.parse.quote_plus(textUrlencode)
textUrlencode = textUrlencode.replace("+", "%20")
textUrlencode = textUrlencode.replace("*", "%2A")
textUrlencode = textUrlencode.replace("%7E", "~")
print('text: ' + textUrlencode)
# GET 请求方式
#processGETRequest(appKey, token, textUrlencode, audioSaveFile, format, sampleRate, voice, volume, speech_rate, pitch_rate)
# POST 请求方式
processPOSTRequest(appKey, token, text, audioSaveFile, format, sampleRate, voice, volume, speech_rate, pitch_rate)
