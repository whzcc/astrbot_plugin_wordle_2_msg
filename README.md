# astrbot_plugin_wordle

Forked from [astrbot_plugin_wordle](https://github.com/Raven95676/astrbot_plugin_wordle)

Astrbot wordle游戏，支持指定位数

Astrbot wordle游戏，支持指定位数，加入了单词拼写检查（通过spellchecker库和自定词库之一即可）、自定义词库和显示字体（去main.py里替换掉"MinecraftAE.ttf"）、释义功能（写在插件目录的wordlist文件夹下的json文件）

如需替换词表，请替换插件根目录下的wordlist文件夹下的json文件，这里使用了[nonebot-plugin-wordle](https://github.com/noneplugin/nonebot-plugin-wordle)的单词表

插件会自动尝试安装“pyspellchecker”库，但建议手动在AstrBot目录中requirements.txt添加一行“pyspellchecker”
