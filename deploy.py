# -*- coding: utf-8 -*
#!/usr/bin/env python

"""
bluewind 批量部署脚本，实现了批量执行linux命令；批量使用rsync进行增量部署
@author     chenz
@version    1.0
@date       2013/8/8 
"""

import pexpect
import threading
import logging
from logging.handlers import RotatingFileHandler


copyr = """
***********************************************************
******* bluewind batch deploy script ---- by chenz ********
***********************************************************
"""
print copyr

#日志模块配置
logging.basicConfig(level=logging.DEBUG,
                format='%(asctime)s %(levelname)s %(message)s',
                datefmt='%a, %d %b %Y %H:%M:%S',
                )
#################################################################################################
#定义一个RotatingFileHandler，最多备份5个日志文件，每个日志文件最大1M
Rthandler = RotatingFileHandler('./log/deploy.log', maxBytes=1*1024*1024,backupCount=5)
Rthandler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(filename)s  %(levelname)s   %(message)s')
Rthandler.setFormatter(formatter)
logging.getLogger('').addHandler(Rthandler)
################################################################################################

#logging.debug('This is debug message')
#logging.info('This is info message')
#logging.warning('This is warning message')

#用户列表
testUser = {'user':'test','password':'****'}# test 用户
rootUser1 = {'user':'root','password':'****'}# root 用户1 www
rootUser3 = {'user':'root','password':'****'}# root 用户2 www
rootUser2 = {'user':'root','password':'****'}# root 用户2 uat

#生产环境主机列表
wwwHosts = [
    #
    {'ip':'10.0.204.199','testUser':testUser,'rootUser':rootUser1,'path':['read1','read2','write']},
    {'ip':'10.0.204.200','testUser':testUser,'rootUser':rootUser1,'path':['read1','read2','write']},
    {'ip':'10.0.204.201','testUser':testUser,'rootUser':rootUser1,'path':['read1','read2','write']},
    {'ip':'10.0.204.202','testUser':testUser,'rootUser':rootUser1,'path':['read1','read2','write']},
    {'ip':'10.0.204.203','testUser':testUser,'rootUser':rootUser1,'path':['read1','read2','write']},
    {'ip':'10.249.22.4','testUser':testUser,'rootUser':rootUser3,'path':['read1','read2','write']},
    {'ip':'10.249.22.8','testUser':testUser,'rootUser':rootUser3,'path':['read1','read2','write']},
    {'ip':'10.249.22.11','testUser':testUser,'rootUser':rootUser3,'path':['read1','read2','write']},
    {'ip':'10.249.22.12','testUser':testUser,'rootUser':rootUser3,'path':['read1','read2','write']},
    {'ip':'10.249.22.19','testUser':testUser,'rootUser':rootUser3,'path':['read1','read2','write']},
    {'ip':'10.249.22.20','testUser':testUser,'rootUser':rootUser3,'path':['read1','read2','write']},
    #搜索服务器
    {'ip':'10.0.204.195','testUser':testUser,'rootUser':rootUser1,'path':['searchEngine','searchEngine2','searchEngine3']},
    {'ip':'10.0.204.196','testUser':testUser,'rootUser':rootUser1,'path':['searchEngine1','searchEngine2','searchEngine3']}
]

#UAT环境主机列表
uatHosts = [
    {'ip':'10.0.204.204','testUser':testUser,'rootUser':rootUser2,'path':['read1','read2','write','searchEngine']},
    #{'ip':'178.18.17.175','testUser':testUser,'rootUser':rootUser1,'path':['read1','read2','write']}
]

#命令列表
cmdList = ['eshopshutdown','eshopreboot','chown -R test /jboss','chmod -R 777 /jboss','chmod -R 755 /jboss','df']

# 批量执行linux命令，su 到root后执行，只能执行单条命令
#user: ssh 主机的用户名
#host：ssh 主机的域名
#password：ssh 主机的密码
#command：即将在远端 ssh 主机上运行的命令
def sshCmd(host, command):
    ssh_newkey = 'Are you sure you want to continue connecting'
    ip = host['ip']
    # test 用户
    user = host['testUser']['user']
    password = host['testUser']['password']
    # root 用户
    rootPass = host['rootUser']['password']
    child = pexpect.spawn('ssh %s@%s'%(user, ip))
    i = child.expect([pexpect.TIMEOUT, ssh_newkey, 'password: '])
    if (i == 0):
        logging.error('SSH could not login. Here is what SSH said:')
        logging.error(child.before, child.after) 
        return None
    elif (i == 1):
        child.sendline ('yes')
        child.expect('password: ')
        child.sendline(password)
        logging.info('---------------------1.login successfully!')
        #return child
    else:
        child.sendline(password)
        logging.info('---------------------2.login successfully!')
        #return child
    # 切换用户
    #child.expect('')
    child.sendline('su - root')
    child.expect('[pP]assword: ')
    child.sendline(rootPass)
    #child.expect('')
    #执行命令
    child.sendline(command)
    child.sendline('exit')
    child.sendline('exit')
    return child
    
 

