# novelTTS
小说本地阅读方案，包括Windows电脑，安卓手机及docker方案

1. Windows 10/11 x64电脑
1.1 Balabolka
   老牌，大文件打开慢。
   下载并安装Balabolka阅读软件：https://www.cross-plus-a.com/cn/balabolka.htm

   TTS:
   下载并安装中文语音-微软晓晓和云希语音：https://www.cross-plus-a.com/cn/voice.htm

   下载本地语音调用：https://github.com/gexgd0419/NaturalVoiceSAPIAdapter/releases
   解压，双击exe，选择32位，安装。balabolka支持32位，不支持64位。
   在NaturalVoiceSAPIAdapter的github页面下载的微软本地语音，不能被调用。

1.2 Anx-Reader
   有一定概率无法调用本地TTS。
   下载地址：https://anx.anxcye.com/
    
    TTS: 
    下载并安装中文语音-微软晓晓和云希语音：https://www.cross-plus-a.com/cn/voice.htm

    下载本地语音调用：https://github.com/gexgd0419/NaturalVoiceSAPIAdapter/releases
    解压，双击exe，选择64位，安装。

2. 安卓手机
    阅读软件：https://github.com/gedoor/legado
    TTS:
    一加手机自带TTS还不错，断句没问题。
    multiTTS: 部分文档断句有问题.不保证原版：https://bbs.tatans.cn/topic/98140

3. Docker
   推荐虚拟机安装istoreOS，有htreader，一键安装。
   https://github.com/hectorqin/reader

4. 类似听歌的桌面歌词模式，Windows 10-11 x64设备
   先安装TTS语音：
      下载并安装中文语音-微软晓晓和云希语音：https://www.cross-plus-a.com/cn/voice.htm
      下载本地语音调用：https://github.com/gexgd0419/NaturalVoiceSAPIAdapter/releases
       解压，双击exe，选择64位，安装。

   小说转音频：https://github.com/Mai-Onsyn/VeloVoice
   双击exe，打开后，在设置界面改为中文。先删除原提示文件。
   先在“文本处理”中选择小说位置，点击加载。在“音频处理”中启用字幕。
   在"TTS"中选择音频保存位置，选择TTS引擎及语音，并调整语速。点击开始，立即生成wav音频文件及srt字幕。
   左侧有几个小说文件，就生成多少个音频文件及字幕文件。对于长小说，可以自行拆分，或者用在线小说拆分工具。

   字幕文件转换：
   听歌软件不识别srt文件，需要先转换为lrc文件。
   字幕的单行长度常常过长，可读性较差，需要分割。
   subtitle edit: https://github.com/SubtitleEdit/subtitleedit
   在设置中选择单行最大长度及最多行数，导入srt文件，全选字幕，点击自动换行。
   在“工具-分割长行”中，选择单行最大长度和行最大长度，点击确认。
   重复自动换行和分割长行，直至单行长度符合要求。
   文件-另存为，选择lrc后缀的第一个。

   桌面歌词模式播放：
   Musicplayer2: https://github.com/zhongyang219/MusicPlayer2
   将音频文件与lrc字幕文件放在同一个文件夹，用musicplayer2打开，点击播放条上方“词”，就可以显示桌面歌词。

   如果不想用桌面歌词模式，能接受长字幕，可以用potplayer打开wav文件和srt文件。
