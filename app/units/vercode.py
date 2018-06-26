import random
import string
import os
import time
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

font = ImageFont.truetype(os.path.abspath(os.path.dirname(__file__)) + '/' + 'Note_this.ttf', 50)


# 随机数字
def rndNum():
    return str(random.randint(0, 9))


# 随机字母
def random_code(x, y):
    return ''.join([random.choice(x) for i in range(y)])


# 随机颜色
def rndColor():
    return (random.randint(64, 255), random.randint(64, 255), random.randint(64, 255))


# 随机颜色2:
def rndColor2():
    return (random.randint(0, 48), random.randint(0, 48), random.randint(0, 48))


# md5
def md5Encode(str):
    m = hashlib.md5()
    m.update(str)
    return m.hexdigest()


class VerCodeImg:

    def __init__(self):
        self.width = 240
        self.height = 60

    def create(self, savepath):

        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))

        # 创建Draw对象
        draw = ImageDraw.Draw(image)

        # 填充每个像素
        for x in range(self.width):
            for y in range(self.height):
                draw.point((x, y), fill=rndColor())

        # 组成文字
        rndCode = ''
        for t in range(4):
            num = rndNum()
            rndCode += num
            # 写入文字
            draw.text((60 * t + 20, 4), num, font=font, fill=rndColor2())

        # 模糊
        image = image.filter(ImageFilter.BLUR)

        # 文件名
        stringbase = string.ascii_letters + string.digits
        imgname = str(time.time()) + random_code(stringbase, 12)
        md5imgname = md5Encode(imgname.encode('utf-8'))

        image.save(savepath + '/' + md5imgname + '.jpg', 'jpeg')
        return {'fileName': md5imgname + '.jpg', 'codeValue': rndCode}