# 批量部署，利用rsync增量发布
def batchDeploy(cType): 
    if(cType == 1):
        remoteHosts = uatHosts
        msg = 'uat'
    elif(cType == 2):
        remoteHosts = wwwHosts
        msg = 'www'
        
    logging.info('-------------------------start deploy all hosts!------------------------')
    for host in remoteHosts:
        logging.info('--------------------------- deploying  ' + host['ip'])
        ssh_newkey = 'Are you sure you want to continue connecting'
        for path in host['path']:
            print 'deploying' + path
            child = pexpect.spawn('rsync -rltDvu /home/aiuap_jc/deploy/deploySrc/eshop.war/ test@'+host['ip']+':/jboss/eshop/jboss_'+path+'/server/web/deploy/eshop.war')
            i = child.expect([pexpect.TIMEOUT, ssh_newkey, 'password: '])
            if (i == 0):
                logging.error('SSH could not login. Here is what SSH said:')
                logging.error(child.before, child.after)
                return None
            elif (i == 1):
                child.sendline ('yes')
                child.expect('[pP]assword: ')
                logging.info('---------------------1.login successfully!')
                #return child
            else:
                #
                logging.info('---------------------2.login successfully!')
                #return child
                
            child.sendline(host['testUser']['password'])
            child.expect(pexpect.EOF)
            logging.info(child.before)
            #关闭连接
            #child.sendline('exit')
            child.close()
       
    logging.info('-------------------deploy is over!')

#批量执行命令
def batchCmd(ctype,cmd):
    #ctype = int(raw_input('please select the command type: 1-uat;2-www \(input 1 or 2\)'))
 
    if(ctype == 1):
        remoteHosts = uatHosts
        msg = 'uat'
    elif(ctype == 2):
        remoteHosts = wwwHosts
        msg = 'www'
    if(cmd==''):
       cmd = int(raw_input('please select the command: 1-shutdown all hosts 2-reboot all hosts \(input 1 or 2\)'))
    #要执行的命令
    cmdStr = cmdList[cmd-1]
    
    #输出提示语
    logging.info('---------------------now \"' + msg + '\" start execute \"' + cmdStr + '\" !------------------------')
    
    for host in remoteHosts:
        logging.info('---------------------' + host['ip'] + ' on duty')
        child = sshCmd(host,cmdStr)
        #child.sendline('\r')
        child.expect(pexpect.EOF)
        print child.before
        #关闭连接
        #child.sendline('exit')
        child.close()
    
    logging.info('---------------------now \"' + msg + '\" execute \"' + cmdStr + '\" is over !------------------------\n')

#批量清除缓存
def batchClean(ctype):
    #ctype = int(raw_input('please select the command type: 1-uat;2-www \(input 1 or 2\)'))
 
    if(ctype == 1):
        remoteHosts = uatHosts
        msg = 'uat'
    elif(ctype == 2):
        remoteHosts = wwwHosts
        msg = 'www'
   
    
    #输出提示语
    logging.info('---------------------now \"' + msg + '\" start execute clean" !------------------------')
    
    for host in remoteHosts:
        for path in host['path']:
            cmdStr = 'rm -f /jboss/eshop/jboss_'+path+'/server/web/log/*;rm -rf /jboss/eshop/jboss_'+path+'/server/web/work/*;rm -rf /jboss/eshop/jboss_'+path+'/server/web/tmp/*'
            logging.info('---------------------' + host['ip'] + ' on duty')
            child = sshCmd(host,cmdStr)
            #child.sendline('\r')
            child.expect(pexpect.EOF)
            print child.before
            #关闭连接
            #child.sendline('exit')
            child.close()
    
    logging.info('---------------------now \"' + msg + '\" execute clean" is over !------------------------\n')

#备份程序
def backupProject(hostType):
    host = wwwHosts[0]#备份保存的主机
    cmdStr = 'tar -zcvf /home/aiuap_jc/deploy/backup/eshop.tar.gz --exclude-from=/home/aiuap_jc/deploy/exclude.txt -C /jboss/eshop/jboss_read1/server/web/deploy/eshop.war .'

    if(hostType==1):
        host = uatHosts[0]
        #debug
    child = sshCmd(host,cmdStr)
    #child.sendline('\r')
    child.expect(pexpect.EOF)
    print child.before
    logging.info('---------------------now execute backup command------------------------')
    #关闭连接
    #child.sendline('exit')
    child.close()

#发布回滚，目前只能回滚到上一个版本
def deployRollback(hostType):
    #解压命令
    cmdStr = 'tar -zxvf /home/aiuap_jc/deploy/backup/eshop.tar.gz -C /home/aiuap_jc/deploy/deploySrc/eshop.war'
    #批量部署
    batchDeploy(hostType)

def main():
    #选择执行命令的主机
    hostType = int(raw_input('please select the host type: 1-----uat;2-----www;\n\(input 1or2\)'))
    #选择命令的类型
    #1：批量执行ssh命令
    #2：批量rsync发布
    #3：一键执行部署命令（带备份）
    #4：一键执行部署命令（不备份）
    #5：版本回滚
    #6：待定
    dtype = int(raw_input('please select the command type:\n\
                          1-batch execute ssh;\n\
                          2-batch excute rsync deploy;\n\
                          3-onekey deploy with backup \n\
                          4-onekey deploy without backup \n\
                          5-backup project \n\
                          6-version rollback \n\
                          7-clean cache \n\
                          (input 1,2,3,4,5,6,7\)? '))
    
    if(dtype==1):
        batchCmd(hostType,'')
    elif(dtype==2):
        batchDeploy(hostType)
    elif(dtype==3):
        batchCmd(hostType,1)
        backupProject(hostType)
        batchDeploy(hostType)
        batchCmd(hostType,2)
    elif(dtype==4):
        batchCmd(hostType,1)
        batchDeploy(hostType)
        batchCmd(hostType,2)
    elif(dtype==5):
        backupProject(hostType)
    elif(dtype==6):
        deployRollback()
    elif(dtype==7):
        batchClean(hostType)
#分布命令；一键部署UAT，一键部署www；回滚  

if __name__=='__main__':
    main()
    #batchDeploy()
    #
    
