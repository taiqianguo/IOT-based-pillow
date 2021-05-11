import config
import RPi.GPIO as GPIO
import time
import datetime
import schedule #定时执行
import requests
import smbus
import config #跨文件调用参数，参数都在config
import json
from ads1015 import ADS1015

APIKEY = 'zieeHiHqPsN1NeCUPFZ3SHHouKs='

DEVICE_BUS = 1
DEVICE_ADDR = 0x17

TEMP_REG = 0x01
LIGHT_REG_L = 0x02
LIGHT_REG_H = 0x03
STATUS_REG = 0x04
ON_BOARD_TEMP_REG = 0x05
ON_BOARD_HUMIDITY_REG = 0x06
ON_BOARD_SENSOR_ERROR = 0x07
BMP280_TEMP_REG = 0x08
BMP280_PRESSURE_REG_L = 0x09
BMP280_PRESSURE_REG_M = 0x0A
BMP280_PRESSURE_REG_H = 0x0B
BMP280_STATUS = 0x0C
HUMAN_DETECT = 0x0D

bus = smbus.SMBus(DEVICE_BUS)
aReceiveBuf = []
aReceiveBuf.append(0x00) 


bagport1_in=23
bagport1_de=24
bagport2_in=25
bagport2_de=16
bagport3_in=17 
bagport3_de=27
bagport4_in=22
bagport4_de=5


is_sleep=1
weak_count=0#数值大到一定程度判断结束睡眠
is_snore =0
snore_freq=0#打呼噜的频率，被检测到的次数
snore_frequence=0
sleep_time=[1,2]
pressure=0#枕头上的压力
pressure0=0#上一次枕头的压力
light=[]
temp=[]
humidity=[]
air_pressure=[]
Turn_over_count=0 #转身次数
bad_weak_up=0 #起夜次数（或元组？)
head_position=0#头的位置


def Motor_action(on_which_gasbag,inflate_deflate):
    
    GPIO.setwarnings(False)
    GPIO.cleanup()
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(bagport1_in,GPIO.OUT)
    GPIO.setup(bagport1_de,GPIO.OUT)
    GPIO.setup(bagport2_in,GPIO.OUT)
    GPIO.setup(bagport2_de,GPIO.OUT)
    GPIO.setup(bagport3_in,GPIO.OUT)
    GPIO.setup(bagport3_de,GPIO.OUT)
    GPIO.setup(bagport4_in,GPIO.OUT)
    GPIO.setup(bagport4_de,GPIO.OUT) #fenbieduiying1234qinang
    #zhexieyinggaifangchuqu
    
    if on_which_gasbag==1 and inflate_deflate=='inflate':
        GPIO.output(bagport1_in,GPIO.HIGH)
        GPIO.output(bagport1_de,GPIO.LOW)
        time.sleep(10)
    elif on_which_gasbag==1 and inflate_deflate=='deflate':
        GPIO.output(bagport1_in,GPIO.LOW)
        GPIO.output(bagport1_de,GPIO.HIGH)
        time.sleep(10)
    elif on_which_gasbag==2 and inflate_deflate=='inflate':
        GPIO.output(bagport2_in,GPIO.HIGH)
        GPIO.output(bagport2_de,GPIO.LOW)
        time.sleep(10)
    elif on_which_gasbag==2 and inflate_deflate=='deflate':
        GPIO.output(bagport2_in,GPIO.LOW)
        GPIO.output(bagport2_de,GPIO.HIGH)
        time.sleep(10)
    elif on_which_gasbag==3 and inflate_deflate=='inflate':
        GPIO.output(bagport3_in,GPIO.HIGH)
        GPIO.output(bagport3_de,GPIO.LOW)
        time.sleep(10)
    elif on_which_gasbag==3 and inflate_deflate=='deflate':
        GPIO.output(bagport3_in,GPIO.LOW)
        GPIO.output(bagport3_de,GPIO.HIGH)
        time.sleep(10)
    elif on_which_gasbag==4 and inflate_deflate=='inflate':
        GPIO.output(bagport4_in,GPIO.HIGH)
        GPIO.output(bagport4_de,GPIO.LOW)
        time.sleep(10)
    elif on_which_gasbag==4 and inflate_deflate=='deflate':
        GPIO.output(bagport4_in,GPIO.LOW)
        GPIO.output(bagport4_de,GPIO.HIGH)
        time.sleep(10)


def get_head_position():#得到一个离散的包含姿态的字典
    global is_sleep
    from face_pose4 import face
    face()
    pitch=111#test_value
    global head_position#1平，0侧
    if pitch>=180:
        head_position=1
    if pitch<180:
        head_position=0
    if is_sleep==0:
        return schedule.cancel_job

def get_snore():#判断是否在打呼噜,并记录打呼噜的频率
    global is_sleep
    global snore_freq
    #from sopare import id
    global is_snore
    is_snore=int(1)
    if is_snore==1:
        snore_freq=snore_freq+1
    if is_sleep==0:
        return schedule.cancel_job

     
def get_pillow_pressure():#枕头压力,并判断与上一次调用时是否翻身,以及是否起夜
    global pressure
    global pressure0
    global Turn_over_count
    global bad_weak_up
    global is_sleep
    import time
   
 
    CHANNELS = ['in0/ref', 'in1/ref', 'in2/ref']
    pressure0=pressure
      #更新枕头压力
    ads1015 = ADS1015()
    ads1015.set_mode('single')
    ads1015.set_programmable_gain(2.048)
    ads1015.set_sample_rate(3600)
    reference = ads1015.get_reference_voltage()
    pressure = ads1015.get_compensated_voltage('in0/ref', reference_voltage=reference)
    print(pressure)
    if abs(pressure-pressure0)>20 and pressure!=0:#这里要实际测一下
        Turn_over_count= Turn_over_count+1
    if pressure!=0 and pressure!=pressure0:
        bad_weak_up=bad_weak_up+1
    if is_sleep==0:
        return schedule.cancel_job


