TTSservice是基于Django搭建的web交互框架
使用前，将Tacotron2代码及模型文件放入TTSservice/Tacotron/中，模型放入logs-Tacotron/pre_trained/。
服务器端启动命令：python manage.py runserver 0.0.0.0:8000
在TTSservice/TTS/views.py中
①首先预加载Tacotron2模型，其中checkpoint为模型路径
②然后在每次接收到客户端请求后进入index函数，根据请求方式（POST/GET）传入相应参数，调用Crystal中函数对文本进行标准化处理，然后调用syn函数执行合成。
③服务器上合成音频的路径为：TTSservice/media/tacotron_output/logs-eval/wavs/[随机生成名].wav

RESTful API接口：
客户端脚本见API_demo.py（参照https://help.aliyun.com/document_detail/94737.html?spm=a2c4g.11186623.6.597.1cc1259eJFTS8I#h2-python-demo13） 
需要根据主机地址修改host，语音合成所用参数详细设置见代码。提供POST、GET两种请求方式，运行脚本成功交互后本地会生成音频文件（默认syAudio.wav）。
正确运行会响应：
Response status and response reason:
200 OK
audio/wav
The POST request succeed!
