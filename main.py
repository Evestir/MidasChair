import undetected_chromedriver as uc
from profiles import Profiles
from modes import Versions
from config import Config
from loguru import logger
from kkutu import Kkutu
from time import sleep

pegasus = None
midas = None
logger.debug("Initializing undetected-chromdriver...")
options = uc.ChromeOptions()
options.add_argument('--mute-audio')
driver = uc.Chrome(options=options, user_data_dir=Profiles.getPath(), use_subprocess=True)
if Config.VERSION == Versions.Korea:
    from Daemons.pegasus import Pegasus
    pegasus = Pegasus(driver)
    pegasus.start_running()
elif Config.VERSION == Versions.Io:
    from Daemons.midas import Midas
    midas = Midas(driver)
    midas.start_running()

while True:
    try:
        sleep(5)
    except KeyboardInterrupt:
        logger.info("Bye :)")
        if midas:
            midas.stop_running()
        elif pegasus:
            pegasus.stop_running()
        driver.quit()