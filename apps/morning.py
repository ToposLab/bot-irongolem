start("早安~准备好过上新的一天了吗？",(1,0,0))
do('灌热水到杯子里')
do("刷牙",["刷满2分钟","俯身","刷完清洗牙杯"])
if do('找衣服',['按dress code找到外衣','根据气温决定是否加毛衣','找好内裤和内衣']):
    do('洗澡', ['洗面奶','肥皂','沐浴露','洗发膏','干毛巾','干净的内裤','干净的内衣','塑料拖鞋'])
    do('穿上衣服')
    do('护肤', ['拍爽肤水', '涂防晒霜', '涂素颜霜', '涂遮瑕霜'])
    if ask('洗澡的时候洗头了吗？')=='是':
        do('吹头发')
do('剃胡须')
do('剪指甲', ['手指', '脚趾'])
do('涂润唇膏')
do('洗掉换下来的脏衣服')
do('出门买早点')