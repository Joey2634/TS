# coding=utf-8
import sys, os, shutil

#安装包文件名
ctsVer = '1.208_Test'

eggFile = 'CTSlib-' + ctsVer + '_py' + str(sys.version_info[0]) + str(sys.version_info[1]) + '.egg'

#获取安装包的绝对路径，与setyp.py在同一目录中
if os.name == "nt":
    eggPath = os.path.abspath(os.path.split(os.path.realpath(__file__))[0] + '\\' + eggFile)
else:
    eggPath = os.path.abspath(os.path.split(os.path.realpath(__file__))[0] + '/' + eggFile)

def uninstall():
    '''
    卸载CTSlib安装包
    '''
    
    #在系统环境变量中，查找ctslib安装路径
    ctsPath = []
    for x in sys.path:
        x = os.path.abspath(x)
        if x.lower().find('ctslib') > 0:
            ctsPath.append(x)
            print(x)
    
    if (len(ctsPath) == 0):
        print (u'CTSlib未安装')
        return
    
    #切换当前工作目录
    if os.name == "nt":
        os.chdir(sys.prefix + '\Scripts')
   
    #执行卸载命令
    result = os.popen('easy_install --m CTSlib')
    
    #打印卸载信息
    print(result.read())
    
    #删除ctslib安装目录
    for x in ctsPath:
        print(('remove dir:' + x))
        shutil.rmtree(x, True)
    
    noRemove = []
    #验证卸载是否成功
    for x in ctsPath:
        if (os.path.exists(x)):
            noRemove.append(x)
    
    if (len(noRemove) != 0):
        print (u'卸载失败，以下目录未删除成功：')
        for x in noRemove:
            print (x)
    else:
        print (u'卸载成功')
    
def install():
    '''
    安装CTSlib安装包
    '''

    #切换当前工作目录
    if os.name == "nt":
        os.chdir(sys.prefix + '\Scripts')

    #执行安装命令
    result = os.popen('easy_install ' + eggPath)
    
    #打印安装信息
    print(result.read())

    #安装完成
    print(u'安装成功')


if len(sys.argv) >= 2:
    if (sys.argv[1] == 'install'):
        if (not os.path.exists(eggPath)):
            print((u'文件不存在:' + eggPath))
            exit()

        print (u'开始卸载旧版本CTSlib安装包')
        uninstall()
        
        print (u'开始安装')
        install()
        
    elif(sys.argv[1] == 'uninstall'):
        print (u'开始卸载')
        uninstall()
        
    else:
        print (u'参数错误，请输入参数 install/uninstall')
        
else:
    uninstall()
    print (u'请输入参数 install/uninstall')