def get_env():#得到环境模块中的参数
    global aReceiveBuf
    global is_sleep
    for i in range(TEMP_REG,HUMAN_DETECT + 1):
      aReceiveBuf.append(bus.read_byte_data(DEVICE_ADDR, i))
    global temp
    temp.append(aReceiveBuf[TEMP_REG])
    global light
    light.append(aReceiveBuf[LIGHT_REG_H])
    http_put(aReceiveBuf[4],'light')
    global humidity
    humidity.append(aReceiveBuf[ON_BOARD_HUMIDITY_REG])
    global is_people
    is_people=aReceiveBuf[HUMAN_DETECT]
    global air_pressure
    air_pressure.append(aReceiveBuf[BMP280_PRESSURE_REG_L])
    if is_sleep==0:
        return schedule.cancel_job


def http_put(value,id):
    CurTime = datetime.datetime.now()
    url = 'http://api.heclouds.com/devices/684494714/datapoints'
    #这部分
    values = {'datastreams': [{"id": id, "datapoints": [{"at": CurTime.isoformat(), "value": value}]}]}
    headers = {'api-key': APIKEY}
    print("the time is: %s" % CurTime.isoformat())
   # print("The upload temperature value is: %.3f" % env)
    jdata = json.dumps(values).encode("utf-8")
    print(jdata)
    r = requests.post(url=url, headers=headers, data=jdata)
    
def up_load_bad_env():#当环境内某参数不适宜睡眠时，在微信小程序中做出提醒
    get_env()
    if aReceiveBuf[2]>=10:#室内光照过大
        http_put(aReceiveBuf[2],"light")
        #上传一句话：提示：您的室内过亮，科学研究表明，昏暗的环境有助于睡眠哦
    if  aReceiveBuf[1]>=28: #室温过高
        1#http_put(1,"env")
    if aReceiveBuf[1]<=10:#室温过低
        1#http_put(2,"env")
    if aReceiveBuf[6]<=10:#湿度过低
        1#http_put(3,"env")
    if aReceiveBuf[6]>=60:#注意防潮
        1#http_put(4,"env")
    if aReceiveBuf[10]<=90:#气压过低
        1#http_put(5,"env")
    #保留环境噪音参数


def schedule_tree():#当确认开始睡觉时，转到初始化，并开始执行事件树
    global is_sleep
    global sleep_time
    #鼓起全部气囊
    for i in range(4):
        Motor_action(i+1,'inflate')
    #记录环境变量，不合适时在微信小程序上打出提示
    up_load_bad_env()
    #每10分钟记录一次环境质量
    schedule.every(2).seconds.do(get_env)
    #每20s更新一次head_position
    schedule.every(2).seconds.do(get_head_position)
    #每20s执行一次枕头压力，并判断是否翻身
    schedule.every(1).seconds.do(get_pillow_pressure)
    #每20s判断是否打呼噜
    schedule.every(1).seconds.do(get_snore)
    #每2s执行一次main函数
    schedule.every(2).seconds.do(main_controller)
    #判断是否睡醒
    schedule.every(2).seconds.do(weak_up_judge)
    #记录开始本次开始睡眠的时间
    if is_sleep==True:
        sleep_time[0]=time.localtime(time.time ())
    if is_sleep==0:
        sleep_time[0]=time.localtime(time.time ())
        end_one_sleep()


def main_controller():#执行枕头的实时判断和调节功能
    global is_snore
    global is_sleep
    global head_position
    if is_snore==0 and head_position==1:
        Motor_action(1,'inflate')
        Motor_action(2,'deflate')
        Motor_action(3,'inflate')
        Motor_action(4,'inflate')
    if is_snore==1 and head_position==1:
        Motor_action(1,'inflate')
        Motor_action(2,'inflate')#升一半
        Motor_action(3,'inflate')
        Motor_action(4,'deflate')
    if is_snore==0 and head_position==0:
        Motor_action(1,'inflate')
        Motor_action(2,'inflate')#升一半
        Motor_action(3,'inflate')
        Motor_action(4,'deflate')
    if is_snore==0 and head_position==0:
        Motor_action(1,'inflate')#三个气囊各升一半
        Motor_action(2,'inflate')
        Motor_action(3,'inflate')
        Motor_action(4,'deflate')


def sleep_judge():
    global is_sleep
    get_pillow_pressure()
    if pressure>=-1:#如果感应到压力，则执行schedule_tree,结束判断是否正在睡觉
        schedule_tree()
        is_sleep=1
        return schedule.cancel_job


def weak_up_judge():
    global pressure
    global pressure0
    global weak_count
    if pressure<-6 and pressure0<-6:
        weak_count=weak_count+1
    else :
        weak_count=0
    if weak_count>=1:#大约10分钟
        is_sleep=0
        return schedule.cancel_job
        
     
def end_one_sleep():
    deltahour=end.tm_min-start.tm_min
    deltasec=end.tm_sec-start.tm_sec
    if deltasec<0:
       deltasec=+60
       deltahour=-1
    if deltahour<0:
       deltahour=+24
    sleep_time=(deltahour,deltasec)

#记录睡眠

#上传数据
    http_put((deltahour,deltasec),"sleep_time")
#重置变量
    #file= open('', 'w')
    #file.write('')
#开始执行的第一句
    global is_sleep
    if is_sleep==0:
         schedule.every(1).seconds.do(sleep_judge)

       
#开始执行的第一句
schedule.every(1).seconds.do(sleep_judge)


while True:
    schedule.run_pending()
    time.sleep(2)