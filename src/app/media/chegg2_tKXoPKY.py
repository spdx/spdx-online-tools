import pyautogui
from PIL import Image
import numpy as np
from time import sleep


# im = pyautogui.screenshot(region=(378,625, 200, 40))
# im.save('src.png')
# pix = np.array(im)
#
#

# print np.array_equal(np.array(pyautogui.screenshot(region=(186,446, 180, 26))),np.array(Image.open('search.png')))
i = 0
# while np.array_equal(np.array(pyautogui.screenshot(region=(378,625, 200, 40))),np.array(Image.open('src.png'))) == True:
#     sleep(0.2)
#     #print np.array_equal(np.array(pyautogui.screenshot(region=(186,446, 180, 26))),np.array(Image.open('search.png'))),i
#     i = i + 1
# print i
#
# # print pyautogui.locateOnScreen('search.png')
a = pyautogui.screenshot(region=(488, 610, 20, 20))
a.save("src.png")
#a.show()
while True:
    while np.array_equal(np.array(pyautogui.screenshot(region=(488, 610, 20, 20))), np.array(Image.open('src.png'))):
        sleep(0.5)
    print i
    i = i + 1
    pyautogui.moveTo(308,520,duration=0.1) #works 520
    pyautogui.click()
    #pyautogui.keyDown('pageup')
    pyautogui.moveTo(538,245,duration=0.3) # 585 230
    pyautogui.click()
    #pyautogui.keyDown('pageup')
    pyautogui.moveTo(525,545,duration=0.3) #519,535
    pyautogui.click()
    #pyautogui.keyDown('pageup')
    pyautogui.typewrite('Hey! I can help you with this. I am an expert on this. Ping me.', interval=0)
    pyautogui.moveTo(544,705,duration=0.3) #544, 700
    pyautogui.click()
    pyautogui.keyDown('pageup')
    pyautogui.moveTo(145,236,duration=0.1)
    pyautogui.click()
    pyautogui.keyDown('pageup')
    pyautogui.keyUp('pageup')
    sleep(5)
